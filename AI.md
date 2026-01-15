# 🤖 AI Reference: 점심 메뉴 추천 서비스 (Lunch Menu Finder)

이 문서는 AI 에이전트가 이 프로젝트를 이해하고 작업을 이어받을 때 참고해야 할 핵심 정보를 담고 있습니다.

## 1. 프로젝트 개요
- **목표**: 현재 위치 또는 지정된 지역(예: 강남역) 주변의 맛집을 검색하고, 리뷰를 분석하여 점심 메뉴를 추천해주는 서비스.
- **주요 기능**:
    - 📍 **위치 기반 검색**: 네이버 검색 API를 활용한 맛집 데이터 수집.
    - 🧠 **AI 메뉴 추천**: 리뷰 데이터를 LLM(Gemini)으로 분석하여 메뉴 추천 (현재 MVP 배포를 위해 잠시 비활성화).
    - 🎲 **랜덤 추천**: 결정장애 해결을 위한 단순 랜덤 추천 기능.

## 2. 기술 스택 및 아키텍처
- **Frontend**: React, Vite, Tailwind CSS v4
- **Backend**: FastAPI (Python 3.10)
- **Database**: 현재 없음 (네이버 API 실시간 검색 + 인메모리 처리)
- **Deployment**: AWS Serverless (Lambda + API Gateway + S3 Website Hosting)

## 3. 핵심 구현 사항 (Critical Context)

### ⚠️ 배포 환경 (Deployment Specifics)
이 프로젝트는 **AWS Lambda** 환경에서 동작하며, 독특한 배포 설정을 가지고 있습니다. 수정 시 주의가 필요합니다.

1.  **의존성 관리 (Dependency Bundling)**:
    - `serverless-python-requirements` 플러그인의 자동 압축 기능이 크로스 플랫폼(Mac -> Linux) 문제로 실패했습니다.
    - **현재 해결책**: `vendor` 폴더에 Linux 호환(`manylinux2014_x86_64`) 바이너리를 직접 설치하여 포함시켰습니다.
    - `fastapi_app/main.py` 상단에 `sys.path.append('vendor')` 코드가 있어 이 폴더를 참조합니다.
    - **라이브러리 추가 시**: 단순히 `pip install` 하면 안 되고, 아래 명령어로 `vendor`에 설치해야 합니다.
      ```bash
      pip install --platform manylinux2014_x86_64 --target=vendor --implementation cp --python-version 3.10 --only-binary=:all: --upgrade <패키지명>
      ```

2.  **Python 버전**:
    - `Python 3.10` 런타임을 사용합니다. (Type Hint `|` 문법 지원을 위해 3.9에서 업그레이드됨)

3.  **AI 모드 (Gemini)**:
    - 현재 배포 용량 제한 및 초기 로딩 속도를 위해 `requirements-deploy.txt`에서 `google-genai` 라이브러리를 제외했습니다.
    - AI 기능을 다시 살리려면 의존성을 추가하고 Lambda 용량(250MB)을 관리해야 합니다.

## 4. 작업 히스토리 (Troubleshooting Log)
*2026-01-15 기준*

- **이슈**: Lambda에서 `ImportError: No module named 'fastapi'` 및 `pydantic-core` 로드 실패.
    - **원인**: Mac/Arm64 환경에서 설치한 바이너리가 AWS Lambda(Linux/x86)와 호환되지 않음.
    - **해결**: `vendor` 디렉토리에 Linux x86용 바이너리를 강제 설치하고 경로를 연결함.
- **이슈**: `SyntaxError` (Type Hint `|` 사용 불가) 및 `exceptiongroup` 누락.
    - **해결**: Lambda 런타임 Python 3.10으로 상향 조정 및 `exceptiongroup` 명시적 설치.
- **이슈**: "위치를 가져올 수 없습니다" (Geolocation API 차단).
    - **원인**: S3 웹 호스팅이 HTTP만 지원하여 브라우저 보안 정책에 걸림.
    - **해결 예정**: CloudFront를 연동하여 HTTPS를 지원해야 함.

## 5. 주요 파일 및 경로
- `serverless.yml`: 배포 설정 파일. (`vendor` 포함 방식, S3 동기화 설정 등)
- `fastapi_app/`: 백엔드 소스 코드.
- `frontend/`: 프론트엔드 소스 코드.
- `requirements-deploy.txt`: 배포용 경량화 패키지 목록.
