# AI 추천 모드 구현 완료 기록

**작업 일시**: 2026-01-13
**작업자**: Claude Sonnet 4.5 + User
**상태**: ✅ 로컬 테스트 완료, 배포 대기 중

---

## 📋 구현 완료 사항

### 1. Fast Mode / AI Mode 분리
- **Fast Mode** (기존): 즉시 메뉴 칩 표시 (카테고리 기반)
- **AI Mode** (신규): Gemini AI가 네이버 플레이스 리뷰를 분석하여 맞춤 추천

### 2. 핵심 기능
- ✅ AI/Fast 모드 토글 (사이드바)
- ✅ 대화형 컨텍스트 입력 ("오늘 속이 안 좋아" 등)
- ✅ Google Search grounding으로 실제 리뷰 자동 수집
- ✅ 병렬 처리 (ThreadPoolExecutor, 5-10개 레스토랑 분석)
- ✅ 신뢰도 점수 (긍정 리뷰 비율 기반)
- ✅ 추천 이유 + 리뷰 요약 제공
- ✅ 6시간 AI 캐싱 (SQLite)

### 3. 기술 스택
- **API**: Google Gemini API (`google-genai >= 1.47.0`)
- **모델**: `gemini-flash-latest` (10-30초 응답 목표)
- **검색**: Google Search tool integration
- **캐싱**: SQLite (`restaurant.db`, 6시간 유효)

---

## 📂 수정/생성된 파일

### 신규 파일
```
backend/gemini_service.py          # ~400 lines - 핵심 AI 서비스
docs/AI_MODE_IMPLEMENTATION.md     # 이 문서
```

### 수정된 파일
```
.env.example                       # GEMINI_API_KEY 추가
requirements.txt                   # google-genai>=1.47.0 추가
backend/db_manager.py              # AI 캐시 메서드 (get_ai_cache, save_ai_cache)
app.py                             # UI 통합 (토글, 컨텍스트, AI 처리 로직, 표시)
CLAUDE.md                          # AI Mode 섹션 추가
README.md                          # 주요 기능에 AI 모드 추가
```

---

## 🔧 기술적 세부사항

### backend/gemini_service.py 주요 구조
```python
class GeminiRecommendationService:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.model_name = 'gemini-flash-latest'
        self.search_tool = types.Tool(google_search=types.GoogleSearch())

    def analyze_restaurants_for_menu(
        restaurants: List[Dict],
        user_context: str = None,
        max_restaurants: int = 10
    ) -> Dict:
        # 1. 검색 쿼리 생성 (네이버 플레이스 [식당명] [주소] 리뷰)
        # 2. 병렬 분석 (ThreadPoolExecutor, 5 workers)
        # 3. 추천 집계 (메뉴별 언급 횟수, 감정 분석)
        # 4. 대화형 응답 생성 (user_context 기반)
```

### 중요 변경 이력
1. **API 마이그레이션**: `google-generativeai` (deprecated) → `google-genai`
2. **Tool 수정**: `google_search_retrieval` → `google_search`
3. **모델 업데이트**: `gemini-1.5-flash` → `gemini-flash-latest`

### app.py 통합 지점
- **Lines 95-125**: AI 모드 토글 + 컨텍스트 입력
- **Lines 177-183**: AI 세션 상태 초기화
- **Lines 288-336**: AI 처리 로직 (진행 표시 포함)
- **Lines 351-392**: AI 추천 결과 표시

---

## ✅ 테스트 결과

### 로컬 테스트 (2026-01-13)
```bash
# Import 테스트
✓ 모든 백엔드 모듈 import 성공
✓ GeminiRecommendationService 초기화 성공

# Streamlit 앱 실행
✓ 앱 시작 성공 (http://localhost:8501)
✓ 에러 없음

# Gemini API 테스트
✓ API 연결 성공
✓ 한국어 응답 정상 ("김치찌개는..." 테스트)
✓ Google Search 통합 확인 (15.3초, 1개 레스토랑)
✓ 추천 생성 성공 ("밥상정식/시골정식", 신뢰도 100%)
```

---

## 📝 Git 커밋 내역

```
62c5dfb - fix: Update Gemini model and tool configuration
4259701 - fix: Update Gemini API to use google-genai package
9e8ae1b - feat: Add AI recommendation mode with Gemini API integration
```

**Push 완료**: origin/main에 반영됨

---

## 🚀 다음 작업: Streamlit Cloud 배포

### 1. Streamlit Cloud 접속
- URL: https://share.streamlit.io/
- 리포지토리: `hjkim909/Restaurant_rating_normailzation`

### 2. Secrets 설정 (중요!)
Streamlit Cloud 대시보드 → 앱 설정 → Secrets에 추가:

