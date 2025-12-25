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
params = {
    "query": "강남역 맛집",
    "display": 100, # Requesting 100
    "start": 1,
    "sort": "comment"
}

response = requests.get(url, headers=headers, params=params)
if response.status_code == 200:
    data = response.json()
    items = data.get('items', [])
    print(f"Status: {response.status_code}")
    print(f"Items Count: {len(items)}")
    print(f"First Item: {items[0]['title'] if items else 'None'}")
else:
    print(f"Error: {response.status_code}")
    print(response.text)
