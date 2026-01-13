# API Security Agent

## When to use
- User asks: "API 보안 체크", "보안 검토", "security check"
- Before deployment
- After API integration changes

## Check these files
- `backend/naver_api.py`
- `backend/db_manager.py`
- `app.py` (API key usage)

## Critical checks

### 1. Hardcoded secrets
```python
# ❌ Bad
CLIENT_ID = "abc123xyz"

# ✅ Good
CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
if not CLIENT_ID:
    raise ValueError("API key not found")
```

### 2. SQL injection in cache
```python
# ❌ Bad - f-string in SQL
cursor.execute(f"SELECT * FROM cache WHERE key = '{key}'")

# ✅ Good - parameterized query
cursor.execute("SELECT * FROM cache WHERE key = ?", (key,))
```

### 3. HTTPS enforcement
```python
# ❌ Bad
base_url = "http://openapi.naver.com"

# ✅ Good
base_url = "https://openapi.naver.com"
```

### 4. XSS in Streamlit
```python
# ❌ Bad - user input with unsafe HTML
st.markdown(f"<div>{user_input}</div>", unsafe_allow_html=True)

# ✅ Good - sanitize first
clean = re.sub('<.*?>', '', user_input)
st.markdown(clean)
```

### 5. Secrets in cache
```python
# ❌ Bad - caching API keys
cache_data = {
    'items': items,
    'api_key': self.client_id  # Never!
}

# ✅ Good - only cache public data
cache_data = {
    'timestamp': time.time(),
    'items': items
}
```

## Output format
```
🔒 API Security Report: [file]

🔴 Critical (must fix):
  - Line X: [issue]
  - Fix: [suggestion]

🟡 Warnings:
  - Line Y: [issue]

🟢 Good practices:
  - [what's working well]

Risk Score: X/100
```

## Run automated scan (optional)
```bash
python scripts/agents/api_security_check.py backend/naver_api.py
```
