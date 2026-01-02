from backend.db_manager import DatabaseManager
from backend.naver_api import NaverPlaceAPI
import os
import json
import sqlite3

def create_dummy_legacy_cache():
    data = {
        "test_query_migration": {
            "timestamp": 1234567890.0,
            "items": [{"title": "Legacy Item"}]
        }
    }
    with open("restaurant_cache.json", "w", encoding="utf-8") as f:
        json.dump(data, f)
    print("✅ Created dummy legacy cache file.")

def verify_migration():
    # Ensure no DB exists yet
    if os.path.exists("restaurant.db"):
        os.remove("restaurant.db")
        
    create_dummy_legacy_cache()
    
    # Initialize API (triggers migration)
    print("--- Initializing API (Triggers Migration) ---")
    api = NaverPlaceAPI("test_id", "test_secret")
    
    # Check DB content
    print("--- Verifying DB Content ---")
    db = DatabaseManager()
    cached = db.get_cache("test_query_migration")
    
    if cached and cached['items'][0]['title'] == "Legacy Item":
        print("✅ Migration Successful: Found legacy item in SQLite.")
    else:
        print("❌ Migration Failed: Item not found in DB.")
        
    # Check Backup
    if os.path.exists("restaurant_cache.json.bak"):
        print("✅ Backup file created.")
    else:
        print("❌ Backup file missing.")

def verify_rewrite():
    print("--- Verifying Read/Write ---")
    db = DatabaseManager()
    key = "new_query_test"
    data = {"items": [{"title": "New Item"}]}
    
    db.save_cache(key, data)
    
    loaded = db.get_cache(key)
    if loaded and loaded['items'][0]['title'] == "New Item":
        print("✅ Read/Write Successful.")
    else:
        print("❌ Read/Write Failed.")

if __name__ == "__main__":
    verify_migration()
    verify_rewrite()
