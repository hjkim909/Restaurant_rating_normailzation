from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from fastapi_app.services.ai_service import GeminiService
from fastapi_app.services.naver_service import NaverService

router = APIRouter()

class AIRequest(BaseModel):
    user_context: str
    location: str
    lat: Optional[float] = None
    lng: Optional[float] = None

class AIResponse(BaseModel):
    conversational_response: str
    recommendations: List[dict]

def get_ai_service():
    return GeminiService()

def get_naver_service():
    return NaverService()

@router.post("/recommend", response_model=AIResponse)
async def recommend_menu(
    request: AIRequest,
    ai_service: GeminiService = Depends(get_ai_service),
    naver_service: NaverService = Depends(get_naver_service)
):
    # 1. Fetch Candidates (Naver Search)
    # Use context or just "popular" to fetch base candidates
    search_query = f"{request.location} 맛집"
    candidates = naver_service.search_places(
        search_query, 
        search_mode="popular",
        user_lat=request.lat,
        user_lng=request.lng
    )
    
    if not candidates:
        return {"conversational_response": "주변에 맛집을 찾을 수 없어요.", "recommendations": []}

    # 2. AI Analysis
    try:
        result = ai_service.analyze_restaurants_for_menu(
            candidates,
            user_context=request.user_context,
            max_restaurants=5 # Limit for speed
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
