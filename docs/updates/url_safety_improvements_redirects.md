# URL Safety Check - Improved Redirect Handling

## Overview
This update significantly enhances the URL safety checker's ability to analyze redirected URLs, particularly those utilizing URL shorteners such as shorturl.at, bit.ly, etc. The system now performs comprehensive safety analysis on both the original shortened URL and its final destination URL.

## Key Improvements

### 1. Enhanced Redirect Resolution
- **Third-Party URL Expansion Services**: Added integration with multiple URL expansion services to reliably resolve shortened URLs
- **Service Cascading**: Implemented a fallback system that tries multiple expansion services until successful resolution
- **Improved GET Request Method**: Switched from HEAD to GET requests for redirect detection to better handle URL shorteners that don't properly respond to HEAD requests
- **Advanced Browser Emulation**: Added comprehensive browser emulation headers to bypass anti-bot protections on URL shortener services
- **Anti-Bot Protection Bypass**: Implemented multiple fallback strategies to handle services that actively block bot access
- **Meta Refresh Detection**: Added capability to detect and follow JavaScript and meta refresh redirects that don't use standard HTTP redirects
- **JavaScript Redirect Detection**: Added specialized detection of JavaScript-based redirects used by many URL shorteners
- **Special Handler for shorturl.at**: Implemented dedicated handling for shorturl.at URLs which use complex JavaScript-based redirects
- **Relative URL Handling**: Properly resolves relative URLs in redirects (e.g., when Location header contains "/path" instead of a full URL)

### 2. Comprehensive Safety Analysis of Redirect Chains
- **Full Chain Analysis**: Both shortened URLs and their destinations are now properly analyzed
- **Result Correlation**: Safety analysis results from the destination URL are properly tied back to the original shortened URL
- **Enhanced Result Structure**: Expanded result objects now contain clear information about redirect relationships
- **Simplified Logic**: Restructured URL checking logic for better clarity and consistency

### 3. Technical Improvements
- **Enhanced Logging**: Better logging of redirect chains and analysis steps
- **Robust Error Handling**: Improved error recovery when redirect resolution fails
- **Efficient Request Handling**: Minimized unnecessary API calls by linking original and destination URL results
- **External Service Integration**: Added integration with specialized URL expansion services:
  - urlexpander.io API for bulk URL expansion
  - unshorten.me service for reliable shortener resolution
  - expandurl.net for comprehensive URL chain expansion
- **Service Fallback Chain**: System tries each service in sequence until successful expansion
- **Multiple Fallback Approaches**: Implements a cascade of resolution techniques when primary methods fail:
  - Public API endpoints for URL shortener services
  - HTTP header redirects with browser-like headers
  - HTML content analysis for JavaScript redirects
  - Pattern matching for "Skip Ad" and "Continue" buttons
  - Alternative API formats for different shortener services
  - Direct access to redirect endpoints based on shortcode patterns
- **Multi-pattern Detection**: Uses multiple regex patterns to detect various forms of redirects including:
  - HTTP header redirects (301, 302, etc.)
  - META refresh tags
  - window.location.href JavaScript redirects
  - document.location JavaScript redirects
  - setTimeout-based delayed redirects
  - Button/link-based redirects in shorturl.at pages

## How It Works

### Redirect Resolution Process
1. When a URL is detected, the system checks if it matches any known URL shortener domains
2. For shorturl.at URLs, a multi-tier resolution system is used:
   - First tries specialized URL expansion services:
     - urlexpander.io API
     - unshorten.me service
     - expandurl.net service
   - If external services fail, falls back to direct methods with:
     - HEAD request with full redirect following
     - GET request with alternate User-Agent
     - JavaScript/Meta refresh detection if direct access succeeds
3. For other URLs, the system attempts to resolve the final destination by:
   - Making a GET request with browser-like headers
   - Following HTTP 301/302/303/307/308 redirects
   - Detecting and following META refresh tags in HTML responses
   - Detecting and following JavaScript redirects in HTML content
   - Properly handling relative URLs in redirect paths
4. Both the original shortened URL and the final destination URL are analyzed for safety

### Third-Party Expansion Services
The system now leverages specialized URL expansion services to handle the most difficult URL shorteners:

- **urlexpander.io**: 
  - Professional API service specialized in URL expansion
  - High success rate for most URL shorteners
  - Transparent redirect chain resolution

