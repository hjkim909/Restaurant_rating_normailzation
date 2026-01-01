import os
from dotenv import load_dotenv
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.naver_api import NaverPlaceAPI

load_dotenv()
client_id = os.getenv("NAVER_CLIENT_ID")
client_secret = os.getenv("NAVER_CLIENT_SECRET")

if not client_id:
    print("No keys")
    exit()

api = NaverPlaceAPI(client_id, client_secret)
# Request 50 items to check if it actually returns 50 or caps at 5
data = api.search_places("강남역 맛집", display=50)

if data and 'items' in data:
    items = data['items']
    print(f"Requested 50, Got {len(items)} items")
    if items:
        print(f"Sample Item: {items[0]['title']}")
        print(f"Mapx: {items[0].get('mapx')}, Mapy: {items[0].get('mapy')}")
else:
    print("No data")
