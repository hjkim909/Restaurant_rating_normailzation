import streamlit as st
import folium
from streamlit_folium import st_folium
import os
import random
from dotenv import load_dotenv
from backend.naver_api import NaverPlaceAPI
from backend.data import DataProcessor
from backend.menu_recommender import MenuRecommender
from backend.user_prefs import UserPreferences
from streamlit_js_eval import get_geolocation
from backend.geo_utils import get_address_from_coords

# Load environment variables
load_dotenv()

# Setup Page
st.set_page_config(
    page_title="오늘 뭐 먹지?",
    page_icon="🍱",
    layout="wide"
)

# Initialize Backend
CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

# Mock data for demo
MOCK_DATA = [
    {"title": "<b>시골밥상</b>", "category": "한식,김치찌개", "address": "강남구 역삼동", "mapx":"314000", "mapy":"544000", "description": "맛난 김치찌개"},
    {"title": "<b>은행골</b>", "category": "일식,초밥", "address": "강남구 역삼동", "description": "입에서 녹는 초밥"},
    {"title": "<b>홍대개미</b>", "category": "일식,덮밥", "address": "강남구 역삼동", "description": "스테이크 덮밥"},
    {"title": "<b>마포만두</b>", "category": "분식,만두", "address": "강남구 역삼동", "description": "갈비만두"},
    {"title": "<b>땀땀</b>", "category": "아시아음식,쌀국수", "address": "강남구 역삼동", "description": "곱창 쌀국수"},
    {"title": "<b>알라보</b>", "category": "양식,샐러드", "address": "강남구 역삼동", "description": "아보카도 샐러드"}
]

def clean_html(raw_html):
    import re
    cleanr = re.compile('<.*?>')
    return re.sub(cleanr, '', raw_html)

