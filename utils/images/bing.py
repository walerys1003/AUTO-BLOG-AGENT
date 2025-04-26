"""
Bing Image Search API Module

This module provides search functionality for Bing Image Search.
Microsoft Azure offers a free tier with 1,000 transactions per month.
"""
import os
import logging
import requests
from typing import List, Dict, Any, Optional

# Setup logging
logger = logging.getLogger(__name__)

# Bing Search API key from config
from config import Config

BING_SEARCH_API_KEY = Config.BING_SEARCH_API_KEY
BING_SEARCH_ENDPOINT = "https://api.bing.microsoft.com/v7.0/images/search"

def search_bing_images(
    query: str,
    per_page: int = 20,
    page: int = 1,
    orientation: Optional[str] = None,
    size: Optional[str] = None,
    safe_search: str = "Moderate"
) -> List[Dict[str, Any]]:
    """
    Search for images using Bing Image Search API
    
    Args:
        query: Search query
        per_page: Number of results per page (max 150)
        page: Page number
        orientation: Optional orientation filter (Square, Wide, Tall)
        size: Optional size filter (Small, Medium, Large, Wallpaper)
        safe_search: Safe search filter (Off, Moderate, Strict)
        
    Returns:
        List of image data dictionaries
    """
    # Constrain per_page
    per_page = min(per_page, 150)  # Bing allows max 150 results per query
    
    logger.info(f"Searching Bing Images for: {query}")
    
    # Check if we have API key
    if not BING_SEARCH_API_KEY:
        logger.warning("No Bing Search API key found. Set BING_SEARCH_API_KEY environment variable.")
        return []
    
    # Calculate offset for pagination
    offset = (page - 1) * per_page
    
    # Setup parameters
    params = {
        "q": query,
        "count": per_page,
        "offset": offset,
        "mkt": "en-US",  # Market
        "safeSearch": safe_search
    }
    
    # Add optional filters
    if orientation:
        # Map to Bing's expected values
        if orientation.lower() == "landscape":
            params["aspect"] = "Wide"
        elif orientation.lower() == "portrait":
            params["aspect"] = "Tall"
        elif orientation.lower() == "square":
            params["aspect"] = "Square"
    
    # Add size filter if provided
    if size:
        params["size"] = size
    
    # Setup headers with API key
    headers = {
        "Ocp-Apim-Subscription-Key": BING_SEARCH_API_KEY
    }
    
    try:
        # Make request to Bing Image Search API
        response = requests.get(BING_SEARCH_ENDPOINT, headers=headers, params=params)
        response.raise_for_status()
        
        # Parse JSON response
        data = response.json()
        
        # Check if results are present
        if "value" in data and isinstance(data["value"], list):
            # Process image results
            results = []
            for image in data["value"]:
                # Build image object with standardized fields for our system
                image_obj = {
                    "id": image.get("imageId", ""),
                    "url": image.get("contentUrl", ""),
                    "thumb_url": image.get("thumbnailUrl", ""),
                    "width": image.get("width", 0),
                    "height": image.get("height", 0),
                    "description": image.get("name", ""),
                    "source": "bing",
                    "attribution_text": f"Image from {image.get('hostPageDisplayUrl', 'Bing')}",
                    "attribution_url": image.get("hostPageUrl", ""),
                    "user": {
                        "name": image.get("hostPageDisplayUrl", "Unknown"),
                        "profile_url": image.get("hostPageUrl", "")
                    }
                }
                results.append(image_obj)
            
            logger.info(f"Found {len(results)} images for '{query}' via Bing Image Search")
            return results
        else:
            logger.warning(f"No image results found for '{query}' via Bing Image Search")
            return []
            
    except Exception as e:
        logger.error(f"Error searching Bing Images: {str(e)}")
        return []

def get_bing_image_details(image_id: str) -> Dict[str, Any]:
    """
    Get details for a specific image by ID
    
    Args:
        image_id: Bing Image ID
        
    Returns:
        Image data dictionary
    """
    # This functionality would require additional API calls.
    # For now, we return a placeholder since image details should already be stored when searching
    logger.warning("Bing Image detail retrieval not fully implemented. Returning placeholder.")
    return {
        "id": image_id,
        "url": "",
        "thumb_url": "",
        "description": "Bing image details not available",
        "source": "bing",
        "attribution_text": "Image from Bing Search",
        "attribution_url": ""
    }