# 🍱 Mechu (Lunch Menu Picker)

**"맛집 찾기보다 메뉴 고르기가 더 힘든 당신을 위해"**

주변 식당 데이터를 실시간으로 분석하여, **지금 바로 먹을 수 있는 점심 메뉴**를 추천해주는 서비스입니다.

> 🚨 **NOTICE**: 이 프로젝트는 "오늘 뭐 먹지?"에서 **"Mechu"**로 리브랜딩되었습니다.

## 🎯 주요 기능
- **📍 주변 메뉴 스캔**: 현재 위치(강남/여의도 등) 근처 식당들의 메뉴를 자동으로 수집합니다.
- **🤖 AI 추천 모드**: Gemini AI가 네이버 플레이스 리뷰를 분석하여 "오늘 속이 안 좋아" 같은 상황에 맞는 메뉴를 추천해줍니다.
- **🎲 랜덤 메뉴 추천**: 결정 장애 해결을 위한 룰렛 기능.
- **🛰️ 스마트 반경 확장**: 결과가 없으면 자동으로 1km, 2km까지 탐색 범위를 넓힙니다.

## 🛠 기술 스택 (Modernized)
- **Frontend**: React 18, Vite, Tailwind CSS v4
- **Backend**: FastAPI, Python 3.10
- **Cloud**: AWS Lambda (Serverless Framework), API Gateway, S3 + CloudFront

[![Live Demo](https://img.shields.io/badge/demo-active-success)](https://d295iyxb2t8br9.cloudfront.net)

## 🚀 Live Demo
**[오늘 뭐 먹지? 바로가기](https://d295iyxb2t8br9.cloudfront.net)**
*(주의: AWS 비용 절감을 위해 서버가 잠시 중단되었을 수 있습니다.)*
## 🚀 시작하기 (Getting Started)

### 1. Backend (FastAPI)
```bash
# 가상환경 활성화
python -m venv venv
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# 로컬 실행
uvicorn fastapi_app.main:app --reload
```

### 2. Frontend (React)
```bash
cd frontend
npm install
npm run dev
```

### 3. 필수 환경 변수 (.env)
```bash
NAVER_CLIENT_ID=your_id
NAVER_CLIENT_SECRET=your_secret
KAKAO_REST_API_KEY=your_key
GEMINI_API_KEY=your_gemini_key
```

## 📚 문서 가이드
개발이나 AI 에이전트 작업을 위해서는 반드시 **[AI.md](AI.md)** 파일을 참고하세요. 프로젝트의 아키텍처, 배포 특이사항, API 스펙 등 모든 상세 내용이 정리되어 있습니다.

- **[AI.md](AI.md)**: 통합 개발 가이드 & AI Reference (필독)
- **[docs/PRD.md](docs/PRD.md)**: 기획서 및 요구사항
- **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)**: 배포 상세 가이드
