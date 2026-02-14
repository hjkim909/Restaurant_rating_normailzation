# 🤖 AI Reference: Mechu (Lunch Menu Finder)

이 문서는 AI 에이전트(Claude, Gemini 등)가 이 프로젝트를 이해하고 작업을 이어받을 때 참고해야 할 **Single Source of Truth**입니다.

## 1. 프로젝트 개요 (Project Overview)
- **서비스명**: "Mechu" (구: 오늘 뭐 먹지?)
- **목표**: 결정 장애를 겪는 직장인을 위해 현재 위치 기반으로 '실제 먹을 수 있는' 점심 메뉴를 추천합니다.
- **핵심 철학**: Restaurant-First가 아닌 **Menu-First** 접근. (식당을 찾고 메뉴를 보는 게 아니라, 메뉴를 고르면 식당을 알려줌)
- **Live Demo**: (Render + Vercel 배포 예정)
- **신규 기능 (2026-01)**:
    - **장르 필터링**: "한식", "일식" 등 카테고리별 보기.
    - **랜덤 메뉴**: 결정 장애 해결을 위한 뽑기 기능.
    - **지도 보기**: 리스트와 지도를 오가는 하이브리드 UX (Kakao Maps).
- **신규 기능 (2026-02)**:
    - **SQLite 캐싱**: 동일 쿼리 24시간 캐싱으로 API 호출 절감.
    - **공유 기능**: Web Share API + 클립보드 복사로 식당 정보 공유.
    - **메뉴 뽑기**: 랜덤 메뉴 선택 → 해당 메뉴 가게 검색 연동.
    - **AI 상황 프리셋**: 혼밥/다이어트/해장 등 8개 빠른 선택 버튼.
    - **AI 추천 개선**: 상황 기반 검색 + 인원 수 설정(1~8명) 지원.
    - **Render/Vercel 마이그레이션**: AWS Lambda에서 Render + Vercel로 전환 (2026-02-14).

## 2. 기술 스택 (Tech Stack)
기존 Streamlit 모놀리식 → Serverless MSA → **Render + Vercel PaaS**로 전환되었습니다.

### Backend (`/fastapi_app`)
- **Framework**: FastAPI (Python 3.10)
- **Deployment**: **Render** Web Service (uvicorn 직접 실행)
- **Data Source**: Naver Search API (Primary), Kakao Local API (Secondary)
- **Caching**: SQLite (`mechu_cache.db`) - 동일 쿼리 24시간 캐싱으로 API 호출 절감
- **AI**: Gemini 1.5 Flash (Google Search Grounding) - 상황 기반 메뉴 추천

### Frontend (`/frontend`)
- **Framework**: React 18 (Vite)
- **Styling**: Tailwind CSS v4, Lucide React
    - **UI Theme**: Orange/Amber (식욕 자극 컬러).
    - **UX**: 가로 스크롤 필터, Snap interaction.
- **Maps**: `react-kakao-maps-sdk`
    - **Custom Marker**: 내 위치는 붉은 핀 대신 **Blue Dot (Pulsing)** 로 표시.
    - **Context Aware**: 랜덤 추천 시 모달 내부에 미니맵 표시.
- **Deployment**: **Vercel** (HTTPS 자동 제공 - Geolocation API 사용 위해 필수)

## 3. 핵심 구현 사항 및 컨텍스트 (Critical Context)

### ⚠️ 배포 환경 (Deployment Specifics)
2026-02-14부터 AWS Lambda가 아닌 **Render + Vercel** 조합으로 배포합니다.

1.  **의존성 관리**: 일반 `pip install -r requirements.txt`로 모든 의존성 설치. 더 이상 `vendor/` 디렉토리 수동 관리 불필요.
2.  **Render 배포**: `render.yaml` Blueprint 파일로 설정. GitHub 연동하여 push 시 자동 배포.
3.  **Vercel 배포**: `frontend/vercel.json`으로 SPA 설정. GitHub 연동.

### ⚠️ AI 모드 (Gemini) - 주의사항
- 사용 모델: `gemini-flash-latest` (Google Search Grounding 활용)
- **중요**: `GoogleSearch` Tool과 `response_mime_type="application/json"`은 **동시에 사용할 수 없음** (400 Error).
  - 해결: `_parse_json_from_text()` 헬퍼로 텍스트에서 JSON 수동 파싱.
- 역할: 네이버 플레이스 리뷰를 분석하여 "오늘 속이 안 좋아" 같은 상황에 맞는 메뉴 추천.

### 좌표계 이슈 (Coordinate System)
- **Naver Search API**: WGS84 좌표를 **10,000,000배(10^7)한 정수값** 반환.
    - `mapx: 1270292507` -> `127.0292507` (경도 E)
    - `mapy: 374997698` -> `37.4997698` (위도 N)
