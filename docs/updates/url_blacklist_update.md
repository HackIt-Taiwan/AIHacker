# URL Blacklist Feature Update

**Date**: 2024-03-26

## Overview

We've added a URL blacklist feature to the Discord bot that efficiently stores and checks against previously detected unsafe URLs. This reduces API usage, improves response time, and enhances protection against repeated threats.

## New Functionality

The URL blacklist system:

1. Automatically records URLs that have been identified as unsafe by VirusTotal
2. Checks incoming URLs against the blacklist before unshortening or API checks 
3. Immediately identifies malicious URLs without requiring repeated external API calls
4. Optionally blacklists entire domains for severe threats (phishing, malware)

## Technical Implementation

### New Module

```python
from app.ai.service.url_blacklist import URLBlacklist
```

The `URLBlacklist` class provides thread-safe persistence and access to the URL blacklist:

```python
# Initialize blacklist
blacklist = URLBlacklist("data/url_blacklist.json")

# Check if URL is blacklisted
result = blacklist.is_blacklisted("https://example.com/malware")
if result:
    print(f"URL is blacklisted: {result['reason']}")
    
# Add unsafe URL to blacklist
blacklist.add_unsafe_result(url, safety_check_result)

# Add specific URL or domain
blacklist.add_url("https://malicious.com/phish", {"reason": "Phishing site"})
blacklist.add_domain("malicious.com", {"reason": "Known malicious domain"})

# Remove entries
blacklist.remove_url("https://example.com/safe")
blacklist.remove_domain("safe-domain.com")

# Clean up when done
blacklist.close()  # Saves to disk
```

### Integration with URL Safety Checker

The URL blacklist is now integrated with the existing URL safety checker:

1. URLs are first checked against the blacklist
2. Blacklisted URLs are immediately marked as unsafe without further processing
3. Unshortened URLs are also checked against the blacklist
4. Newly detected unsafe URLs are automatically added to the blacklist

## Configuration

Add the following to your `.env` file to configure the URL blacklist:

```
# URL Blacklist Configuration
URL_BLACKLIST_ENABLED=True         # Enable or disable URL blacklist
URL_BLACKLIST_FILE=data/url_blacklist.json  # Path to the blacklist file
URL_BLACKLIST_AUTO_DOMAIN=False    # Auto-blacklist domains for severe threats
```

## Benefits

- **Improved Performance**: Immediate identification of known threats without API calls
- **Reduced API Usage**: Less reliance on external services for previously seen threats
- **Lower Latency**: Skip unshortening and API checks for known malicious URLs
- **Persistence**: URL threat information persists across bot restarts

## Storage Format

The blacklist is stored as a JSON file with the following structure:

```json
{
  "urls": {
    "https://example.com/malware": {
      "reason": "Malware detected",
      "threat_types": ["MALWARE"],
      "severity": 10,
      "check_time": "2024-03-26T12:34:56.789Z",
      "blacklisted_at": 1711466096.789
    }
  },
  "domains": {
    "malicious-domain.com": {
      "reason": "Domain of unsafe URL: Phishing website",
      "threat_types": ["PHISHING"],
      "severity": 9,
      "source_url": "https://malicious-domain.com/fake-login",
      "blacklisted_at": 1711466096.789
    }
  },
  "last_updated": 1711466096.789
}
```

## Command Line Management (Coming Soon)

Future updates will include Discord slash commands for staff to manage the blacklist:

- `/blacklist_add <url>` - Add a URL to the blacklist
- `/blacklist_remove <url>` - Remove a URL from the blacklist
- `/blacklist_stats` - View blacklist statistics 