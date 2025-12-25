import os
import requests
from dotenv import load_dotenv

load_dotenv()
client_id = os.getenv("NAVER_CLIENT_ID")
client_secret = os.getenv("NAVER_CLIENT_SECRET")

def debug_search():
    query = "강남역 맛집"
    base_url = "https://openapi.naver.com/v1/search/local.json"
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret
    }
    
    # Page 1
    params1 = {"query": query, "display": 5, "start": 1, "sort": "random"}
    res1 = requests.get(base_url, headers=headers, params=params1).json()
    items1 = res1.get('items', [])
    titles1 = [i['title'] for i in items1]
    print(f"Page 1 (Start 1, Random): Found {len(items1)} items")
    print(titles1)
    
    # Page 2
    params2 = {"query": query, "display": 5, "start": 6, "sort": "random"}
    res2 = requests.get(base_url, headers=headers, params=params2).json()
    items2 = res2.get('items', [])
    titles2 = [i['title'] for i in items2]
    print(f"\nPage 2 (Start 6, Random): Found {len(items2)} items")
    print(titles2)
    
    # Check overlap
    overlap = set(titles1) & set(titles2)
    print(f"\nOverlap: {overlap}")

if __name__ == "__main__":
    if not client_id:
        print("No keys found")
    else:
        debug_search()
