import os
import requests
import time
import logging
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
        
        # Setup logging
        logging.basicConfig(
            filename='api_usage.csv', 
            level=logging.INFO, 
            format='%(asctime)s,%(message)s'
        )
        self.logger = logging.getLogger('NaverAPI')

    def _get_headers(self):
        return {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret
        }

    def _log_request(self, endpoint, params, status):
        self.logger.info(f"{endpoint},{params},{status}")

    def _get_cache_key(self, endpoint, params):
        # Create a stable string representation of params for the key
        params_str = str(sorted(params.items()))
        return f"{endpoint}:{params_str}"

    def search_places(self, query, display=5):
        """
        Search for places using Naver Local Search API.
        """
        endpoint = self.base_url
        params = {
            "query": query,
            "display": display,
            "sort": "comment" # Sort by review count to get popular places
        }

        cache_key = self._get_cache_key("search", params)
        if cache_key in API_CACHE:
            cached_item = API_CACHE[cache_key]
            if time.time() - cached_item["timestamp"] < CACHE_DURATION:
                print(f"Cache hit for {query}")
                return cached_item["data"]

        headers = self._get_headers()
        
        try:
            response = requests.get(endpoint, headers=headers, params=params)
            self._log_request("search", params, response.status_code)
            
            if response.status_code == 200:
                data = response.json()
                # Store in cache
                API_CACHE[cache_key] = {
                    "data": data,
                    "timestamp": time.time()
                }
                return data
            elif response.status_code == 401:
                print("Error: Unauthorized. Check API keys.")
                return None
            elif response.status_code == 429:
                print("Error: Rate limit exceeded.")
                time.sleep(1) # simple backoff
                return None
            else:
                print(f"Error: {response.status_code} - {response.text}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Network error: {e}")
            return None

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
