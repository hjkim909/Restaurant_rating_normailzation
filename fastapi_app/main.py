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
    title="Restaurant Menu Finder API",
    description="API for finding lunch menus based on Naver Search results",
    version="1.0.0"
)

# CORS Configuration
origins = [
    "http://localhost:3000", # React Local
    "http://localhost:8000", # API Local
    "http://localhost:5173", # Vite Local
    "*" # Allow all for MVP (S3, CloudFront)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
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
