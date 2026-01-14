import os
import time
import json
import logging
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None
    logging.warning("google-genai not installed. AI mode will not work.")

from fastapi_app.core.config import get_settings

class GeminiService:
    def __init__(self):
        self.settings = get_settings()
        if not self.settings.GEMINI_API_KEY:
             logging.warning("GEMINI_API_KEY not found.")
             self.client = None
             return

        if genai is None:
             self.client = None
             return

        self.client = genai.Client(api_key=self.settings.GEMINI_API_KEY)
        self.model_name = 'gemini-1.5-flash'
        self.search_tool = types.Tool(
            google_search=types.GoogleSearch()
        )
        self.logger = logging.getLogger(__name__)

    def analyze_restaurants_for_menu(
        self,
        restaurants: List[Dict],
        user_context: str = None,
        max_restaurants: int = 5 
    ) -> Dict:
        if not self.client:
            return {"error": "AI Service unavailable (Missing Key or Package)"}

        search_queries = []
        # Limit to 5 for speed in V1
        for restaurant in restaurants[:max_restaurants]:
            query = self._construct_naver_place_query(restaurant)
            search_queries.append({
                'restaurant': restaurant,
                'search_query': query
            })

        restaurant_analyses = self._parallel_analyze_reviews(search_queries)

        if not restaurant_analyses:
            return {
                'recommendations': [],
                'conversational_response': '죄송합니다. 리뷰 분석 중 오류가 발생했습니다.'
            }

        recommendations = self._aggregate_recommendations(restaurant_analyses, user_context)
        conversational_response = self._generate_conversational_response(recommendations, user_context)

        return {
            'recommendations': recommendations[:3], 
            'conversational_response': conversational_response
        }

    def _construct_naver_place_query(self, restaurant: Dict) -> str:
        clean_title = restaurant.get('title', '').replace('<b>', '').replace('</b>', '')
        address = restaurant.get('address', '') or restaurant.get('roadAddress', '')
        location_parts = address.split()[:2] if address else []
        location = ' '.join(location_parts)
        return f"네이버 플레이스 {clean_title} {location} 리뷰"

    def _parallel_analyze_reviews(self, search_queries: List[Dict]) -> List[Dict]:
        results = []
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_restaurant = {
                executor.submit(self._analyze_single_restaurant, sq['restaurant'], sq['search_query']): sq['restaurant']
                for sq in search_queries
            }
            for future in as_completed(future_to_restaurant):
                try:
                    result = future.result()
                    if result: results.append(result)
                except Exception as e:
                    print(f"Error: {e}")
        return results

    def _analyze_single_restaurant(self, restaurant: Dict, search_query: str) -> Optional[Dict]:
        clean_title = restaurant.get('title', '').replace('<b>', '').replace('</b>', '')
        category = restaurant.get('category', '')

        prompt = f"""
다음 식당의 네이버 플레이스 리뷰를 검색하고 분석하세요:
식당: {clean_title} ({category})
쿼리: {search_query}

분석 항목:
1. 대표 메뉴 3개 (빈도수 기준)
2. 각 메뉴 평가 (긍정/부정)
3. 점심 적합도 (1-10)

JSON 응답:
{{
  "top_menus": [
    {{ "menu": "메뉴명", "mention_count": 0, "sentiment": "긍정/부정", "summary": "요약" }}
  ],
  "lunch_suitability": 0
}}
"""
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[self.search_tool],
                    temperature=0.7,
                    response_mime_type="application/json"
                )
            )
            data = json.loads(response.text)
            return {'restaurant': restaurant, 'analysis': data}
        except Exception as e:
            print(f"AI Error ({clean_title}): {e}")
            return None

    def _aggregate_recommendations(self, analyses: List[Dict], user_context: Optional[str]) -> List[Dict]:
        menu_scores = {}
        for ra in analyses:
            analysis = ra.get('analysis', {})
            restaurant = ra['restaurant']
            
            for item in analysis.get('top_menus', []):
                menu = item.get('menu')
                if not menu: continue
                if menu not in menu_scores:
                    menu_scores[menu] = {'menu': menu, 'mentions': 0, 'restaurants': [], 'sentiments': [], 'summaries': []}
                
                menu_scores[menu]['mentions'] += item.get('mention_count', 1)
                menu_scores[menu]['restaurants'].append(restaurant)
                menu_scores[menu]['sentiments'].append(item.get('sentiment', '중립'))
                menu_scores[menu]['summaries'].append(item.get('summary', ''))

        recommendations = []
        for menu, data in sorted(menu_scores.items(), key=lambda x: x[1]['mentions'], reverse=True):
             pos = data['sentiments'].count('긍정')
             total = len(data['sentiments'])
             conf = (pos / total) if total > 0 else 0.5
             
             recommendations.append({
                 'menu': menu,
                 'confidence': conf,
                 'restaurants': data['restaurants'][:3],
                 'reasoning': f"{len(data['restaurants'])}곳에서 추천함 (긍정 {pos}회)",
                 'review_summary': data['summaries'][0] if data['summaries'] else ""
             })
        return recommendations

    def _generate_conversational_response(self, recommendations: List[Dict], user_context: Optional[str]) -> str:
        if not recommendations: return "추천할 메뉴를 찾지 못했습니다."
        top = ", ".join([r['menu'] for r in recommendations[:3]])
        
        prompt = f"상황: '{user_context or '선택 없음'}'\n추천: {top}\n사용자에게 친근하게 한 문장으로 추천해주세요."
        try:
            resp = self.client.models.generate_content(model=self.model_name, contents=prompt)
            return resp.text.strip()
        except:
             return f"'{recommendations[0]['menu']}' 메뉴는 어떠세요?"
