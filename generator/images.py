import logging
import json
import random
import requests
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from config import Config
import traceback

# Setup logging
logger = logging.getLogger(__name__)

def search_unsplash_images(query: str, count: int = 1) -> List[Dict[str, Any]]:
    """
    Search for images on Unsplash based on query
    
    Args:
        query: Search query for images
        count: Number of images to return
        
    Returns:
        List of image data dictionaries containing url, alt_text, and attribution
    """
    try:
        # Check if we have an Unsplash API key
        api_key = Config.UNSPLASH_API_KEY
        if not api_key:
            logger.warning("No Unsplash API key found, using alternative image source")
            return search_alternative_images(query, count)
        
        # Construct API URL
        api_url = "https://api.unsplash.com/search/photos"
        
        # Set up parameters
        params = {
            "query": query,
            "per_page": min(count, 10),  # Max 10 per page
            "orientation": "landscape",
            "content_filter": "high"
        }
        
        # Set up headers
        headers = {
            "Authorization": f"Client-ID {api_key}"
        }
        
        # Make request
        response = requests.get(api_url, params=params, headers=headers)
        
        # Check response
        if response.status_code != 200:
            logger.error(f"Error searching Unsplash: {response.status_code}, {response.text}")
            return search_alternative_images(query, count)
        
        # Parse response
        data = response.json()
        results = data.get("results", [])
        
        if not results:
            logger.warning(f"No images found on Unsplash for query: {query}")
            return search_alternative_images(query, count)
        
        # Format results
        images = []
        for result in results[:count]:
            image_data = {
                "id": result.get("id"),
                "url": result.get("urls", {}).get("regular"),
                "download_url": result.get("urls", {}).get("full"),
                "width": result.get("width"),
                "height": result.get("height"),
                "alt_text": result.get("alt_description") or query,
                "attribution": {
                    "name": result.get("user", {}).get("name", "Unsplash Photographer"),
                    "username": result.get("user", {}).get("username"),
                    "url": result.get("user", {}).get("links", {}).get("html")
                },
                "source": "unsplash"
            }
            images.append(image_data)
        
        return images
        
    except Exception as e:
        logger.error(f"Error searching Unsplash: {str(e)}")
        logger.error(traceback.format_exc())
        return search_alternative_images(query, count)

def search_alternative_images(query: str, count: int = 1) -> List[Dict[str, Any]]:
    """
    Search for images from alternative sources when Unsplash fails
    
    Args:
        query: Search query for images
        count: Number of images to return
        
    Returns:
        List of image data dictionaries with fallback images
    """
    try:
        # In a real system, this would search an alternative API
        # For now, return placeholder images
        
        images = []
        for i in range(count):
            # Generate a unique identifier for each image
            timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            unique_id = f"{timestamp}_{i}_{hash(query) % 10000}"
            
            image_data = {
                "id": unique_id,
                "url": f"https://picsum.photos/seed/{unique_id}/800/600",
                "download_url": f"https://picsum.photos/seed/{unique_id}/1200/800",
                "width": 1200,
                "height": 800,
                "alt_text": query,
                "attribution": {
                    "name": "Lorem Picsum",
                    "username": "picsum",
                    "url": "https://picsum.photos"
                },
                "source": "picsum"
            }
            images.append(image_data)
        
        return images
        
    except Exception as e:
        logger.error(f"Error searching alternative images: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Return a very basic fallback
        return [{
            "id": "fallback",
            "url": "https://picsum.photos/800/600",
            "download_url": "https://picsum.photos/1200/800",
            "width": 1200,
            "height": 800,
            "alt_text": query,
            "attribution": {
                "name": "Lorem Picsum",
                "username": "picsum",
                "url": "https://picsum.photos"
            },
            "source": "fallback"
        }]

def get_featured_image_for_article(title: str, keywords: List[str]) -> Dict[str, Any]:
    """
    Get a featured image for an article based on title and keywords
    
    Args:
        title: Article title
        keywords: Article keywords
        
    Returns:
        Dictionary with image data
    """
    try:
        # Build query from title and primary keywords
        query_parts = [title]
        
        # Add up to 3 keywords
        for keyword in keywords[:3]:
            if keyword.lower() not in title.lower():
                query_parts.append(keyword)
        
        # Join query parts
        query = " ".join(query_parts)
        
        # Get image
        images = search_unsplash_images(query, count=1)
        
        if images and len(images) > 0:
            return images[0]
        else:
            logger.warning(f"No featured image found for article: {title}")
            return {}
        
    except Exception as e:
        logger.error(f"Error getting featured image: {str(e)}")
        logger.error(traceback.format_exc())
        return {}

def get_multiple_images_for_article(title: str, keywords: List[str], count: int = 3) -> List[Dict[str, Any]]:
    """
    Get multiple images for an article based on different keywords
    
    Args:
        title: Article title
        keywords: Article keywords
        count: Number of images to retrieve
        
    Returns:
        List of image data dictionaries
    """
    try:
        images = []
        
        # First, try to get a primary image based on the title
        primary_image = get_featured_image_for_article(title, keywords)
        if primary_image:
            images.append(primary_image)
        
        # If we need more images, try individual keywords
        if len(images) < count and keywords:
            # Shuffle keywords for variety
            shuffled_keywords = keywords.copy()
            random.shuffle(shuffled_keywords)
            
            # Try each keyword
            for keyword in shuffled_keywords:
                if len(images) >= count:
                    break
                    
                # Check if we already have an image for this keyword
                keyword_used = False
                for image in images:
                    if keyword.lower() in image.get("alt_text", "").lower():
                        keyword_used = True
                        break
                
                if keyword_used:
                    continue
                
                # Search for an image with this keyword
                keyword_images = search_unsplash_images(keyword, count=1)
                if keyword_images and len(keyword_images) > 0:
                    images.append(keyword_images[0])
        
        # If we still need more images, use a generic search
        if len(images) < count:
            remaining = count - len(images)
            generic_query = title if not images else f"{title} {random.choice(keywords)}"
            generic_images = search_unsplash_images(generic_query, count=remaining)
            images.extend(generic_images)
        
        return images[:count]
        
    except Exception as e:
        logger.error(f"Error getting multiple images: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Return basic fallback images
        return search_alternative_images(title, count)