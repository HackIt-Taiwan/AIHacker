"""
Content moderation service using OpenAI's Moderation API.
"""
import os
import logging
import base64
import aiohttp
import io
from typing import Dict, List, Union, Tuple, Optional, Any
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

def convert_to_dict(obj: Any) -> Union[Dict, Any]:
    """
    Convert an object to a dictionary for JSON serialization.
    Works recursively for nested objects with __dict__ attribute.
    
    Args:
        obj: The object to convert
        
    Returns:
        A dictionary representation or the original object if conversion not possible
    """
    if hasattr(obj, '__dict__'):
        return {key: convert_to_dict(value) for key, value in obj.__dict__.items()}
    return obj

class ContentModerator:
    """
    A class to moderate content using OpenAI's moderation API.
    
    This class provides methods to check both text and images for inappropriate content.
    """
    
    def __init__(self, openai_client: Optional[AsyncOpenAI] = None):
        """
        Initialize the content moderator with an OpenAI client.
        
        Args:
            openai_client: An optional AsyncOpenAI client. If not provided, a new one will be created.
        """
        # Initialize with provided client or create a new one using standard OpenAI API
        self.client = openai_client or AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
    async def moderate_text(self, text: str) -> Tuple[bool, Dict]:
        """
        Moderate text content using OpenAI's moderation API.
        
        Args:
            text: The text content to moderate.
            
        Returns:
            A tuple containing a boolean indicating if the content violates policies,
            and a dictionary with detailed results.
        """
        try:
            response = await self.client.moderations.create(
                input=[{"type": "text", "text": text}],
                model="omni-moderation-latest"
            )
            
            # Get the result from the first (and only) entry
            result = response.results[0]
            
            # Check if the content is flagged
            is_flagged = result.flagged
            
            # Convert Categories and CategoryScores objects to dictionaries for JSON serialization
            categories_dict = convert_to_dict(result.categories)
            category_scores_dict = convert_to_dict(result.category_scores)
            
            # Return flagged status and detailed results
            return is_flagged, {
                "categories": categories_dict,
                "category_scores": category_scores_dict,
                "flagged": result.flagged
            }
        
        except Exception as e:
            logger.error(f"Error moderating text: {str(e)}")
            # In case of error, return False to prevent false positives
            return False, {"error": str(e)}
    
    async def moderate_image(self, image_url: str) -> Tuple[bool, Dict]:
        """
        Moderate image content using OpenAI's moderation API.
        
        Args:
            image_url: The URL of the image to moderate.
            
        Returns:
            A tuple containing a boolean indicating if the image violates policies,
            and a dictionary with detailed results.
        """
        try:
            response = await self.client.moderations.create(
                input=[{"type": "image_url", "image_url": {"url": image_url}}],
                model="omni-moderation-latest"
            )
            
            # Get the result from the first (and only) entry
            result = response.results[0]
            
            # Check if the content is flagged
            is_flagged = result.flagged
            
            # Convert Categories and CategoryScores objects to dictionaries for JSON serialization
            categories_dict = convert_to_dict(result.categories)
            category_scores_dict = convert_to_dict(result.category_scores)
            
            # Return flagged status and detailed results
            return is_flagged, {
                "categories": categories_dict,
                "category_scores": category_scores_dict,
                "flagged": result.flagged
            }
        
        except Exception as e:
            logger.error(f"Error moderating image: {str(e)}")
            # In case of error, return False to prevent false positives
            return False, {"error": str(e)}
    
    async def moderate_image_from_file(self, image_data: bytes, image_type: str) -> Tuple[bool, Dict]:
        """
        Moderate image content from binary data using OpenAI's moderation API.
        
        Args:
            image_data: The binary image data to moderate.
            image_type: The MIME type of the image (e.g., 'image/png').
            
        Returns:
            A tuple containing a boolean indicating if the image violates policies,
            and a dictionary with detailed results.
        """
        try:
            # Convert image data to base64
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            # Create data URL format for the image
            data_url = f"data:{image_type};base64,{base64_image}"
            
            response = await self.client.moderations.create(
                input=[{"type": "image_url", "image_url": {"url": data_url}}],
                model="omni-moderation-latest"
            )
            
            # Get the result from the first (and only) entry
            result = response.results[0]
            
            # Check if the content is flagged
            is_flagged = result.flagged
            
            # Convert Categories and CategoryScores objects to dictionaries for JSON serialization
            categories_dict = convert_to_dict(result.categories)
            category_scores_dict = convert_to_dict(result.category_scores)
            
            # Return flagged status and detailed results
            return is_flagged, {
                "categories": categories_dict,
                "category_scores": category_scores_dict,
                "flagged": result.flagged
            }
        
        except Exception as e:
            logger.error(f"Error moderating image from file: {str(e)}")
            # In case of error, return False to prevent false positives
            return False, {"error": str(e)}
    
    async def download_image(self, image_url: str) -> Tuple[Optional[bytes], Optional[str]]:
        """
        Download an image from a URL.
        
        Args:
            image_url: The URL of the image to download.
            
        Returns:
            A tuple containing the binary image data and its content type, or None if an error occurred.
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    if response.status == 200:
                        content_type = response.headers.get('Content-Type', 'image/jpeg')
                        image_data = await response.read()
                        return image_data, content_type
                    else:
                        logger.error(f"Failed to download image. Status: {response.status}")
                        return None, None
        except Exception as e:
            logger.error(f"Error downloading image: {str(e)}")
            return None, None
    
    async def moderate_content(self, text: str = None, image_urls: List[str] = None) -> Tuple[bool, Dict]:
        """
        Moderate both text and images in a single call.
        
        Args:
            text: Optional text content to moderate.
            image_urls: Optional list of image URLs to moderate.
            
        Returns:
            A tuple containing a boolean indicating if any content violates policies,
            and a dictionary with detailed results.
        """
        results = {
            "text_result": None,
            "image_results": [],
            "flagged": False
        }
        
        # Moderate text if provided
        if text:
            text_flagged, text_result = await self.moderate_text(text)
            results["text_result"] = text_result
            if text_flagged:
                results["flagged"] = True
        
        # Moderate images if provided
        if image_urls:
            for url in image_urls:
                image_flagged, image_result = await self.moderate_image(url)
                results["image_results"].append({
                    "url": url,
                    "result": image_result
                })
                if image_flagged:
                    results["flagged"] = True
        
        return results["flagged"], results 