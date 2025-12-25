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

class NaverPlaceAPI:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://openapi.naver.com/v1/search/local.json"
        
        # Persistent Cache File
        self.cache_file = "restaurant_cache.json"
        self._load_file_cache()

        # Setup logging (kept for general class logging, though _log_request now writes directly)
        logging.basicConfig(
            filename='api_usage.csv', 
            level=logging.INFO, 
            format='%(asctime)s,%(message)s'
        )
        self.logger = logging.getLogger('NaverAPI')

    def _load_file_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.file_cache = json.load(f)
            except Exception as e:
                print(f"Error loading cache file: {e}. Initializing empty cache.")
                self.file_cache = {}
        else:
            self.file_cache = {}

    def _save_file_cache(self):
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.file_cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Failed to save cache: {e}")

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
        Uses 'Category Explosion' strategy: querying many specific keywords in parallel
        to overcome the API's 'display=5' per request limit.
        force_refresh: If True, ignore existing cache and fetch fresh data.
        """
        import concurrent.futures
        
        # Construct Cache Key
        cache_key = f"{query}_{search_mode}_v3" # v3 for clean concurrent strategy
        
        # 1. Check File Cache (Skip if force_refresh is True)
        if not force_refresh and cache_key in self.file_cache:
            cached_entry = self.file_cache[cache_key]
            if time.time() - cached_entry['timestamp'] < 86400:
                print(f"✅ Local Cache Hit for '{cache_key}'")
                return {"items": cached_entry['items']}
            else:
                print(f"⚠️ Cache expired for '{cache_key}', re-fetching...")

        # 2. Category Explosion Strategy
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
        
        print(f"📡 Fetching live data via Category Explosion ({len(detailed_keywords)} keywords) for '{query}'...")
        
        def fetch_category(keyword):
            # Construct sub-query
            # If query already contains keyword, skip appending to avoid redundancy if meaningful?
            # E.g. query="강남역 국밥 맛집" and keyword="국밥" -> "강남역 국밥 맛집"
            if keyword in query:
                sub_query = query
            else:
                # Insert keyword before '맛집' if possible, or just append
                if '맛집' in query:
                    sub_query = query.replace('맛집', f'{keyword} 맛집')
                else:
                    sub_query = f"{query} {keyword}"
            
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
            # If user already specified "Samsun Gukbap", we probably shouldn't search "Pizza".
            # But the user might want "similar" things? 
            # The current App logic passes "Location + Category" to query.
            # If user selected "Korean", query is "Gangnam Korean".
            # Then we should only use Korean keywords?
            # Refining target_keywords based on typical categories might be too complex for this single file.
            # Let's just SEARCH ALL. The results for "Gangnam Korean Pizza" will likely be empty or auto-corrected by Naver.
            # We rely on Naver's smartness.
            pass

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            future_to_keyword = {executor.submit(fetch_category, kw): kw for kw in target_keywords}
            
            for future in concurrent.futures.as_completed(future_to_keyword):
                items = future.result()
                for item in items:
                    # Clean title for key
                    title_clean = item['title'].replace('<b>', '').replace('</b>', '')
                    unique_key = (item.get('mapx'), item.get('mapy'), title_clean)
                    
                    if unique_key not in seen_keys:
                        seen_keys.add(unique_key)
                        all_items.append(item)
        
        print(f"  -> Aggregated {len(all_items)} unique items.")

        # 3. Save to Cache
        self.file_cache[cache_key] = {
            "timestamp": time.time(),
            "items": all_items
        }
        self._save_file_cache()
        
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
