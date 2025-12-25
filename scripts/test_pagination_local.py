import os
import requests
from dotenv import load_dotenv

load_dotenv()
client_id = os.getenv("NAVER_CLIENT_ID")
client_secret = os.getenv("NAVER_CLIENT_SECRET")

url = "https://openapi.naver.com/v1/search/local.json"
headers = {
    "X-Naver-Client-Id": client_id,
    "X-Naver-Client-Secret": client_secret
}

def fetch(start_val, sort_val):
    params = {
        "query": "강남역 맛집",
        "display": 5,
        "start": start_val,
        "sort": sort_val
    }
    resp = requests.get(url, headers=headers, params=params)
    if resp.status_code == 200:
        items = resp.json().get('items',[])
        if items:
            print(f"Sort={sort_val}, Start={start_val} -> First: {items[0]['title']}")
        else:
            print(f"Sort={sort_val}, Start={start_val} -> No items")
    else:
        print(f"Error: {resp.status_code}")

print("--- Testing sort='comment' ---")
fetch(1, 'comment')
fetch(6, 'comment')

print("\n--- Testing sort='random' ---")
fetch(1, 'random')
fetch(6, 'random')
