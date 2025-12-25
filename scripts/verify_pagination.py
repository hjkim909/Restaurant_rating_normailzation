import os
import time
from dotenv import load_dotenv
from backend.naver_api import NaverPlaceAPI

# Load .env
load_dotenv()
client_id = os.getenv("NAVER_CLIENT_ID")
client_secret = os.getenv("NAVER_CLIENT_SECRET")

if not client_id:
    print("Error: No API keys found.")
    exit()

api = NaverPlaceAPI(client_id, client_secret)

print("--- Testing 'Popular' Mode with Category Explosion ---")
start_time = time.time()
# This should internally fetch ~200 items by modifying query into sub-queries
result = api.search_places("개포4동 맛집", search_mode='popular')
items = result.get('items', [])
print(f"Total Items Fetched: {len(items)}")
print(f"Time Taken: {time.time() - start_time:.2f}s")

if len(items) > 100:
    print("✅ SUCCESS: Category Explosion working! Got significantly more than 5 items.")
else:
    print(f"⚠️ WARNING: Got {len(items)} items. Loop might not be effective or query is too narrow.")

print("\n--- Testing 'Hidden Gem' Mode ---")
result_random = api.search_places("개포4동 맛집", search_mode='random')
items_random = result_random.get('items', [])
print(f"Total Random Items: {len(items_random)}")
