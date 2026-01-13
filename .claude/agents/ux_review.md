# UX Review Agent

## When to use
- User asks: "UX 리뷰", "사용자 경험", "UI 개선"
- Before deployment
- After UI changes

## Philosophy
> "사용자는 고민 없이 밥을 먹으러 가야 한다"

Goal: 결정 장애 해결. UX는 단순하고 직관적이어야 함.

## Check these files
- `app.py` (main UI)

## Critical checks

### 1. Loading feedback
```python
# ❌ Bad - silent loading
data = api.search_places(query)

# ✅ Good - show spinner
with st.spinner("📡 식당 스캔 중..."):
    data = api.search_places(query)
```

### 2. Error messages
```python
# ❌ Bad - technical error
st.error(f"HTTPError 429: Too Many Requests")

# ✅ Good - user-friendly
st.error("잠시 후 다시 시도해주세요 (요청이 많습니다)")
```

### 3. Empty state
```python
# ❌ Bad - blank screen
if not items:
    pass  # Nothing shown

# ✅ Good - guide user
if not items:
    st.warning("😢 근처에 식당이 없어요. 다른 지역을 선택해주세요.")
```

### 4. First-time user
```python
# ❌ Bad - unclear what to do
st.title("오늘 뭐 먹지?")

# ✅ Good - clear CTA
st.title("오늘 뭐 먹지?")
st.caption("주변 맛집 데이터를 분석해 메뉴를 추천해드려요")
st.info("👆 위에서 메뉴를 선택하거나 랜덤 버튼을 눌러보세요!")
```

### 5. Error recovery
```python
# ❌ Bad - just show error
except Exception as e:
    st.error(str(e))

# ✅ Good - offer solution
except ConnectionError:
    st.error("인터넷 연결을 확인해주세요")
    if st.button("다시 시도"):
        st.rerun()
```

## User scenarios to test

1. **First visit**: Can user understand what to do in 3 seconds?
2. **Empty results**: Does user know what to do next?
3. **Network error**: Is error message clear + recovery offered?
4. **Slow loading**: Does user know app is working?
5. **Mobile**: Are buttons easy to tap?

## Quick checks

```python
# Count spinners
spinners = content.count("st.spinner")  # Should have 1+

# Check error handling
try_except = content.count("try:")  # Should have 1+

# Empty state handling
if_not = content.count("if not")  # Should check empty cases
```

## Output format
```
🎨 UX Review: app.py

Loading states:
  ✅ Line X: Spinner for API call
  ⚠️ Line Y: Long operation without feedback

Error handling:
  ❌ No try-except around API call
  ✅ Empty state handled well (line Z)

Messages:
  ✅ User-friendly language
  ⚠️ Technical term exposed (line W)

First-time UX:
  ⚠️ Unclear what to do initially
  Suggestion: Add welcome message

Mobile:
  ✅ Responsive columns
  ✅ Touch-friendly buttons
```

## Quick wins

```python
# 1. Add error handling
try:
    with st.spinner("데이터 로딩 중..."):
        data = api.search_places(query)
except Exception as e:
    logging.error(f"Error: {e}")
    st.error("데이터를 불러올 수 없습니다. 다시 시도해주세요.")
    if st.button("🔄 재시도"):
        st.rerun()
    st.stop()

# 2. First-time guide
if 'first_visit' not in st.session_state:
    st.session_state.first_visit = True
    st.info("👋 메뉴 칩을 클릭하거나 '랜덤 뽑기'를 눌러보세요!")
```
