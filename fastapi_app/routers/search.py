from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from fastapi_app.services.naver_service import NaverService
from fastapi_app.services.data_processing_service import DataProcessingService
from fastapi_app.models.schemas import SearchResponse

router = APIRouter()

def get_naver_service():
    return NaverService()

def get_data_service():
    return DataProcessingService()

@router.get("/search", response_model=SearchResponse)
async def search_restaurants(
    query: str = Query(..., min_length=2),
    sort: str = Query("comment", regex="^(comment|random)$"),
    naver_service: NaverService = Depends(get_naver_service),
    data_service: DataProcessingService = Depends(get_data_service)
):
    # 1. Fetch raw data
    raw_results = naver_service.search_places(query, search_mode=sort)
    
    # 2. Process data (normalize, analyze)
    processed_results = data_service.process_places(raw_results)
    
    return {
        "items": processed_results,
        "total_count": len(processed_results)
    }
