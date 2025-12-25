# 🍱 오늘 뭐 먹지? (Lunch Menu Picker)

**"맛집 찾기보다 메뉴 고르기가 더 힘든 당신을 위해"**

주변 식당 데이터를 실시간으로 분석하여, **지금 바로 먹을 수 있는 점심 메뉴**를 추천해주는 서비스입니다.

## 🎯 주요 기능
- **📍 주변 메뉴 스캔**: 현재 위치(강남/여의도 등) 근처 식당들의 메뉴를 자동으로 수집합니다.
- **🎲 랜덤 메뉴 추천**: 결정 장애가 올 때, 버튼 하나로 메뉴를 정해드립니다.
- **📊 실시간 데이터**: 네이버 검색 API를 사용하여 "지금 영업 중인" 가게들의 메뉴를 기반으로 추천합니다.

## 🛠 기술 스택
- **Language**: Python 3.9+
- **Frontend**: Streamlit
- **API**: Naver Search API (Local)
- **Deployment**: [Streamlit Community Cloud](docs/DEPLOYMENT.md)

## 📂 프로젝트 구조
```bash
.
├── app.py # 메인 애플리케이션 (Streamlit)
├── backend/ # 핵심 로직 (API, 데이터 처리)
├── docs/ # 문서 (기획서, 배포 가이드 등)
├── scripts/ # 테스트 및 유틸리티 스크립트
└── requirements.txt # 의존성 패키지
```

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
네이버 검색 API 키가 필요합니다. [네이버 개발자 센터](https://developers.naver.com/)에서 발급받으세요. (`docs/Naver_API_Guide.md` 참조)

`.env` 파일을 생성하고 키를 입력합니다:
```bash
NAVER_CLIENT_ID=your_id
NAVER_CLIENT_SECRET=your_secret
```

### 3. 앱 실행
```bash
streamlit run app.py
```

## 📝 라이선스
MIT License
