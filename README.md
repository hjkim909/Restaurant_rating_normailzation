# 🍱 오늘 뭐 먹지? (Lunch Menu Picker)

**"맛집 찾기보다 메뉴 고르기가 더 힘든 당신을 위해"**

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://restaurantratingnormailzation-zjcarw4nbej4jgihurwnad.streamlit.app/)
👉 **[실시간 데모 바로가기](https://restaurantratingnormailzation-zjcarw4nbej4jgihurwnad.streamlit.app/)**

주변 식당 데이터를 실시간으로 분석하여, **지금 바로 먹을 수 있는 점심 메뉴**를 추천해주는 서비스입니다.

## 🎯 주요 기능
- **📍 주변 메뉴 스캔**: 현재 위치(강남/여의도 등) 근처 식당들의 메뉴를 자동으로 수집합니다.
- **🤖 AI 추천 모드** (NEW): Gemini AI가 네이버 플레이스 리뷰를 분석하여 맞춤 메뉴를 추천합니다.
  - 상황 기반 추천 ("오늘 속이 안 좋아" → 부드러운 메뉴 제안)
  - 리뷰 근거 제시 (왜 이 메뉴를 추천하는지 설명)
  - 신뢰도 점수 표시 (긍정 리뷰 비율 기반)
- **🎲 랜덤 메뉴 추천**: 결정 장애가 올 때, 버튼 하나로 메뉴를 정해드립니다.
- **👅 개인화 추천**: 싫어하는 음식(오이, 고수 등)은 빼고, 좋아하는 음식은 더 자주 나오게 설정할 수 있습니다.
- **🛰️ 스마트 반경 확장**: 500m 이내에 식당이 없으면 자동으로 1km, 2km까지 탐색 범위를 넓혀드립니다.
- **📊 실시간 데이터**: 네이버 검색 API를 사용하여 "지금 영업 중인" 가게들의 메뉴를 기반으로 추천합니다.

## 🛠 기술 스택
- **Language**: Python 3.9+
- **Frontend**: Streamlit
- **API**: Naver Search API (Local) + Kakao Local API
- **Database**: SQLite (캐싱)
- **Deployment**: [Streamlit Community Cloud](docs/DEPLOYMENT.md)

## 📂 프로젝트 구조
```bash
.
├── app.py # Legacy Main App (Streamlit)
├── backend/ # Legacy Backend Logic
├── fastapi_app/ # [NEW] Serverless Backend (FastAPI + Lambda)
│   ├── main.py
│   ├── routers/
│   └── services/
├── docs/ # 문서 (기획서, 배포 가이드 등)
└── requirements.txt
```

## 🏗️ 아키텍처 (Serverless Migration)
기존 Streamlit 모놀리식 구조에서 **Serverless MSA (Microservice Architecture)**로 마이그레이션이 진행 중입니다.

### 📅 프로젝트 진행 상황
- [x] **Phase 1: 백엔드 (FastAPI + Lambda)** - 완료 ✅
    - `NaverPlaceAPI` 및 데이터 로직 이식 완료.
    - `/api/v1/search`, `/api/v1/recommend` 엔드포인트 구축.
- [x] **Phase 2: 프론트엔드 (React + Vite)** - 완료 ✅
    - 모바일 퍼스트 반응형 UI 구현.
    - 위치 기반(GPS) 검색 및 스마트 반경 필터링 복구.
- [x] **Phase 3: AI 모드 (Gemini)** - 완료 ✅
    - Google Gemini 1.5 Flash 연동.
    - 상황 기반 메뉴 추천 및 대화형 UI 구현.
- [x] **Phase 4: UI/UX 개선** - 완료 ✅
    - 사용자 경험 중심의 디자인 리파인먼트.
- [ ] **Phase 5: 배포 (AWS Serverless)** - 진행 중 🚧
    - AWS 가입 및 키 발급 대기 중.

### Backend Structure
- **Stack**: FastAPI, AWS Lambda (via Mangum)
- **Data Source**: Naver Search API (Parallel Fetching + Subdivision Strategy)
- **Path**: `/fastapi_app`

### Frontend Structure
- **Stack**: React (Vite), Tailwind CSS v4, Lucide React
- **Path**: `/frontend`


## 🚀 시작하기

### 1. 설치 및 환경 설정
```bash
# 저장소 클론
git clone https://github.com/hjkim909/Restaurant_rating_normailzation.git
cd Restaurant_rating_normailzation

# 가상환경 생성 (선택)
python -m venv venv
source venv/bin/activate  # Mac/Linux
# venv\Scripts\activate  # Windows

# 의존성 설치
pip install -r requirements.txt
```

### 2. API 키 설정
**네이버 검색 API** (필수) 및 **카카오 로컬 API** (권장)가 필요합니다.

- **네이버**: [네이버 개발자 센터](https://developers.naver.com/) (`docs/Naver_API_Guide.md` 참조)
- **카카오**: [카카오 개발자](https://developers.kakao.com/) → 내 애플리케이션 → REST API 키

`.env` 파일을 생성하고 키를 입력합니다:
```bash
# 네이버 (필수)
NAVER_CLIENT_ID=your_naver_client_id
NAVER_CLIENT_SECRET=your_naver_client_secret

# 카카오 (선택, 하지만 권장 - 더 많은 식당 데이터)
KAKAO_REST_API_KEY=your_kakao_rest_api_key
```

💡 **Tip**: 두 API를 모두 사용하면 **2-3배 더 많은 식당** 데이터를 수집합니다!

### 3. 앱 실행
```bash
streamlit run app.py
```

## 📚 문서 가이드 (Documentation)

이 프로젝트의 문서는 목적에 따라 다음과 같이 구분되어 있습니다. 궁금한 내용이 있다면 해당 문서를 참고하세요.

### 🗺 프로젝트 개요 (General)
- **[PRD.md](docs/PRD.md)**: 기획서입니다. 프로젝트의 목표, 해결하려는 문제, 핵심 기능 정의가 담겨 있습니다.
- **[CLAUDE.md](CLAUDE.md)**: AI(Claude)를 위한 가이드지만, 프로젝트의 전체 아키텍처와 기술적 맥락을 이해하는 데 가장 유용합니다.

### 👩‍💻 개발 가이드 (For Developers)
- **[AGENTS.md](docs/AGENTS.md)**: 개발 에이전트들의 역할 정의(Architect, Designer 등)와 협업 프로세스입니다.
- **[CODE_REVIEW.md](docs/CODE_REVIEW.md)**: 자동화된 코드 리뷰 툴 사용법과 규칙입니다.
- **[AI_MODE_IMPLEMENTATION.md](docs/AI_MODE_IMPLEMENTATION.md)**: AI 추천 모드 구현 내역과 작업 로그입니다.

### ⚙️ 설치 및 배포 (Setup & Deploy)
- **[Naver_API_Guide.md](docs/Naver_API_Guide.md)**: 네이버 검색 API 발급 및 키 설정 방법입니다. 필수 과정입니다.
- **[Naver_API_Guide.md](docs/Naver_API_Guide.md)**: 네이버 검색 API 발급 및 키 설정 방법입니다. 필수 과정입니다.
- **[DEPLOYMENT.md](docs/DEPLOYMENT.md)**: AWS Serverless (Lambda + S3/CloudFront) 배포 가이드입니다.



## 📝 라이선스
MIT License
