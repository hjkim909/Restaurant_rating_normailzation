import os
import time
import json
import re
import logging
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from google import genai
    from google.genai import types
except ImportError as e:
    genai = None
    types = None
    import_error_msg = str(e)
    logging.warning(f"google-genai not installed: {e}")

from fastapi_app.core.config import get_settings

class GeminiService:
    def __init__(self):
        self.settings = get_settings()
        self.error_reason = None
        
        if not self.settings.GEMINI_API_KEY:
             logging.warning("GEMINI_API_KEY not found.")
             self.client = None
             self.error_reason = "API Key not configured"
             return

        if genai is None:
             self.client = None
             self.error_reason = f"Lib missing: {import_error_msg}"
             return

        try:
            self.client = genai.Client(api_key=self.settings.GEMINI_API_KEY)
            # Why: gemini-2.0-flash-lite는 무료 tier 쿼타가 더 높음 (RPM 30 vs 15)
            self.model_name = 'gemini-2.0-flash-lite'
            self.search_tool = types.Tool(
                google_search=types.GoogleSearch()
            )
            self.logger = logging.getLogger(__name__)
        except Exception as e:
            self.client = None
            self.error_reason = f"Init failed: {str(e)}"

    def analyze_restaurants_for_menu(
        self,
        restaurants: List[Dict],
        user_context: str = None,
        max_restaurants: int = 5 
    ) -> Dict:
        """기존 메뉴 기반 분석 (하위 호환용)"""
        return self.analyze_restaurants_for_context(restaurants, user_context, max_restaurants)

    def analyze_restaurants_for_context(
        self,
        restaurants: List[Dict],
        user_context: str = None,
        max_restaurants: int = 8
    ) -> Dict:
        """상황 기반 식당 추천 (개선된 버전)"""
        if not self.client:
            # AI 서비스 불가 시에도 AIResponse 형식으로 반환
            msg = f"AI 서비스 불가 ({self.error_reason})" if self.error_reason else "AI 서비스 연결 실패"
            return self._fallback_recommendations(restaurants, max_restaurants, msg)

        # 식당 정보 요약 생성
        restaurant_summaries = []
        for i, r in enumerate(restaurants[:max_restaurants]):
            clean_title = r.get('title', '').replace('<b>', '').replace('</b>', '')
            category = r.get('category', '알 수 없음')
            address = r.get('roadAddress', '') or r.get('address', '')
            rating = r.get('rating', 'N/A')
            restaurant_summaries.append(
                f"{i+1}. {clean_title} ({category}) - {address}, 평점: {rating}"
            )
        
        restaurants_text = "\n".join(restaurant_summaries)

        prompt = f"""
사용자 상황: {user_context or '맛있는 점심 추천'}

아래 식당 목록에서 사용자 상황에 가장 적합한 3곳을 선정해주세요.
각 식당에 대해 구글 검색을 통해 리뷰와 특징을 파악하고, 왜 이 상황에 적합한지 설명해주세요.

식당 목록:
{restaurants_text}

중요 지침:
- 사용자 상황(혼밥/다이어트/회식/데이트 등)에 맞는 식당을 우선 선정
- 리뷰에서 관련 키워드(1인석, 분위기, 양, 가격 등)를 찾아 근거 제시
- 확신이 없으면 가장 평점이 높은 곳 추천

JSON 형식으로 응답:
{{
  "recommendations": [
    {{
      "index": 1,
      "name": "식당명",
      "reason": "추천 이유 (2-3문장)",
      "confidence": 0.9,
      "keywords": ["혼밥 가능", "빠른 식사"]
    }}
  ],
  "summary": "사용자에게 전할 친근한 한 문장 요약"
}}
"""

        # 전략: GoogleSearch 있는 모드 시도 → 429 시 GoogleSearch 없는 경량 모드 → 최종 fallback
        # Why: GoogleSearch가 토큰을 많이 소모하므로, 429 시 검색 없이 식당 목록만으로 분석
        last_error = None
        
        # 1차 시도: GoogleSearch Tool 포함 (고품질)
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[self.search_tool],
                    temperature=0.7,
                )
            )
            
            result = self._process_ai_response(response.text, restaurants)
            if result:
                return result
                
        except Exception as e:
            last_error = e
            error_str = str(e)
            if '429' in error_str or 'RESOURCE_EXHAUSTED' in error_str:
                self.logger.warning("GoogleSearch 모드 429 에러, 경량 모드로 전환...")
            else:
                self.logger.error(f"AI Error (GoogleSearch mode): {e}")
        
        # 2차 시도: GoogleSearch 없는 경량 모드 (쿼타 절약)
        try:
            self.logger.info("경량 AI 분석 모드 실행 (GoogleSearch 없음)")
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    # Why: GoogleSearch 제거로 쿼타 대폭 절약, JSON 모드 사용 가능
                    response_mime_type="application/json",
                )
            )
            
            result = self._process_ai_response(response.text, restaurants)
            if result:
                return result
                
        except Exception as e:
            last_error = e
            self.logger.error(f"AI Error (lightweight mode): {e}")
        
        print(f"AI Error (all modes failed): {last_error}")
        return self._fallback_recommendations(restaurants, max_restaurants)
    
    def _process_ai_response(self, response_text: str, restaurants: List[Dict]) -> Optional[Dict]:
        """AI 응답 텍스트를 파싱하여 추천 결과로 변환"""
        data = self._parse_json_from_text(response_text)
        if not data or not data.get('recommendations'):
            return None
        
        recommendations = []
        for rec in data.get('recommendations', [])[:3]:
            idx = rec.get('index', 1) - 1
            if 0 <= idx < len(restaurants):
                original = restaurants[idx]
                recommendations.append({
                    'menu': rec.get('name', original.get('title', '')).replace('<b>', '').replace('</b>', ''),
                    'confidence': rec.get('confidence', 0.7),
                    'reasoning': rec.get('reason', '추천 식당입니다.'),
                    'keywords': rec.get('keywords', []),
                    'restaurants': [original]
                })
        
        if not recommendations:
            return None
            
        return {
            'recommendations': recommendations,
            'conversational_response': data.get('summary', '맛있는 식사 되세요!')
        }

    
    def _fallback_recommendations(self, restaurants: List[Dict], max_restaurants: int, message: str = None) -> Dict:
        """AI 실패 시 거리+평점 기반 폴백 추천
        
        Why: AI가 사용 불가할 때도 사용자에게 의미 있는 추천 제공.
        거리(가까운 순)와 평점(높은 순)을 함께 고려하여 정렬.
        """
        def safe_rating(r):
            try:
                val = r.get('rating') or r.get('userRating') or 0
                return float(val) if val else 0.0
            except (ValueError, TypeError):
                return 0.0
        
        def safe_distance(r):
            try:
                return float(r.get('distance', 999999))
            except (ValueError, TypeError):
                return 999999
        
        # 거리순으로 먼저 필터 (가까운 곳 우선), 그 중 평점 높은 순
        candidates = restaurants[:max_restaurants]
        # 거리 정보가 있는 경우 거리+평점 하이브리드 정렬
        has_distance = any(r.get('distance') for r in candidates)
        if has_distance:
            sorted_restaurants = sorted(
                candidates,
                key=lambda r: (-safe_rating(r), safe_distance(r))
            )[:3]
        else:
            sorted_restaurants = sorted(
                candidates,
                key=safe_rating,
                reverse=True
            )[:3]
        
        # 음식점 카테고리가 아닌 것 필터 (카페, 편의점 등 제외)
        food_categories = ['한식', '중식', '일식', '양식', '분식', '음식점', '매운탕', '치킨', '피자', '햄버거', '국밥', '고기']
        filtered = [r for r in sorted_restaurants if any(cat in (r.get('category', '') or '') for cat in food_categories)]
        if not filtered:
            filtered = sorted_restaurants  # 필터 후 없으면 원본 유지
        
        fallback_msg = message or '주변 인기 맛집을 추천해드릴게요! 🍽️'
        
        return {
            'recommendations': [
                {
                    'menu': r.get('title', '').replace('<b>', '').replace('</b>', ''),
                    'confidence': 0.6,
                    'reasoning': self._build_fallback_reason(r),
                    'keywords': [],
                    'restaurants': [r]
                }
                for r in filtered
            ],
            'conversational_response': fallback_msg
        }
    
    def _build_fallback_reason(self, r: Dict) -> str:
        """fallback 추천 이유 문구 생성"""
        parts = []
        rating = r.get('userRating') or r.get('rating')
        if rating:
            parts.append(f"평점 {rating}점")
        distance = r.get('distance')
        if distance:
            if distance < 1000:
                parts.append(f"도보 {int(distance)}m 거리")
            else:
                parts.append(f"{distance/1000:.1f}km 거리")
        category = r.get('category', '')
        if category:
            parts.append(f"{category.split('>')[-1].strip()} 전문")
        return ', '.join(parts) + '의 인기 맛집입니다.' if parts else '인기 식당입니다.'

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
                )
            )
            data = self._parse_json_from_text(response.text)
            return {'restaurant': restaurant, 'analysis': data}
        except Exception as e:
            print(f"AI Error ({clean_title}): {e}")
            return None

    def _parse_json_from_text(self, text: str) -> Dict:
        """Gemini 응답 텍스트에서 JSON 블록을 안전하게 추출
        
        Why: GoogleSearch Tool 사용 시 response_mime_type="application/json" 설정 불가.
        Gemini가 마크다운 코드블록이나 자유 텍스트 안에 JSON을 포함하여 응답하므로 파싱 필요.
        """
        if not text:
            return {}
        
        # 1차 시도: 전체 텍스트가 유효한 JSON인 경우
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # 2차 시도: ```json ... ``` 코드블록에서 추출
        code_block_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
        if code_block_match:
            try:
                return json.loads(code_block_match.group(1).strip())
            except json.JSONDecodeError:
                pass
        
        # 3차 시도: 첫 번째 { ... } 블록 추출 (중첩 브레이스 대응)
        brace_start = text.find('{')
        if brace_start != -1:
            depth = 0
            for i in range(brace_start, len(text)):
                if text[i] == '{':
                    depth += 1
                elif text[i] == '}':
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(text[brace_start:i+1])
                        except json.JSONDecodeError:
                            break
        
        self.logger.warning(f"JSON 파싱 실패. 원본 텍스트: {text[:200]}...")
        return {}

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
