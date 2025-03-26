"""
URL blacklist service.

This module provides functionality to manage a blacklist of URLs that have been
previously identified as unsafe by the URL safety checker.
"""
import os
import json
import time
import logging
import threading
from typing import Dict, List, Optional, Set
from urllib.parse import urlparse

# Create a logger for this module
logger = logging.getLogger(__name__)

class URLBlacklist:
    """
    Manages a persistent blacklist of unsafe URLs.
    
    This class provides methods to check, add, and remove URLs from the blacklist.
    The blacklist is stored in a JSON file and periodically saved to disk.
    """
    
    def __init__(self, blacklist_file: str = "data/url_blacklist.json"):
        """
        Initialize the URL blacklist.
        
        Args:
            blacklist_file: Path to the JSON file storing the blacklist
        """
        self.blacklist_file = blacklist_file
        self.blacklist = {}  # Dict mapping URLs to metadata (detection time, threat types, etc.)
        self.domains_blacklist = {}  # Dict mapping domains to metadata
        self.shortened_urls_map = {}  # Dict mapping shortened URLs to their expanded versions
        self.modified = False
        self.lock = threading.RLock()  # Reentrant lock for thread safety
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(self.blacklist_file), exist_ok=True)
        
        # Load existing blacklist if available
        self._load_blacklist()
        
        # Start background save thread
        self._start_save_thread()
        
    def _load_blacklist(self) -> None:
        """Load the blacklist from the JSON file."""
        try:
            if os.path.exists(self.blacklist_file):
                with open(self.blacklist_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.blacklist = data.get('urls', {})
                    self.domains_blacklist = data.get('domains', {})
                    self.shortened_urls_map = data.get('shortened_urls', {})
                    logger.info(f"Loaded URL blacklist with {len(self.blacklist)} URLs, {len(self.domains_blacklist)} domains, and {len(self.shortened_urls_map)} shortened URLs")
            else:
                logger.info(f"No existing URL blacklist found at {self.blacklist_file}")
                self.blacklist = {}
                self.domains_blacklist = {}
                self.shortened_urls_map = {}
        except Exception as e:
            logger.error(f"Error loading URL blacklist: {str(e)}")
            self.blacklist = {}
            self.domains_blacklist = {}
            self.shortened_urls_map = {}
        
    def _save_blacklist(self) -> None:
        """Save the blacklist to the JSON file if modified."""
        with self.lock:
            if not self.modified:
                return
            
            try:
                with open(self.blacklist_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'urls': self.blacklist,
                        'domains': self.domains_blacklist,
                        'shortened_urls': self.shortened_urls_map,
                        'last_updated': time.time()
                    }, f, indent=2)
                self.modified = False
                logger.info(f"Saved URL blacklist with {len(self.blacklist)} URLs, {len(self.domains_blacklist)} domains, and {len(self.shortened_urls_map)} shortened URLs")
            except Exception as e:
                logger.error(f"Error saving URL blacklist: {str(e)}")
                
    def _start_save_thread(self) -> None:
        """Start a background thread to periodically save the blacklist."""
        def save_loop():
            while True:
                time.sleep(60)  # Save every minute if modified
                self._save_blacklist()
                
        save_thread = threading.Thread(target=save_loop, daemon=True)
        save_thread.start()
        
    def is_blacklisted(self, url: str) -> Dict:
        """
        Check if a URL is in the blacklist.
        
        Args:
            url: The URL to check
            
        Returns:
            A dict with metadata if the URL is blacklisted, empty dict otherwise
        """
        # 去除不必要的鎖，因為我們已經在主函數中批量處理
        # 使用快速路徑檢查
        
        # First check exact URL match (最快的路徑)
        if url in self.blacklist:
            logger.info(f"URL found in blacklist: {url}")
            return self.blacklist[url]
        
        # Then check if it's a shortened URL we've seen before (第二快的路徑)
        if url in self.shortened_urls_map:
            expanded_url = self.shortened_urls_map[url]
            if expanded_url in self.blacklist:
                logger.info(f"Shortened URL found in blacklist: {url} -> {expanded_url}")
                result = self.blacklist[expanded_url].copy()
                result['original_shortened_url'] = url
                result['expanded_url'] = expanded_url
                return result
        
        # Then check domain match (if enabled)
        try:
            domain = urlparse(url).netloc.lower()
            if domain and domain in self.domains_blacklist:
                logger.info(f"Domain found in blacklist: {domain} (URL: {url})")
                return self.domains_blacklist[domain]
        except Exception as e:
            logger.warning(f"Error parsing domain from URL {url}: {str(e)}")
            
        return {}
    
    def add_url(self, url: str, metadata: Dict) -> None:
        """
        Add a URL to the blacklist.
        
        Args:
            url: The URL to blacklist
            metadata: Information about the URL (detection time, threat types, etc.)
        """
        with self.lock:
            self.blacklist[url] = {
                **metadata,
                'blacklisted_at': time.time()
            }
            self.modified = True
            logger.info(f"Added URL to blacklist: {url}")
            
    def add_domain(self, domain: str, metadata: Dict) -> None:
        """
        Add a domain to the blacklist.
        
        Args:
            domain: The domain to blacklist
            metadata: Information about the domain (detection time, threat types, etc.)
        """
        with self.lock:
            self.domains_blacklist[domain.lower()] = {
                **metadata,
                'blacklisted_at': time.time()
            }
            self.modified = True
            logger.info(f"Added domain to blacklist: {domain}")
            
    def add_shortened_url(self, shortened_url: str, expanded_url: str) -> None:
        """
        Add a mapping from shortened URL to its expanded version.
        
        Args:
            shortened_url: The original shortened URL
            expanded_url: The expanded URL that it redirects to
        """
        if shortened_url != expanded_url:
            with self.lock:
                self.shortened_urls_map[shortened_url] = expanded_url
                self.modified = True
                logger.info(f"Added shortened URL mapping: {shortened_url} -> {expanded_url}")
    
    def add_unsafe_result(self, url: str, result: Dict, original_url: str = None, blacklist_domain: bool = False) -> None:
        """
        Add a URL to the blacklist based on a safety check result.
        
        Args:
            url: The URL to blacklist (expanded URL)
            result: The safety check result dictionary
            original_url: The original shortened URL (if applicable)
            blacklist_domain: Whether to also blacklist the domain
        """
        with self.lock:
            # Add the URL to the blacklist
            self.add_url(url, {
                'reason': result.get('message', 'Unknown threat'),
                'threat_types': result.get('threat_types', ['UNKNOWN']),
                'severity': result.get('severity', 5),
                'unsafe_score': result.get('unsafe_score', 1.0),
                'check_time': result.get('check_time')
            })
            
            # If this was a shortened URL, add the mapping
            if original_url and original_url != url:
                self.add_shortened_url(original_url, url)
            
            # Optionally blacklist the domain for high-severity threats
            if blacklist_domain and result.get('severity', 0) >= 8:
                try:
                    domain = urlparse(url).netloc.lower()
                    if domain:
                        self.add_domain(domain, {
                            'reason': f"Domain of unsafe URL: {result.get('message', 'Unknown threat')}",
                            'threat_types': result.get('threat_types', ['UNKNOWN']),
                            'severity': result.get('severity', 5),
                            'source_url': url,
                            'unsafe_score': result.get('unsafe_score', 1.0),
                            'check_time': result.get('check_time')
                        })
                except Exception as e:
                    logger.warning(f"Error extracting domain from URL {url}: {str(e)}")
            
    def remove_url(self, url: str) -> bool:
        """
        Remove a URL from the blacklist.
        
        Args:
            url: The URL to remove
            
        Returns:
            True if the URL was in the blacklist and removed, False otherwise
        """
        with self.lock:
            if url in self.blacklist:
                del self.blacklist[url]
                self.modified = True
                logger.info(f"Removed URL from blacklist: {url}")
                return True
            return False
            
    def remove_domain(self, domain: str) -> bool:
        """
        Remove a domain from the blacklist.
        
        Args:
            domain: The domain to remove
            
        Returns:
            True if the domain was in the blacklist and removed, False otherwise
        """
        with self.lock:
            domain_lower = domain.lower()
            if domain_lower in self.domains_blacklist:
                del self.domains_blacklist[domain_lower]
                self.modified = True
                logger.info(f"Removed domain from blacklist: {domain}")
                return True
            return False
            
    def remove_shortened_url(self, shortened_url: str) -> bool:
        """
        Remove a shortened URL mapping from the blacklist.
        
        Args:
            shortened_url: The shortened URL to remove
            
        Returns:
            True if the URL was in the blacklist and removed, False otherwise
        """
        with self.lock:
            if shortened_url in self.shortened_urls_map:
                del self.shortened_urls_map[shortened_url]
                self.modified = True
                logger.info(f"Removed shortened URL from blacklist: {shortened_url}")
                return True
            return False
            
    def clear(self) -> None:
        """Clear the entire blacklist."""
        with self.lock:
            self.blacklist.clear()
            self.domains_blacklist.clear()
            self.modified = True
            logger.info("Cleared URL blacklist")
            
    def close(self) -> None:
        """Save the blacklist and clean up resources."""
        self._save_blacklist() 