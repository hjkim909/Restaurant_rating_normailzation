from fastapi.testclient import TestClient
from fastapi_app.main import app
import json
import os

# Ensure env vars are loaded for TestClient
from dotenv import load_dotenv
load_dotenv()

client = TestClient(app)

def test_search():
    print("🧪 Testing /api/v1/search endpoint...")
    
    # Check if API keys are present
    if not os.getenv("NAVER_CLIENT_ID"):
        print("⚠️  No NAVER_CLIENT_ID found. Skipping actual API call logic might fail or return mock.")
    
    # Simple search
    response = client.get("/api/v1/search", params={"query": "강남역 맛집"})
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success! Found {data['total_count']} items.")
        if data['items']:
            first = data['items'][0]
            print(f"   First item: {first['title']} (Rating: {first.get('adjusted_rating')})")
            print(f"   Lunch Score: {first.get('lunch_score')}")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_search()
