# URL Safety Module Enhancement

## Overview

The URL safety module has been completely rewritten to significantly improve short URL detection and tracking capabilities. This update focuses on:

1. Enhanced short URL expansion with advanced local methods
2. Improved redirection tracking
3. Better domain impersonation detection
4. More reliable detection of suspicious URLs

## Key Improvements

### Advanced Local URL Expansion Methods

- **Multiple Browser Emulation** - Uses various user agent strings to bypass bot detection
- **Service-Specific Parsers** - Custom parsers for common URL shorteners (bit.ly, t.co, tinyurl.com, etc.)
- **Advanced JavaScript Redirect Detection** - Pattern matching for over 15 different types of JS redirects
- **Shortener-Specific Pattern Recognition** - Identifies unique patterns used by popular URL shorteners
- **Concurrent Processing** - Processes multiple URLs in parallel for better performance

### Enhanced Redirect Detection

- **Multi-Layer Redirect Following** - Automatically follows chains of redirects
- **Meta Refresh Detection** - Identifies HTML meta refresh redirects
- **JavaScript Redirect Analysis** - Detects window.location, setTimeout, and other JS redirect methods
- **Base64 URL Decoding** - Finds and decodes obfuscated base64-encoded URLs

### API Integration

The module continues to support both VirusTotal and Google Safe Browsing APIs with improved integration:

- More reliable API result handling
- Enhanced retry logic with exponential backoff
- Better error handling and recovery

### Local Pattern Detection

Even without API access, the system can detect:

- Domain impersonation and typosquatting
- Suspicious path patterns (gifts, free items, etc.)
- Attempts to hide malicious content behind URL shorteners

## API Changes

### Main Functions

- `extract_urls(text)`: Extracts all URLs from text
- `check_urls(urls)`: Checks multiple URLs for safety, including expanding short URLs
- `check_url(url)`: Checks a single URL for safety

### Response Format

URL check results now include:

```json
{
  "url": "https://example.com",
  "is_unsafe": true|false,
  "unsafe_score": 0.8,  // Score between 0-1
  "threat_types": ["PHISHING", "SUSPICIOUS"],
  "severity": 9,
  "reason": "Domain appears to be typosquatting example.com",
  "check_time": "2023-03-25T12:34:56.789Z"
}
```

For short URLs, additional fields are included:

```json
{
  "url": "https://bit.ly/abc123",
  "expanded_url": "https://malicious-site.com",
  "is_unsafe": true,
  "redirected": true,
  "reason": "Redirects to unsafe URL: https://malicious-site.com"
}
```

## Configuration

The module uses the following configuration parameters from `config.py`:

- `URL_SAFETY_CHECK_API`: API provider ('virustotal' or 'googlesafe')
- `URL_SAFETY_API_KEY`: API key for the selected provider
- `URL_SAFETY_THRESHOLD`: Score threshold for marking URLs as unsafe (0.0-1.0)
- `URL_SAFETY_MAX_RETRIES`: Maximum retry attempts for API calls
- `URL_SAFETY_RETRY_DELAY`: Base delay in seconds between retries
- `URL_SAFETY_REQUEST_TIMEOUT`: Timeout for HTTP requests
- `URL_SAFETY_IMPERSONATION_DOMAINS`: List of known phishing domains

## Usage Example

```python
from app.ai.service.url_safety import URLSafetyChecker

async def check_message_safety(message_content):
    checker = URLSafetyChecker()
    
    # Extract URLs from message
    urls = await checker.extract_urls(message_content)
    
    if urls:
        # Check all URLs for safety
        is_unsafe, results = await checker.check_urls(urls)
        
        if is_unsafe:
            # Handle unsafe URL detection
            unsafe_urls = [url for url, result in results.items() if result.get('is_unsafe')]
            print(f"Detected {len(unsafe_urls)} unsafe URLs: {unsafe_urls}")
            return False
    
    return True
```

## Technical Details

### URL Expansion Process

The URL expansion system now uses a multi-phase approach:

1. **URL Identification** - Detect if a URL is from a known shortener service
2. **Advanced GET Request** - Try expanding with sophisticated browser headers
3. **Multiple User Agents** - If first method fails, try with multiple browser identities
4. **Service-Specific Parsing** - Use shortener-specific extraction for popular services
5. **Advanced JS Detection** - Parse HTML for various JavaScript redirect techniques

### Pattern Matching Capabilities

The module can detect:

- Standard HTTP 301/302 redirects
- HTML meta refresh redirects
- JavaScript window.location redirects
- JavaScript setTimeout-based redirects
- Base64-encoded redirect URLs
- Variable-based redirects (where URL is stored in a variable)
- Service-specific redirect formats (bit.ly, t.co, etc.)
- Click-through redirect pages

## Notes

- The module is fully asynchronous for better performance
- No longer relies on external URL expansion services
- Error handling has been improved throughout
- Logging is comprehensive for debugging and monitoring 