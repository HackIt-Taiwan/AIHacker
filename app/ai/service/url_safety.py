"""
URL safety checking service.
"""
import re
import logging
import aiohttp
import asyncio
import json
import time
from typing import Dict, List, Tuple, Optional, Any, Set
from datetime import datetime

from app.config import (
    URL_SAFETY_CHECK_API,
    URL_SAFETY_API_KEY,
    URL_SAFETY_THRESHOLD,
    URL_SAFETY_SEVERITY_LEVELS,
    URL_SAFETY_MAX_RETRIES,
    URL_SAFETY_RETRY_DELAY,
    URL_SAFETY_REQUEST_TIMEOUT,
    URL_SAFETY_IMPERSONATION_DOMAINS
)

logger = logging.getLogger(__name__)

# URL regex pattern
URL_PATTERN = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w\.-]*(?:\?[-\w%&=.]*)?(?:#[-\w]*)?'

# Common URL shorteners and redirect services
URL_SHORTENERS = [
    'bit.ly', 'tinyurl.com', 'goo.gl', 't.co', 'is.gd', 'cli.gs', 'pic.gd',
    'DwarfURL.com', 'ow.ly', 'snipurl.com', 'tiny.cc', 'bit.do', 
    'shorte.st', 'adf.ly', 'j.mp', 'prettylinkpro.com', 'viralurl.com', 
    'twitthis.com', 'beam.to', 'fur.ly', 'vgd.me', 'short.to', 'tiny.pl',
    'urlcut.com', 'picshar.es', 'cur.lv', 'q.gs', 'lnk.co', 'u.to',
    'shorturl.at', 'cutt.ly', 'rebrand.ly', 'shorturl.com', 'qr.net'
]

# Typosquatting detection patterns
# Maps original domain to regex patterns that might be typosquatting attempts
TYPOSQUATTING_PATTERNS = {
    # Steam related patterns
    'steam': [
        r'ste[a@]m',  # steam, ste@m
        r'st[e3][a@]m',  # steam, st3am, st3@m
        r'ste[a@]n',  # stean, ste@n
        r'st[e3][a@][mn]',  # steam, stean, st3am, st3an
        r'steamcommun[a-z]*',  # steamcommunity, steamcommunety, etc.
    ],
    # Add other common platforms as needed
    'discord': [
        r'd[i!1][s5]c[o0]rd',  # discord, d1scord, d!sc0rd, etc.
        r'd[i!1][s5]c[o0][rd]d'  # discord, discard, disc0dd, etc.
    ],
    'roblox': [
        r'r[o0]bl[o0]x',  # roblox, r0bl0x
        r'r[o0]bl[o0]k[sx]'  # roblox, r0bloks, roblks
    ],
    'minecraft': [
        r'm[i!1]n[e3]cr[a@]ft',  # minecraft, m1n3cr@ft
        r'm[i!1]n[e3]kr[a@]ft'  # minekraft, m1n3kr@ft
    ],
    'nintendo': [
        r'n[i!1]nt[e3]nd[o0]',  # nintendo, n1nt3nd0
        r'n[e3]nt[e3]nd[o0]'  # nentendo, n3nt3nd0
    ],
    'playstation': [
        r'pl[a@]yst[a@]t[i!1][o0]n',  # playstation, pl@yst@t!0n
        r'pl[a@]yst[e3][i!]t[i!1][o0]n'  # playsteition, pl@yst3!t!0n
    ],
    'xbox': [
        r'xb[o0]x',  # xbox, xb0x
        r'[e3]xb[o0]x'  # exbox, 3xb0x
    ],
    'epic': [
        r'[e3]p[i!1]c',  # epic, 3p!c
        r'[e3]p[i!1]cg[a@]m[e3]s'  # epicgames, 3p!cg@m3s
    ],
    'origin': [
        r'[o0]r[i!1]g[i!1]n',  # origin, 0r!g!n
        r'[o0]r[e3]g[i!1]n'  # oregin, 0r3g!n
    ],
    'ubisoft': [
        r'[u\µ]b[i!1]s[o0]ft',  # ubisoft, µb!s0ft
        r'[u\µ]b[i!1]s[o0]f'  # ubisof, µb!s0f
    ],
    'battlenet': [
        r'b[a@]ttl[e3][n]?[e3]t',  # battlenet, b@ttl3net, battle3t
        r'b[a@]tt[l1][e3][n]?[e3]t'  # battlenet, b@tt13net, batt13t
    ],
    'rockstar': [
        r'r[o0]ckst[a@]r',  # rockstar, r0ckst@r
        r'r[o0]kst[a@]r'  # rokstar, r0kst@r
    ],
    'twitch': [
        r'tw[i!1]tch',  # twitch, tw!tch
        r'tw[e3]tch'  # twetch, tw3tch
    ],
    'youtube': [
        r'y[o0]utub[e3]',  # youtube, y0utub3
        r'y[o0]ut[u\µ]b[e3]'  # youtube, y0utµb3
    ],
    'facebook': [
        r'f[a@]c[e3]b[o0][o0]k',  # facebook, f@c3b00k
        r'f[a@]c[e3]b[u\µ]k'  # facebuk, f@c3bµk
    ],
    'instagram': [
        r'[i!1]nst[a@]gr[a@]m',  # instagram, !nst@gr@m
        r'[i!1]n[s5]t[a@]gr[a@]m'  # instagram, !n5t@gr@m
    ],
    'twitter': [
        r'tw[i!1]tt[e3]r',  # twitter, tw!tt3r
        r'tw[e3]tt[e3]r'  # twetter, tw3tt3r
    ],
    'tiktok': [
        r't[i!1]kt[o0]k',  # tiktok, t!kt0k
        r't[i!1]ct[o0]c'  # tictoc, t!ct0c
    ],
    'snapchat': [
        r'sn[a@]pch[a@]t',  # snapchat, sn@pch@t
        r'sn[a@]pch[e3]t'  # snapchet, sn@pch3t
    ],
    'reddit': [
        r'r[e3]dd[i!1]t',  # reddit, r3dd!t
        r'r[e3]d[i!1]t'  # redit, r3d!t
    ],
}

# Gift card and activation related keywords
SUSPICIOUS_PATH_PATTERNS = [
    r'gift',
    r'redeem',
    r'claim',
    r'free',
    r'activation',
    r'login',
    r'signin',
    r'auth',
    r'verify',
    r'account',
    r'profile',
    r'update',
    r'password',
    r'secure',
    r'wallet',
    r'balance',
    r'payment',
    r'billing',
    r'code',
    r'key',
    r'token',
    r'reward',
    r'bonus',
    r'prize',
    r'win',
    r'limited',
    r'exclusive',
    r'offer'
]

class URLSafetyChecker:
    """
    Check URLs for safety using various APIs.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the URL safety checker.
        
        Args:
            api_key: Optional API key (will use the one from config if not provided)
        """
        self.api = URL_SAFETY_CHECK_API.lower()
        self.api_key = api_key or URL_SAFETY_API_KEY
        self.threshold = URL_SAFETY_THRESHOLD
        self.severity_levels = URL_SAFETY_SEVERITY_LEVELS
        self.max_retries = URL_SAFETY_MAX_RETRIES
        self.retry_delay = URL_SAFETY_RETRY_DELAY
        self.request_timeout = URL_SAFETY_REQUEST_TIMEOUT
        self.impersonation_domains = URL_SAFETY_IMPERSONATION_DOMAINS
        
    async def extract_urls(self, text: str) -> List[str]:
        """
        Extract URLs from text.
        
        Args:
            text: The text to extract URLs from
            
        Returns:
            A list of URLs
        """
        if not text:
            return []
            
        # Find all URLs in the text
        urls = re.findall(URL_PATTERN, text)
        
        # Remove duplicates while preserving order
        seen: Set[str] = set()
        unique_urls = [url for url in urls if not (url in seen or seen.add(url))]
        
        logger.info(f"Extracted {len(unique_urls)} unique URLs from text")
        return unique_urls
        
    async def check_urls(self, urls: List[str]) -> Tuple[bool, Dict]:
        """
        Check multiple URLs for safety.
        
        Args:
            urls: List of URLs to check
            
        Returns:
            Tuple of (is_unsafe, results)
        """
        if not urls:
            return False, {}
            
        # Check each URL
        results = {}
        is_unsafe = False
        
        logger.info(f"Checking {len(urls)} URLs for safety")
        
        # First, resolve redirects for all URLs
        expanded_urls = {}
        for url in urls:
            # Check if it's a URL shortener
            is_shortener = any(shortener in url for shortener in URL_SHORTENERS)
            if is_shortener:
                logger.info(f"URL {url} appears to be a shortened URL. Attempting to resolve...")
                try:
                    final_url = await self._follow_redirects(url)
                    if final_url != url:
                        logger.info(f"URL {url} redirects to {final_url}")
                        expanded_urls[url] = final_url
                    else:
                        logger.info(f"URL {url} does not redirect to another URL")
                except Exception as e:
                    logger.error(f"Error following redirects for URL {url}: {str(e)}")
                    expanded_urls[url] = url  # Use original URL if redirect fails
            else:
                expanded_urls[url] = url  # No need to expand
        
        # Now check all original URLs and their redirects
        all_urls = set(urls + list(expanded_urls.values()))
        logger.info(f"Checking {len(all_urls)} URLs (including redirects)")
        
        for url in all_urls:
            # First perform a quick check for domain impersonation
            impersonation_result = self._check_domain_impersonation(url)
            if impersonation_result:
                logger.warning(f"Domain impersonation detected for URL {url}: {impersonation_result['reason']}")
                results[url] = impersonation_result
                
                # Mark as unsafe
                is_unsafe = True
                continue
                
            # If not immediately identified as impersonation, check with API
            url_is_unsafe, url_result = await self.check_url(url)
            
            # Store result
            results[url] = url_result
            
            # If it's unsafe, update main result
            if url_is_unsafe:
                is_unsafe = True
                logger.warning(f"Unsafe URL detected: {url}")
            
            # If this was a redirect target, also mark the original URL as unsafe
            for original_url, expanded_url in expanded_urls.items():
                if expanded_url == url and url_is_unsafe and original_url != url:
                    # Copy the result but note it's from a redirect
                    redirect_result = url_result.copy()
                    redirect_result["redirected_to"] = url
                    redirect_result["is_unsafe"] = True
                    results[original_url] = redirect_result
                    logger.warning(f"Original URL {original_url} redirects to unsafe URL {url}")
                
        return is_unsafe, results
    
    async def check_url(self, url: str) -> Tuple[bool, Dict]:
        """
        Check a single URL for safety.
        
        Args:
            url: The URL to check
            
        Returns:
            Tuple of (is_unsafe, result)
        """
        logger.info(f"Checking URL safety: {url}")
        if self.api == 'virustotal':
            return await self._check_url_virustotal(url)
        elif self.api == 'googlesafe':
            return await self._check_url_google_safe_browsing(url)
        else:
            logger.warning(f"Unsupported URL safety API: {self.api}")
            return False, {"error": f"Unsupported URL safety API: {self.api}"}
    
    def _check_domain_impersonation(self, url: str) -> Optional[Dict]:
        """
        Check if a URL appears to be impersonating a legitimate domain.
        
        Args:
            url: The URL to check
            
        Returns:
            Dictionary with impersonation details if detected, None otherwise
        """
        try:
            # Parse the URL
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()
            path = parsed_url.path.lower()
            
            # Skip if domain is empty
            if not domain:
                return None
                
            # 1. Check explicitly banned domains
            for impersonation_domain in self.impersonation_domains:
                if impersonation_domain in domain:
                    return {
                        "url": url,
                        "is_unsafe": True,
                        "unsafe_score": 1.0,
                        "threat_types": ["PHISHING"],
                        "severity": self.severity_levels.get("PHISHING", 9),
                        "reason": f"Domain matches known impersonation pattern: {impersonation_domain}",
                        "check_time": datetime.now().isoformat(),
                        "impersonation_detection": True,
                    }
            
            # 2. Check for typosquatting of popular domains
            for original_domain, patterns in TYPOSQUATTING_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, domain, re.IGNORECASE):
                        # Confirm this isn't the legitimate domain
                        if original_domain not in domain:
                            # If it contains gift/activate in URL path, increase suspicion
                            suspicious_path = False
                            for suspicious_pattern in SUSPICIOUS_PATH_PATTERNS:
                                if re.search(suspicious_pattern, path, re.IGNORECASE):
                                    suspicious_path = True
                                    break
                                    
                            return {
                                "url": url,
                                "is_unsafe": True,
                                "unsafe_score": 0.9 if suspicious_path else 0.8,
                                "threat_types": ["PHISHING"],
                                "severity": self.severity_levels.get("PHISHING", 9),
                                "reason": f"Domain appears to be typosquatting {original_domain}" + 
                                          (f" with suspicious path containing '{suspicious_pattern}'" if suspicious_path else ""),
                                "check_time": datetime.now().isoformat(),
                                "impersonation_detection": True,
                                "targeted_brand": original_domain
                            }
                            
            # 3. Check for misuse of common domains with suspicious paths
            # This looks for cases like: legitimate-sounding-domain.com/steam-gift/
            if any(re.search(pattern, path, re.IGNORECASE) for pattern in SUSPICIOUS_PATH_PATTERNS):
                for brand, _ in TYPOSQUATTING_PATTERNS.items():
                    if brand in path.lower() and brand not in domain.lower():
                        return {
                            "url": url,
                            "is_unsafe": True,
                            "unsafe_score": 0.7,
                            "threat_types": ["SUSPICIOUS", "PHISHING"],
                            "severity": self.severity_levels.get("PHISHING", 9),
                            "reason": f"URL contains brand name '{brand}' in path with suspicious keywords",
                            "check_time": datetime.now().isoformat(),
                            "impersonation_detection": True,
                        }
                        
            return None
            
        except Exception as e:
            logger.error(f"Error in domain impersonation check: {str(e)}")
            return None
        
    async def _follow_redirects(self, url: str, max_redirects: int = 5) -> str:
        """
        Follow URL redirects to get the final destination URL.
        
        Args:
            url: The URL to follow
            max_redirects: Maximum number of redirects to follow
            
        Returns:
            The final URL after following redirects
        """
        if max_redirects <= 0:
            logger.warning(f"Maximum redirects reached for URL: {url}")
            return url
            
        try:
            async with aiohttp.ClientSession() as session:
                # Use HEAD request with allow_redirects=False to check for redirects
                async with session.head(url, allow_redirects=False, timeout=self.request_timeout) as response:
                    # If we get a redirect status code
                    if response.status in (301, 302, 303, 307, 308):
                        location = response.headers.get('Location')
                        if location:
                            logger.info(f"URL {url} redirects to {location}")
                            # Follow the redirect recursively
                            return await self._follow_redirects(location, max_redirects - 1)
                    
                    # If no redirect, return the original URL
                    return url
        except Exception as e:
            logger.error(f"Error following redirects for URL {url}: {str(e)}")
            return url
    
    async def _check_url_virustotal(self, url: str) -> Tuple[bool, Dict]:
        """
        Check URL using VirusTotal API.
        
        Args:
            url: The URL to check
            
        Returns:
            Tuple of (is_unsafe, result)
        """
        if not self.api_key:
            logger.warning("No VirusTotal API key provided")
            return False, {"error": "No VirusTotal API key provided"}
            
        try:
            # First, get the URL ID
            url_id_endpoint = f"https://www.virustotal.com/api/v3/urls"
            
            async with aiohttp.ClientSession() as session:
                # Step 1: Get the URL ID by submitting it for analysis
                form_data = aiohttp.FormData()
                form_data.add_field('url', url)
                
                logger.info(f"Submitting URL to VirusTotal: {url}")
                
                async with session.post(
                    url_id_endpoint,
                    data=form_data,
                    headers={"x-apikey": self.api_key}
                ) as response:
                    if response.status != 200:
                        logger.error(f"VirusTotal API error: {response.status} - {await response.text()}")
                        return False, {"error": f"VirusTotal API error: {response.status}"}
                        
                    data = await response.json()
                    analysis_id = data.get('data', {}).get('id')
                    if not analysis_id:
                        logger.error(f"No analysis ID received from VirusTotal: {data}")
                        return False, {"error": "No analysis ID received from VirusTotal"}
                
                # Step 2: Get analysis results
                url_report_endpoint = f"https://www.virustotal.com/api/v3/analyses/{analysis_id}"
                
                # Try up to 3 times with increasing delays to get the completed analysis
                max_attempts = self.max_retries
                for attempt in range(1, max_attempts + 1):
                    logger.info(f"Fetching VirusTotal analysis results (attempt {attempt}/{max_attempts})")
                    
                    async with session.get(
                        url_report_endpoint,
                        headers={"x-apikey": self.api_key}
                    ) as response:
                        if response.status != 200:
                            logger.error(f"VirusTotal API error: {response.status} - {await response.text()}")
                            return False, {"error": f"VirusTotal API error: {response.status}"}
                            
                        data = await response.json()
                        
                        # Process the results
                        attributes = data.get('data', {}).get('attributes', {})
                        status = attributes.get('status')
                        
                        logger.info(f"VirusTotal analysis status: {status}")
                        
                        if status == 'completed':
                            # Process the completed analysis
                            stats = attributes.get('stats', {})
                            results = attributes.get('results', {})
                            
                            # Calculate safety score
                            malicious = stats.get('malicious', 0)
                            suspicious = stats.get('suspicious', 0)
                            total = sum(stats.values())
                            
                            if total == 0:
                                logger.warning("No VirusTotal results available")
                                return False, {"error": "No VirusTotal results available"}
                            
                            unsafe_score = (malicious + suspicious) / total
                            is_unsafe = unsafe_score >= self.threshold
                            
                            # Check for specific threat types (phishing, scam, etc.)
                            threat_types = set()
                            for engine, result in results.items():
                                category = result.get('category')
                                if category in ('malicious', 'suspicious'):
                                    threat_type = result.get('result', 'unknown')
                                    if 'phish' in threat_type.lower():
                                        threat_types.add('PHISHING')
                                    elif 'malware' in threat_type.lower():
                                        threat_types.add('MALWARE')
                                    elif 'scam' in threat_type.lower():
                                        threat_types.add('SCAM')
                                    else:
                                        threat_types.add('SUSPICIOUS')
                            
                            # Determine severity based on threat types
                            severity = 0
                            for threat_type in threat_types:
                                severity = max(severity, self.severity_levels.get(threat_type, 0))
                            
                            # Log the final result
                            if is_unsafe:
                                logger.warning(f"URL {url} is unsafe: score={unsafe_score:.2f}, threats={', '.join(threat_types)}")
                            else:
                                logger.info(f"URL {url} is safe: score={unsafe_score:.2f}")
                            
                            return is_unsafe, {
                                "url": url,
                                "unsafe_score": unsafe_score,
                                "is_unsafe": is_unsafe,
                                "malicious": malicious,
                                "suspicious": suspicious,
                                "total_engines": total,
                                "threat_types": list(threat_types),
                                "severity": severity,
                                "check_time": datetime.now().isoformat()
                            }
                        
                        elif status == 'queued':
                            # If the analysis is still queued, wait and retry
                            if attempt < max_attempts:
                                delay = self.retry_delay * (2 ** (attempt - 1))  # Exponential backoff: base_delay, base_delay*2, base_delay*4, ...
                                logger.warning(f"VirusTotal analysis queued, retrying in {delay} seconds")
                                await asyncio.sleep(delay)
                            else:
                                # If we've tried max_attempts times and it's still queued, make a conservative choice
                                logger.warning(f"VirusTotal analysis still queued after {max_attempts} attempts")
                                
                                # Check if the URL appears to be from a URL shortener
                                is_shortener = any(shortener in url for shortener in URL_SHORTENERS)
                                
                                # Check domain impersonation as a fallback
                                impersonation_result = self._check_domain_impersonation(url)
                                if impersonation_result:
                                    logger.warning(f"Domain impersonation detected for URL with queued analysis: {url}")
                                    return True, impersonation_result
                                
                                # For unresolved analyses, check the URL structure for known patterns
                                from urllib.parse import urlparse
                                parsed_url = urlparse(url)
                                domain = parsed_url.netloc.lower()
                                path = parsed_url.path.lower()
                                
                                # Check for suspicious path elements
                                has_suspicious_path = any(re.search(pattern, path, re.IGNORECASE) for pattern in SUSPICIOUS_PATH_PATTERNS)
                                
                                if is_shortener or has_suspicious_path:
                                    # Treat shortened URLs or URLs with suspicious paths as suspicious if we can't resolve them
                                    suspicious_factors = []
                                    if is_shortener:
                                        suspicious_factors.append("URL shortener")
                                    if has_suspicious_path:
                                        suspicious_factors.append("suspicious path keywords")
                                        
                                    logger.warning(f"URL {url} cannot be fully analyzed but has {', '.join(suspicious_factors)} - marking as suspicious")
                                    
                                    return True, {
                                        "url": url,
                                        "is_unsafe": True,
                                        "unsafe_score": 0.6,  # 60% unsafe
                                        "threat_types": ["SUSPICIOUS"],
                                        "severity": self.severity_levels.get("SUSPICIOUS", 0),
                                        "message": f"URL could not be fully analyzed but has {', '.join(suspicious_factors)}",
                                        "check_time": datetime.now().isoformat()
                                    }
                                else:
                                    # For normal URLs, return not unsafe but note that the check was incomplete
                                    logger.info(f"URL {url} analysis incomplete - treating as potentially safe")
                                    return False, {
                                        "url": url,
                                        "is_unsafe": False,
                                        "message": "Analysis incomplete, treated as safe",
                                        "check_time": datetime.now().isoformat()
                                    }
                        else:
                            # Other status (like 'failed')
                            logger.warning(f"VirusTotal analysis has unexpected status: {status}")
                            return False, {"status": status, "message": f"Analysis status: {status}"}
                    
        except Exception as e:
            logger.error(f"Error checking URL with VirusTotal: {str(e)}")
            return False, {"error": f"Error checking URL: {str(e)}"}
    
    async def _check_url_google_safe_browsing(self, url: str) -> Tuple[bool, Dict]:
        """
        Check URL using Google Safe Browsing API.
        
        Args:
            url: The URL to check
            
        Returns:
            Tuple of (is_unsafe, result)
        """
        if not self.api_key:
            logger.warning("No Google Safe Browsing API key provided")
            return False, {"error": "No Google Safe Browsing API key provided"}
            
        try:
            # First check domain impersonation
            impersonation_result = self._check_domain_impersonation(url)
            if impersonation_result:
                logger.warning(f"Domain impersonation detected for URL: {url}")
                return True, impersonation_result
                
            endpoint = f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={self.api_key}"
            
            # Prepare request payload
            payload = {
                "client": {
                    "clientId": "discord-bot",
                    "clientVersion": "1.0.0"
                },
                "threatInfo": {
                    "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE", "POTENTIALLY_HARMFUL_APPLICATION"],
                    "platformTypes": ["ANY_PLATFORM"],
                    "threatEntryTypes": ["URL"],
                    "threatEntries": [
                        {"url": url}
                    ]
                }
            }
            
            logger.info(f"Checking URL with Google Safe Browsing: {url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(endpoint, json=payload) as response:
                    if response.status != 200:
                        logger.error(f"Google Safe Browsing API error: {response.status} - {await response.text()}")
                        return False, {"error": f"Google Safe Browsing API error: {response.status}"}
                    
                    data = await response.json()
                    
                    # If matches found, the URL is unsafe
                    matches = data.get('matches', [])
                    is_unsafe = len(matches) > 0
                    
                    # Extract threat types if matches found
                    threat_types = []
                    if is_unsafe:
                        for match in matches:
                            threat_type = match.get('threatType')
                            if threat_type == 'SOCIAL_ENGINEERING':
                                threat_types.append('PHISHING')
                            elif threat_type == 'MALWARE':
                                threat_types.append('MALWARE')
                            elif threat_type in ('UNWANTED_SOFTWARE', 'POTENTIALLY_HARMFUL_APPLICATION'):
                                threat_types.append('SUSPICIOUS')
                    
                    # Determine severity based on threat types
                    severity = 0
                    for threat_type in threat_types:
                        severity = max(severity, self.severity_levels.get(threat_type, 0))
                    
                    # Log the result
                    if is_unsafe:
                        logger.warning(f"URL {url} is unsafe according to Google Safe Browsing: threats={', '.join(threat_types)}")
                    else:
                        # If Google Safe Browsing didn't flag it but it has suspicious elements, check further
                        from urllib.parse import urlparse
                        parsed_url = urlparse(url)
                        path = parsed_url.path.lower()
                        
                        # Check for suspicious path elements
                        has_suspicious_path = any(re.search(pattern, path, re.IGNORECASE) for pattern in SUSPICIOUS_PATH_PATTERNS)
                        
                        if has_suspicious_path:
                            # For borderline cases, treat as suspicious
                            return True, {
                                "url": url,
                                "is_unsafe": True,
                                "threat_types": ["SUSPICIOUS"],
                                "reason": "URL contains suspicious keywords in path",
                                "severity": self.severity_levels.get("SUSPICIOUS", 5),
                                "check_time": datetime.now().isoformat()
                            }
                        
                        logger.info(f"URL {url} is safe according to Google Safe Browsing")
                    
                    return is_unsafe, {
                        "url": url,
                        "is_unsafe": is_unsafe,
                        "threat_types": threat_types,
                        "matches": matches,
                        "severity": severity,
                        "check_time": datetime.now().isoformat()
                    }
                    
        except Exception as e:
            logger.error(f"Error checking URL with Google Safe Browsing: {str(e)}")
            return False, {"error": f"Error checking URL: {str(e)}"} 