- **unshorten.me**:
  - Reliable service that handles a wide range of shorteners
  - Works well with shorturl.at and similar services
  - Returns full redirect information

- **expandurl.net**:
  - Provides comprehensive redirect chain analysis
  - Handles multi-step redirects effectively
  - Returns all URLs in the redirect chain

### Anti-Bot Protection Bypass
The system now employs sophisticated techniques to bypass anti-bot protections:
- **External Services**: Uses professional URL expansion services that are not blocked by shorteners
- **Complete Browser Headers**: Full set of browser-like headers including Accept, Accept-Language, Referer, etc.
- **Multiple Fallback Approaches**: If one method fails, the system tries alternative methods
- **API-Based Resolution**: Direct API calls to shortener services to bypass web interface restrictions
- **Direct Endpoint Access**: Attempts to directly access known redirect endpoints based on URL patterns
- **Error Recovery**: Graceful handling of various error conditions to ensure maximum reliability

### JavaScript Redirect Detection
The system now recognizes various JavaScript redirect techniques commonly used by URL shorteners:
- `window.location.href = 'https://destination.com';`
- `window.location = 'https://destination.com';`
- `document.location = 'https://destination.com';`
- `setTimeout(function() { window.location.href = 'https://destination.com'; }, 5000);`

Additionally, for shorturl.at specifically, we employ special HTML parsing to find:
- Links with specific CSS classes indicating they are destination links
- Contextual clues like "proceed to" or "continue to" text near links
- Form actions that might be handling redirects
- "Skip Ad" buttons and similar interactive elements

### Safety Analysis Flow
1. The system checks the destination URL first through:
   - Domain impersonation detection
   - VirusTotal or Google Safe Browsing API checks
   - Path keyword analysis
2. If the destination URL is deemed unsafe, the original shortened URL is automatically marked unsafe as well
3. Each URL in the chain gets a detailed safety result, with shortened URLs referencing their expanded forms

### Example Scenario
**Before the update:**
- User posts: `https://shorturl.at/ruo7Y`
- System would analyze only this direct URL
- System might miss malicious content at the destination

**After the update:**
- User posts: `https://shorturl.at/ruo7Y`
- System recognizes this as a shorturl.at URL and uses the specialized handler
- Handler first tries external expansion services (urlexpander.io, unshorten.me, etc.)
- If external services succeed, it gets the true destination URL
- If external services fail, it falls back to direct methods with anti-bot bypassing
- System fully analyzes both the shortener and destination
- If the destination is malicious, both URLs are marked as unsafe

## Implementation Details

### Key Code Changes
- Added integration with multiple URL expansion services (urlexpander.io, unshorten.me, expandurl.net)
- Implemented a service fallback chain to try multiple methods in sequence
- Added sophisticated browser emulation with full header sets
- Added multiple fallback approaches for resolving shortened URLs
- Implemented direct API access methods for shortener services
- Added specialized handler for shorturl.at URLs that detects JavaScript redirects
- Added general JavaScript redirect detection for all URLs
- Switched from `session.head()` to `session.get()` with appropriate headers for following redirects
- Added HTML parsing to detect meta refresh redirects
- Completely restructured the URL checking logic to properly handle redirect chains
- Enhanced result objects to include redirect relationship information
- Added proper relative URL resolution

### Configuration
No new configuration options are needed. The system utilizes existing settings:
- `URL_SAFETY_REQUEST_TIMEOUT`: Controls request timeouts when following redirects
- `URL_SAFETY_MAX_RETRIES`: Controls retry attempts for API calls
- `URL_SHORTENERS`: The list of known URL shortener domains to check

## Security Benefits
This update significantly improves the bot's ability to detect malicious URLs that are obscured through URL shorteners or redirect chains, which is a common tactic used in phishing and scam campaigns. By performing full security analysis on the entire redirect chain, the system can now catch malicious URLs that might have previously evaded detection, even when they use complex JavaScript-based redirection techniques or implement anti-bot measures to hide their true destination.

The integration with professional URL expansion services provides a much more reliable way to resolve shortened URLs, even those that actively try to prevent bots from discovering their destination. This ensures comprehensive security analysis even for the most sophisticated attempts to hide malicious content behind URL shorteners. 