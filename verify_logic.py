
from backend.nlp import ReviewAnalyzer
from backend.data import DataProcessor
from backend.naver_api import NaverPlaceAPI

def test_nlp():
    print("Testing NLP...")
    analyzer = ReviewAnalyzer()
    
    # Test 1: Positive
    res1 = analyzer.analyze_reviews(["음식이 진짜 빨리 나와요. 회전율 대박"])
    assert res1['score'] > 50, f"Expected > 50, got {res1['score']}"
    assert "빠르다" in ' '.join(res1['keywords']) or "회전율" in ' '.join(res1['keywords']), "Keywords missing"
    
    # Test 2: Negative
    res2 = analyzer.analyze_reviews(["웨이팅 너무 길고 음식도 느리게 나옴"])
    assert res2['score'] < 50, f"Expected < 50, got {res2['score']}"
    
    print("NLP Test Passed")

def test_data_normalization():
    print("Testing Data Normalization...")
    processor = DataProcessor()
    
    places = [
        {"name": "A", "userRating": "4.5", "rating_float": 4.5},
        {"name": "B", "userRating": "3.5", "rating_float": 3.5}
    ]
    
    normalized = processor.normalize_ratings(places)
    # Avg = 4.0. A should be +0.5, B should be -0.5
    
    p1 = next(p for p in normalized if p['name'] == "A")
    p2 = next(p for p in normalized if p['name'] == "B")
    
    assert p1['rating_diff'] == 0.5, f"Expected 0.5, got {p1['rating_diff']}"
    assert p2['rating_diff'] == -0.5, f"Expected -0.5, got {p2['rating_diff']}"
    
    print("Data Normalization Test Passed")

def test_api_mock():
    print("Testing API Mock Handling...")
    # Intentionally bad keys
    api = NaverPlaceAPI("bad_id", "bad_secret")
    res = api.search_places("Test")
    assert res is None, "Should return None for bad auth"
    print("API Mock Test Passed")

def test_menu_recommender():
    print("Testing Menu Recommender...")
    from backend.menu_recommender import MenuRecommender
    recommender = MenuRecommender()
    
    places = [
        {"category": "한식>김치찌개", "lunch_score": 80},
        {"category": "한식,된장찌개", "lunch_score": 60},
        {"category": "일식>돈까스", "lunch_score": 90},
        {"category": "한식>김치찌개", "lunch_score": 70}, # Duplicate kimchi
        {"category": "카페", "lunch_score": 90} # Should be ignored by logic or stop words?
    ]
    
    top = recommender.extract_top_menus(places, top_n=3)
    # Expected: "김치찌개" (2), "돈까스" (1), "된장찌개" (1)
    
    assert "김치찌개" in top, f"Expected 김치찌개 in {top}"
    assert "카페" not in top, f"Expected 카페 to be ignored (if stop word) or just count check. Got {top}"
    
    print("Menu Recommender Test Passed")

def test_real_api_connection():
    import os
    from dotenv import load_dotenv
    from backend.naver_api import NaverPlaceAPI
    
    load_dotenv()
    client_id = os.getenv("NAVER_CLIENT_ID")
    client_secret = os.getenv("NAVER_CLIENT_SECRET")
    
    if not client_id or "your_client_id" in client_id:
        print("Skipping Real API Test: No valid keys in .env")
        return

    print("Testing Real Naver API Connection...")
    api = NaverPlaceAPI(client_id, client_secret)
    # Search for something simple
    result = api.search_places("강남역 맛집", display=1)
    
    if result and 'items' in result:
        print(f"Success! Found {len(result['items'])} items.")
        print(f"Sample: {result['items'][0]['title']}")
    else:
        print("Failed to fetch data from Naver API. Check keys or quota.")

if __name__ == "__main__":
    # test_nlp()
    # test_data_normalization()
    # test_api_mock()
    # test_menu_recommender()
    test_real_api_connection()
