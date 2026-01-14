import requests

def test_cors():
    url = "http://localhost:8000/api/v1/search"
    headers = {
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "GET"
    }
    
    try:
        # Preflight OPTIONS check (Standard CORS behavior)
        resp = requests.options(url, headers=headers)
        print(f"OPTIONS Status: {resp.status_code}")
        print(f"Allow-Origin: {resp.headers.get('access-control-allow-origin')}")
        
        # Actual GET request
        resp2 = requests.get(url, params={"query": "test"}, headers=headers)
        print(f"GET Status: {resp2.status_code}")
        print(f"Allow-Origin: {resp2.headers.get('access-control-allow-origin')}")
        
        if resp2.headers.get('access-control-allow-origin') == 'http://localhost:5173':
            print("✅ CORS is working correctly.")
        else:
            print("❌ CORS header missing or incorrect.")
            
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    test_cors()
