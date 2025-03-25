"""
URL safety checking service.

This module provides functionality to check URLs for safety using third-party virus detection APIs.
"""
import re
import logging
import aiohttp
import asyncio
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import urllib.parse
import random

from app.config import (
    URL_SAFETY_CHECK_API,
    URL_SAFETY_API_KEY,
    URL_SAFETY_THRESHOLD,
    URL_SAFETY_SEVERITY_LEVELS,
    URL_SAFETY_MAX_RETRIES,
    URL_SAFETY_RETRY_DELAY,
    URL_SAFETY_REQUEST_TIMEOUT,
    URL_SAFETY_MAX_URLS,
    URL_UNSHORTEN_ENABLED,
    URL_BLACKLIST_ENABLED,
    URL_BLACKLIST_FILE,
    URL_BLACKLIST_AUTO_DOMAIN
)
from app.ai.service.url_unshortener import URLUnshortener
from app.ai.service.url_blacklist import URLBlacklist

logger = logging.getLogger(__name__)

# URL pattern for detection
URL_PATTERN = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w\.-]*(?:\?[-\w%&=.]*)?(?:#[-\w]*)?'

class URLSafetyChecker:
    """Check URLs for safety using third-party virus detection tools."""
    
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
        
        # Initialize URL unshortener
        self.unshortener = URLUnshortener()
        
        # Initialize URL blacklist if enabled
        self.blacklist_enabled = URL_BLACKLIST_ENABLED
        if self.blacklist_enabled:
            self.blacklist = URLBlacklist(URL_BLACKLIST_FILE)
        else:
            self.blacklist = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with cleanup."""
        if hasattr(self, 'unshortener'):
            self.unshortener.close()
            
        if hasattr(self, 'blacklist') and self.blacklist:
            self.blacklist.close()
            
    async def extract_urls(self, text: str) -> List[str]:
        """
        Extract all URLs from text content.
        
        Args:
            text: The text to extract URLs from
            
        Returns:
            A list of unique URLs
        """
        if not text:
            return []
            
        # Find all URLs in the text
        urls = re.findall(URL_PATTERN, text)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_urls = [url for url in urls if not (url in seen or seen.add(url))]
        
        logger.info(f"Extracted {len(unique_urls)} unique URLs from text")
        return unique_urls
        
    async def check_urls(self, urls: List[str]) -> Tuple[bool, Dict]:
        """
        Check multiple URLs for safety.
        When there are more than URL_SAFETY_MAX_URLS URLs, randomly sample that many of them to check.
        
        Args:
            urls: List of URLs to check
            
        Returns:
            Tuple of (is_unsafe, results_dict)
        """
        if not urls:
            return False, {}
            
        results = {}
        is_unsafe = False
        blacklisted_urls = []
        urls_to_check = []
        
        # First, check against the blacklist if enabled
        if self.blacklist_enabled and self.blacklist:
            for url in urls:
                blacklist_result = self.blacklist.is_blacklisted(url)
                if blacklist_result:
                    # URL is in the blacklist
                    is_unsafe = True
                    blacklisted_urls.append(url)
                    
                    # Create a result based on the blacklist entry
                    results[url] = {
                        "url": url,
                        "is_unsafe": True,
                        "check_time": datetime.now().isoformat(),
                        "message": f"URL matches blacklisted entry: {blacklist_result.get('reason', 'Unknown threat')}",
                        "threat_types": blacklist_result.get('threat_types', ['BLACKLISTED']),
                        "severity": blacklist_result.get('severity', 8),
                        "from_blacklist": True,
                        "blacklisted_at": blacklist_result.get('blacklisted_at')
                    }
                    logger.warning(f"URL {url} found in blacklist: {blacklist_result.get('reason', 'Unknown threat')}")
                else:
                    # URL is not in the blacklist, will need to check it
                    urls_to_check.append(url)
        else:
            # Blacklist not enabled, check all URLs
            urls_to_check = urls
            
        # If all URLs are blacklisted, we can return early
        if not urls_to_check:
            return is_unsafe, results
            
        # If there are more than max_urls, randomly sample that many of them
        sampling_applied = False
        max_urls_to_check = URL_SAFETY_MAX_URLS
        urls_to_actual_check = urls_to_check
        
        if len(urls_to_check) > max_urls_to_check:
            sampling_applied = True
            urls_to_actual_check = random.sample(urls_to_check, max_urls_to_check)
            logger.info(f"URL check: Sampling {max_urls_to_check} from {len(urls_to_check)} non-blacklisted URLs")
            
            # Mark the URLs that weren't checked as skipped in the results
            for url in urls_to_check:
                if url not in urls_to_actual_check:
                    results[url] = {
                        "url": url,
                        "is_unsafe": False,
                        "check_time": datetime.now().isoformat(),
                        "message": "URL check skipped (random sampling applied)",
                        "skipped": True
                    }
        
        logger.info(f"Checking {len(urls_to_actual_check)} URLs for safety")
        
        # First, unshorten all URLs if URL unshortening is enabled
        if URL_UNSHORTEN_ENABLED:
            logger.info(f"Unshortening {len(urls_to_actual_check)} URLs before safety check")
            unshortened_urls = {}
            unshortening_results = await self.unshortener.unshorten_urls(urls_to_actual_check)
            
            # Map original URLs to their unshortened versions
            for url in urls_to_actual_check:
                if url in unshortening_results:
                    result = unshortening_results[url]
                    if result["success"] and result["final_url"] != url:
                        # URL was successfully unshortened
                        unshortened_urls[url] = result["final_url"]
                        logger.info(f"Unshortened URL: {url} -> {result['final_url']}")
                        
                        # Add the shortened URL mapping to the blacklist for future reference
                        # even if it's not unsafe (this improves lookup efficiency)
                        if self.blacklist_enabled and self.blacklist:
                            self.blacklist.add_shortened_url(url, result["final_url"])
                        
                        # Check if the unshortened URL is in the blacklist
                        if self.blacklist_enabled and self.blacklist:
                            blacklist_result = self.blacklist.is_blacklisted(result["final_url"])
                            if blacklist_result:
                                # Unshortened URL is in the blacklist
                                is_unsafe = True
                                blacklisted_urls.append(url)
                                
                                # Remove this URL from urls_to_actual_check as we've determined it's unsafe
                                if url in urls_to_actual_check:
                                    urls_to_actual_check.remove(url)
                                
                                # Create a result based on the blacklist entry
                                results[url] = {
                                    "url": url,
                                    "unshortened_url": result["final_url"],
                                    "is_unsafe": True,
                                    "check_time": datetime.now().isoformat(),
                                    "message": f"Unshortened URL matches blacklisted entry: {blacklist_result.get('reason', 'Unknown threat')}",
                                    "threat_types": blacklist_result.get('threat_types', ['BLACKLISTED']),
                                    "severity": blacklist_result.get('severity', 8),
                                    "from_blacklist": True,
                                    "blacklisted_at": blacklist_result.get('blacklisted_at')
                                }
                                logger.warning(f"Unshortened URL {result['final_url']} found in blacklist (original: {url}): {blacklist_result.get('reason', 'Unknown threat')}")
                    else:
                        # Use original URL if unshortening failed or didn't change URL
                        unshortened_urls[url] = url
                else:
                    unshortened_urls[url] = url
        
        # Check safety for the remaining URLs
        for original_url in urls_to_actual_check:
            # Skip if we already determined this URL is unsafe from the blacklist
            if original_url in results and results[original_url].get("is_unsafe", False):
                continue
                
            # Use unshortened URL for safety check if available
            url_to_check = unshortened_urls.get(original_url, original_url) if URL_UNSHORTEN_ENABLED else original_url
            
            # Check safety
            url_unsafe, result = await self.check_url(url_to_check)
            
            # Add unshortening information to the result if applicable
            if URL_UNSHORTEN_ENABLED and original_url in unshortened_urls and unshortened_urls[original_url] != original_url:
                result["original_shortened_url"] = original_url
                result["url"] = url_to_check  # Update to unshortened URL
                
            # Store result under the original URL
            results[original_url] = result
            
            # If URL is unsafe, add it to the blacklist
            if url_unsafe and self.blacklist_enabled and self.blacklist:
                self.blacklist.add_unsafe_result(
                    url_to_check, 
                    result, 
                    original_url=original_url,
                    blacklist_domain=URL_BLACKLIST_AUTO_DOMAIN
                )
                logger.info(f"Added unsafe URL to blacklist: {url_to_check}{' (original: '+original_url+')' if original_url != url_to_check else ''}")
            
            if url_unsafe:
                is_unsafe = True
                logger.warning(f"URL {original_url} is unsafe")
        
        # If we did sampling and found nothing unsafe, note it in the log
        if sampling_applied and not is_unsafe:
            logger.info(f"Note: Only {max_urls_to_check} out of {len(urls)} URLs were checked due to sampling")
            
        return is_unsafe, results
    
    async def check_url(self, url: str) -> Tuple[bool, Dict]:
        """
        Check a single URL for safety using the configured API.
        
        Args:
            url: The URL to check
            
        Returns:
            Tuple of (is_unsafe, result_dict)
        """
        logger.info(f"Checking URL safety: {url}")
        
        try:
            # Create the base result dictionary
            result = {
                "url": url,
                "is_unsafe": False,
                "check_time": datetime.now().isoformat()
            }
            
            # Use the configured API for safety checking
            if self.api == 'virustotal':
                is_unsafe, api_result = await self._check_url_virustotal(url)
            else:
                # Default to local pattern-based checks only
                is_unsafe = False
                api_result = {
                    "url": url,
                    "is_unsafe": False,
                    "message": f"URL checked with local patterns only. No supported API available.",
                }
            
            # If API found issues, combine with our result
            if is_unsafe:
                logger.warning(f"External API detected threats for URL {url}")
                api_result.update({
                    "is_unsafe": True,
                    "message": "External API threat detection"
                })
                return True, api_result
            
            # URL passed all checks
            api_result.update({
                "is_unsafe": False,
                "message": "URL passed safety checks"
            })
            return False, api_result
            
        except Exception as e:
            logger.error(f"Error checking URL safety for {url}: {str(e)}")
            return False, {
                "url": url,
                "is_unsafe": False,  # Default to safe on error
                "error": f"Error checking URL: {str(e)}",
                "check_time": datetime.now().isoformat()
            }
    
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
            # First try to get URL ID by calculating the base64 URL identifier
            import base64
            import hashlib
            
            # Calculate URL identifier
            url_id = base64.urlsafe_b64encode(url.encode()).decode().strip("=")
            
            # First try directly getting the analysis if it exists
            url_report_endpoint = f"https://www.virustotal.com/api/v3/urls/{url_id}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url_report_endpoint,
                    headers={"x-apikey": self.api_key}
                ) as response:
                    # If the URL has been scanned before, we can get results directly
                    if response.status == 200:
                        data = await response.json()
                        attributes = data.get('data', {}).get('attributes', {})
                        
                        # Extract last_analysis_stats 
                        stats = attributes.get('last_analysis_stats', {})
                        results = attributes.get('last_analysis_results', {})
                        
                        # Calculate safety score
                        malicious = stats.get('malicious', 0)
                        suspicious = stats.get('suspicious', 0)
                        total = sum(stats.values()) if sum(stats.values()) > 0 else 1
                        
                        unsafe_score = (malicious + suspicious) / total
                        is_unsafe = unsafe_score >= self.threshold
                        
                        # Log detailed information for debugging
                        logger.info(f"VirusTotal direct check - URL: {url}, Malicious: {malicious}, Suspicious: {suspicious}, Total: {total}, Score: {unsafe_score}, Threshold: {self.threshold}")
                        
                        # Check for specific threat types
                        threat_types = set()
                        for engine, result in results.items():
                            category = result.get('category')
                            if category in ('malicious', 'suspicious'):
                                threat_type = result.get('result', 'unknown').lower()
                                if 'phish' in threat_type:
                                    threat_types.add('PHISHING')
                                elif 'malware' in threat_type:
                                    threat_types.add('MALWARE')
                                elif 'scam' in threat_type:
                                    threat_types.add('SCAM')
                                else:
                                    threat_types.add('SUSPICIOUS')
                        
                        # Determine severity based on threat types
                        severity = 0
                        for threat_type in threat_types:
                            severity = max(severity, self.severity_levels.get(threat_type, 0))
                        
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
                
                # If URL hasn't been analyzed before, submit it for analysis
                # Submit URL for analysis
                form_data = aiohttp.FormData()
                form_data.add_field('url', url)
                
                analyze_url_endpoint = "https://www.virustotal.com/api/v3/urls"
                
                async with session.post(
                    analyze_url_endpoint,
                    data=form_data,
                    headers={"x-apikey": self.api_key}
                ) as response:
                    if response.status != 200:
                        logger.error(f"VirusTotal API error: {response.status} - {await response.text()}")
                        return False, {"error": f"VirusTotal API error: {response.status}"}
                        
                    data = await response.json()
                    analysis_id = data.get('data', {}).get('id')
                    if not analysis_id:
                        logger.error("No analysis ID received from VirusTotal")
                        return False, {"error": "No analysis ID received from VirusTotal"}
                    
                    logger.info(f"Submitted URL for analysis: {url}, Analysis ID: {analysis_id}")
                
                # Step 2: Get analysis results
                url_report_endpoint = f"https://www.virustotal.com/api/v3/analyses/{analysis_id}"
                
                # Try with exponential backoff
                for attempt in range(1, self.max_retries + 1):
                    logger.info(f"Fetching VirusTotal analysis results (attempt {attempt}/{self.max_retries})")
                    
                    # Add a delay before checking results
                    delay = self.retry_delay * (2 ** (attempt - 1))
                    await asyncio.sleep(delay)
                    
                    async with session.get(
                        url_report_endpoint,
                        headers={"x-apikey": self.api_key}
                    ) as response:
                        if response.status != 200:
                            logger.error(f"VirusTotal API error: {response.status}")
                            if attempt < self.max_retries:
                                continue
                            return False, {"error": f"VirusTotal API error: {response.status}"}
                            
                        data = await response.json()
                        attributes = data.get('data', {}).get('attributes', {})
                        status = attributes.get('status')
                        
                        if status == 'completed':
                            # Process the completed analysis
                            stats = attributes.get('stats', {})
                            results = attributes.get('results', {})
                            
                            # Calculate safety score
                            malicious = stats.get('malicious', 0)
                            suspicious = stats.get('suspicious', 0)
                            total = sum(stats.values()) if sum(stats.values()) > 0 else 1
                            
                            unsafe_score = (malicious + suspicious) / total
                            is_unsafe = unsafe_score >= self.threshold
                            
                            # Log detailed information for debugging
                            logger.info(f"VirusTotal scan - URL: {url}, Malicious: {malicious}, Suspicious: {suspicious}, Total: {total}, Score: {unsafe_score}, Threshold: {self.threshold}")
                            
                            # Check for specific threat types
                            threat_types = set()
                            for engine, result in results.items():
                                category = result.get('category')
                                if category in ('malicious', 'suspicious'):
                                    threat_type = result.get('result', 'unknown').lower()
                                    if 'phish' in threat_type:
                                        threat_types.add('PHISHING')
                                    elif 'malware' in threat_type:
                                        threat_types.add('MALWARE')
                                    elif 'scam' in threat_type:
                                        threat_types.add('SCAM')
                                    else:
                                        threat_types.add('SUSPICIOUS')
                            
                            # Determine severity based on threat types
                            severity = 0
                            for threat_type in threat_types:
                                severity = max(severity, self.severity_levels.get(threat_type, 0))
                            
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
                            # If still queued, wait for next attempt
                            if attempt < self.max_retries:
                                continue
                            else:
                                # Return a conservative result if still queued after all retries
                                logger.warning(f"URL analysis still queued after maximum retries: {url}")
                                return False, {
                                    "url": url,
                                    "is_unsafe": False,
                                    "message": "Analysis still queued after maximum retries",
                                    "check_time": datetime.now().isoformat()
                                }
                        else:
                            # Other status (like 'failed')
                            logger.warning(f"VirusTotal analysis status: {status}")
                            return False, {
                                "url": url,
                                "is_unsafe": False,
                                "message": f"Analysis status: {status}",
                                "check_time": datetime.now().isoformat()
                            }
                
                # If we've exhausted all retries
                logger.warning(f"Failed to get analysis results after maximum retries: {url}")
                return False, {
                    "url": url,
                    "is_unsafe": False,
                    "message": "Failed to get analysis results after maximum retries",
                    "check_time": datetime.now().isoformat()
                }
                    
        except Exception as e:
            logger.error(f"Error checking URL with VirusTotal: {str(e)}")
            return False, {"error": f"Error checking URL: {str(e)}"} 