- 프론트엔드 지도에 표시할 때는 반드시 **10,000,000.0**으로 나누어야 합니다.

## 4. 아키텍처 및 로직 (Architecture & Logic)

### 데이터 흐름 (Data Flow)
1.  **Client (React)**: 사용자의 GPS 좌표 또는 선택된 역(강남역 등) 정보를 전송.
2.  **Render Web Service**: 요청 수신 (uvicorn → FastAPI).
3.  **Search Service**:
    - **Location Subdivision**: "강남역"을 ["강남역 1번출구", "강남역 CGV" ...] 로 세분화하여 검색.
    - **Category Explosion**: "한식", "중식", "일식" 등 카테고리별로 병렬 요청.
    - **Deduplication**: `(mapx, mapy, title)` 튜플을 키로 중복 제거.
4.  **Menu Extraction**: 식당 `category` 필드("한식>찌개,전골")를 파싱하여 메뉴 키워드 추출.
5.  **Response**: 추출된 메뉴 태그 클라우드 및 식당 리스트 반환.

### API 사용 규칙
- **Naver API**: 무료 티어 사용(일 25,000건). 호출 최소화를 위해 로컬 테스트 시 Mock Data 사용 권장.
- **Geolocation**: HTTPS가 아니면 브라우저에서 차단됨. 로컬(`localhost`)은 작동하나 배포 시 HTTPS 필수.

## 5. 명령어 가이드 (Commands)

### Frontend (Local)
```bash
cd frontend
npm install
npm run dev
```

### Backend (Local)
```bash
# 가상환경 활성화 상태에서
uvicorn fastapi_app.main:app --reload
```

### Deployment
- **백엔드**: Render 대시보드에서 GitHub 연동 → 자동 배포
- **프론트엔드**: Vercel 대시보드에서 GitHub 연동 → 자동 배포

## 6. 작업 히스토리 (Troubleshooting Log)
- **2026-01**: Streamlit -> React/FastAPI 마이그레이션 완료.
- **이슈**: Lambda `ImportError` (pydantic-core). **해결**: `vendor` 폴더에 `manylinux` 바이너리 수동 설치.
- **이슈**: 브라우저 Geolocation 차단. **해결**: CloudFront 도입.
- **2026-01 (Feature)**: 장르 필터, 랜덤 메뉴, 지도(Kakao Map) 통합 완료.
- **2026-02 (Performance)**: SQLite 캐싱 도입.
- **2026-02-14 (Migration)**: **AWS Lambda → Render/Vercel 마이그레이션**.
    - **원인**: `google-genai` 크로스 컴파일 문제 + Lambda 용량/타임아웃 제한 + GoogleSearch Tool 호환성 버그.
    - **해결**: AWS 인프라 전체 제거, Render(백엔드) + Vercel(프론트엔드)로 전환.
    - **상세**: [docs/MIGRATION_AWS_TO_RENDER.md](docs/MIGRATION_AWS_TO_RENDER.md) 참조.
    - **상태**: ✅ 코드 변경 완료, 배포 진행 중.

## 7. 주요 파일 구조
- `render.yaml`: Render 배포 Blueprint (백엔드).
- `frontend/vercel.json`: Vercel 배포 설정 (프론트엔드).
- `fastapi_app/`: 백엔드 로직.
- `frontend/`: 프론트엔드 로직.

## 8. 🚨 보안 가이드라인 (Security Protocol)
**이 프로젝트는 과거 AWS Key 유출 사고가 있었습니다. 아래 수칙을 엄격히 준수하세요.**

1.  **NO COMMIT**: `.env`, `.env.production` 등 자격 증명이 포함된 파일은 절대 커밋하지 마세요.
2.  **Pre-commit Hook 활성화**: `.git/hooks/pre-commit` 스크립트가 `.env` 파일 및 AWS Access Key 패턴을 자동 차단합니다.
3.  **환경 변수는 플랫폼 대시보드에서만 설정**: Render, Vercel 대시보드에서 환경 변수를 직접 설정합니다.

### 보안 사고 이력
| 날짜 | 내용 | 조치 |
|-----|-----|-----|
| 2026-01 (초) | AWS 키 유출로 `AWSCompromisedKeyQuarantine` 적용 | 키 재발급, AI.md에 보안 가이드라인 추가 |
| 2026-01-19 | 배포 중 키 차단 재발생 | 키 재발급, **pre-commit hook 설치** |
| 2026-02-03 | Google Gemini API Key 유출 (403 Error) | Key 재발급, `.env` 보안 상태 점검 |
| 2026-02-03 | GoogleSearch + JSON 호환성 이슈 (400 Error) | `_parse_json_from_text` 헬퍼로 수동 파싱 |
| 2026-02-14 | AWS 인프라 완전 제거 | Render + Vercel로 전환 |
