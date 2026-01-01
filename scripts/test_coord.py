import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.geo_utils import calculate_distance, katech_to_wgs84

# Mock Data (Gangnam Station approx)
# Based on existing mock in app.py: mapx="314000", mapy="544000"
# Real Gangnam Station: 37.498, 127.027
# Let's check what 314000, 544000 maps to.

# Test multiple projections
from pyproj import Transformer

projections = {
    "EPSG:5179 (Korea Unified)": "epsg:5179",
    "EPSG:5174 (Old Korea Central)": "epsg:5174",
    "EPSG:2097 (Korean 1985)": "epsg:2097",
    "EPSG:5181 (Korea Central Belt 2010)": "epsg:5181",
    "EPSG:5178 (KATECH)": "epsg:5178" 
}
real_lat = 37.498085
real_lon = 127.027621

for name, epsg in projections.items():
    try:
        transformer = Transformer.from_crs(epsg, "epsg:4326")
        lat, lon = transformer.transform(314000, 544000)
        from geopy.distance import geodesic
        dist = geodesic((real_lat, real_lon), (lat, lon)).meters
        print(f"[{name}] -> {lat:.5f}, {lon:.5f} (Dist: {dist:.0f}m)")
    except Exception as e:
        print(f"[{name}] Failed: {e}")

