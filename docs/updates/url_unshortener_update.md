# URL Unshortener Feature Update

**Date**: 2024-03-26

## Overview

We have added a new URL unshortening feature to the Discord bot that expands shortened URLs before security scanning. This update improves the bot's security by detecting potentially malicious links hidden behind URL shortening services.

## API Changes

### New Module

```python
from app.ai.service.url_unshortener import URLUnshortener
```

The new `URLUnshortener` class provides functionality to expand shortened URLs using multiple methods including HTTP requests, JavaScript redirect detection, and headless browser simulation when Selenium is available.

### Modified Functionality

The URL safety checking module now integrates with the URL unshortener, expanding shortened URLs before scanning them for threats:

```python
# Example usage
unshortener = URLUnshortener()
try:
    # Unshorten a single URL
    result = await unshortener.unshorten_url("https://bit.ly/example")
    final_url = result["final_url"]
    
    # Unshorten multiple URLs in parallel
    results = await unshortener.unshorten_urls(["https://bit.ly/example1", "https://tinyurl.com/example2"])
finally:
    unshortener.close()  # Important for cleanup
```

## Configuration

Add the following to your `.env` file to configure the URL unshortening feature:

```
# URL Unshortening Configuration
URL_UNSHORTEN_ENABLED=True         # Enable/disable URL unshortening
URL_UNSHORTEN_TIMEOUT=5.0          # Timeout in seconds for unshortening requests
URL_UNSHORTEN_MAX_REDIRECTS=10     # Maximum number of redirects to follow
URL_UNSHORTEN_RETRY_COUNT=2        # Number of retries for failed unshortening attempts
```

## Installation Requirements

The basic URL unshortening functionality requires no additional dependencies.

For enhanced capabilities with headless browser simulation, install Selenium:

```bash
pip install selenium
```

And download the appropriate Chrome WebDriver for your system.

## Usage Examples

### Basic Usage

```python
from app.ai.service.url_unshortener import URLUnshortener

async def main():
    unshortener = URLUnshortener()
    try:
        # Unshorten a URL
        result = await unshortener.unshorten_url("https://bit.ly/example")
        
        if result["success"]:
            print(f"Unshortened URL: {result['original_url']} -> {result['final_url']}")
            print(f"Method used: {result['method']}")
            print(f"Time taken: {result['elapsed_time']} seconds")
            
            if "redirect_history" in result:
                print("Redirect path:")
                for i, url in enumerate(result["redirect_history"]):
                    print(f"  {i+1}. {url}")
        else:
            print(f"Failed to unshorten URL: {result['error']}")
    finally:
        unshortener.close()
```

### Integration with URL Safety Checking

The integration with URL safety checking is now automatic. When URLs are extracted from a message, they will be unshortened before being checked for safety if the feature is enabled.

## Response Format

The unshortening operation returns a dictionary with the following information:

```json
{
  "original_url": "https://bit.ly/example",
  "final_url": "https://example.com/full-path",
  "success": true,
  "method": "requests",
  "redirect_count": 2,
  "redirect_history": [
    "https://bit.ly/example",
    "https://bitly.com/redirect",
    "https://example.com/full-path"
  ],
  "elapsed_time": 0.453
}
```

In case of failure:

```json
{
  "original_url": "https://bit.ly/example",
  "final_url": "https://bit.ly/example",
  "success": false,
  "method": "combined",
  "error": "Request error: Connection timeout"
}
```

## Troubleshooting

1. **URL unshortening is slow**: This might happen when using the Selenium method. You can adjust the timeout using the `URL_UNSHORTEN_TIMEOUT` setting.

2. **Selenium not working**: Make sure you have installed Selenium and the appropriate WebDriver for your system. The feature will fall back to the HTTP method if Selenium is unavailable.

3. **Excessive memory usage**: If you're processing many URLs and experiencing memory issues, consider reducing the `URL_SAFETY_MAX_URLS` setting to check fewer URLs at once. 