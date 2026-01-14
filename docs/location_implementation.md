# Location Search Implementation

## Backend
1. **Geo Service**: Port `geo_utils.py` to `fastapi_app/services/geo_service.py`.
   - `get_address_from_coords(lat, lng)` -> "Yeoksam-dong"
   - `calculate_distance(lat1, lon1, mapx, mapy)`
2. **Search Service**: Update `NaverService.search_places` to accept optional `lat, lng`.
   - If `lat, lng` present:
     - Get address.
     - Set query = f"{address} 맛집".
     - Fetch results.
     - **Filter** results by distance (Start 500m -> 1km -> 2km).
3. **API**: Update `/search` router.

## Frontend
1. **UI**: Add Loop/Location Icon button inside search bar or next to it.
2. **Logic**: `navigator.geolocation`.
3. **State**: Handle "Locating..." state.
