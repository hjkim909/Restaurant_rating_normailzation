"""
SQLite Cache Service for Mechu API

캐시 데이터를 SQLite에 저장하여 동일 쿼리 시 API 호출을 줄입니다.
Lambda 환경에서는 캐시 실패 시에도 정상 동작하도록 예외 처리됩니다.
"""
import sqlite3
import json
import time
from typing import Optional, List, Dict, Any


class CacheService:
    """SQLite 기반 캐시 서비스 (Graceful Degradation 지원)"""

    # Lambda 환경에서는 /tmp만 쓰기 가능
    DB_PATH = "/tmp/mechu_cache.db"
    TTL_SECONDS = 86400  # 24시간

    def __init__(self):
        self._enabled = True
        try:
            self._init_db()
        except Exception as e:
            print(f"⚠️ Cache initialization failed: {e}. Running without cache.")
            self._enabled = False

    def _init_db(self):
        """데이터베이스 및 테이블 초기화"""
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cache_key TEXT UNIQUE NOT NULL,
                data TEXT NOT NULL,
                created_at REAL NOT NULL
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_cache_key ON cache(cache_key)
        """)
        conn.commit()
        conn.close()

    def generate_key(self, query: str, lat: Optional[float], lng: Optional[float]) -> str:
        """캐시 키 생성 (위도/경도 소수점 3자리 반올림)"""
        lat_key = f"{lat:.3f}" if lat else "none"
        lng_key = f"{lng:.3f}" if lng else "none"
        return f"{query.strip().lower()}_{lat_key}_{lng_key}"

    def get(self, cache_key: str) -> Optional[List[Dict[str, Any]]]:
        """캐시에서 데이터 조회. 실패 시 None 반환."""
        if not self._enabled:
            return None
        
        try:
            conn = sqlite3.connect(self.DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT data, created_at FROM cache WHERE cache_key = ?",
                (cache_key,)
            )
            row = cursor.fetchone()
            conn.close()

            if row is None:
                return None

            data_json, created_at = row
            age = time.time() - created_at

            if age > self.TTL_SECONDS:
                self._delete(cache_key)
                return None

            return json.loads(data_json)
        except Exception as e:
            print(f"⚠️ Cache get failed: {e}")
            return None

    def set(self, cache_key: str, data: List[Dict[str, Any]]) -> None:
        """데이터를 캐시에 저장. 실패해도 예외를 발생시키지 않음."""
        if not self._enabled:
            return
        
        try:
            conn = sqlite3.connect(self.DB_PATH)
            cursor = conn.cursor()
            data_json = json.dumps(data, ensure_ascii=False)
            created_at = time.time()
            cursor.execute("""
                INSERT INTO cache (cache_key, data, created_at)
                VALUES (?, ?, ?)
                ON CONFLICT(cache_key) DO UPDATE SET
                    data = excluded.data,
                    created_at = excluded.created_at
            """, (cache_key, data_json, created_at))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"⚠️ Cache set failed: {e}")

    def _delete(self, cache_key: str) -> None:
        """만료된 캐시 삭제"""
        try:
            conn = sqlite3.connect(self.DB_PATH)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cache WHERE cache_key = ?", (cache_key,))
            conn.commit()
            conn.close()
        except Exception:
            pass
