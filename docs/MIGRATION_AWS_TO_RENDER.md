# AWS → Render/Vercel 마이그레이션 기록

## 마이그레이션 일자
2026-02-14

## 배경 (Why)
기존 AWS Lambda + S3 + CloudFront 배포 구조에서 **AI 추천 기능이 작동하지 않는 문제**가 지속적으로 발생했습니다.

### 해결되지 않은 AWS 관련 이슈들
1. **`google-genai` 라이브러리 크로스 컴파일 문제**
   - Mac에서 `pip install --platform manylinux2014_x86_64 --target=vendor`로 설치해도 런타임 에러 발생
   - Lambda 환경의 250MB 패키지 크기 제한에 걸림
   
2. **Gemini API 호환성 버그**
   - `GoogleSearch` Tool과 `response_mime_type="application/json"`을 동시에 사용할 수 없음 (400 Error)
   - Lambda 타임아웃(기본 6초)으로 Gemini API 응답 시간 초과 빈번

3. **배포 파이프라인 복잡도**
   - `serverless-python-requirements` 플러그인 자동 압축 실패
   - `vendor/` 디렉토리 수동 관리 필요 (1,243개 파일)
   - CloudFront 캐시 무효화 필요

4. **AWS Key 유출 사고** (2회 발생)
   - `.env` 파일 관리 부주의로 API Key 노출

## 변경 사항 (What)

### 삭제된 파일/디렉토리
| 파일/디렉토리 | 역할 |
|------------|------|
| `serverless.yml` | AWS Lambda + API Gateway + S3 + CloudFront 배포 설정 |
| `vendor/` | Lambda용 Python 의존성 바이너리 (manylinux) |
| `.serverless/` | Serverless Framework 상태 파일 |
| `.requirements.zip` | Lambda 의존성 압축 파일 |
| `requirements-deploy.txt` | Lambda 배포 전용 의존성 목록 |
| `package.json` (루트) | Serverless Framework 플러그인용 |
| `package-lock.json` (루트) | 위와 동일 |
| `node_modules/` (루트) | Serverless Framework 플러그인 |

### 새로 추가된 파일
| 파일 | 역할 |
|-----|------|
| `render.yaml` | Render 백엔드 배포 Blueprint |
| `frontend/vercel.json` | Vercel 프론트엔드 배포 설정 |

### 수정된 파일
| 파일 | 변경 내용 |
|-----|---------|
| `fastapi_app/main.py` | Lambda 전용 코드(vendor path, Mangum) 제거 |
| `requirements.txt` | `mangum` 제거, `google-genai` 명시적 추가 |
| `fastapi_app/services/ai_service.py` | GoogleSearch + JSON 동시 사용 버그 수정 |

## 새로운 아키텍처 (After)
- **백엔드**: Render Web Service (FastAPI + uvicorn)
- **프론트엔드**: Vercel (React + Vite)
- 두 플랫폼 모두 무료 tier 사용, Git push 시 자동 배포