```toml
GEMINI_API_KEY = "AIzaSyCX1z..." # 실제 API 키 입력

# 기존 키도 확인
NAVER_CLIENT_ID = "..."
NAVER_CLIENT_SECRET = "..."
KAKAO_REST_API_KEY = "..."
```

### 3. 배포 트리거
- 자동: Git push 시 자동 재배포
- 수동: Streamlit Cloud 대시보드에서 "Reboot app" 클릭

### 4. 배포 후 확인사항
- [ ] Fast Mode 동작 확인 (AI 토글 OFF)
- [ ] AI Mode 경고 확인 (API 키 없이 토글 시)
- [ ] AI Mode 동작 확인 (10-30초 후 추천 표시)
- [ ] 에러 로그 확인 (Streamlit Cloud 로그)

---

## 🔍 다음 세션에서 참조할 파일

### 작업 재개 시 반드시 읽어야 할 문서
1. **이 문서**: `docs/AI_MODE_IMPLEMENTATION.md` (전체 컨텍스트)
2. **플랜 파일**: `/Users/hyunjoon/.claude/plans/magical-baking-spark.md` (구현 계획)
3. **프로젝트 가이드**: `CLAUDE.md` (AI Mode 섹션 참조)

### 배포 관련 문서
- `docs/DEPLOYMENT.md` (기존 배포 가이드)
- `.env.example` (필요한 환경변수 목록)

### 코드 파일
- `backend/gemini_service.py` (AI 서비스 핵심 로직)
- `app.py` (UI 통합, lines 95-125, 288-336, 351-392)

### 트러블슈팅 시 참조
- `requirements.txt` (의존성 버전)
- Git 커밋 내역 (위 섹션 참조)

---

## ⚠️ 알려진 이슈 & 주의사항

### 1. Python 버전 경고
- 현재 Python 3.9 사용 중
- Google 패키지들이 EOL 경고 표시하지만 **정상 동작**
- 향후 Python 3.10+ 업그레이드 권장

### 2. Gemini API Rate Limits
- 무료 tier: 60 RPM, 1,500 RPD
- 현재 구현: 10개 레스토랑 × 1 요청 = 10 RPM 사용
- 캐싱(6시간)으로 대부분 커버됨

### 3. Google Search 속도
- 첫 요청: 15-30초 (실제 웹 검색)
- 캐시 히트: 즉시 응답
- 타임아웃 설정 없음 (필요시 추가)

### 4. Streamlit Cloud 메모리 제한
- 병렬 처리 워커: 5개로 제한됨
- 동시 분석 레스토랑: 10개로 제한됨
- 메모리 초과 시 워커 수 줄이기

---

## 💡 개선 아이디어 (향후)

### Phase 2 기능
- [ ] 스트리밍 응답 (부분 결과 실시간 표시)
- [ ] 멀티턴 대화 ("김치찌개에 대해 더 알려줘")
- [ ] 사용자 피드백 수집 (👍/👎)
- [ ] A/B 테스트 (Fast vs AI 사용률 추적)

### 성능 최적화
- [ ] 비동기 처리 (asyncio)
- [ ] 리뷰 임베딩 캐싱 (RAG 파이프라인)
- [ ] 응답 시간 메트릭 수집

---

## 📞 문제 발생 시

### AI 모드가 작동하지 않을 때
1. Streamlit Cloud Secrets에 `GEMINI_API_KEY` 설정 확인
2. 로그에서 "API key not found" 또는 "404 NOT_FOUND" 확인
3. 모델 이름 확인: `gemini-flash-latest` (변경 가능성)

### 에러 메시지별 해결법
- **429 RESOURCE_EXHAUSTED**: API quota 초과 → 24시간 대기 또는 유료 플랜
- **503 UNAVAILABLE**: 모델 과부하 → 다른 모델 시도 (`gemini-2.0-flash`)
- **400 INVALID_ARGUMENT**: Tool 설정 오류 → `google_search` 확인

---

## 📌 다음 세션 시작 프롬프트 예시

```
AI 추천 모드 구현 작업을 이어서 진행하려고 합니다.

다음 파일들을 읽어주세요:
1. docs/AI_MODE_IMPLEMENTATION.md (작업 기록)
2. /Users/hyunjoon/.claude/plans/magical-baking-spark.md (구현 계획)

현재 상황:
- 로컬 테스트 완료 (AI 모드 정상 작동)
- Git push 완료 (origin/main)
- Streamlit Cloud 배포 대기 중

다음 작업:
1. Streamlit Cloud에 GEMINI_API_KEY Secrets 추가
2. 배포 후 AI 모드 테스트
3. 에러 발생 시 디버깅

작업을 시작해주세요.
```

---

**작성 완료**: 2026-01-13
**다음 업데이트**: Streamlit Cloud 배포 완료 후
