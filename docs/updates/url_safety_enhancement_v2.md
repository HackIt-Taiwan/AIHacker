# URL Safety Enhancement: Advanced Local URL Expansion Update

## Summary
This update significantly improves the URL safety module by implementing a recursive local URL expansion system that no longer relies on external APIs like unshorten.me. The new implementation can detect and follow multiple redirect layers, including HTTP redirects, meta refreshes, and JavaScript redirects, with specific handling for various URL shorteners including `shorturl.at` and `reurl.cc`.

## Key Improvements

1. **Recursive URL Expansion**: Implements a depth-first approach to follow multiple layers of redirects (up to a configurable maximum to prevent infinite loops).

2. **Comprehensive Shortener Detection**: Adds enhanced pattern detection for many URL shorteners, with specific patterns for:
   - bit.ly
   - t.co
   - tinyurl.com
   - shorturl.at
   - reurl.cc
   - And generic patterns that work across multiple shorteners

3. **Multi-type Redirect Handling**:
   - HTTP 301/302/303/307/308 redirects
   - Meta refresh redirects
   - JavaScript-based redirects
   - Shortener-specific redirect mechanisms

4. **Browser Emulation**: Uses modern browser-like headers to bypass bot detection.

5. **Cycle Detection**: Prevents redirect loops by tracking visited URLs.

6. **Enhanced Performance**: Fully asynchronous implementation for better concurrency.

7. **Improved Error Handling**: Gracefully handles failures at any step in the redirect chain.

## Technical Changes

### URL Expansion Process

The improved implementation uses the following approach:

1. When checking URLs, the system now uses `_expand_url_recursive` to follow redirects recursively.
2. For each URL, it performs a GET request with browser-like headers and disabled auto-redirects.
3. For HTTP redirects (status codes 301-308), it extracts the `Location` header and follows it recursively.
4. For 200 responses, it examines the HTML content for:
   - Meta refresh tags
   - JavaScript redirects
   - Shortener-specific patterns (domain-specific and generic)
5. All relative URLs are properly resolved to absolute URLs before following.
6. The system maintains a limit on redirect depth to prevent infinite loops.

### Expanded Shortener Detection

The new system uses a comprehensive set of patterns to detect redirects:

- **Domain-specific patterns**: Custom regex patterns for popular URL shorteners
- **Generic patterns**: Common patterns found across multiple shorteners:
  - Meta tags (OpenGraph, Twitter)
  - Input fields with URLs
  - JavaScript redirects and variables
  - Click-through links with specific text
  - Main buttons on the page
  - Base64 encoded URLs

## API Changes

The public API functions remain the same:

```python
async def check_url(self, url: str) -> Dict[str, Any]
async def check_urls(self, urls: List[str]) -> Dict[str, List[Dict[str, Any]]]
def extract_urls(self, text: str) -> List[str]
```

### Response Format

The URL check response includes:

```python
{
    "original_url": "https://shorturl.at/example",
    "expanded_url": "https://actual-destination.com/page",
    "is_safe": True/False,
    "threats": ["MALWARE", "PHISHING", etc.],  # If any detected
    "domain_category": "SOCIAL_MEDIA",  # Domain categorization
    "domain_reputation": 0.93,  # Domain reputation score (0-1)
    "is_impersonating": False,  # Domain impersonation detection
    "redirects": 2,  # Number of redirects followed
    "shortener_detected": True  # Whether a URL shortener was detected
}
```

## Usage Example

No changes in usage are required. The URL safety module is used in the same way:

```python
# Example usage in your application
from app.ai.service.url_safety import URLSafetyService

async def check_message_safety(message_content):
    url_service = URLSafetyService()
    urls = url_service.extract_urls(message_content)
    if urls:
        results = await url_service.check_urls(urls)
        # Process safety results
        return results
    return None
```

## Testing

This implementation has been tested with various URL shorteners, including:
- shorturl.at
- reurl.cc
- bit.ly
- t.co
- tinyurl.com
- goo.gl
- is.gd
- and others

Testing confirmed successful expansion of URLs with multiple levels of redirection, including:
- Chained URL shorteners
- Meta refresh redirects
- JavaScript-based redirects
- Mixed redirect types

## Debugging and Logging

Enhanced logging has been added to track the expansion process:
- Detailed logs of redirect chains
- URL shortener detection
- Parsing errors
- Expansion failures

Debug logs can be used to monitor successful expansions and identify patterns that may need additional handling.

## Additional Notes

1. This implementation no longer relies on external services, improving reliability and reducing potential rate limiting issues.

2. The module maintains a timeout limit for each request to prevent hanging on slow or malicious services.

3. Future improvements could include:
   - Rate limiting for domains to prevent abuse
   - Caching of expansion results for improved performance
   - Additional patterns for newly discovered URL shorteners 