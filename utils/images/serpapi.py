"""
SerpAPI Google Images search module

This module provides search functionality for Google Images using SerpAPI.
"""
import os
import logging
import requests
import json
from typing import List, Dict, Any, Optional, Union

# Setup logging
logger = logging.getLogger(__name__)

# SerpAPI key from environment (or Config)
SERPAPI_KEY = os.environ.get("SERPAPI_KEY", "57d393880136bab7d3159bf1d56d251fa3945bf56e6d1fa3448199e7c10e069c")

def search_google_images_serpapi(
    query: str,
    per_page: int = 20,
    page: int = 1,
    orientation: Optional[str] = None,
    safe_search: bool = True,
    location: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Search Google Images using SerpAPI
    
    Args:
        query: Search query
        per_page: Number of results per page
        page: Page number
        orientation: Image orientation (landscape, portrait, square)
        safe_search: Whether to enable safe search
        location: Optional location for the search
        
    Returns:
        List of image data dictionaries
    """
    logger.info(f"Searching Google Images via SerpAPI for: {query}")
    
    # Base URL for SerpAPI
    api_url = "https://serpapi.com/search"
    
    # Setup parameters
    params = {
        "engine": "google_images",
        "q": query,
        "api_key": SERPAPI_KEY,
        "ijn": page - 1,  # Google page number
    }
    
    # Add location if provided
    if location:
        params["location"] = location
    
    # Add orientation if provided
    if orientation:
        if orientation == "landscape":
            params["imgar"] = "w"  # Wide
        elif orientation == "portrait":
            params["imgar"] = "t"  # Tall
        elif orientation == "square":
            params["imgar"] = "s"  # Square
            
    # Add safe search if required
    if safe_search:
        params["safe"] = "active"
    
    try:
        # Make request to SerpAPI
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        
        # Parse JSON response
        data = response.json()
        
        # Check if images are present
        if "images_results" in data and isinstance(data["images_results"], list):
            # Process image results
            results = []
            for image in data["images_results"][:per_page]:
                # Build image object with all necessary fields
                image_obj = {
                    "id": str(image.get("position", 0)),
                    "url": image.get("original", image.get("thumbnail", "")),
                    "thumb_url": image.get("thumbnail", ""),
                    "width": image.get("original_width", 0),
                    "height": image.get("original_height", 0),
                    "description": image.get("title", ""),
                    "source": "google",
                    "attribution_text": image.get("source", "Google Images"),
                    "attribution_url": image.get("source_page", image.get("link", "")),
                    "user": {
                        "name": image.get("source", "Unknown"),
                        "profile_url": image.get("source_page", "")
                    }
                }
                results.append(image_obj)
            
            logger.info(f"Found {len(results)} images for '{query}' via SerpAPI")
            return results
        else:
            logger.warning(f"No image results found for '{query}' via SerpAPI")
            return []
            
    except Exception as e:
        logger.error(f"Error searching Google Images via SerpAPI: {str(e)}")
        # Re-raise exception after logging
        raise

def get_google_image_details_serpapi(image_id: str) -> Dict[str, Any]:
    """
    Get details for a specific Google image by ID through SerpAPI cache
    
    Args:
        image_id: Image ID (position in search results)
        
    Returns:
        Image data dictionary
    """
    # This is not directly supported by SerpAPI
    # In practice, we should store the full details when performing the search
    # and retrieve them here. This function is included for API completeness.
    raise NotImplementedError("Google Images detail retrieval via SerpAPI not supported directly.")