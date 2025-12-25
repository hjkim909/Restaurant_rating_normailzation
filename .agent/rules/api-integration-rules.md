---
trigger: always_on
---

# API Integration Project Rules

## Project Context
- This project integrates external APIs (Naver, Kakao, etc.)
- Budget: free tiers only
- Error tolerance: high (graceful degradation)

## API Client Design
- Create a dedicated client class per API
- Example structure:
```python
  class NaverPlaceAPI:
      def __init__(self, client_id, client_secret):
          self.client_id = client_id
          self.client_secret = client_secret
          self.base_url = "https://openapi.naver.com"
      
      def search_places(self, query, location):
          # implementation
```

## Rate Limiting
- Track API usage (log each call)
- Add warnings when approaching free tier limits
- Implement exponential backoff for rate limit errors

## Caching
- Cache API responses for 1 hour (use simple dict or Redis)
- Cache key format: f"{endpoint}:{params_hash}"
- Clear cache daily to prevent stale data

## Error Handling
- Distinguish between:
  - Network errors (retry)
  - Auth errors (fail fast, check API keys)
  - Rate limit errors (wait and retry)
  - Data errors (log and continue)

## Response Processing
- Validate API responses with assertions
- Extract only needed fields (don't keep full responses)
- Convert timestamps to datetime objects immediately

## Logging
- Log all API calls with: timestamp, endpoint, params, status
- Log to CSV file for easy analysis
- Rotate logs weekly