import streamlit as st
import folium
from streamlit_folium import st_folium
import os
import time
import random
from dotenv import load_dotenv
from backend.naver_api import NaverPlaceAPI
from backend.kakao_api import KakaoPlaceAPI
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
KAKAO_REST_API_KEY = os.getenv("KAKAO_REST_API_KEY")

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

    # Initialize session state for data persistence (RESTORED)
    if 'processed_results' not in st.session_state:
        st.session_state.processed_results = []
    if 'top_menus' not in st.session_state:
        st.session_state.top_menus = []
    if 'last_query' not in st.session_state:
        st.session_state.last_query = ""
    if 'last_mode' not in st.session_state: # Track mode changes
        st.session_state.last_mode = ""

    # Initialize AI mode session state
    if 'ai_recommendations' not in st.session_state:
        st.session_state.ai_recommendations = None
    if 'ai_context' not in st.session_state:
        st.session_state.ai_context = ""
    if 'last_ai_mode' not in st.session_state:
        st.session_state.last_ai_mode = False

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
        

        
    # Layout: Top Level Tabs
    tab_fast, tab_ai = st.tabs(["⚡️ 빠른 추천", "🤖 AI 미식가"])

    # ---------------------------------------------------------
    # TAB 1: FAST MODE (Original Functionality)
    # ---------------------------------------------------------
    with tab_fast:
        st.caption("🚀 카테고리 기반으로 빠르게 메뉴를 추천해드립니다.")
        
        # State Checking for Fast Mode
        if 'fast_selected_menu' not in st.session_state:
            st.session_state.fast_selected_menu = None
            
        col_rand, col_chips = st.columns([1, 2])

        with col_rand:
            st.markdown("### 🎲 못 고르겠다면?")
            if st.button("랜덤 메뉴 뽑기!", type="primary", use_container_width=True, key="btn_random_fast"):
                if st.session_state.top_menus and len(st.session_state.top_menus) > 0:
                    st.session_state.fast_selected_menu = random.choice(st.session_state.top_menus)
                else:
                    st.error("추천할 메뉴 데이터가 부족해요.")

        with col_chips:
            st.markdown(f"### 🔥 {location} 인기 메뉴")
            if st.session_state.top_menus:
                 # CSS hack for chips
                st.markdown("""
                <style>
                .stButton button {border-radius: 20px;}
                </style>
                """, unsafe_allow_html=True)
                
                menus_to_show = st.session_state.top_menus
                rows = [menus_to_show[i:i + 5] for i in range(0, len(menus_to_show), 5)]
                for row in rows:
                    cols = st.columns(len(row))
                    for i, menu in enumerate(row):
                        if cols[i].button(f"#{menu}", key=f"btn_fast_{menu}", type="secondary"):
                            st.session_state.fast_selected_menu = menu
            else:
                st.info("메뉴를 추출하는 중입니다...")
        
        st.divider()
        
        # Fast Mode Results
        if st.session_state.fast_selected_menu:
            target_menu = st.session_state.fast_selected_menu
            st.header(f"😋 오늘의 추천: [{target_menu}]")
            
            matched_places = [
                p for p in processed_results 
                if target_menu in p.get('category', '') or target_menu in p.get('title', '') or target_menu in p.get('description', '')
            ]
            
            if matched_places:
                display_results(matched_places, location, target_menu)
            else:
                st.warning(f"'{target_menu}' 관련 식당을 찾지 못했어요.")
        else:
             st.markdown("""
            <div style="text-align: center; padding: 30px; color: #666;">
                <h3>👆 위에서 메뉴를 선택하거나 랜덤 버튼을 눌러보세요!</h3>
            </div>
            """, unsafe_allow_html=True)

    # ---------------------------------------------------------
    # TAB 2: AI MODE (Gemini Integration)
    # ---------------------------------------------------------
    with tab_ai:
        st.caption("🤖 Gemini AI가 리뷰를 심층 분석하여 맞춤 메뉴를 제안합니다.")
        
        # Validation
        gemini_key = os.getenv("GEMINI_API_KEY")
        if not gemini_key:
            st.warning("⚠️ .env 파일에 GEMINI_API_KEY를 설정해주세요.")
        
        # AI Context Input
        ai_context = st.text_area(
            "🗣️ AI에게 상황 설명하기",
            value=st.session_state.get('ai_context', ''),
            placeholder="예: '오늘 속이 안 좋아', '가볍게 먹고 싶어', '매운 거 땡겨'",
            key="ai_context_input",
            height=100
        )
        
        col_ai_btn, _ = st.columns([1, 4])
        with col_ai_btn:
            if st.button("🚀 AI 분석 시작", disabled=not gemini_key, type="primary", key="btn_ai_start"):
                st.session_state.ai_analyze_trigger = True
                st.session_state.ai_context = ai_context
                st.session_state.ai_recommendations = None
        
        # AI Logic Execution
        if st.session_state.get('ai_analyze_trigger', False) and gemini_key:
            if st.session_state.ai_recommendations is None:
                from backend.gemini_service import GeminiRecommendationService
                gemini_service = GeminiRecommendationService(gemini_key)
                
                with st.spinner("🤖 AI가 맛집 리뷰를 분석하고 있습니다... (최대 30초)"):
                    try:
                        # Logic identical to previous implementation but isolated here
                        sample_restaurants = random.sample(
                            st.session_state.processed_results,
                            min(10, len(st.session_state.processed_results))
                        )
                        ai_result = gemini_service.analyze_restaurants_for_menu(
                            restaurants=sample_restaurants,
                            user_context=st.session_state.ai_context,
                            max_restaurants=10
                        )
                        st.session_state.ai_recommendations = ai_result
                    except Exception as e:
                        st.error(f"AI 분석 중 오류: {str(e)}")
            
            # AI Results Display
            if st.session_state.ai_recommendations:
                ai_result = st.session_state.ai_recommendations
                if ai_result.get('conversational_response'):
                    st.info(f"💬 {ai_result['conversational_response']}")
                
                if ai_result.get('recommendations'):
                    for idx, rec in enumerate(ai_result['recommendations'][:5]):
                        with st.expander(f"**{idx+1}. {rec['menu']}** (신뢰도: {rec['confidence']*100:.0f}%)", expanded=(idx==0)):
                            st.markdown(f"**📝 추천 이유:**\n{rec['reasoning']}")
                            if rec.get('review_summary'):
                                st.markdown(f"**🗣️ 리뷰 요약:**\n{rec['review_summary']}")
                            
                            # View Restaurants Button
                            if st.button(f"'{rec['menu']}' 식당 보기", key=f"ai_view_{idx}"):
                                st.session_state.ai_selected_restaurants = rec['restaurants']
                                st.session_state.ai_selected_menu_name = rec['menu']

                    # Check if user selected a menu to view details
                    if st.session_state.get('ai_selected_restaurants'):
                         st.divider()
                         target_name = st.session_state.get('ai_selected_menu_name', '추천 메뉴')
                         st.header(f"🧑‍🍳 AI 추천 식당: [{target_name}]")
                         display_results(st.session_state.ai_selected_restaurants, location, target_name)
                else:
                    st.warning("추천할 메뉴를 찾지 못했습니다.")

