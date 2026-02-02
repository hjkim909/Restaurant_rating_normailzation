# 🤖 AI Reference: Mechu (Lunch Menu Finder)

이 문서는 AI 에이전트(Claude, Gemini 등)가 이 프로젝트를 이해하고 작업을 이어받을 때 참고해야 할 **Single Source of Truth**입니다.

## 1. 프로젝트 개요 (Project Overview)
- **서비스명**: "Mechu" (구: 오늘 뭐 먹지?)
- **목표**: 결정 장애를 겪는 직장인을 위해 현재 위치 기반으로 '실제 먹을 수 있는' 점심 메뉴를 추천합니다.
- **핵심 철학**: Restaurant-First가 아닌 **Menu-First** 접근. (식당을 찾고 메뉴를 보는 게 아니라, 메뉴를 고르면 식당을 알려줌)
- **Live Demo**: (Serverless 배포 예정)
- **신규 기능 (2026-01)**:
    - **장르 필터링**: "한식", "일식" 등 카테고리별 보기.
    - **랜덤 메뉴**: 결정 장애 해결을 위한 뽑기 기능.
    - **지도 보기**: 리스트와 지도를 오가는 하이브리드 UX (Kakao Maps).

## 2. 기술 스택 (Tech Stack)
기존 Streamlit 모놀리식 구조에서 **Serverless MSA**로 완전히 전환되었습니다.

### Backend (`/fastapi_app`)
- **Framework**: FastAPI (Python 3.10)
- **Deployment**: AWS Lambda (Serverless Framework) via `mangum` adapter
- **Data Source**: Naver Search API (Primary), Kakao Local API (Secondary)
- **Caching**: SQLite (`/tmp/mechu_cache.db`) - 동일 쿼리 24시간 캐싱으로 API 호출 절감

### Frontend (`/frontend`)
- **Framework**: React 18 (Vite)
- **Styling**: Tailwind CSS v4, Lucide React
    - **UI Theme**: Orange/Amber (식욕 자극 컬러).
    - **UX**: 가로 스크롤 필터, Snap interaction.
- **Maps**: `react-kakao-maps-sdk`
    - **Custom Marker**: 내 위치는 붉은 핀 대신 **Blue Dot (Pulsing)** 로 표시.
    - **Context Aware**: 랜덤 추천 시 모달 내부에 미니맵 표시.
- **Deployment**: AWS S3 Website Hosting + CloudFront (HTTPS 필수 - Geolocation API 사용 위해)

## 3. 핵심 구현 사항 및 컨텍스트 (Critical Context)

### ⚠️ 배포 환경 (Deployment Specifics - DO NOT IGNORE)
이 프로젝트는 AWS Lambda 환경의 제약사항을 우회하기 위한 독특한 설정을 가지고 있습니다.

1.  **의존성 번들링 (Dependency Bundling)**:
    - `serverless-python-requirements` 플러그인의 자동 압축이 Mac -> Linux 크로스 컴파일 문제로 실패합니다.
    - **해결책**: `vendor/` 디렉토리에 Linux 호환(`manylinux2014_x86_64`) 바이너리를 직접 포함시켰습니다.
    - **중요**: 라이브러리 추가 시 단순히 `pip install` 하거나 `requirements.txt`에 넣으면 안 됩니다. 아래 명령어로 `vendor`에 설치해야 합니다.
      ```bash
      pip install --platform manylinux2014_x86_64 --target=vendor --implementation cp --python-version 3.10 --only-binary=:all: --upgrade <패키지명>
      ```
    - `fastapi_app/main.py` 상단에 `sys.path.append('vendor')` 코드가 있어 이 폴더를 참조합니다.

2.  **AI 모드 (Gemini)**:
    - 사용 모델: Gemini 1.5 Flash (Google Search Grounding 활용)
    - 역할: 네이버 플레이스 리뷰를 분석하여 "오늘 속이 안 좋아" 같은 상황에 맞는 메뉴 추천.
    - 상태: 현재 배포 용량 최적화를 위해 `google-genai` 라이브러리가 제외되어 있을 수 있습니다. 활성화 시 용량 모니터링 필수.

3.  **좌표계 이슈 (Coordinate System)**:
    - **Naver Search API**: `KATECH`나 `TM128`이 아닌, **WGS84 좌표를 1,000,0000배(10^7)한 정수값**을 반환합니다.
        - `mapx: 1270292507` -> `127.0292507` (경도 E)
        - `mapy: 374997698` -> `37.4997698` (위도 N)
    - 프론트엔드 지도(Naver Maps/Kakao Maps)에 표시할 때는 반드시 **10,000,000.0**으로 나누어야 합니다.

## 4. 아키텍처 및 로직 (Architecture & Logic)

### 데이터 흐름 (Data Flow)
1.  **Client (React)**: 사용자의 GPS 좌표 또는 선택된 역(강남역 등) 정보를 전송.
2.  **API Gateway -> Lambda**: 요청 수신.
3.  **Search Service**:
    - **Location Subdivision**: "강남역"을 ["강남역 1번출구", "강남역 CGV" ...] 로 세분화하여 검색 (커버리지 확대).
    - **Category Explosion**: "한식", "중식", "일식" 등 카테고리별로 병렬 요청 (다양성 확보).
    - **Deduplication**: `(mapx, mapy, title)` 튜플을 키로 중복 제거.
