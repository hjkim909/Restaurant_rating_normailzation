import re

class ReviewAnalyzer:
    def __init__(self):
        # Keywords based on PRD
        self.positive_keywords = [
            r"빠르다", r"빨라", r"빠름", 
            r"회전율", r"빨리",
            r"점심", r"음식.*나오", # Context: lunch, food coming out
            r"혼밥"
        ]
        self.negative_keywords = [
            r"느리다", r"느려", r"느림", r"늦게",
            r"웨이팅", r"대기", r"기다림",
            r"오래", r"정신없다"
        ]
        
    def analyze_reviews(self, reviews):
        """
        Analyze a list of review texts.
        Returns a dictionary with score and extracted keywords.
        """
        if not reviews:
            return {
                "score": 0,
                "sentiment": "Unknown",
                "keywords": []
            }
            
        total_score = 0
        extracted_keywords = set()
        
        for review in reviews:
            # Simple scoring
            for kw in self.positive_keywords:
                if re.search(kw, review):
                    total_score += 10
                    extracted_keywords.add(kw.replace(r".*", " ")) # Clean up regex for display
            
            for kw in self.negative_keywords:
                if re.search(kw, review):
                    total_score -= 10
                    extracted_keywords.add(kw)

        # Normalize score to 0-100 scale (approximation)
        # Base score 50, max 100, min 0
        final_score = 50 + total_score
        final_score = max(0, min(100, final_score))
        
        return {
            "score": final_score,
            "sentiment": "Good" if final_score >= 70 else ("Bad" if final_score <= 30 else "Neutral"),
            "keywords": list(extracted_keywords)
        }

if __name__ == "__main__":
    # Test
    analyzer = ReviewAnalyzer()
    sample_reviews = [
        "음식이 빨리 나와서 좋아요",
        "점심시간에 웨이팅이 좀 있네요",
        "맛은 있는데 너무 늦게 나와요"
    ]
    print(analyzer.analyze_reviews(sample_reviews))