def display_results(places, location, target_menu):
    c1, c2 = st.columns([1, 1])
    with c1:
        st.caption(f"**{len(places)}곳**의 식당을 찾았습니다.")
        for i, place in enumerate(places):
            clean_title = clean_html(place['title'])
            from urllib.parse import quote
            encoded_query = quote(f"{location} {clean_title}")
            link = f"https://map.naver.com/v5/search/{encoded_query}"
            
            st.markdown(f"""
            **{i+1}. [{clean_title}]({link})** <span style="color:#888">({place.get('category')})</span>  
            📍 {place.get('roadAddress', place.get('address'))}
            """, unsafe_allow_html=True)
    
    with c2:
        lats = [p['lat'] for p in places if 'lat' in p]
        lngs = [p['lng'] for p in places if 'lng' in p]
        
        if lats and lngs:
            center = [sum(lats)/len(lats), sum(lngs)/len(lngs)]
        else:
            center = [37.4979, 127.0276]
            
        m = folium.Map(location=center, zoom_start=14)
        for p in places:
            if 'lat' in p and 'lng' in p:
               folium.Marker(
                   [p['lat'], p['lng']], 
                   popup=clean_html(p['title']), 
                   tooltip=p.get('category')
               ).add_to(m)
            
        st_folium(m, height=300, use_container_width=True)

if __name__ == "__main__":
    main()
