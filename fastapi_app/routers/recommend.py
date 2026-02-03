from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from fastapi_app.services.ai_service import GeminiService
from fastapi_app.services.naver_service import NaverService

router = APIRouter()

# 상황별 검색 키워드 매핑
CONTEXT_KEYWORDS = {
    "혼밥": "혼밥 1인식사",
    "다이어트": "샐러드 건강식 저칼로리",
    "해장": "해장 국물요리",
    "회식": "회식 단체석",
    "데이트": "분위기 데이트",
    "가성비": "가성비 저렴한",
    "매운맛": "매운 불닭 매콤",
    "가볍게": "브런치 카페 간단한",
}

def extract_context_keyword(user_context: str) -> str:
    """사용자 상황에서 검색 키워드 추출"""
    context_lower = user_context.lower()
    
    for key, keyword in CONTEXT_KEYWORDS.items():
        if key in context_lower:
            return keyword
    
    # 인원 수 추출 (예: "4명", "5인")
    import re
    party_match = re.search(r'(\d+)\s*[명인]', user_context)
    if party_match:
        count = int(party_match.group(1))
        if count == 1:
            return "혼밥 1인식사"
        elif count <= 4:
            return "소모임"
        else:
            return "단체석 대형"
    
    return ""  # 키워드 없으면 빈 문자열


class AIRequest(BaseModel):
    user_context: str
    location: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    party_size: Optional[int] = None  # 인원 수 추가

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
    # 1. 상황 기반 검색 쿼리 생성
    context_keyword = extract_context_keyword(request.user_context)
    
    # 인원 수가 명시되면 키워드에 반영
    if request.party_size:
        if request.party_size == 1:
            context_keyword = "혼밥 1인식사"
        elif request.party_size <= 4:
            context_keyword = context_keyword or "소모임"
        else:
            context_keyword = "단체석 회식"
    
    # 검색 쿼리: "강남역 혼밥 맛집" 형태
    search_query = f"{request.location} {context_keyword} 맛집".strip()
    
    candidates = naver_service.search_places(
        search_query, 
        search_mode="popular",
        user_lat=request.lat,
        user_lng=request.lng
    )
    
    if not candidates:
        # 키워드 없이 재시도
        fallback_query = f"{request.location} 맛집"
        candidates = naver_service.search_places(
            fallback_query,
            search_mode="popular",
            user_lat=request.lat,
            user_lng=request.lng
        )
    
    if not candidates:
        return {"conversational_response": "주변에 맛집을 찾을 수 없어요.", "recommendations": []}

    # 2. AI 분석 (상황 + 인원 수 전달)
    full_context = request.user_context
    if request.party_size:
        full_context = f"{request.user_context} (인원: {request.party_size}명)"
    
    try:
        result = ai_service.analyze_restaurants_for_context(
            candidates,
            user_context=full_context,
            max_restaurants=8  # 더 많은 후보에서 선별
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
