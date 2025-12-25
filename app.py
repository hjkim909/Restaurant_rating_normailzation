import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import os
from dotenv import load_dotenv
from backend.naver_api import NaverPlaceAPI
from backend.data import DataProcessor

# Load environment variables
load_dotenv()

# Setup Page
st.set_page_config(
    page_title="직장인 점심 맛집 파인더",
    page_icon="🍱",
    layout="wide"
)

# Initialize Backend
CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

# Mock data for demonstration if API fails or keys missing
MOCK_DATA = [
    {
        "title": "<b>시골밥상</b>",
        "category": "한식,김치찌개",
        "address": "서울 강남구 역삼동",
        "roadAddress": "서울 강남구 테헤란로",
        "mapx": "314000", "mapy": "544000", 
        "description": "음식 빨리 나오고 김치찌개가 맛있어요. 점심에 딱입니다.",
        "userRating": "4.5"
    },
    {
        "title": "<b>파스타가든</b>",
        "category": "양식,파스타",
        "address": "서울 강남구 서초동",
        "roadAddress": "서울 서초구 서초대로",
        "description": "분위기는 좋은데 웨이팅이 너무 길어요. 30분 기다림.",
        "userRating": "4.2"
    },
    {
        "title": "<b>홍대개미</b>",
        "category": "일식,덮밥",
        "address": "서울 강남구 역삼동",
        "description": "스테이크 덮밥이 맛있고 회전율이 빨라요.",
        "userRating": "4.4"
    },
    {
        "title": "<b>마포만두</b>",
        "category": "분식,만두",
        "address": "서울 강남구 역삼동",
        "description": "갈비만두가 유명해요. 혼밥하기 좋음.",
        "userRating": "4.1"
    },
    {
        "title": "<b>은행골</b>",
        "category": "일식,초밥",
        "address": "서울 강남구 역삼동",
        "description": "초밥이 입에서 녹아요. 점심 특선 있음.",
        "userRating": "4.6"
    }
]

# Helper to clean HTML tags from title
def clean_html(raw_html):
    import re
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext

def main():
    st.title("🍱 직장인 점심 맛집 파인더")
    st.markdown("네이버 평점 거품을 걷어내고, **점심시간에 딱 맞는** 맛집을 찾아드립니다.")

    # Sidebar
    with st.sidebar:
        st.header("검색 설정")
        location = st.selectbox(
            "지역 선택",
            ["강남역", "여의도역", "홍대입구역"]
        )
        category = st.selectbox(
            "음식 종류",
            ["한식", "양식", "중식", "일식", "분식"]
        )
        
        st.markdown("---")
        st.header("필터")
        filter_lunch = st.checkbox("🍱 점심 적합도 높은 곳만", value=True)
        # filter_rating = st.checkbox("⭐ 상대평점 상위 20%", value=False)
        
        search_btn = st.button("맛집 찾기", type="primary")

    # Main Content
    if search_btn or True: # Load on start for demo
        with st.spinner(f"{location} 주변 {category} 맛집 찾는 중..."):
            
            # API Call
            query = f"{location} {category}"
            api = NaverPlaceAPI(CLIENT_ID, CLIENT_SECRET)
            
            if CLIENT_ID and CLIENT_SECRET and CLIENT_ID != "your_client_id_here":
                raw_data = api.search_places(query, display=20)
            else:
                raw_data = None
                if not (CLIENT_ID):
                     st.warning("⚠️ 네이버 API 키가 설정되지 않았습니다. 데모 데이터를 표시합니다.")

            # Process Data
            items = []
            if raw_data and 'items' in raw_data:
                items = raw_data['items']
            else:
                 # Use mock items logic extended for demo
                 items = MOCK_DATA
            
            processor = DataProcessor()
            processed_results = processor.process_places(items)
            
            # --- MENU RECOMMENDATION START ---
            from backend.menu_recommender import MenuRecommender
            menu_recommender = MenuRecommender()
            top_menus = menu_recommender.extract_top_menus(processed_results)
            
            # Session State for Menu Filter
            if 'selected_menu' not in st.session_state:
                st.session_state.selected_menu = None

            st.markdown("### 🍽️ 오늘의 추천 메뉴")
            if top_menus:
                # Create columns for simple button-like selection (or use radio horizontal)
                # Using a horizontal radio button styled as chips could be cleaner, but native options limited.
                # Let's use simple columns for buttons to act as filters.
                
                # Reset button
                cols = st.columns([1] + [1] * len(top_menus))
                if cols[0].button("전체보기", type="secondary" if st.session_state.selected_menu else "primary"):
                    st.session_state.selected_menu = None
                    # st.experimental_rerun() # might be needed, but button press usually reruns
                
                for i, menu in enumerate(top_menus):
                    is_selected = (st.session_state.selected_menu == menu)
                    if cols[i+1].button(f"#{menu}", type="primary" if is_selected else "secondary"):
                        st.session_state.selected_menu = menu
                        # st.experimental_rerun()

            # Apply Menu Filter
            if st.session_state.selected_menu:
                # Filter places that contain the selected menu in category or title
                filtered_results = []
                for p in processed_results:
                    cat = p.get('category', '')
                    title = p.get('title', '')
                    target = st.session_state.selected_menu
                    if target in cat or target in title:
                        filtered_results.append(p)
                processed_results = filtered_results
                st.info(f"'{st.session_state.selected_menu}' 관련 맛집 {len(processed_results)}곳을 찾았습니다.")
            # --- MENU RECOMMENDATION END ---

            # Filtering
            if filter_lunch:
                 processed_results = [p for p in processed_results if p['lunch_score'] >= 50]

            # Layout: Map vs List
            col1, col2 = st.columns([1, 1])

            with col1:
                st.subheader(f"📍 {location} 맛집 리스트 ({len(processed_results)}곳)")
                
                for i, place in enumerate(processed_results):
                    title = clean_html(place['title'])
                    
                    # Highlight cards
                    card_style = "padding: 15px; border-radius: 10px; margin-bottom: 10px; border: 1px solid #ddd;"
                    if place['lunch_score'] >= 80:
                        card_style += "background-color: #f0f9ff; border-color: #bae6fd;" # Light blue for high score
                    
                    with st.container():
                        st.markdown(f"""
                        <div style="{card_style}">
                            <b>{i+1}. {title}</b> 
                            <span style="color: #666; font-size: 0.9em;">({place.get('category','한식')})</span><br>
                            ⭐ <b>{place['adjusted_rating']}</b> <small>({place['rating_diff_str']})</small> 
                            | 🍱 점심점수: <b>{place['lunch_score']}</b>
                            <br>
                            <small style="color: #444;">"{place.get('description', '')}"</small>
                            <br>
                            {' '.join([f"<span style='background:#eee; padding:2px 5px; border-radius:4px; font-size:0.8em;'>#{k}</span>" for k in place.get('lunch_keywords', [])])}
                        </div>
                        """, unsafe_allow_html=True)
            
            with col2:
                # Map Visualization
                # Center for Gangnam (Mock coordinates)
                gangnam_coords = [37.4979, 127.0276] 
                m = folium.Map(location=gangnam_coords, zoom_start=14)
                
                # Markers (Normally we need real lat/lon, here we just show center for demo)
                folium.Marker(
                    gangnam_coords, 
                    popup="강남역", 
                    tooltip="현재 위치"
                ).add_to(m)
                
                st_folium(m, width="100%", height=500)

if __name__ == "__main__":
    main()
