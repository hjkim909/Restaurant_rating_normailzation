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
    #     params_str = str(sorted(params.items()))
    #     return f"{endpoint}:{params_str}"

    def search_places(self, query, display=5, search_mode='popular'):
        """
        Search for places with persistent caching and deduplication.
        search_mode: 'popular' (review count) or 'random' (similarity + variety)
        """
        
        # Construct Cache Key
        cache_key = f"{query}_{search_mode}"
        
        # 1. Check File Cache
        if cache_key in self.file_cache:
            cached_entry = self.file_cache[cache_key]
            # Expire after 24 hours (86400 seconds)
            if time.time() - cached_entry['timestamp'] < 86400:
                print(f"✅ Local Cache Hit for '{cache_key}'")
                return {"items": cached_entry['items']}
            else:
                print(f"⚠️ Cache expired for '{cache_key}', re-fetching...")

        # 2. Fetch from API with Category Expansion
        # Simply paging with 'start' yields duplicates often.
        # Strategy: Iterate through categories to get variety.
        categories = ["한식", "양식", "일식", "중식", "분식", "고기", "카페"]
        
        all_items = []
        seen_keys = set() 
        
        print(f"📡 Fetching live data via Category Expansion for '{query}'...")
        
        for cat in categories:
            # Construct sub-query, e.g. "강남역 맛집 한식"
            # If query already contains category (e.g. "강남역 한식"), just run once.
            if cat in query:
                sub_query = query
            else:
                sub_query = f"{query} {cat}"
                
            req_size = 100
            
            # Param Logic based on Mode
            sort_method = "comment"
            start_idx = 1
            
            if search_mode == 'random':
                import random
                sort_method = "random" # 'random' is Naver's Accuracy/Similiarity sort
                # Mix it up: sometimes get page 1, sometimes page 2 (start=101)
                # Since req_size is 100, next page is 101.
                start_idx = random.choice([1, 1, 101]) 
            
            params = {
                "query": sub_query,
                "display": req_size,
                "start": start_idx, 
                "sort": sort_method
            }
            
            headers = self._get_headers()
            try:
                response = requests.get(self.base_url, headers=headers, params=params)
                self._log_request("search", params, response.status_code)
                
                if response.status_code == 200:
                    data = response.json()
                    items = data.get('items', [])
                    
                    for item in items:
                        # Clean title for key
                        title_clean = item['title'].replace('<b>', '').replace('</b>', '')
                        unique_key = (item.get('mapx'), item.get('mapy'), title_clean)
                        
                        if unique_key not in seen_keys:
                            seen_keys.add(unique_key)
                            all_items.append(item)
                    
                    time.sleep(0.05) 
            except Exception as e:
                print(f"Network Error: {e}")
            
            # If original query was specific (e.g. "강남역 한식"), no need to iterate others
            if cat in query:
                break
        
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
