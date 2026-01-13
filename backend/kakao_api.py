import os
import requests
import time
import logging
from backend.db_manager import DatabaseManager


class KakaoPlaceAPI:
    """
    Kakao Local API client for place search.

    Advantages over Naver:
    - display=15 (vs Naver's 5)
    - Better pagination support
    - Free tier: 300,000 requests/day

    API Docs: https://developers.kakao.com/docs/latest/ko/local/dev-guide
    """

    def __init__(self, rest_api_key):
        self.rest_api_key = rest_api_key
        self.base_url = "https://dapi.kakao.com/v2/local/search/keyword.json"

        # Database Manager (shared with Naver API)
        self.db = DatabaseManager()

        # Setup logging
        logging.basicConfig(
            filename='api_usage.csv',
            level=logging.INFO,
            format='%(asctime)s,%(message)s'
        )
        self.logger = logging.getLogger('KakaoAPI')

    def _get_headers(self):
        return {
            "Authorization": f"KakaoAK {self.rest_api_key}"
        }

    def _log_request(self, endpoint, params, status):
        with open("api_usage.csv", "a", encoding='utf-8') as f:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            params_str = '&'.join(f"{k}={v}" for k, v in params.items())
            f.write(f"{timestamp},kakao,{endpoint},{params_str},{status}\n")

    def search_places(self, query, size=15, search_mode='popular', force_refresh=False):
        """
        Search for places using Kakao Local API.

        Args:
            query: Search query (e.g., "강남역 맛집")
            size: Results per page (max 15)
            search_mode: 'popular' (accuracy) or 'random' (ignored for Kakao)
            force_refresh: Bypass cache

        Returns:
            dict: {"items": [...]} in Naver-compatible format
        """
        import concurrent.futures

        # Construct Cache Key
        cache_key = f"kakao_{query}_{search_mode}_v1"

        # 1. Check DB Cache
        if not force_refresh:
            cached_entry = self.db.get_cache(cache_key)
            if cached_entry:
                print(f"✅ Kakao Cache Hit (SQLite) for '{cache_key}'")
                return {"items": cached_entry['items']}

        # 2. Category Explosion (same strategy as Naver, but with size=15)
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

        print(f"🟡 Kakao API: Fetching via Category Explosion ({len(detailed_keywords)} keywords)...")

        def fetch_category(keyword):
            # Construct sub-query
            if keyword in query:
                sub_query = query
            else:
                if '맛집' in query:
                    sub_query = query.replace('맛집', f'{keyword} 맛집')
                else:
                    sub_query = f"{query} {keyword}"

            # Kakao parameters
            # sort: 'accuracy' (정확도순) or 'distance' (거리순)
            # We use accuracy for "popular" mode
            params = {
                "query": sub_query,
                "size": size,  # Max 15
                "page": 1,     # Kakao uses page (1-based)
                "sort": "accuracy"
            }

            try:
                resp = requests.get(self.base_url, headers=self._get_headers(), params=params)
                self._log_request("search", params, resp.status_code)

                if resp.status_code == 200:
                    data = resp.json()
                    documents = data.get('documents', [])

                    # Convert Kakao format to Naver-compatible format
                    converted_items = []
                    for doc in documents:
                        item = {
                            'title': f"<b>{doc['place_name']}</b>",
                            'category': doc.get('category_name', '').split(' > ')[-1],  # Get last category
                            'address': doc.get('address_name', ''),
                            'roadAddress': doc.get('road_address_name', ''),
                            'mapx': str(int(float(doc['x']) * 10000000)),  # Convert to scaled WGS84 format
                            'mapy': str(int(float(doc['y']) * 10000000)),
                            'description': doc.get('category_name', ''),
                            'telephone': doc.get('phone', ''),
                            'link': doc.get('place_url', ''),
                            'source': 'kakao'  # Mark source
                        }
                        converted_items.append(item)

                    return converted_items
            except Exception as e:
                print(f"Kakao API Error: {e}")
                pass
            return []

        # Parallel fetch
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(fetch_category, kw) for kw in detailed_keywords]

            for future in concurrent.futures.as_completed(futures):
                items = future.result()
                for item in items:
                    # Clean title for deduplication
                    title_clean = item['title'].replace('<b>', '').replace('</b>', '')
                    unique_key = (item.get('mapx'), item.get('mapy'), title_clean)

                    if unique_key not in seen_keys:
                        seen_keys.add(unique_key)
                        all_items.append(item)

        print(f"  -> Kakao: Aggregated {len(all_items)} unique restaurants")

        # 3. Save to Cache
        cache_data = {
            "timestamp": time.time(),
            "items": all_items
        }
        self.db.save_cache(cache_key, cache_data)

        return {"items": all_items}


if __name__ == "__main__":
    # Test stub
    from dotenv import load_dotenv
    load_dotenv()

    rest_api_key = os.getenv("KAKAO_REST_API_KEY")

    if rest_api_key:
        api = KakaoPlaceAPI(rest_api_key)
        result = api.search_places("강남역 맛집")
        print(f"Found {len(result['items'])} places")
    else:
        print("No Kakao API key found in .env")
