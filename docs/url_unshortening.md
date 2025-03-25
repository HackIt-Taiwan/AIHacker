# URL Unshortening Feature

## Overview

The URL unshortening feature enhances the security of the bot by expanding shortened URLs before they undergo safety checks. This helps detect potentially malicious links that might be hidden behind URL shorteners like bit.ly, tinyurl.com, and others.

## How It Works

1. When a message containing URLs is processed, the bot first extracts all URLs.
2. Before performing safety checks, the bot attempts to unshorten each URL using multiple methods:
   - HTTP requests with appropriate headers
   - Selenium headless browser simulation (if available)
   - Special handlers for popular URL shorteners

3. Once the final destination URLs are obtained, they are passed to the URL safety checker.
4. This approach provides more accurate safety assessment by revealing the actual destination behind shortened links.

## Configuration

The URL unshortening feature can be configured via the following environment variables in `.env`:

```
# URL Unshortening Configuration
URL_UNSHORTEN_ENABLED=True         # Enable or disable URL unshortening (True/False)
URL_UNSHORTEN_TIMEOUT=5.0          # Timeout in seconds for unshortening requests
URL_UNSHORTEN_MAX_REDIRECTS=10     # Maximum number of redirects to follow
URL_UNSHORTEN_RETRY_COUNT=2        # Number of retries for failed unshortening attempts
```

## Integration with URL Safety Check

The URL unshortening feature integrates seamlessly with the existing URL safety checking system:

1. URLs are first extracted from message content
2. If there are more than the maximum allowed URLs to check, a random sample is selected
3. Each URL in the sample is unshortened to reveal its final destination
4. The final URLs are checked for safety using the configured safety checking API
5. Results are returned mapping the original URLs to their safety assessment

## Implementation Details

### Methods Used

The unshortener employs multiple methods to ensure the highest success rate:

1. **Standard HTTP Method**: Uses HTTP requests with appropriate headers to follow redirects
2. **JavaScript Redirect Detection**: Analyzes HTML responses for JavaScript-based redirects
3. **Headless Browser Simulation**: Uses Selenium (when available) to handle complex redirects that require JavaScript execution
4. **Special Domain Handlers**: Custom logic for popular URL shorteners like bit.ly, t.co, goo.gl, etc.

### Performance Considerations

- The system first tries the faster HTTP method
- Only falls back to Selenium for URLs that cannot be resolved with the HTTP method
- Employs parallel processing to unshorten multiple URLs efficiently

## Requirements

- Python 3.7+
- aiohttp
- Selenium (optional, for advanced unshortening capabilities)
- Chrome WebDriver (if using Selenium)

## Selenium Installation (Optional)

For enhanced unshortening capabilities, you can install Selenium and Chrome WebDriver:

```bash
pip install selenium
```

Then download the appropriate Chrome WebDriver for your system from:
https://sites.google.com/a/chromium.org/chromedriver/downloads

## Logging

The URL unshortener logs detailed information about its operations:

- Successful unshortening operations with original and final URLs
- Failed unshortening attempts with error details
- Performance metrics (time taken for each operation)

Log level can be controlled via the `LOG_LEVEL` environment variable. 