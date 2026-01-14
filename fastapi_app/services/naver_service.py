import requests
import time
import concurrent.futures
from typing import List, Dict, Any
from fastapi_app.core.config import get_settings

class NaverService:
    def __init__(self):
        self.settings = get_settings()
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

    def _fetch_page(self, query: str, sort: str = "comment") -> List[Dict[str, Any]]:
        params = {
            "query": query,
            "display": 5,
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

    def search_places(self, query: str, search_mode: str = "popular") -> List[Dict[str, Any]]:
        # 1. Location Subdivision
        target_locations = [query]
        for major_loc, subdivisions in self.location_subdivisions.items():
            if major_loc in query:
                base_query = query.replace(major_loc, '{}')
                target_locations = [base_query.format(sub) for sub in subdivisions]
                break # Only handle one major location split

        # 2. Category Explosion
        # Filter keywords if the user query is already specific
        detected_categories = [k for k in self.detailed_keywords if k in query]
        target_keywords = detected_categories if detected_categories else self.detailed_keywords

        all_items = []
        seen_keys = set()
        
        # Parallel Execution
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = []
            for loc in target_locations:
                for kw in target_keywords:
                    # Construct sub-query
                    if kw in loc:
                        sub_query = loc
                    else:
                        sub_query = f"{loc} {kw}"
                    
                    futures.append(executor.submit(self._fetch_page, sub_query))
            
            for future in concurrent.futures.as_completed(futures):
                items = future.result()
                for item in items:
                    # Deduplication Key
                    # Clean title needed? Naver uses <b> tags.
                    title_clean = item['title'].replace('<b>', '').replace('</b>', '')
                    unique_key = (item.get('mapx'), item.get('mapy'), title_clean)
                    
                    if unique_key not in seen_keys:
                        seen_keys.add(unique_key)
                        all_items.append(item)
                        
        return all_items
