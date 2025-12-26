from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import ssl
import certifi

def get_address_from_coords(lat, lng):
    """
    Reverse geocode coordinates to a structured address.
    Returns a string like "역삼동" or "강남구 역삼동".
    """
    # Fix for SSL certificate errors on some environments
    ctx = ssl.create_default_context(cafile=certifi.where())
    geolocator = Nominatim(user_agent="lunch_picker_app", ssl_context=ctx)
    
    try:
        location = geolocator.reverse((lat, lng), exactly_one=True, language='ko')
        if location:
            address = location.raw['address']
            # Prioritize Dong -> Gu -> City
            dong = address.get('neighbourhood') or address.get('quarter') or address.get('suburb')
            if dong:
                return dong
            
            gu = address.get('city_district') or address.get('borough')
            if gu:
                return gu
                
            city = address.get('city') or address.get('town') or address.get('village')
            if city:
                return city
                
            return location.address.split(',')[0]
    except Exception as e:
        print(f"Geocoding Error: {e}")
        return None
    return None

def katech_to_wgs84(mapx, mapy):
    """
    Convert Naver's Search API coordinates to WGS84 (Lat, Lon).
    Based on observation, Naver Search API returns WGS84 * 10,000,000 as integers.
    e.g. Mapx: 1270292507 -> 127.0292507 (Lon)
         Mapy: 374997698 -> 37.4997698 (Lat)
    """
    try:
        if not mapx or not mapy: return None, None
        
        # Check format. If it looks like 127... then it's * 1e7.
        # If it looks like 300000, it's KATECH (old).
        # But our debug shows 127...!
        
        mx = float(mapx)
        my = float(mapy)
        
        # Simple heuristic check
        if mx > 120000000 and my > 30000000:
             lat = my / 10000000.0
             lon = mx / 10000000.0
             return lat, lon
        
        # If it's small (legacy KATECH ~300,000), we fail or try TM128?
        # For now, let's assume standard API behavior verified by debug_api.
        return None, None

    except Exception as e:
        print(f"Coord Conversion Error: {e}")
        return None, None

def calculate_distance(lat1, lon1, mapx, mapy):
    """
    Calculate distance in meters between WGS84 (lat1, lon1) and Naver KATECH (mapx, mapy).
    """
    from geopy.distance import geodesic
    
    lat2, lon2 = katech_to_wgs84(mapx, mapy)
    
    if lat2 is None:
        return 999999 # Return huge distance if conversion fails
             
    try:
        return geodesic((lat1, lon1), (lat2, lon2)).meters
    except:
        return 999999
