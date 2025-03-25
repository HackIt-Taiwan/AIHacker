# URL Blacklist Feature

## Overview

The URL blacklist feature enhances the bot's security by maintaining a persistent list of previously detected unsafe URLs. This allows the bot to immediately identify and block known malicious URLs without needing to recheck them through external services.

## How It Works

1. When the URL safety checker identifies a URL as unsafe (via VirusTotal or other services), it automatically adds the URL to the blacklist.
2. Both the original shortened URL and the expanded destination URL are recorded in the blacklist.
3. For all future messages, any URLs are first checked against this blacklist.
4. If a match is found, the URL is immediately flagged as unsafe, and appropriate actions are taken without needing to:
   - Unshorten the URL
   - Send API requests to VirusTotal
   - Wait for response/analysis
5. This provides faster response times and reduces API usage for known threats.

## Configuration

The URL blacklist feature can be configured via the following environment variables in `.env`:

```
# URL Blacklist Configuration
URL_BLACKLIST_ENABLED=True         # Enable or disable URL blacklist (True/False)
URL_BLACKLIST_FILE=data/url_blacklist.json  # Path to the blacklist JSON file
URL_BLACKLIST_AUTO_DOMAIN=False    # Whether to automatically blacklist domains of severe threats
```

## Performance Benefits

- **Faster Response**: Immediate identification of known unsafe URLs
- **Reduced API Usage**: No need to repeatedly check the same malicious URLs
- **Lower Latency**: Skips unshortening process for known threats
- **Better User Protection**: Quick response to repeated sharing of known threats

## Implementation Details

### Storage Format

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
    },
    ...
  },
  "domains": {
    "malicious-domain.com": {
      "reason": "Domain of unsafe URL: Phishing website",
      "threat_types": ["PHISHING"],
      "severity": 9,
      "source_url": "https://malicious-domain.com/fake-login",
      "blacklisted_at": 1711466096.789
    },
    ...
  },
  "last_updated": 1711466096.789
}
```

### Domain Blacklisting

When `URL_BLACKLIST_AUTO_DOMAIN` is enabled, domains of highly severe threats (severity ≥ 8) are automatically blacklisted. This means any URL from that domain will be immediately flagged, even if the specific path hasn't been seen before.

### Thread Safety

The blacklist implementation uses thread locks to ensure thread safety when multiple messages are processed concurrently.

### Automatic Saving

The blacklist is automatically saved to disk:
- Every time a new unsafe URL is added
- Periodically (every minute) if modified
- When the bot is shutting down

## Processing Flow

1. Extract URLs from message
2. Check each URL against the blacklist
3. If a URL is blacklisted, mark it as unsafe immediately
4. For non-blacklisted URLs, proceed with normal processing:
   - Sampling (if too many URLs)
   - Unshortening
   - Safety checking via VirusTotal
5. Add any newly detected unsafe URLs to the blacklist

## Command Line Tools

You can manage the blacklist using the following discord slash commands (for staff only):

- `/blacklist_add <url>` - Manually add a URL to the blacklist
- `/blacklist_remove <url>` - Remove a URL from the blacklist
- `/blacklist_domain_add <domain>` - Add a domain to the blacklist
- `/blacklist_domain_remove <domain>` - Remove a domain from the blacklist
- `/blacklist_stats` - Show statistics about the blacklist

## Future Enhancements

- Blacklist expiration/aging for older entries
- Blacklist sharing between bot instances
- Regular expression pattern matching for more flexible URL matching 