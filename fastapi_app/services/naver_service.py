import requests
import time
import concurrent.futures
from typing import List, Dict, Any, Optional
from fastapi_app.core.config import get_settings
from fastapi_app.services.geo_service import GeoService
from fastapi_app.services.cache_service import CacheService

class NaverService:
    def __init__(self):
        self.settings = get_settings()
        self.geo_service = GeoService()
        self.cache = CacheService()
        self.base_url = "https://openapi.naver.com/v1/search/local.json"
        self.headers = {
            "X-Naver-Client-Id": self.settings.NAVER_CLIENT_ID,
            "X-Naver-Client-Secret": self.settings.NAVER_CLIENT_SECRET
        }

        self.location_subdivisions = {
            '강남역': ['강남역 1번출구', '강남역 11번출구', '역삼동 테헤란로'],
            '여의도역': ['여의도역 3번출구', '여의도 IFC몰', '여의도 국회의사당'],
            '판교역': ['판교역 1번출구', '판교 테크노밸리', '판교 알파돔시티'],
            '성수역': ['성수역 1번출구', '성수 카페거리', '뚝섬역 근처'],
            '을지로입구역': ['을지로입구역 1번출구', '명동 근처'],
            '역삼역': ['역삼역 1번출구', '역삼동 테헤란로'],
        }

        self.detailed_keywords = [
            '한식', '국밥', '삼겹살', '김치찌개', '된장찌개', 
            '중식', '짜장면', '마라탕', 
            '일식', '초밥', '돈까스', '라멘', 
            '양식', '파스타', '피자', '버거',
            '분식', '떡볶이', '김밥', '카페'
        ]

    def _fetch_page(self, query: str, sort: str = "comment", display_count: int = 5) -> List[Dict[str, Any]]:
        params = {
            "query": query,
            "display": display_count,
            "start": 1,
            "sort": sort
        }
        try:
            resp = requests.get(self.base_url, headers=self.headers, params=params)
            if resp.status_code == 200:
                data = resp.json()
                return data.get('items', [])
        except Exception as e:
            print(f"Error fetching {query}: {e}")
        return []

    def search_places(self, query: str, search_mode: str = "popular", user_lat: Optional[float] = None, user_lng: Optional[float] = None, optimize_for_ai: bool = False) -> List[Dict[str, Any]]:
        # 🔥 Cache Check
        cache_key = self.cache.generate_key(query + ("_ai" if optimize_for_ai else ""), user_lat, user_lng)
        cached_data = self.cache.get(cache_key)
        if cached_data is not None:
            print(f"🎯 Cache HIT for '{cache_key}'")
            return cached_data
        print(f"📡 Cache MISS for '{cache_key}' - calling Naver API")

        # 0. Reverse Geocoding if lat/lng provided but query is generic or empty
        # If user just sent lat/lng, we need to find "Where am I?"
        # But usually frontend sends "Gangnam Station" + lat/lng.
        # If query is empty or just "맛집", we MUST use coords.
        
        current_location_name = ""
        if user_lat and user_lng:
             address = self.geo_service.get_address_from_coords(user_lat, user_lng)
             if address:
                 current_location_name = address
                 # If query is generic, prepend location
                 if "맛집" not in query and not query.strip():
                     query = f"{address} 맛집"
                 elif query.strip() == "맛집":
                     query = f"{address} 맛집"
        
        # 1. Location Subdivision
        target_locations = [query]
        for major_loc, subdivisions in self.location_subdivisions.items():
            if major_loc in query:
                base_query = query.replace(major_loc, '{}')
                target_locations = [base_query.format(sub) for sub in subdivisions]
                break

        # 2. Category Explosion
        if optimize_for_ai:
            # AI 모드에서는 카테고리 폭발을 스킵하여 속도 최적화 (API 타임아웃 방지)
            target_keywords = ['']
        else:
            detected_categories = [k for k in self.detailed_keywords if k in query]
            target_keywords = detected_categories if detected_categories else self.detailed_keywords

        all_items = []
        seen_keys = set()
        
        display_cnt = 10 if optimize_for_ai else 5

        # Parallel Execution
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = []
            for loc in target_locations:
                for kw in target_keywords:
                    if kw in loc:
                        sub_query = loc
                    else:
                        sub_query = f"{loc} {kw}"
                    futures.append(executor.submit(self._fetch_page, sub_query, search_mode, display_cnt))
            
            for future in concurrent.futures.as_completed(futures):
                items = future.result()
                for item in items:
                    title_clean = item['title'].replace('<b>', '').replace('</b>', '')
                    unique_key = (item.get('mapx'), item.get('mapy'), title_clean)
                    
                    if unique_key not in seen_keys:
                        seen_keys.add(unique_key)
                        all_items.append(item)
        
        # 3. Smart Radius Filtering (The Core "Near Me" Logic)
        if user_lat and user_lng and all_items:
             # Radii to try: 500m -> 1km -> 2km
             radii = [500, 1000, 2000]
             filtered_items = []
             found_radius = None
             
             # Pre-calculate distances for efficiency
             items_with_dist = []
             for item in all_items:
                 dist = self.geo_service.calculate_distance(user_lat, user_lng, item.get('mapx'), item.get('mapy'))
                 item['distance'] = dist
                 items_with_dist.append(item)
             
             items_with_dist.sort(key=lambda x: x['distance']) # Sort by distance
             
             for r in radii:
                 temp = [item for item in items_with_dist if item['distance'] <= r]
                 if len(temp) >= 5: # Threshold to consider "enough results"
                     filtered_items = temp
                     found_radius = r
                     print(f"🎯 Found {len(temp)} items within {r}m radius.")
                     break
            
             # If we found a good subset, return it. 
             # If even 2km has < 5 items, users prefer seeing *something* over nothing, 
             # so we might return the 2km set or just fallback to everything sorted by distance.
             if filtered_items:
                 self.cache.set(cache_key, filtered_items)
                 return filtered_items
             else:
                 # Fallback: Just return everything sorted by distance
                 self.cache.set(cache_key, items_with_dist)
                 return items_with_dist

        self.cache.set(cache_key, all_items)
        return all_items
