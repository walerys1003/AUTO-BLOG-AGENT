import requests
import logging
import json
import random
import base64
from typing import Optional, Dict, Any, List
import traceback
from config import Config
from urllib.parse import quote_plus

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
        # Check if Unsplash API key is available
        api_key = Config.UNSPLASH_API_KEY
        if not api_key:
            logger.warning("No Unsplash API key found, falling back to alternative sources")
            return search_alternative_images(query, count)
        
        # Prepare API request
        url = "https://api.unsplash.com/search/photos"
        headers = {
            "Authorization": f"Client-ID {api_key}"
        }
        params = {
            "query": query,
            "per_page": count,
            "orientation": "landscape"
        }
        
        # Make API request
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            images = []
            
            # Process results
            for result in data.get("results", [])[:count]:
                image = {
                    "url": result.get("urls", {}).get("regular"),
                    "thumb_url": result.get("urls", {}).get("thumb"),
                    "alt_text": result.get("alt_description") or query,
                    "attribution": {
                        "name": result.get("user", {}).get("name"),
                        "link": result.get("user", {}).get("links", {}).get("html")
                    },
                    "width": result.get("width"),
                    "height": result.get("height")
                }
                images.append(image)
            
            return images
        else:
            logger.warning(f"Failed to fetch images from Unsplash: {response.status_code}")
            return search_alternative_images(query, count)
            
    except Exception as e:
        logger.error(f"Error searching Unsplash images: {str(e)}")
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
    # Alternative image sources could include Pexels, Pixabay, etc.
    # For now, we'll use a simplified approach with public domain placeholder images
    
    # List of free placeholder image services
    placeholder_services = [
        {
            "url": f"https://placehold.co/600x400/png?text={quote_plus(query)}",
            "thumb_url": f"https://placehold.co/300x200/png?text={quote_plus(query)}",
            "alt_text": query,
            "attribution": {
                "name": "Placeholder Service",
                "link": "https://placehold.co/"
            },
            "width": 600,
            "height": 400
        },
        {
            "url": f"https://fakeimg.pl/600x400/cccccc/909090/?text={quote_plus(query)}&font_size=24",
            "thumb_url": f"https://fakeimg.pl/300x200/cccccc/909090/?text={quote_plus(query)}&font_size=18",
            "alt_text": query,
            "attribution": {
                "name": "Fake Image",
                "link": "https://fakeimg.pl/"
            },
            "width": 600,
            "height": 400
        },
        {
            "url": f"https://dummyimage.com/600x400/000/fff&text={quote_plus(query)}",
            "thumb_url": f"https://dummyimage.com/300x200/000/fff&text={quote_plus(query)}",
            "alt_text": query,
            "attribution": {
                "name": "Dummy Image",
                "link": "https://dummyimage.com/"
            },
            "width": 600,
            "height": 400
        }
    ]
    
    # Return requested number of placeholder images
    return random.sample(placeholder_services, min(count, len(placeholder_services)))

def get_featured_image_for_article(title: str, keywords: List[str]) -> Dict[str, Any]:
    """
    Get a featured image for an article based on title and keywords
    
    Args:
        title: Article title
        keywords: Article keywords
        
    Returns:
        Dictionary with image data
    """
    # Combine title and primary keywords for better image search results
    search_query = title
    if keywords and len(keywords) > 0:
        # Add the first keyword if it's not already in the title
        if keywords[0].lower() not in title.lower():
            search_query = f"{keywords[0]} {title}"
    
    # Search for images
    images = search_unsplash_images(search_query)
    
    # Return the first image or a fallback
    if images and len(images) > 0:
        return images[0]
    else:
        # Create a basic fallback image
        return {
            "url": f"https://placehold.co/800x450/png?text={quote_plus(title)}",
            "thumb_url": f"https://placehold.co/400x225/png?text={quote_plus(title)}",
            "alt_text": title,
            "attribution": {
                "name": "Placeholder Image",
                "link": "https://placehold.co/"
            },
            "width": 800,
            "height": 450
        }

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
    images = []
    
    # Add main image based on title
    main_image = get_featured_image_for_article(title, keywords)
    images.append(main_image)
    
    # If we need more images, search based on keywords
    if count > 1 and keywords and len(keywords) > 0:
        # Use different keywords for diversity
        for i in range(min(len(keywords), count - 1)):
            keyword_images = search_unsplash_images(keywords[i], 1)
            if keyword_images and len(keyword_images) > 0:
                images.append(keyword_images[0])
    
    # If we still need more images, use alternatives
    while len(images) < count:
        search_term = random.choice(keywords) if keywords else title
        alt_images = search_alternative_images(search_term, 1)
        if alt_images and len(alt_images) > 0:
            images.append(alt_images[0])
    
    return images[:count]
