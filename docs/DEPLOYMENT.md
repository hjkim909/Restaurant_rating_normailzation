# 🚀 배포 가이드 (Streamlit Community Cloud)

이 프로젝트를 인터넷에서 다른 사람들도 볼 수 있게 배포하는 가장 쉬운 방법은 **Streamlit Community Cloud**를 사용하는 것입니다. 무료이고, GitHub와 연동되어 매우 편리합니다.

## 1. 사전 준비 (필수)
- GitHub에 프로젝트가 업로드되어 있어야 합니다. (이미 완료하셨습니다! 👍)
- `requirements.txt` 파일이 있어야 합니다. (이미 있습니다!)

## 2. Streamlit Cloud에 가입
1. [share.streamlit.io](https://share.streamlit.io/) 에 접속합니다.
2. **"Continue with GitHub"** 버튼을 눌러 GitHub 계정으로 로그인합니다.

## 3. 앱 배포하기
1. 로그인 후 우측 상단의 **"New app"** 버튼 클릭.
2. **"Use existing repo"** 선택.
3. 설정 입력:
   - **Repository**: `hjkim909/Restaurant_rating_normailzation` (또는 해당 리포지토리 선택)
   - **Branch**: `main`
   - **Main file path**: `app.py`
4. **"Deploy!"** 버튼 클릭.

## 4. API 키 설정 (중요 🔑)
앱이 실행되려면 네이버 API 키가 필요합니다. 로컬에서는 `.env` 파일에 있었지만, 클라우드에서는 **Secrets** 기능으로 넣어줘야 합니다.

1. 배포가 시작되면(또는 완료된 앱 화면에서) 우측 하단 **"Manage app"** (또는 Settings 아이콘) 클릭.
2. **"Settings"** > **"Secrets"** 탭 클릭.
3. 아래 내용을 복사해서 붙여넣기 합니다 (본인의 실제 키로 변경하세요!):

```toml
NAVER_CLIENT_ID = "여러분의_Client_ID"
NAVER_CLIENT_SECRET = "여러분의_Client_Secret"
```

4. **"Save"** 버튼 클릭.
5. 앱이 자동으로 다시 시작(Reboot)됩니다.

## 5. 완료! 🎉
이제 상단 주소창의 URL (예: `https://lunch-picker.streamlit.app`)을 친구들에게 공유하면 됩니다.

---

### 주의사항
- **Sleep Mode**: 무료 버전은 오랫동안 접속이 없으면 잠자기 모드로 들어갑니다. 접속하면 깨어나는 데 시간이 조금 걸릴 수 있습니다.
- **Resource Limits**: 메모리 사용량이 너무 많으면 앱이 꺼질 수 있습니다. (현재 앱은 가벼워서 괜찮습니다)
