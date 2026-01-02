import pytest
import sys
import os

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.geo_utils import katech_to_wgs84, calculate_distance

def test_katech_to_wgs84_valid():
    # Helper: Naver API "KATECH" which is actually WGS84 * 1e7 based on the code analysis
    # mapx: 1270292507 -> 127.0292507 (Lon)
    # mapy: 374997698 -> 37.4997698 (Lat)
    
    mapx = "1270292507"
    mapy = "374997698"
    
    lat, lon = katech_to_wgs84(mapx, mapy)
    
    assert lat == 37.4997698
    assert lon == 127.0292507

def test_katech_to_wgs84_invalid_inputs():
    assert katech_to_wgs84(None, None) == (None, None)
    assert katech_to_wgs84("", "") == (None, None)

def test_katech_to_wgs84_legacy_small_numbers():
    # The code explicitly checks for > 120000000 for x and > 30000000 for y
    # Small numbers (like real KATECH ~300,000) should return None, None as per current fallback logic
    lat, lon = katech_to_wgs84("300000", "500000")
    assert lat is None
    assert lon is None

def test_calculate_distance_valid():
    # Location 1: Gangnam Station approx
    lat1 = 37.4979
    lon1 = 127.0276
    
    # Location 2: A bit away (using the long int format)
    # 37.4997698, 127.0292507
    mapx = "1270292507"
    mapy = "374997698"
    
    dist = calculate_distance(lat1, lon1, mapx, mapy)
    
    # Distance should be reasonable (e.g., within 500m for these close points)
    assert dist is not None
    assert 0 < dist < 1000

def test_calculate_distance_invalid_target():
    # If target is invalid, it returns 999999
    lat1 = 37.4979
    lon1 = 127.0276
    
    dist = calculate_distance(lat1, lon1, None, None)
    assert dist == 999999
