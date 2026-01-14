from pydantic import BaseModel
from typing import List, Optional

class Restaurant(BaseModel):
    title: str
    link: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    telephone: Optional[str] = None
    address: Optional[str] = None
    roadAddress: Optional[str] = None
    mapx: Optional[str] = None
    mapy: Optional[str] = None
    userRating: Optional[str] = None # Naver returns string usually
    
    # Processed fields
    lat: Optional[float] = None
    lng: Optional[float] = None
    rating_float: Optional[float] = None
    adjusted_rating: Optional[float] = None
    rating_diff_str: Optional[str] = None
    lunch_score: Optional[float] = None
    lunch_keywords: List[str] = []
    sentiment: Optional[str] = None

class SearchResponse(BaseModel):
    items: List[Restaurant]
    total_count: int
