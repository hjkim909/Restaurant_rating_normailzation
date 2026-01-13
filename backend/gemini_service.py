"""
Gemini AI Service for Restaurant Recommendation

Uses Google Gemini API with Google Search grounding to analyze Naver Place reviews
and provide personalized menu recommendations.

Key Features:
- Google Search grounding for automatic review fetching
- Parallel processing for multiple restaurants
- Conversational context support
- Review-based confidence scoring
"""

import os
import time
import json
import logging
from typing import List, Dict, Generator, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import google.generativeai as genai
except ImportError:
    genai = None
    logging.warning("google-generativeai not installed. AI mode will not work.")

from backend.db_manager import DatabaseManager


class GeminiRecommendationService:
    """
    Gemini-powered restaurant recommendation service.

    Analyzes Naver Place reviews using Google Search grounding to provide
    context-aware menu recommendations with reasoning.
    """

    def __init__(self, api_key: str):
        """
        Initialize Gemini service.

        Args:
            api_key: Google Gemini API key
        """
        if genai is None:
            raise ImportError("google-generativeai package not installed. Run: pip install google-generativeai")

        genai.configure(api_key=api_key)

        # Use Flash for speed (meets 10-30s target)
        self.model = genai.GenerativeModel(
            'gemini-1.5-flash',
            tools='google_search_retrieval'  # Enable Google Search grounding
        )

        self.db = DatabaseManager()
        self.logger = logging.getLogger(__name__)

    def analyze_restaurants_for_menu(
        self,
        restaurants: List[Dict],
        user_context: str = None,
        max_restaurants: int = 10
    ) -> Dict:
        """
        Analyze restaurants using Google Search grounding to fetch reviews.

        Args:
            restaurants: List of restaurant dictionaries from API
            user_context: Optional user context (e.g., "오늘 속이 안 좋아")
            max_restaurants: Maximum number of restaurants to analyze

        Returns:
            Dict with:
                - recommendations: List of menu recommendations with reasoning
                - conversational_response: Context-aware message
                - metadata: Processing info
        """
        start_time = time.time()

        self.logger.info(f"Starting AI analysis for {len(restaurants)} restaurants")

        # Step 1: Construct search queries for each restaurant
        search_queries = []
        for restaurant in restaurants[:max_restaurants]:
            query = self._construct_naver_place_query(restaurant)
            search_queries.append({
                'restaurant': restaurant,
                'search_query': query
            })

        # Step 2: Analyze reviews with Gemini (parallel)
        restaurant_analyses = self._parallel_analyze_reviews(search_queries)

        if not restaurant_analyses:
            self.logger.warning("No successful restaurant analyses")
            return {
                'recommendations': [],
                'conversational_response': '죄송합니다. 리뷰 분석 중 오류가 발생했습니다.',
                'metadata': {
                    'search_queries': [q['search_query'] for q in search_queries],
                    'processing_time': time.time() - start_time,
                    'error': 'No successful analyses'
                }
            }

        # Step 3: Aggregate and rank recommendations
        recommendations = self._aggregate_recommendations(
            restaurant_analyses,
            user_context
        )

        # Step 4: Generate conversational response
        conversational_response = self._generate_conversational_response(
            recommendations,
            user_context
        )

        processing_time = time.time() - start_time

        self.logger.info(f"AI analysis complete in {processing_time:.2f}s")

        return {
            'recommendations': recommendations[:5],  # Top 5
            'conversational_response': conversational_response,
            'metadata': {
                'search_queries': [q['search_query'] for q in search_queries],
                'processing_time': processing_time,
                'model': 'gemini-1.5-flash',
                'analyzed_count': len(restaurant_analyses)
            }
        }

    def _construct_naver_place_query(self, restaurant: Dict) -> str:
        """
        Construct optimal search query for Naver Place reviews.

        Args:
            restaurant: Restaurant dictionary with title, address, etc.

        Returns:
            Search query string
        """
        clean_title = restaurant.get('title', '').replace('<b>', '').replace('</b>', '')
        address = restaurant.get('address', '') or restaurant.get('roadAddress', '')

        # Extract location (e.g., "강남구 역삼동")
        location_parts = address.split()[:2] if address else []
        location = ' '.join(location_parts)

        # Construct search query that will find Naver Place page
        query = f"네이버 플레이스 {clean_title} {location} 리뷰"

        self.logger.debug(f"Constructed query: {query}")

        return query

    def _parallel_analyze_reviews(
        self,
        search_queries: List[Dict]
    ) -> List[Dict]:
        """
        Analyze multiple restaurants in parallel.

        Args:
            search_queries: List of dicts with 'restaurant' and 'search_query'

        Returns:
            List of analysis results
        """
        results = []

        # Use ThreadPoolExecutor for parallel API calls
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Submit all analysis tasks
            future_to_restaurant = {
                executor.submit(
                    self._analyze_single_restaurant,
                    sq['restaurant'],
                    sq['search_query']
                ): sq['restaurant']
                for sq in search_queries
            }

            # Collect results as they complete
            for future in as_completed(future_to_restaurant):
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                        self.logger.debug(f"Successfully analyzed: {result['restaurant'].get('title', 'Unknown')}")
                except Exception as e:
                    restaurant = future_to_restaurant[future]
                    self.logger.error(f"Error analyzing restaurant {restaurant.get('title', 'Unknown')}: {str(e)}")

        return results

    def _analyze_single_restaurant(
        self,
        restaurant: Dict,
        search_query: str
    ) -> Optional[Dict]:
        """
        Analyze a single restaurant using Gemini with Google Search.

        Args:
            restaurant: Restaurant dictionary
            search_query: Naver Place search query

        Returns:
            Analysis result or None on error
        """
        clean_title = restaurant.get('title', '').replace('<b>', '').replace('</b>', '')
        category = restaurant.get('category', '')

        # Construct analysis prompt
        prompt = f"""
다음 식당의 네이버 플레이스 리뷰를 검색하고 분석해주세요:

식당명: {clean_title}
카테고리: {category}
검색 쿼리: {search_query}

분석 내용:
1. 가장 많이 언급되는 메뉴 3개 (빈도수 기준)
2. 각 메뉴에 대한 평가 요약 (긍정/부정)
3. 점심 식사로 적합한지 평가 (1-10점)

JSON 형식으로 응답해주세요:
{{
  "top_menus": [
    {{
      "menu": "메뉴명",
      "mention_count": 숫자,
      "sentiment": "긍정/부정/중립",
      "summary": "간단한 요약"
    }}
  ],
  "lunch_suitability": 숫자,
  "overall_summary": "전체 요약"
}}
"""

        try:
            # Call Gemini with Google Search grounding
            response = self.model.generate_content(prompt)

            # Parse response
            response_text = response.text

            # Extract JSON (handle markdown code blocks)
            if '```json' in response_text:
                json_str = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                json_str = response_text.split('```')[1].split('```')[0].strip()
            else:
                json_str = response_text

            analysis = json.loads(json_str)

            return {
                'restaurant': restaurant,
                'analysis': analysis,
                'search_query': search_query
            }

        except json.JSONDecodeError as e:
            self.logger.error(f"JSON parse error for {clean_title}: {str(e)}")
            self.logger.debug(f"Response text: {response_text[:500]}")
            return None
        except Exception as e:
            self.logger.error(f"Error analyzing {clean_title}: {str(e)}")
            return None

    def _aggregate_recommendations(
        self,
        restaurant_analyses: List[Dict],
        user_context: Optional[str]
    ) -> List[Dict]:
        """
        Aggregate analyses into menu recommendations.

        Args:
            restaurant_analyses: List of analysis results
            user_context: Optional user context

        Returns:
            Ranked list of menu recommendations
        """
        # Count menu mentions across all restaurants
        menu_scores = {}

        for ra in restaurant_analyses:
            analysis = ra.get('analysis', {})
            restaurant = ra['restaurant']

            for menu_item in analysis.get('top_menus', []):
                menu_name = menu_item.get('menu', '')
                if not menu_name:
                    continue

                if menu_name not in menu_scores:
                    menu_scores[menu_name] = {
                        'menu': menu_name,
                        'total_mentions': 0,
                        'restaurants': [],
                        'sentiments': [],
                        'summaries': []
                    }

                menu_scores[menu_name]['total_mentions'] += menu_item.get('mention_count', 1)
                menu_scores[menu_name]['restaurants'].append(restaurant)
                menu_scores[menu_name]['sentiments'].append(menu_item.get('sentiment', '중립'))
                menu_scores[menu_name]['summaries'].append(menu_item.get('summary', ''))

        # Convert to ranked recommendations
        recommendations = []

        for menu, data in sorted(
            menu_scores.items(),
            key=lambda x: x[1]['total_mentions'],
            reverse=True
        ):
            # Calculate confidence score
            positive_count = data['sentiments'].count('긍정')
            total_sentiments = len(data['sentiments'])
            confidence = min(1.0, positive_count / total_sentiments) if total_sentiments > 0 else 0.5

            # Generate reasoning
            reasoning = self._generate_reasoning(data)

            recommendations.append({
                'menu': menu,
                'confidence': confidence,
                'restaurants': data['restaurants'][:3],  # Top 3
                'reasoning': reasoning,
                'review_summary': '. '.join([s for s in data['summaries'][:3] if s])
            })

        return recommendations

    def _generate_reasoning(self, menu_data: Dict) -> str:
        """
        Generate natural language reasoning for recommendation.

        Args:
            menu_data: Menu aggregation data

        Returns:
            Reasoning string
        """
        menu = menu_data['menu']
        mention_count = menu_data['total_mentions']
        restaurant_count = len(menu_data['restaurants'])

        positive_count = menu_data['sentiments'].count('긍정')

        reasoning = f"{menu}는 {restaurant_count}개 식당에서 총 {mention_count}번 언급되었습니다. "

        if positive_count >= restaurant_count * 0.7:
            reasoning += f"리뷰의 {positive_count}/{restaurant_count}가 긍정적이어서 추천드립니다."
        else:
            reasoning += "여러 고객들이 주문했던 메뉴입니다."

        return reasoning

    def _generate_conversational_response(
        self,
        recommendations: List[Dict],
        user_context: Optional[str]
    ) -> str:
        """
        Generate conversational recommendation.

        Args:
            recommendations: List of menu recommendations
            user_context: Optional user context

        Returns:
            Conversational response string
        """
        if not recommendations:
            return "죄송합니다. 추천할 메뉴를 찾지 못했습니다."

        if not user_context:
            return f"주변 리뷰를 분석한 결과, '{recommendations[0]['menu']}'를 가장 추천드립니다!"

        # Use Gemini to generate contextual response
        top_menus = ', '.join([r['menu'] for r in recommendations[:3]])
        prompt = f"""
사용자 상황: {user_context}
추천 메뉴: {top_menus}

사용자 상황에 맞춰 한 문장으로 메뉴를 추천해주세요. 친근하고 자연스럽게.
"""

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            self.logger.error(f"Error generating conversational response: {str(e)}")
            return f"'{recommendations[0]['menu']}'는 어떠세요?"
