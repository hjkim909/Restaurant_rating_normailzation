from collections import Counter
import re

class MenuRecommender:
    def __init__(self):
        # Common generic terms to ignore
        self.stop_words = {
            "음식점", "식당", "맛집", "한식", "양식", "중식", "일식", "분식", 
            "전문점", "요리", "집", "카페", "디저트", "입구", "거리", "역"
        }

    def extract_top_menus(self, places, top_n=5):
        """
        Extract popular menu keywords from a list of places.
        Focuses on places with valid lunch scores.
        """
        # Filter for decent lunch places (score >= 50)
        target_places = [p for p in places if p.get('lunch_score', 0) >= 50]
        
        if not target_places:
            return []

        keywords = []
        
        for place in target_places:
            # 1. Extract from Category
            # Format often: "한식 > 찌개,전골" or just "김치찌개"
            category = place.get('category', '')
            if category:
                # Split by '>' or ','
                parts = re.split(r'[>,]', category)
                for part in parts:
                    clean_part = part.strip()
                    if len(clean_part) > 1 and clean_part not in self.stop_words:
                        keywords.append(clean_part)
            
            # 2. Extract from Title (sometimes)
            # e.g., "시골김치찌개" -> "김치찌개" extraction is hard without heavy NLP.
            # But sometimes title IS the menu name e.g. "마포만두".
            # For now, let's rely mostly on category and description keywords if available.
            
            # 3. Description checks?
            # If description contains known menu names, add them?
            # Simple heuristic: if description has "돈까스", add it.
            # This requires a predefined menu dictionary which we don't have yet.
            # So we stick to Category data which Naver usually provides well.

        # Count frequencies
        counter = Counter(keywords)
        
        # Return top N most common
        return [item for item, count in counter.most_common(top_n)]
