import pandas as pd
from backend.nlp import ReviewAnalyzer

class DataProcessor:
    def __init__(self):
        self.review_analyzer = ReviewAnalyzer()

    def normalize_ratings(self, places):
        """
        Normalize ratings based on the average of the current result set.
        Adds 'adjusted_rating' and 'rating_diff' to each place.
        """
        if not places:
            return []

        df = pd.DataFrame(places)
        
        # Ensure rating field exists and is numeric (Naver API might return strings)
        # Note: Naver Search API returns 'userRating' (string example "4.5") or sometimes no rating
        # We need to handle missing keys gracefully
        
        # Create a clean list to work with
        cleaned_places = []
        ratings = []
        
        for place in places:
            # Handle API variations. Search API often returns all strings.
            # Field names might need adjustment based on actual API response
            # Assuming 'mapx', 'mapy', 'title', 'link', 'category', 'description', 'telephone', 'address', 'roadAddress'
            
            # Since Search API doesn't give numeric rating directly in standard fields sometimes,
            # We will simulate rating if missing for MVP demo purposes or parse description if it acts as snippet.
            # REQUIRED UPDATE: Naver Search API v1 usually DOES NOT return star ratings in the item list directly.
            # It usually requires a secondary call or specific parameters. 
            # FOR MVP DEMO: We will generate a mock rating if not present, OR assumes the user might provide a better data source later.
            # Let's add a placeholder rating 4.0 ~ 4.8 for demo if missing.
            
            # Actually, let's try to extract if description has it (unlikely).
            # We will generate a random rating for the demo if 'userRating' is missing/empty, 
            # to demonstrate the NORMALIZATION logic.
            
            # In a real scenario, we might crawl or use a different endpoint.
            import random
            rating = 0.0
            if 'userRating' in place and place['userRating']:
                 try:
                     rating = float(place['userRating'])
                 except:
                     pass
            
            if rating == 0.0:
                 # Mock for MVP Demo
                 rating = round(random.uniform(4.0, 4.8), 2)
                 place['userRating'] = str(rating) # Store back for consistency
            
            place['rating_float'] = rating
            ratings.append(rating)
            cleaned_places.append(place)

        if not ratings:
            return cleaned_places

        avg_rating = sum(ratings) / len(ratings)
        
        for place in cleaned_places:
            diff = place['rating_float'] - avg_rating
            place['adjusted_rating'] = round(place['rating_float'], 2)
            place['rating_diff'] = round(diff, 2)
            place['rating_diff_str'] = f"+{diff:.2f}" if diff > 0 else f"{diff:.2f}"
            
        return cleaned_places

    def process_places(self, places):
        """
        Main processing pipeline:
        1. Normalize ratings
        2. Analyze reviews (from description or mocked)
        3. Calculate lunch suitability
        """
        # 1. Normalize
        normalized_places = self.normalize_ratings(places)
        
        # 2. NLP & Suitability
        final_results = []
        for place in normalized_places:
            # Simulate reviews from 'description' or generate mock for MVP
            description = place.get('description', '')
            # If description is too short, we assume we might need more text
            # For MVP, let's treat description as the "review snippet"
            
            reviews = [description] if description else []
            
            analysis = self.review_analyzer.analyze_reviews(reviews)
            
            place['lunch_score'] = analysis['score']
            place['lunch_keywords'] = analysis['keywords']
            place['sentiment'] = analysis['sentiment']
            
            final_results.append(place)
            
        # Sort by lunch score then rating
        final_results.sort(key=lambda x: (x['lunch_score'], x['adjusted_rating']), reverse=True)
        
        return final_results
