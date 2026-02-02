import sys
import os

# Add vendor directory to path for Lambda
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'vendor'))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from dotenv import load_dotenv
from fastapi_app.routers import search, recommend

load_dotenv()

app = FastAPI(
    title="Mechu API",
    description="API for finding lunch menus based on Naver Search results",
    version="1.0.0"
)

# CORS Configuration
# Note: allow_credentials=True와 origins=["*"]는 동시에 사용 불가
# 프로덕션에서는 credentials가 필요없으므로 False로 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router, prefix="/api/v1", tags=["search"])
app.include_router(recommend.router, prefix="/api/v1", tags=["recommend"])

@app.get("/")
async def root():
    return {"message": "Restaurant Menu Finder API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Lambda Handler
handler = Mangum(app)
