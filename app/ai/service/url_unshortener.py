"""
URL unshortener service.

This module provides functionality to expand shortened URLs using multiple methods:
1. Simple HTTP requests with headers
2. Headless browser simulation using Selenium (if available)
3. Special handlers for various URL shortening services
"""
import re
import time
import logging
import aiohttp
import asyncio
from typing import Dict, List, Tuple, Optional, Any
import urllib.parse
import random
from urllib.parse import urlparse

from app.config import (
    URL_UNSHORTEN_ENABLED,
    URL_UNSHORTEN_TIMEOUT,
    URL_UNSHORTEN_MAX_REDIRECTS,
    URL_UNSHORTEN_RETRY_COUNT
)

logger = logging.getLogger(__name__)

# Common URL shortening services
SHORT_URL_DOMAINS = [
    'bit.ly', 'tinyurl.com', 'goo.gl', 't.co', 'ow.ly', 'is.gd', 
    'buff.ly', 'adf.ly', 'tiny.cc', 'lnkd.in', 'db.tt', 'qr.ae', 
    'j.mp', 'soo.gd', 's2r.co', 'clicky.me', 'budurl.com', 
    'bc.vc', 'u.to', 'v.gd', 'shorturl.at', 'cutt.ly', 'shorturl.com',
    'tiny.one', 'tinyurl.one', 'rb.gy', 'rebrand.ly', 'plu.sh', 'tny.im',
    'snip.ly', 'short.io', 'shorturl.com', 'x.co', 'yourls.org',
    'fw.io', 'vurl.com', 'tiny.pl', 'n9.cl', 'short.gy', 'tr.im',
    'ur1.ca', 'hoo.gl', 'me2.do', 'upto.site', 'adpop.me', 'liip.to',
    'urlzs.com', 'frama.link', 'url.ie', 't.me', 'cli.re', 'wp.me',
    'dlvr.it', 'urlz.fr', 'urlb.at', 'turl.ca', 'urls.im', 'go2l.ink',
    'get.to', 'sui.li', 'zpr.io', 'v.ht', '1w.tf', 'rlu.ru', 'mcaf.ee',
    'shorturl.at', 'ln.is', 'shr.lc', 'dai.ly', 'cort.as', 'shrtco.de',
    'surl.li', 'trib.al', 'urlr.me', 'lc.chat', 'ift.tt', 'crm.is',
    'gl.am', 'bom.to', 'smarturl.it', 'drop.lk', 'yep.it', 'mfun.us',
    'post.ly', 'huff.to', 'perma.cc', 'ouo.io', 'lix.in'
]

# Special handlers for certain URL shorteners
SPECIAL_HANDLERS = {
    'bit.ly': {
        'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1',
        'headers': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.google.com/',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'cross-site',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache'
        }
    },
    't.co': {
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'headers': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://twitter.com/',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    },
    'goo.gl': {
        'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15',
        'headers': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    }
}