4.  **Menu Extraction**: 식당 `category` 필드("한식>찌개,전골")를 파싱하여 메뉴 키워드 추출.
5.  **Response**: 추출된 메뉴 태그 클라우드 및 식당 리스트 반환.

### API 사용 규칙
- **Naver API**: 무료 티어 사용(일 25,000건). 호출 최소화를 위해 로컬 테스트 시 Mock Data 사용 권장.
- **Geolocation**: HTTPS가 아니면 브라우저에서 차단됨. 로컬(`localhost`)은 작동하나 배포 시 CloudFront 필수.

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

### Deployment (Serverless)
```bash
# Frontend Build + Backend Deploy (Env vars loaded)
cd frontend && npm run build && cd .. && set -a; source .env; set +a; npx serverless deploy
```

## 6. 작업 히스토리 (Troubleshooting Log)
- **2026-01**: Streamlit -> React/FastAPI 마이그레이션 완료.
- **이슈**: Lambda `ImportError` (pydantic-core). **해결**: `vendor` 폴더에 `manylinux` 바이너리 수동 설치.
- **이슈**: 브라우저 Geolocation 차단. **해결**: CloudFront 도입 필요.
- **2026-01 (Feature)**: 장르 필터, 랜덤 메뉴, 지도(Kakao Map) 통합 완료.
- **이슈**: 배포 후 구버전이 보이는 **Ghost Cache** 현상.
    - **원인**: S3에는 최신 빌드가 업로드되지만 CloudFront가 구버전을 캐싱.
    - **해결**: `serverless-cloudfront-invalidate` 플러그인을 도입하여 배포 시 자동으로 `/index.html`과 `/assets/*`를 무효화하도록 설정.
    - **상태**: ✅ 해결 완료 (2026-01-15). 이제 `npx serverless deploy` 실행 시 자동으로 캐시 무효화됨.
- **이슈**: 배포 환경에서 Kakao 지도 로드 실패.
    - **원인**: CloudFront 도메인이 Kakao Developers Console에 등록되지 않음.
    - **해결**: 사이트 도메인에 CloudFront URL 추가 완료.
    - **상태**: ✅ 완료.
- **2026-01 (Workflow)**: 신규 기능 구현 및 배포를 위한 `/add-feature` 워크플로우를 정의함.
    - 브라우저 테스트 및 배포 절차 표준화.
    - 상태: ✅ 완료.
- **2026-01 (UI)**: 랜덤 메뉴 모달 UX 개선.
    - "다시 뽑기" 버튼 스타일 개선 (아이콘 + 배경색).
    - 식당 제목 클릭 시 네이버 지도 검색 페이지로 이동.
    - 지도 마커 인포윈도우 클릭 시 외부 지도 링크로 이동.
    - 상태: ✅ 완료.
- **2026-02 (Performance)**: SQLite 캐싱 도입.
    - `cache_service.py` 생성: 동일 쿼리 결과를 24시간 캐싱.
    - 캐시 히트 시 API 호출 스킵, 응답 시간 0.1초 미만.
    - 상태: ✅ 완료 (2026-02-02).

## 7. 주요 파일 구조
- `serverless.yml`: AWS 배포 설정 (가장 중요).
- `fastapi_app/`: 백엔드 로직.
- `frontend/`: 프론트엔드 로직.
- `vendor/`: Lambda용 Python 바이너리 (절대 삭제 금지).

## 8. 🚨 보안 가이드라인 (Security Protocol)
**이 프로젝트는 과거 AWS Key 유출 사고가 있었습니다. 아래 수칙을 엄격히 준수하세요.**

1.  **NO COMMIT**: `.env`, `.env.production`, `aws_config` 등 자격 증명이 포함된 파일은 절대 커밋하지 마세요.
    - 작업 전 `git status`로 `.env`가 추적되고 있는지 반드시 확인하세요.
    - 실수로 커밋했다면 즉시 해당 커밋을 되돌리고(`git reset`), API Key를 재발급받아야 합니다.
2.  **Pre-commit Hook 활성화** (2026-01-19 추가):
    - `.git/hooks/pre-commit` 스크립트가 설치되어 있습니다.
    - 이 훅은 `.env` 파일 및 AWS Access Key 패턴(`AKIA...`)이 커밋에 포함되면 **자동으로 차단**합니다.
    - 새 클론 시 자동 복사되지 않으므로, 팀원은 수동으로 설치해야 합니다.
3.  **키 노출 시 대처**:
    - 즉시 AWS IAM에서 해당 키를 `Deactivate` 및 `Delete` 처리합니다.
    - `AWSCompromisedKeyQuarantine` 정책이 붙었는지 확인하고 제거합니다.
4.  **로그 주의**: 터미널 출력이나 에러 로그에 API Key가 찍히지 않도록 주의하세요 (`grep` 등으로 검사 시 주의).

### 보안 사고 이력
| 날짜 | 내용 | 조치 |
|-----|-----|-----|
| 2026-01 (초) | AWS 키 유출로 `AWSCompromisedKeyQuarantine` 적용 | 키 재발급, AI.md에 보안 가이드라인 추가 |
| 2026-01-19 | 배포 중 키 차단 재발생 | 키 재발급, **pre-commit hook 설치** |
