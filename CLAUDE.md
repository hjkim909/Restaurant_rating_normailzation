# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

"오늘 뭐 먹지?" (Lunch Menu Picker) is a Streamlit-based web app that recommends lunch menus by analyzing nearby restaurants using the Naver Search API. The core philosophy is **menu-first, not restaurant-first**: users pick a menu (e.g., "김치찌개"), then see nearby restaurants that serve it.

**Live Demo**: https://restaurantratingnormailzation-zjcarw4nbej4jgihurwnad.streamlit.app/

## Commands

### Development
```bash
# Run the application locally
streamlit run app.py

# Run tests
pytest tests/

# Run a specific test file
pytest tests/test_geo_utils.py -v

# Code review (check security, performance, style)
python scripts/code_review.py                    # Review entire project
python scripts/code_review.py backend/app.py     # Review specific file

# Run utility scripts
python scripts/verify_db.py          # Verify SQLite database integrity
python scripts/test_user_prefs.py    # Test user preference system
python scripts/test_coord.py         # Test coordinate conversion logic
```

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Environment variables required in .env
NAVER_CLIENT_ID=your_id
NAVER_CLIENT_SECRET=your_secret
```

## Architecture

### Core Data Flow
1. **User Input** → Location selection (manual or GPS-based via `streamlit_js_eval`)
2. **API Layer** → Parallel fetch from two sources:
   - `backend/naver_api.py` → "Location Subdivision" + "Category Explosion" strategy
   - `backend/kakao_api.py` → Category explosion (display=15 per request)
3. **Caching Layer** (`backend/db_manager.py`) → SQLite database for 24-hour cache (migrated from JSON)
4. **Processing** (`backend/data.py`) → Normalizes ratings, converts coordinates (scaled WGS84 → standard WGS84), deduplicates
5. **Menu Extraction** (`backend/menu_recommender.py`) → Extracts menu keywords from categories with user preference filtering
6. **UI** (`app.py`) → Displays menu chips, handles selection, shows restaurant list + Folium map

### Key Technical Patterns

#### Data Collection Strategies

**1. Location Subdivision** (`naver_api.py:133-151`)
- Subdivides major locations into 5-7 smaller areas
- Example: "강남역" → ["강남역 1번출구", "강남역 CGV", "역삼동 테헤란로", ...]
- Multiplies coverage: 7 locations × 50 keywords × 5 results = 1,750 queries

**2. Category Explosion** (`naver_api.py:153-170`, `kakao_api.py:66-89`)
- Naver: display=5 limit, Kakao: display=15 limit
- Queries 50+ detailed keywords concurrently (한식, 초밥, 파스타, etc.)
- Uses `ThreadPoolExecutor` with 20-30 workers for parallel fetching
- Deduplicates by `(mapx, mapy, title)` tuple

**3. Multi-API Aggregation** (`app.py:163-196`)
- Fetches from both Naver and Kakao simultaneously
- Typical result: 200-400 unique restaurants (Naver: 150-250, Kakao: 100-150)
- Cross-API deduplication in data processor

#### Smart Radius Filtering (`app.py:177-210`)
Progressive expansion to handle sparse data:
1. Try 500m radius first
2. If insufficient results → expand to 1km
3. If still insufficient → expand to 2km
4. Fallback to unfiltered results if needed

#### Coordinate System (`backend/geo_utils.py`)
Naver Search API returns WGS84 coordinates scaled by 10,000,000:
- `mapx: 1270292507` → `127.0292507` (longitude)
- `mapy: 374997698` → `37.4997698` (latitude)
- Conversion formula: `lat = mapy / 10000000.0`

#### User Preferences (`backend/user_prefs.py`)
Stored in `user_preferences.json`:
- **Dislikes**: Keywords (오이, 고수, 마라) are filtered out from menu extraction
- **Favorites**: Keywords (고기, 치즈) get 3x weight boost in `MenuRecommender.extract_top_menus()`

### State Management (Streamlit)
Critical session state variables:
- `st.session_state.processed_results`: Cached restaurant list (cleared on query/mode change)
- `st.session_state.top_menus`: Extracted menu keywords (regenerated when preferences change)
- `st.session_state.selected_menu`: Currently selected menu for display
- `st.session_state.current_location`: Tracks location for GPS feature

## Important Context

### API Integration Rules (from `.agent/rules/api-integration-rules.md`)
- **Budget**: Free tier only for Naver API
- **Caching**: SQLite-based (`restaurant.db`), 24-hour expiry
- **Error handling**: Graceful degradation (returns empty list on failure, shows demo data if no API keys)
- **Logging**: All API calls logged to `api_usage.csv` with timestamp, endpoint, params, status

### Search Modes
- **Popular mode** (`sort=comment`): Default, sorts by review count
- **Random mode** (`sort=random`): "Hidden gem" toggle for discovering diverse restaurants

### Menu Extraction Logic
Parses `category` field from Naver API (format: `"한식>찌개,전골"`) and splits on `>,`:
- Filters generic stopwords (맛집, 전문점, 식당, etc.)
- Applies user dislikes/favorites
- Returns random sample of 15 menus from top 50 candidates for variety

### Testing
Single test file exists: `tests/test_geo_utils.py` - Tests coordinate conversion logic.
No pytest configuration file exists yet. Tests can be run directly with `pytest tests/`.

## Common Gotchas

1. **Coordinate Confusion**: Old comments mention "KATECH" or "TM128" but Naver Search API actually returns scaled WGS84. Don't add conversion formulas beyond division by 10^7.

2. **Cache Invalidation**: Use `force_refresh=True` in `search_places()` or click "🔄 데이터 다시 불러오기" button. Session state persists across Streamlit reruns.

3. **Empty Results**: If GPS is enabled but `location_coords` doesn't match `current_location` dropdown, filtering is skipped (prevents mismatched coordinate system usage).

4. **Mock Data**: If API keys contain "your_client_id" or are missing, app falls back to `MOCK_DATA` in `app.py:29`.

5. **HTML Tags in Titles**: Naver API returns `<b>` tags in titles. Always use `clean_html()` before display.

## Sub-Agent System

When users request specific checks (e.g., "API 보안 체크해줘"), **read the corresponding agent file** in `.claude/agents/` and follow its checklist.

### Active Agents

| User Command | Agent File | Purpose |
|-------------|------------|---------|
| "API 보안 체크" | `.claude/agents/api_security.md` | API keys, SQL injection, XSS |
| "좌표 검증" | `.claude/agents/coordinate_validation.md` | Naver coordinate conversion |
| "DB 성능" | `.claude/agents/db_performance.md` | SQLite caching & queries |
| "UX 리뷰" | `.claude/agents/ux_review.md` | Streamlit user experience |

Each agent is 1-2KB with focused checklist and examples. See `.claude/agents/README.md` for details.

## Code Review

When asked to review code, **always read `.claude/code_review_rules.md` first** for project-specific guidelines and common pitfalls. Then run the automated tool if needed:

```bash
python scripts/code_review.py [file_path]
```

The `.claude/code_review_rules.md` file contains project-specific context like coordinate system quirks, caching requirements, and common mistakes.

## Adding New Features

When user requests a new feature, **read `.claude/workflows/feature_addition.md`** and follow the workflow:

1. Clarify requirements
2. Assess impact (read PRD, CLAUDE.md)
3. Enter Plan Mode if non-trivial
4. Implement following existing patterns
5. **Update docs** (PRD, CLAUDE.md, README, requirements.txt, code_review_rules)
6. **Run relevant agents** (API 보안/UX/DB 성능/좌표 검증)
7. Write tests
8. Commit with Co-authored-by tag

The workflow file contains detailed steps, examples, and a checklist to ensure nothing is missed.

## Documentation References
- `.claude/code_review_rules.md`: **READ THIS FIRST** when doing code reviews - project-specific rules and gotchas
- `docs/PRD.md`: Product requirements and feature specifications
- `docs/AGENTS.md`: Role-based development process (Architect/Experience Designer/Reliability Engineer)
- `docs/Naver_API_Guide.md`: Naver API setup instructions
- `docs/DEPLOYMENT.md`: Streamlit Cloud deployment guide
- `docs/CODE_REVIEW.md`: Automated code review tool documentation
