from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import ssl
import certifi

class GeoService:
    def __init__(self):
        # Fix for SSL certificate errors
        ctx = ssl.create_default_context(cafile=certifi.where())
        self.geolocator = Nominatim(user_agent="lunch_picker_app_v2", ssl_context=ctx)

    def get_address_from_coords(self, lat: float, lng: float) -> str | None:
        try:
            location = self.geolocator.reverse((lat, lng), exactly_one=True, language='ko')
            if location:
                address = location.raw['address']
                # Prioritize: Dong -> Gu -> City
                dong = address.get('neighbourhood') or address.get('quarter') or address.get('suburb')
                if dong: return dong
                
                gu = address.get('city_district') or address.get('borough')
                if gu: return gu
                
                city = address.get('city') or address.get('town')
                if city: return city
                
                return location.address.split(',')[0]
        except Exception as e:
            print(f"Geocoding Error: {e}")
            return None
        return None

    def katech_to_wgs84(self, mapx: str, mapy: str):
        try:
            if not mapx or not mapy: return None, None
            mx = float(mapx)
            my = float(mapy)
            # Naver Search API returns WGS84 * 10,000,000
            # e.g. 1270292507 -> 127.0292507
            if mx > 120000000:
                return my / 10000000.0, mx / 10000000.0
            return None, None
        except:
            return None, None

    def calculate_distance(self, lat1: float, lon1: float, mapx: str, mapy: str) -> float:
        try:
            lat2, lon2 = self.katech_to_wgs84(mapx, mapy)
            if lat2 is None: return 999999
            
            return geodesic((lat1, lon1), (lat2, lon2)).meters
        except:
            return 999999
