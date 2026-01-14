from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    NAVER_CLIENT_ID: str
    NAVER_CLIENT_SECRET: str
    KAKAO_REST_API_KEY: str | None = None
    GEMINI_API_KEY: str | None = None
    
    class Config:
        env_file = ".env"
        extra = "ignore"

@lru_cache()
def get_settings():
    return Settings()
