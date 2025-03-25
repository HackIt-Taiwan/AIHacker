#!/usr/bin/env python3
"""
Test script for URL expansion module.
This script tests the recursive URL expansion functionality with example URLs.
"""

import asyncio
import sys
from app.ai.service.url_safety import URLSafetyService

async def test_url_expansion():
    """Test URL expansion functionality with various URL shorteners."""
    service = URLSafetyService()
    
    # Test URLs
    test_urls = [
        "https://shorturl.at/C4sc4",
        "https://reurl.cc/4La7yR",
        "https://bit.ly/3yRpw6d",
        "https://tinyurl.com/2p8z44je"
    ]
    
    for url in test_urls:
        print(f"\nTesting URL: {url}")
        try:
            expanded_url = await service._expand_url_recursive(url)
            print(f"✅ Expanded to: {expanded_url}")
            
            # Test the full URL expansion pipeline
            original, expanded = await service._expand_url(url)
            print(f"  Full pipeline: {original} → {expanded}")
        except Exception as e:
            print(f"❌ Error expanding URL: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_url_expansion()) 