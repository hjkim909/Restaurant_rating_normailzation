# 배포 가이드

## 사전 요구사항
1.  **AWS CLI**: 설치 및 설정 완료 (`aws configure`).
2.  **Node.js & NPM**: 설치 완료.
3.  **Serverless Framework**: 설치 완료 (아래 참조).

## 0. AWS 개념 잡기 (초보자 가이드)

배포를 위해 **AWS 계정**이 반드시 필요합니다. (신규 가입 시 1년간 프리 티어 무료)

*   **AWS Lambda (서버)**: 
    *   **역할**: 요리사 👨‍🍳
    *   **설명**: 24시간 켜져 있는 서버가 아니라, 요청이 들어올 때만 실행되는 '함수'입니다. 비용이 매우 저렴합니다. FastAPI 백엔드 코드가 여기서 실행됩니다.
*   **Amazon S3 (스토리지)**:
    *   **역할**: 접시/메뉴판 🍽️
    *   **설명**: HTML, CSS, JS 같은 프론트엔드 파일들을 저장하는 창고입니다.
*   **이 두 가지를 사용하기 위해 '자격 증명(열쇠)'이 필요합니다.**

## 1. 백엔드 배포 (AWS Lambda)

Serverless Framework를 사용하여 FastAPI 앱을 배포합니다.

1.  **플러그인 및 도구 설치**:
    ```bash
    npm install -D serverless serverless-python-requirements
    ```

2.  **배포**:
    ```bash
    npx serverless deploy
    ```

3.  **API 엔드포인트 URL 확인**:
    배포 후 출력되는 엔드포인트 URL을 확인하세요 (예: `https://xyz.execute-api.ap-northeast-2.amazonaws.com/dev`).
    **이 URL을 복사해두세요.**

## 2. 프론트엔드 배포 (AWS S3 + CloudFront)

1.  **API URL 업데이트**:
    *   `frontend/.env.production` 파일을 생성합니다.
    *   `VITE_API_BASE_URL`을 위에서 복사한 Lambda 엔드포인트로 설정합니다.

2.  **빌드**:
    ```bash
    cd frontend
    npm run build
    ```

3.  **S3 배포** (버킷이 생성되어 있다고 가정):
    ```bash
    aws s3 sync dist/ s3://YOUR-BUCKET-NAME --acl public-read
    ```

4.  **CloudFront**:
    *   CloudFront가 S3 버킷을 가리키도록 설정합니다.
    *   도메인이 다른 경우 CORS 설정을 확인하세요.