def main():
    st.title("🍱 오늘 점심, 뭐 먹지?")
    st.caption("주변 맛집 데이터를 분석해 **실제 먹을 수 있는 메뉴**만 추천해 드려요.")

    # Sidebar
    with st.sidebar:
        st.header("📍 내 위치 설정")
        
        # Geolocation Button
        use_geo = st.toggle("📍 현재 위치 사용", value=True)
        location_coords = None
        if use_geo:
             loc = get_geolocation()
             if loc:
                 location_coords = (loc['coords']['latitude'], loc['coords']['longitude'])
                 st.success("위치를 가져왔습니다!")

        # Initialize session state for location
        if 'current_location' not in st.session_state:
            st.session_state.current_location = "강남역"

        # Update location if coords found
        if location_coords:
            address = get_address_from_coords(location_coords[0], location_coords[1])
            if address:
                if st.session_state.current_location != address:
                    st.session_state.current_location = address
                    st.rerun()
                # If equal, do nothing (prevent loop)
            else:
                st.error("주소를 찾을 수 없습니다.")

        # Location Selection
        # Add current_location to options if it's new
        default_locations = ["강남역", "오목교역", "여의도역", "판교역", "성수역", "을지로입구역", "역삼역"]
        if st.session_state.current_location not in default_locations:
            default_locations.insert(0, st.session_state.current_location)
            
        location = st.selectbox(
            "지역 선택", 
            default_locations, 
            index=default_locations.index(st.session_state.current_location)
        )
        
        # Update session state if user manually changes it
        if location != st.session_state.current_location:
            st.session_state.current_location = location
        
        st.header("⚙️ 옵션")
        # Hidden Gem Toggle
        use_hidden_gem = st.toggle("💎 숨은 맛집 찾기 (랜덤/다양성)", 
                                   help="활성화하면 리뷰순이 아닌 랜덤순으로 다양한 식당을 가져옵니다.")
                                   
        category_options = st.multiselect(
            "선호 종류 (선택 안 하면 전체)", 
            ["한식", "양식", "중식", "일식", "분식", "아시아"],
            default=[]
        )

        st.divider()
        with st.expander("👅 내 입맛 설정 (My Taste)"):
            prefs = UserPreferences()
            
            # Dislikes
            current_dislikes = prefs.get_dislikes()
            new_dislikes = st.multiselect(
                "❌ 싫어하는 메뉴 키워드 (제외)",
                options=list(set(current_dislikes + ["오이", "고수", "마라", "회", "곱창", "가지"])),
                default=current_dislikes
            )
            
            # Favorites
            current_favorites = prefs.get_favorites()
            new_favorites = st.multiselect(
                "❤️ 좋아하는 메뉴 키워드 (추천 UP)",
                options=list(set(current_favorites + ["고기", "치즈", "매운", "딸기", "초밥", "떡볶이"])),
                default=current_favorites
            )
            
            if new_dislikes != current_dislikes or new_favorites != current_favorites:
                prefs.save_preferences(new_dislikes, new_favorites)
                st.success("취향이 저장되었습니다! (다음 검색부터 적용)")
                # If we want immediate effect on MENUS (not api call), we might just rerun if data exists
                if st.session_state.processed_results:
                     st.session_state.top_menus = [] # Force re-extraction
                     st.rerun()
        
    # Main Logic
    # 1. Fetch Data
    query = f"{location} 맛집"
    if category_options:
        query = f"{location} {' '.join(category_options)} 맛집"

    # Initialize session state for data persistence
    if 'processed_results' not in st.session_state:
        st.session_state.processed_results = []
    if 'top_menus' not in st.session_state:
        st.session_state.top_menus = []
    if 'last_query' not in st.session_state:
        st.session_state.last_query = ""
    if 'last_mode' not in st.session_state: # Track mode changes
        st.session_state.last_mode = ""

    # Clear cache only if requested explicitly or implicitly by changing options
    need_refresh = False
    if st.button("🔄 데이터 다시 불러오기", type="secondary"):
        st.cache_data.clear() # Clear streamlit cache
        need_refresh = True
        
    current_mode = 'random' if use_hidden_gem else 'popular'
    
    # Check if we need to fetch new data (Query changed, Mode changed, or Refresh requested)
    if (query != st.session_state.last_query) or (current_mode != st.session_state.last_mode) or need_refresh or not st.session_state.processed_results:
        st.session_state.last_query = query
        st.session_state.last_mode = current_mode
        st.session_state.selected_menu = None # Reset selection on new search
        
        api = NaverPlaceAPI(CLIENT_ID, CLIENT_SECRET)
        
        with st.spinner(f"📡 {location} 주변 식당 스캔 중... (모드: {'숨은 맛집' if use_hidden_gem else '인기 맛집'})"):
            if CLIENT_ID and CLIENT_SECRET and "your_client_id" not in CLIENT_ID:
                # API handles file caching internally now
                # Pass need_refresh to force API to ignore file cache
                raw_data = api.search_places(query, display=50, search_mode=current_mode, force_refresh=need_refresh) 
                items = raw_data['items'] if raw_data else []
            else:
                items = MOCK_DATA
                if not CLIENT_ID: st.warning("데모 모드: API 키 설정을 확인해주세요.")
            
            processor = DataProcessor()
            processed_temp = processor.process_places(items)
            
            # 🟢 SMART RADIUS FILTERING (Progressive Expansion)
            # Only filter if we have valid user coordinates matching the current view
            if use_geo and location_coords and location == st.session_state.current_location:
                 from backend.geo_utils import calculate_distance
                 # Filter only if explicitly using current location
                 
                 user_lat, user_lng = location_coords
                 
                 # Progressive check: 500m -> 1km -> 2km -> All
                 radii = [500, 1000, 2000]
                 found_radius = None
                 filtered_items = []
                 
                 for r in radii:
                     temp_items = []
                     for item in processed_temp:
                         dist = calculate_distance(user_lat, user_lng, item.get('mapx'), item.get('mapy'))
                         if dist <= r:
                             temp_items.append(item)
                     
                     if temp_items:
                         filtered_items = temp_items
                         found_radius = r
                         break
                 
                 # Feedback to user
                 if filtered_items:
                     radius_text = f"{found_radius}m" if found_radius < 1000 else f"{found_radius/1000}km"
                     if found_radius == 500:
                        st.info(f"📍 현재 위치 반경 {radius_text} 이내 맛집 {len(filtered_items)}개를 찾았습니다.")
                     else:
                        st.warning(f"⚠️ 500m 이내에 식당이 없어 검색 범위를 **{radius_text}**까지 넓혔습니다. ({len(filtered_items)}개 발견)")
                     processed_temp = filtered_items
                 else:
                     st.error("⚠️ 반경 2km 이내에도 식당이 없어 검색된 모든 결과를 보여드립니다.")
                     # Fallback to all items (no filtering)
            
            st.session_state.processed_results = processed_temp
            
            # 2. Extract Menus (Only once per fetch)
            recommender = MenuRecommender()
            # Load fresh prefs
            current_prefs = UserPreferences()
            st.session_state.top_menus = recommender.extract_top_menus(
                st.session_state.processed_results, 
                top_n=15, 
                dislikes=current_prefs.get_dislikes(),
                favorites=current_prefs.get_favorites()
            )

    
    # Use cached data
    processed_results = st.session_state.processed_results
    
    # Show Cache Stats (Simple indicator)
    if processed_results:
        st.caption(f"💾 로컬 데이터베이스 사용 중 ({len(processed_results)}개 식당 저장됨)")

    
    # State management for selection
    if 'selected_menu' not in st.session_state:
        st.session_state.selected_menu = None

    # Layout: Top Section (Random & Chips)
    col_rand, col_chips = st.columns([1, 2])
    
    with col_rand:
        st.markdown("### 🎲 못 고르겠다면?")
        if st.button("랜덤 메뉴 뽑기!", type="primary", use_container_width=True):
            if st.session_state.top_menus:
                # Re-apply preference weight for random pick slightly? 
                # Already done in extraction, but let's just pick one.
                st.session_state.selected_menu = random.choice(st.session_state.top_menus)
            else:
                st.error("추천할 메뉴 데이터가 부족해요.")

    with col_chips:
        st.markdown(f"### 🔥 {location} 인기 메뉴")
        # Display chips nicely
        if st.session_state.top_menus:
            # CSS hack for horizontal scroll or nice wrapping chips
            st.markdown("""
            <style>
            .stButton button {border-radius: 20px;}
            </style>
            """, unsafe_allow_html=True)
            
            # Simple flow layout using columns is hard, let's use a specialized row approach or just simple buttons
            # Grouping buttons in rows of 5
            menus_to_show = st.session_state.top_menus
            rows = [menus_to_show[i:i + 5] for i in range(0, len(menus_to_show), 5)]
            for row in rows:
                cols = st.columns(len(row))
                for i, menu in enumerate(row):
                    if cols[i].button(f"#{menu}", key=f"btn_{menu}", type="primary" if st.session_state.selected_menu == menu else "secondary"):
                        st.session_state.selected_menu = menu
        else:
            st.info("메뉴를 추출하는 중입니다...")

    st.divider()

    # Layout: Bottom Section (Results)
    if st.session_state.selected_menu:
        target_menu = st.session_state.selected_menu
        st.header(f"😋 오늘의 추천: [{target_menu}]")
        
        # Filter restaurants
        matched_places = [
            p for p in processed_results 
            if target_menu in p.get('category', '') or target_menu in p.get('title', '') or target_menu in p.get('description', '')
        ]
        
        if matched_places:
            c1, c2 = st.columns([1, 1])
            with c1:
                st.caption(f"근처에 **{len(matched_places)}곳**의 식당이 있습니다.")
                for i, place in enumerate(matched_places):
                    clean_title = clean_html(place['title'])
                    # User request: Link to Naver Map, not homepage
                    # Construct search URL for Naver Map
                    # query format: https://map.naver.com/v5/search/{name}
                    from urllib.parse import quote
                    encoded_query = quote(f"{location} {clean_title}") # Include location to be precise
                    link = f"https://map.naver.com/v5/search/{encoded_query}"
                    
                    st.markdown(f"""
                    **{i+1}. [{clean_title}]({link})** <span style="color:#888">({place.get('category')})</span>  
                    📍 {place.get('roadAddress', place.get('address'))}
                    """, unsafe_allow_html=True)
            
            with c2:
                # Map Visualization
                # Calculate center from matched places if coords exist
                lats = [p['lat'] for p in matched_places if 'lat' in p]
                lngs = [p['lng'] for p in matched_places if 'lng' in p]
                
                if lats and lngs:
                    center = [sum(lats)/len(lats), sum(lngs)/len(lngs)]
                else:
                    center = [37.4979, 127.0276] # Default Gangnam
                    
                m = folium.Map(location=center, zoom_start=14)
                
                # Add markers
                for p in matched_places:
                    if 'lat' in p and 'lng' in p:
                       folium.Marker(
                           [p['lat'], p['lng']], 
                           popup=clean_html(p['title']), 
                           tooltip=p.get('category')
                       ).add_to(m)
                    
                st_folium(m, height=300, use_container_width=True)
        else:
            st.warning(f"아쉽게도 '{target_menu}' 관련 식당을 찾지 못했어요. 다른 메뉴를 골라보세요!")
            
    else:
        st.markdown("""
        <div style="text-align: center; padding: 50px; color: #666;">
            <h3>👆 위에서 메뉴를 선택하거나 랜덤 버튼을 눌러보세요!</h3>
            <p>현재 위치 주변의 맛집 데이터를 분석해서 리스트를 보여드립니다.</p>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
