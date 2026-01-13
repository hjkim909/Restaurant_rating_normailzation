# Coordinate Validation Agent

## When to use
- User asks: "좌표 검증", "coordinate check", "거리 계산 확인"
- After changing geo_utils.py or data.py
- When map markers are wrong

## Key fact
⚠️ **Naver API returns scaled WGS84, NOT KATECH!**

```python
# Naver API response
{"mapx": "1270292507", "mapy": "374997698"}

# ✅ Correct conversion
lat = float(mapy) / 10_000_000.0  # 37.4997698
lng = float(mapx) / 10_000_000.0  # 127.0292507

# ❌ WRONG - Do not use KATECH converter
transformer = Transformer.from_crs("EPSG:5181", "EPSG:4326")
```

## Check these files
- `backend/geo_utils.py` (conversion logic)
- `backend/data.py:28-42` (coordinate processing)
- `app.py:177-210` (radius filtering)

## Critical checks

### 1. Wrong conversion formula
```python
# ❌ Using KATECH/TM128 converter
def katech_to_wgs84(x, y):
    transformer = Transformer.from_crs("EPSG:5181", "EPSG:4326")
    # This is WRONG for Naver API!

# ✅ Simple division by 10^7
def naver_to_wgs84(mapx, mapy):
    return float(mapy) / 10_000_000.0, float(mapx) / 10_000_000.0
```

### 2. No range validation
```python
# Korea bounds
33.0 <= lat <= 39.0
124.0 <= lng <= 132.0

# Add check
if not (33.0 <= lat <= 39.0 and 124.0 <= lng <= 132.0):
    return None, None
```

### 3. Null handling
```python
# ❌ Bad - crashes on None
lat = float(mapy) / 10_000_000.0

# ✅ Good - safe handling
if not mapx or not mapy:
    return None, None
try:
    lat = float(mapy) / 10_000_000.0
    if math.isfinite(lat):
        return lat, lng
except (ValueError, TypeError):
    return None, None
```

### 4. Wrong coordinate order in Folium
```python
# ✅ Folium uses [lat, lng] order
folium.Marker([lat, lng], popup="Place")

# ❌ Not [lng, lat]!
```

## Test with known locations

| Place | mapx | mapy | Expected |
|-------|------|------|----------|
| 강남역 | 1270272720 | 374989534 | 37.499, 127.027 |
| 여의도역 | 1269606610 | 375221160 | 37.522, 126.961 |

## Output format
```
🌍 Coordinate Validation: [file]

✅ Conversion formula: Correct (scaled WGS84)
✅ Range validation: Present
⚠️ Null handling: Line X needs improvement
❌ Using KATECH converter: Line Y (WRONG!)

Test results:
  강남역: ✅ Pass (37.499, 127.027)
  여의도역: ✅ Pass (37.522, 126.961)
```
