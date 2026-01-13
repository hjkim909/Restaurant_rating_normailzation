import os
import requests
import time
import logging
import json
from datetime import datetime
import os
from urllib.parse import quote

# Simple in-memory cache
# Format: { "endpoint:params_hash": { "data": response_json, "timestamp": time.time() } }
API_CACHE = {}
CACHE_DURATION = 3600  # 1 hour

from backend.db_manager import DatabaseManager

class NaverPlaceAPI:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://openapi.naver.com/v1/search/local.json"
        
        # Database Manager
        self.db = DatabaseManager()
        
        # Legacy Migration
        legacy_cache = "restaurant_cache.json"
        if os.path.exists(legacy_cache):
             print("📦 Migrating legacy JSON cache to SQLite...")
             success, msg = self.db.migrate_from_json(legacy_cache)
             print(f"Migration result: {msg}")

        # Setup logging (kept for general class logging, though _log_request now writes directly)
        logging.basicConfig(
            filename='api_usage.csv', 
            level=logging.INFO, 
            format='%(asctime)s,%(message)s'
        )
        self.logger = logging.getLogger('NaverAPI')

    # File cache methods removed in favor of DB
    
    def _get_headers(self):
        return {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret
        }

    def _get_headers(self):
        return {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret
        }

    def _log_request(self, endpoint, params, status):
        # This now writes directly to the CSV, bypassing the standard logging setup for this specific log.
        with open("api_usage.csv", "a", encoding='utf-8') as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Convert params dict to a string for logging
            params_str = '&'.join(f"{k}={v}" for k, v in params.items())
            f.write(f"{timestamp},{endpoint},{params_str},{status}\n")

    # _get_cache_key is no longer needed as the file cache uses the query directly as a key.
    # def _get_cache_key(self, endpoint, params):
    #     # Create a stable string representation of params for the key
    #     # params_str = str(sorted(params.items()))
    #     # return f"{endpoint}:{params_str}"
    def _fetch_items_with_pagination(self, query, max_items=30):
        """
        Fetch items using pagination because Naver Local API limits display=5.
        Loops until max_items is reached or no more items.
        """
        all_items = []
        start = 1
        display_per_req = 5 # Fixed limit by Naver
        
        while len(all_items) < max_items:
            params = {
                "query": query,
                "display": display_per_req,
                "start": start,
                "sort": "comment"
            }
            
            headers = self._get_headers()
            try:
                response = requests.get(self.base_url, headers=headers, params=params)
                self._log_request("search_page", params, response.status_code)
                
                if response.status_code == 200:
                    data = response.json()
                    items = data.get('items', [])
                    if not items:
                        print(f"  Start: {start} -> No items returned.")
                        break # No more data
                        
                    print(f"  Start: {start} -> Got {len(items)} items. First: {items[0]['title']}")
                    all_items.extend(items)
                    start += display_per_req
                    time.sleep(0.05) # Polite delay
                else:
                    break
            except Exception as e:
                print(f"Pagination Error: {e}")
                break
                
        return all_items
    def search_places(self, query, display=5, search_mode='popular', force_refresh=False):
        """
        Search for places with persistent caching and deduplication.
        Uses 'Category Explosion' + 'Location Subdivision' strategy:
        - Subdivides major locations into smaller areas
        - Queries many specific keywords in parallel
        - Overcomes API's 'display=5' per request limit
        force_refresh: If True, ignore existing cache and fetch fresh data.
        """
        import concurrent.futures

        # Construct Cache Key
        cache_key = f"{query}_{search_mode}_v4" # v4 with location subdivision
        
        # 1. Check DB Cache (Skip if force_refresh is True)
        if not force_refresh:
            cached_entry = self.db.get_cache(cache_key)
            if cached_entry:
                print(f"✅ Local Cache Hit (SQLite) for '{cache_key}'")
                return {"items": cached_entry['items']}
            else:
                 pass # Cache miss or expired

        # 2. Location Subdivision Strategy
        # Subdivide major locations into smaller areas for better coverage
        location_subdivisions = {
            '강남역': ['강남역 1번출구', '강남역 10번출구', '강남역 11번출구', '강남역 CGV', '강남역 신논현역 사이', '역삼동 테헤란로', '역삼동 강남대로'],
            '여의도역': ['여의도역 1번출구', '여의도역 3번출구', '여의도 IFC몰', '여의도 공원', '여의도 증권가', '여의도 국회의사당'],
            '판교역': ['판교역 1번출구', '판교 테크노밸리', '판교 알파돔시티', '판교역 현대백화점', '삼평동'],
            '성수역': ['성수역 1번출구', '성수역 2번출구', '성수 카페거리', '성수동 서울숲', '뚝섬역 근처'],
            '을지로입구역': ['을지로입구역 1번출구', '을지로입구역 롯데백화점', '을지로2가', '을지로3가', '명동 근처'],
            '역삼역': ['역삼역 1번출구', '역삼역 7번출구', '역삼동 강남대로', '역삼동 논현로', '역삼동 테헤란로'],
            '오목교역': ['오목교역 1번출구', '오목교역 2번출구', '목동 근처', '양평동']
        }

        # Detect if query contains a major location
        target_locations = [query]  # Default: use original query
        for major_loc, subdivisions in location_subdivisions.items():
            if major_loc in query:
                # Replace major location with subdivisions
                base_query = query.replace(major_loc, '{}')
                target_locations = [base_query.format(sub_loc) for sub_loc in subdivisions]
                print(f"🗺️  Location subdivision detected: {major_loc} → {len(subdivisions)} sub-locations")
                break

        # 3. Category Explosion Strategy
        # Naver Local Search limits 'display' to 5 and 'start' parameter is unreliable.
        # Solution: Query many detailed keywords to aggregate unique results.

        detailed_keywords = [
            # Korean
            '한식', '국밥', '해장국', '삼겹살', '갈비', '곱창', '족발', '보쌈', '김치찌개', '된장찌개', '백반', '냉면', '칼국수',
            # Chinese
            '중식', '짜장면', '짬뽕', '탕수육', '마라탕', '양꼬치',
            # Japanese
            '일식', '초밥', '스시', '돈까스', '라멘', '우동', '이자카야', '덮밥',
            # Western
            '양식', '파스타', '피자', '스테이크', '브런치', '버거', '샐러드',
            # Asian / Others
            '아시안', '쌀국수', '타코', '카레',
            # Snack / Cafe
            '분식', '떡볶이', '김밥', '치킨', '카페', '디저트', '베이커리'
        ]
        
        all_items = []
        seen_keys = set()

        print(f"📡 Fetching live data via Location Subdivision ({len(target_locations)} locations) × Category Explosion ({len(detailed_keywords)} keywords)...")

        def fetch_category(location_query, keyword):
            # Construct sub-query
            # If query already contains keyword, skip appending to avoid redundancy
            if keyword in location_query:
                sub_query = location_query
            else:
                # Insert keyword before '맛집' if possible, or just append
                if '맛집' in location_query:
                    sub_query = location_query.replace('맛집', f'{keyword} 맛집')
                else:
                    sub_query = f"{location_query} {keyword}"
            
            # Param Logic based on Mode
            sort_method = "comment"
            if search_mode == 'random':
                sort_method = "random" 
            
            params = {
                "query": sub_query,
                "display": 5, # Limit is 5
                "start": 1, 
                "sort": sort_method
            }
            
            try:
                resp = requests.get(self.base_url, headers=self._get_headers(), params=params)
                if resp.status_code == 200:
                    return resp.json().get('items', [])
            except:
                pass
            return []

        # Use ThreadPool to fetch fast
        # Only trigger explosion if query is generic (e.g. contains "맛집") or user explicitly wants variety.
        # If user queried "강남역 스시", we probably shouldn't search for "Pork Belly".
        # Heuristic: If query matches one of detailed_keywords, ONLY search that + related?
        # For simplicity in this implementation (Category Explosion), we assume the user WANTS variety if they are using this app.
        # However, if query is specific, we might get irrelevant results.
        # Let's filter: if query contains a category, only search that.
        
        target_keywords = detailed_keywords
        
        # Check if query contains any of the keywords
        detected_categories = [k for k in detailed_keywords if k in query]
        if detected_categories:
            # Hybrid Search Strategy:
            # If the user specifically asks for "Samsun Gukbap", we focus our limited API calls 
            # on "Korean", "Gukbap" related keywords rather than spending quota on "Pizza".
            
            # However, we must be careful. If user asks "Gangnam delicious places", detected is empty -> Search All.
            # If user asks "Gangnam Date", detected is empty -> Search All.
            # If user asks "Gangnam Pizza", detected is ["Pizza"] -> Search only Pizza related.
            
            print(f"🎯 Precise Query Detected: Found categories {detected_categories}. Improving efficiency.")
            
            # Filter target_keywords to only include those that are RELEVANT to the detected categories.
            # Simple approach: Only search for the detected specific keywords? 
            # Better approach: If specific keyword is found, search that AND related broad categories.
            # But our `detailed_keywords` list is flat.
            
            # Let's just narrow down to the detected ones to be strictly efficient as per request.
            target_keywords = detected_categories

        # Execute parallel fetch for all location × keyword combinations
        with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
            futures = []
            for loc in target_locations:
                for kw in target_keywords:
                    futures.append(executor.submit(fetch_category, loc, kw))

            for future in concurrent.futures.as_completed(futures):
                items = future.result()
                for item in items:
                    # Clean title for key
                    title_clean = item['title'].replace('<b>', '').replace('</b>', '')
                    unique_key = (item.get('mapx'), item.get('mapy'), title_clean)

                    if unique_key not in seen_keys:
                        seen_keys.add(unique_key)
                        all_items.append(item)

        print(f"  -> Aggregated {len(all_items)} unique restaurants from {len(target_locations)} locations × {len(target_keywords)} keywords = {len(target_locations) * len(target_keywords)} queries")

        # 3. Save to Cache
        cache_data = {
            "timestamp": time.time(),
            "items": all_items
        }
        self.db.save_cache(cache_key, cache_data)
        
        return {"items": all_items}

    # Note: Naver Search API doesn't provide full review texts directly in the listing.
    # We might need a separate way to get detailed reviews if the basic search result isn't enough.
    # However, for the MVP scope FR-2, we need reviews. 
    # Since official Search API only returns 'description' and 'link', 
    # getting "latest 10 reviews" usually requires crawling or a more specific map API which might not be open.
    # For this MVP, we will try to use the 'description' field if available, 
    # or simulate/mock detailed review fetching if the Search API is too limited, as crawling is flaky.
    # Let's start with basic search results.

if __name__ == "__main__":
    # Test stub
    from dotenv import load_dotenv
    load_dotenv()
    
    client_id = os.getenv("NAVER_CLIENT_ID")
    client_secret = os.getenv("NAVER_CLIENT_SECRET")
    
    if client_id and client_secret:
        api = NaverPlaceAPI(client_id, client_secret)
        # result = api.search_places("강남역 맛집")
        # print(result)
    else:
        print("No keys found in .env")
