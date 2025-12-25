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
                
            city = address.get('city')
            if city:
                return city
                
            return location.address.split(',')[0]
    except Exception as e:
        print(f"Geocoding Error: {e}")
        return None
    return None
