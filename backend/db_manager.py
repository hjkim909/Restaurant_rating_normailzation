import sqlite3
import json
import os
import time
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path="restaurant.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize the database schema."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # simple key-value store structure for caching
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS search_cache (
                    query_key TEXT PRIMARY KEY,
                    json_data TEXT,
                    created_at REAL
                )
            """)
            conn.commit()

    def get_cache(self, query_key, expiry_seconds=86400):
        """
        Retrieve cached data if it exists and hasn't expired.
        Returns dictionary or None.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT json_data, created_at FROM search_cache WHERE query_key = ?", (query_key,))
            row = cursor.fetchone()
            
            if row:
                json_data, created_at = row
                if time.time() - created_at < expiry_seconds:
                    try:
                        return json.loads(json_data)
                    except json.JSONDecodeError:
                        return None
                else:
                    # Optional: Clean up expired cache immediately? 
                    # For now, we just return None and let overwrite happen later.
                    return None
            return None

    def save_cache(self, query_key, data):
        """Save data to cache."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            json_str = json.dumps(data, ensure_ascii=False)
            cursor.execute("""
                INSERT OR REPLACE INTO search_cache (query_key, json_data, created_at)
                VALUES (?, ?, ?)
            """, (query_key, json_str, time.time()))
            conn.commit()

    def migrate_from_json(self, json_path):
        """One-time migration helper."""
        if not os.path.exists(json_path):
            return False, "JSON file not found"
            
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            count = 0
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                for key, value in data.items():
                    # Handle existing format where value might contain 'timestamp' and 'items'
                    # Or just check persistence logic
                    
                    # Based on existing code: value = { "timestamp": float, "items": [] }
                    ts = value.get('timestamp', time.time())
                    items = value.get('items', [])
                    
                    if items:
                        # We store the WHOLE value object to maintain compatibility with 'items' key expected by logic
                        # Or we could just store items. Let's look at how it's used.
                        # NaverPlaceAPI expects {"items": ...} return. 
                        # So we should store the whole structure or reconstruct it.
                        # Let's simple store the value as is.
                        
                        json_str = json.dumps(value, ensure_ascii=False)
                        cursor.execute("""
                            INSERT OR IGNORE INTO search_cache (query_key, json_data, created_at)
                            VALUES (?, ?, ?)
                        """, (key, json_str, ts))
                        count += 1
                conn.commit()
            
            # Rename old file to backup after successful migration
            backup_path = json_path + ".bak"
            os.rename(json_path, backup_path)
            return True, f"Migrated {count} entries. Original file backed up to {backup_path}"
            
        except Exception as e:
            return False, str(e)
