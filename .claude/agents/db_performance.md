# DB Performance Agent

## When to use
- User asks: "DB 성능", "캐시 효율", "쿼리 최적화"
- When app is slow
- Before adding new DB queries

## Check these files
- `backend/db_manager.py`
- `backend/naver_api.py` (caching logic)

## Critical checks

### 1. N+1 query problem
```python
# ❌ Bad - query in loop
for item in items:
    cache = db.get_cache(item.id)  # N queries!

# ✅ Good - bulk query
ids = [item.id for item in items]
caches = db.get_caches_bulk(ids)  # 1 query
```

### 2. Missing index
```sql
-- Current schema
CREATE TABLE search_cache (
    query_key TEXT PRIMARY KEY,  -- ✅ Indexed
    json_data TEXT,
    created_at REAL              -- ⚠️ Not indexed
)

-- Add index for cleanup queries
CREATE INDEX idx_created_at ON search_cache(created_at);
```

### 3. No transaction batching
```python
# ❌ Bad - multiple commits
for key, value in data.items():
    db.save_cache(key, value)  # Commits each time!

# ✅ Good - batch commit
with sqlite3.connect(db_path) as conn:
    for key, value in data.items():
        cursor.execute("INSERT OR REPLACE ...", (key, value))
    conn.commit()  # Once
```

### 4. Large JSON in cache
```python
# Check: What's being cached?
cache_data = {
    'items': items,  # All fields or minimal?
    'timestamp': time.time()
}

# Consider: Cache only needed fields
minimal = [{
    'title': item['title'],
    'category': item['category'],
    'mapx': item['mapx'],
    'mapy': item['mapy']
} for item in items]
```

## Performance tests

### Measure cache speedup
```python
import time

# Cold start
start = time.time()
api.search_places("강남역", force_refresh=True)
cold = time.time() - start

# Warm start
start = time.time()
api.search_places("강남역")
warm = time.time() - start

speedup = cold / warm  # Should be 50x+
```

### Check DB size
```python
import os
size_mb = os.path.getsize("restaurant.db") / (1024 * 1024)
# Warning if > 100MB
```

## Quick wins

1. **Add created_at index**
```python
cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON search_cache(created_at)")
```

2. **Periodic cleanup**
```python
def cleanup_old_cache():
    cutoff = time.time() - 86400  # 24h
    cursor.execute("DELETE FROM search_cache WHERE created_at < ?", (cutoff,))
```

3. **VACUUM after cleanup**
```python
conn.execute("VACUUM")  # Reclaim space
```

## Output format
```
🗄️ DB Performance Report

Schema:
  ✅ PRIMARY KEY on query_key (indexed)
  ⚠️ created_at not indexed (add for cleanup queries)

Queries:
  ✅ Using parameterized queries
  ❌ Line X: N+1 query in loop

Cache stats:
  DB size: 12.5 MB
  Expected speedup: 50-100x

Recommendations:
  1. Add created_at index
  2. Implement cleanup scheduler
  3. Consider caching minimal fields only
```