# URL pattern for detection
URL_PATTERN = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w\.-]*(?:\?[-\w%&=.]*)?(?:#[-\w]*)?'

# Check if Selenium is available
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logger.warning("Selenium not available. Headless browser URL unshortening will be disabled.")

class URLUnshortener:
    """Service to unshorten URLs using various methods."""
    
    def __init__(self):
        """Initialize the URL unshortener with configuration from settings."""
        self.enabled = URL_UNSHORTEN_ENABLED
        self.timeout = URL_UNSHORTEN_TIMEOUT
        self.max_redirects = URL_UNSHORTEN_MAX_REDIRECTS
        self.retry_count = URL_UNSHORTEN_RETRY_COUNT
        self.use_selenium = SELENIUM_AVAILABLE
        self.selenium_initialized = False
        self.driver = None
        
        # Standard browser-like headers
        self.default_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
        
        logger.info(f"URL unshortener initialized. Enabled: {self.enabled}, Selenium available: {SELENIUM_AVAILABLE}")
    
    def _setup_selenium(self):
        """Set up Selenium WebDriver for headless browser simulation."""
        if not SELENIUM_AVAILABLE or self.selenium_initialized:
            return
            
        try:
            # Configure Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument("--disable-popup-blocking")
            chrome_options.add_argument("--log-level=3")
            
            # Set user agent
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
            
            # Create WebDriver instance
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(self.timeout)
            self.selenium_initialized = True
            logger.info("Selenium WebDriver initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Selenium WebDriver: {str(e)}")
            self.use_selenium = False
    
    def _get_domain_from_url(self, url: str) -> str:
        """Extract domain from URL."""
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    
    def _get_headers_for_domain(self, domain: str) -> Dict:
        """Get appropriate headers for the given domain."""
        if domain in SPECIAL_HANDLERS:
            handler = SPECIAL_HANDLERS[domain]
            headers = handler['headers'].copy()
            headers['User-Agent'] = handler['user_agent']
            return headers
        return self.default_headers.copy()
    
    def is_shortened_url(self, url: str) -> bool:
        """Check if a URL is likely a shortened URL."""
        if not url:
            return False
            
        # Ensure the URL has a scheme
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        # Check against known URL shortener domains
        domain = self._get_domain_from_url(url)
        if domain in SHORT_URL_DOMAINS:
            return True
            
        # Check URL structure for shortener patterns
        parsed_url = urlparse(url)
        path = parsed_url.path.strip('/')
        
        # Short path with random-looking characters
        if path and len(path) < 10 and re.match(r'^[a-zA-Z0-9_-]+$', path):
            return True
            
        # Overall short URL length
        if len(url) < 30:
            return True
            
        return False
    
    async def extract_urls(self, text: str) -> List[str]:
        """Extract all URLs from text content."""
        if not text:
            return []
            
        # Find all URLs in the text
        urls = re.findall(URL_PATTERN, text)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_urls = [url for url in urls if not (url in seen or seen.add(url))]
        
        logger.info(f"Extracted {len(unique_urls)} unique URLs from text")
        return unique_urls
    
    async def unshorten_with_requests(self, url: str) -> Dict:
        """Unshorten URL using HTTP requests with appropriate headers."""
        start_time = time.time()
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        domain = self._get_domain_from_url(url)
        headers = self._get_headers_for_domain(domain)
        redirect_history = [url]
        
        try:
            # Create a session to manage cookies and headers
            async with aiohttp.ClientSession() as session:
                # Send HEAD request first to check for immediate redirects
                try:
                    async with session.head(
                        url,
                        headers=headers,
                        allow_redirects=False,
                        timeout=self.timeout
                    ) as response:
                        # If we get a redirect status code
                        if response.status in (301, 302, 303, 307, 308):
                            location = response.headers.get('Location')
                            if location:
                                # Handle relative URLs
                                if not location.startswith(('http://', 'https://')):
                                    if location.startswith('/'):
                                        location = f"{url.split('://', 1)[0]}://{domain}{location}"
                                    else:
                                        location = f"{url.split('://', 1)[0]}://{domain}/{location}"
                                
                                redirect_history.append(location)
                                # Continue with the new location for GET request
                                url = location
                except aiohttp.ClientError as e:
                    logger.warning(f"HEAD request failed for {url}: {str(e)}")
                
                # Now try with GET and allow redirects
                redirects = 0
                current_url = url
                
                while redirects < self.max_redirects:
                    try:
                        async with session.get(
                            current_url,
                            headers=headers,
                            allow_redirects=False,
                            timeout=self.timeout
                        ) as response:
                            # Check for redirect
                            if response.status in (301, 302, 303, 307, 308):
                                location = response.headers.get('Location')
                                if location:
                                    # Handle relative URLs
                                    if not location.startswith(('http://', 'https://')):
                                        current_domain = self._get_domain_from_url(current_url)
                                        if location.startswith('/'):
                                            location = f"{current_url.split('://', 1)[0]}://{current_domain}{location}"
                                        else:
                                            location = f"{current_url.split('://', 1)[0]}://{current_domain}/{location}"
                                    
                                    # Avoid redirect loops
                                    if location in redirect_history:
                                        break
                                        
                                    redirect_history.append(location)
                                    current_url = location
                                    redirects += 1
                                else:
                                    # No Location header despite redirect status
                                    break
                            else:
                                # Try to detect JavaScript redirects from response body
                                if response.status == 200:
                                    # Read a portion of the response to look for JavaScript redirects
                                    html = await response.text(encoding='utf-8', errors='ignore')
                                    js_redirect = self._extract_js_redirect(html)
                                    
                                    if js_redirect:
                                        # Handle relative URLs for JavaScript redirects
                                        if not js_redirect.startswith(('http://', 'https://')):
                                            current_domain = self._get_domain_from_url(current_url)
                                            if js_redirect.startswith('/'):
                                                js_redirect = f"{current_url.split('://', 1)[0]}://{current_domain}{js_redirect}"
                                            else:
                                                js_redirect = f"{current_url.split('://', 1)[0]}://{current_domain}/{js_redirect}"
                                        
                                        if js_redirect not in redirect_history:
                                            redirect_history.append(js_redirect)
                                            current_url = js_redirect
                                            redirects += 1
                                            continue
                                
                                # No more redirects
                                break
                    except aiohttp.ClientError as e:
                        logger.warning(f"GET request failed for {current_url}: {str(e)}")
                        break
        
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"Error unshortening URL with requests: {str(e)}")
            return {
                "original_url": url,
                "final_url": url,
                "success": False,
                "method": "requests",
                "error": str(e),
                "redirect_history": redirect_history,
                "elapsed_time": round(elapsed_time, 3)
            }
        
        elapsed_time = time.time() - start_time
        final_url = redirect_history[-1] if redirect_history else url
        
        return {
            "original_url": url,
            "final_url": final_url,
            "success": True,
            "method": "requests",
            "redirect_count": len(redirect_history) - 1,
            "redirect_history": redirect_history,
            "elapsed_time": round(elapsed_time, 3)
        }
    
    async def unshorten_with_selenium(self, url: str) -> Dict:
        """Unshorten URL using Selenium headless browser."""
        if not self.use_selenium:
            return {
                "original_url": url,
                "final_url": url,
                "success": False,
                "method": "selenium",
                "error": "Selenium not available"
            }
            
        # Make sure Selenium is set up
        if not self.selenium_initialized:
            self._setup_selenium()
            if not self.selenium_initialized:
                return {
                    "original_url": url,
                    "final_url": url,
                    "success": False,
                    "method": "selenium",
                    "error": "Failed to initialize Selenium"
                }
        
        start_time = time.time()
        redirect_history = [url]
        
        try:
            # Navigate to the URL
            self.driver.get(url)
            
            # Wait for the page to load
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Get current URL after potential redirects
            current_url = self.driver.current_url
            if current_url != url:
                redirect_history.append(current_url)
            
            # Wait a bit more for any JavaScript redirects
            time.sleep(1)
            
            # Check if URL changed again due to JS redirects
            final_url = self.driver.current_url
            if final_url != current_url and final_url not in redirect_history:
                redirect_history.append(final_url)
            
            elapsed_time = time.time() - start_time
            
            return {
                "original_url": url,
                "final_url": final_url,
                "success": True,
                "method": "selenium",
                "redirect_count": len(redirect_history) - 1,
                "redirect_history": redirect_history,
                "elapsed_time": round(elapsed_time, 3)
            }
            
        except TimeoutException:
            elapsed_time = time.time() - start_time
            logger.warning(f"Timeout when unshortening URL with Selenium: {url}")
            return {
                "original_url": url,
                "final_url": url,
                "success": False,
                "method": "selenium",
                "error": "Page load timeout",
                "elapsed_time": round(elapsed_time, 3)
            }
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"Error unshortening URL with Selenium: {str(e)}")
            return {
                "original_url": url,
                "final_url": url,
                "success": False,
                "method": "selenium",
                "error": str(e),
                "elapsed_time": round(elapsed_time, 3)
            }
    
    def _extract_js_redirect(self, html: str) -> Optional[str]:
        """Extract JavaScript redirect URL from HTML content."""
        if not html:
            return None
            
        # Common JavaScript redirect patterns
        patterns = [
            r'window\.location\.href\s*=\s*[\'"]([^\'"]+)[\'"]',
            r'window\.location\s*=\s*[\'"]([^\'"]+)[\'"]',
            r'window\.location\.replace\([\'"]([^\'"]+)[\'"]\)',
            r'window\.location\.assign\([\'"]([^\'"]+)[\'"]\)',
            r'<meta\s+http-equiv=[\'"]refresh[\'"]\s+content=[\'"]0;\s*url=([^\'"]+)[\'"]',
            r'<meta\s+content=[\'"]0;\s*url=([^\'"]+)[\'"]\s+http-equiv=[\'"]refresh[\'"]'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                return match.group(1)
                
        return None
    
    async def unshorten_url(self, url: str) -> Dict:
        """
        Unshorten a URL using the best available method.
        
        Args:
            url: The URL to unshorten
            
        Returns:
            Dictionary with unshortening results
        """
        if not self.enabled:
            logger.debug(f"URL unshortening disabled, returning original URL: {url}")
            return {
                "original_url": url,
                "final_url": url,
                "success": True,
                "method": "none",
                "message": "URL unshortening disabled"
            }
            
        if not url:
            return {
                "original_url": "",
                "final_url": "",
                "success": False,
                "error": "Empty URL provided"
            }
            
        # Ensure URL has a scheme
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        logger.info(f"Unshortening URL: {url}")
        
        # First try with requests (faster)
        requests_result = await self.unshorten_with_requests(url)
        
        # If requests method worked and found a different URL, we're done
        if (requests_result["success"] and 
            requests_result["final_url"] != url and 
            requests_result["final_url"] != requests_result["original_url"]):
            logger.info(f"Successfully unshortened URL with requests: {url} -> {requests_result['final_url']}")
            return requests_result
            
        # If requests didn't work or didn't find a redirect, try Selenium if available
        if self.use_selenium:
            logger.info(f"Trying to unshorten URL with Selenium: {url}")
            selenium_result = await self.unshorten_with_selenium(url)
            
            # If Selenium found a redirect, use its result
            if (selenium_result["success"] and 
                selenium_result["final_url"] != url and 
                selenium_result["final_url"] != selenium_result["original_url"]):
                logger.info(f"Successfully unshortened URL with Selenium: {url} -> {selenium_result['final_url']}")
                return selenium_result
        
        # If both methods failed or didn't find redirects, return the best result
        if requests_result["success"]:
            return requests_result
        elif self.use_selenium and selenium_result.get("success", False):
            return selenium_result
        else:
            # Both methods failed, combine error messages
            error_msg = []
            if "error" in requests_result:
                error_msg.append(f"Requests error: {requests_result['error']}")
            if self.use_selenium and "error" in selenium_result:
                error_msg.append(f"Selenium error: {selenium_result['error']}")
                
            logger.warning(f"Failed to unshorten URL: {url} - {' | '.join(error_msg)}")
            
            return {
                "original_url": url,
                "final_url": url,
                "success": False,
                "error": " | ".join(error_msg) if error_msg else "Unknown error",
                "method": "combined"
            }
    
    async def unshorten_urls(self, urls: List[str]) -> Dict[str, Dict]:
        """
        Unshorten multiple URLs in parallel.
        
        Args:
            urls: List of URLs to unshorten
            
        Returns:
            Dictionary mapping original URLs to their unshortening results
        """
        if not urls:
            return {}
            
        logger.info(f"Unshortening {len(urls)} URLs")
        
        # Process URLs in parallel using asyncio.gather
        tasks = [self.unshorten_url(url) for url in urls]
        results = await asyncio.gather(*tasks)
        
        # Create a dictionary mapping original URLs to results
        return {result["original_url"]: result for result in results}
    
    def close(self):
        """Clean up resources."""
        if self.selenium_initialized and self.driver:
            try:
                self.driver.quit()
                self.selenium_initialized = False
                logger.info("Selenium WebDriver closed")
            except Exception as e:
                logger.error(f"Error closing Selenium WebDriver: {str(e)}") 