
import os
import sys
import shutil

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.user_prefs import UserPreferences
from backend.menu_recommender import MenuRecommender

def test_user_prefs():
    print("Testing UserPreferences...")
    test_file = "test_prefs.json"
    prefs = UserPreferences(test_file)
    
    # Test Save
    prefs.save_preferences(["cucumber"], ["meat"])
    
    # Reload
    prefs2 = UserPreferences(test_file)
    assert "cucumber" in prefs2.get_dislikes()
    assert "meat" in prefs2.get_favorites()
    print("✅ Persistence works.")
    
    # Cleanup
    if os.path.exists(test_file):
        os.remove(test_file)

def test_recommender():
    print("Testing MenuRecommender...")
    rec = MenuRecommender()
    
    mock_places = [
        {"category": "한식>김치찌개"},
        {"category": "한식>오이소박이"}, # Should be filtered
        {"category": "일식>초밥"},     # Should be boosted
        {"category": "일식>초밥"},
        {"category": "중식>짜장면"}
    ]
    
    dislikes = ["오이"]
    favorites = ["초밥"]
    
    results = rec.extract_top_menus(mock_places, top_n=10, dislikes=dislikes, favorites=favorites)
    
    print(f"Results: {results}")
    
    assert "오이소박이" not in results, "Filtering failed: Found disliked item"
    # Note: Boosting increases probability/count, but with small sample and extract_top_menus returning list, 
    # we just check presence for now. Boosting logic makes '초밥' count high.
    assert "김치찌개" in results
    assert "초밥" in results
    
    print("✅ Filtering & Extraction works.")

if __name__ == "__main__":
    test_user_prefs()
    test_recommender()
