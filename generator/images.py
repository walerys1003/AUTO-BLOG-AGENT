import os
import logging
import requests
import json
import random
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
        # Use Unsplash API if key is available, otherwise return empty list
        if not Config.UNSPLASH_API_KEY:
            logger.warning("Unsplash API key not configured")
            return []
        
        # Build API URL
        url = f"https://api.unsplash.com/search/photos"
        
        # Set up parameters
        params = {
            "query": query,
            "per_page": count,
            "orientation": "landscape"  # Prefer landscape orientation for blog images
        }
        
        # Set up headers
        headers = {
            "Authorization": f"Client-ID {Config.UNSPLASH_API_KEY}",
            "Accept-Version": "v1"
        }
        
        # Make API request
        response = requests.get(url, params=params, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            
            # Format image data
            images = []
            for image in results:
                image_data = {
                    "url": image.get("urls", {}).get("regular", ""),
                    "alt_text": image.get("alt_description", query),
                    "attribution": {
                        "name": image.get("user", {}).get("name", "Unsplash"),
                        "url": image.get("user", {}).get("links", {}).get("html", "https://unsplash.com")
                    },
                    "download_url": image.get("urls", {}).get("full", ""),
                    "width": image.get("width", 1200),
                    "height": image.get("height", 800)
                }
                images.append(image_data)
            
            return images
        else:
            logger.error(f"Unsplash API error: {response.status_code}, {response.text}")
            return []
            
    except Exception as e:
        logger.error(f"Error searching Unsplash images: {str(e)}")
        logger.error(traceback.format_exc())
        return []

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
        # This is a placeholder for integrating with other image APIs
        # Would be replaced with actual Google Images API or similar
        # For now, return placeholder images
        
        # Create a list of fallback placeholder images
        images = []
        for i in range(min(count, 3)):
            # Use placeholder.com for demo/fallback
            width = 1200
            height = 800
            image_data = {
                "url": f"https://via.placeholder.com/{width}x{height}?text={query.replace(' ', '+')}",
                "alt_text": f"{query} image",
                "attribution": {
                    "name": "Placeholder",
                    "url": "https://placeholder.com"
                },
                "download_url": f"https://via.placeholder.com/{width}x{height}?text={query.replace(' ', '+')}",
                "width": width,
                "height": height
            }
            images.append(image_data)
        
        logger.warning(f"Using alternative image source for query: {query}")
        return images
        
    except Exception as e:
        logger.error(f"Error with alternative image search: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Return very basic fallback in case of total failure
        return [{
            "url": f"https://via.placeholder.com/1200x800?text=Image+Unavailable",
            "alt_text": "Image unavailable",
            "attribution": {
                "name": "Placeholder",
                "url": "https://placeholder.com"
            },
            "download_url": f"https://via.placeholder.com/1200x800?text=Image+Unavailable",
            "width": 1200,
            "height": 800
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
        # Combine title and keywords to create a good search query
        query_terms = [title] + keywords[:3]  # Use title and top 3 keywords
        query = " ".join(query_terms)
        
        # First try Unsplash
        unsplash_images = search_unsplash_images(query)
        
        # If Unsplash found images, use the first one
        if unsplash_images:
            return unsplash_images[0]
        
        # If no Unsplash images, try with just the title
        if title:
            unsplash_title_only = search_unsplash_images(title)
            if unsplash_title_only:
                return unsplash_title_only[0]
        
        # If keywords exist, try with first keyword
        if keywords:
            unsplash_keyword = search_unsplash_images(keywords[0])
            if unsplash_keyword:
                return unsplash_keyword[0]
        
        # Fall back to alternative sources
        alternative_images = search_alternative_images(query)
        if alternative_images:
            return alternative_images[0]
            
        # If everything fails, return a very basic placeholder
        return {
            "url": "https://via.placeholder.com/1200x800?text=Featured+Image",
            "alt_text": "Featured image",
            "attribution": {
                "name": "Placeholder",
                "url": "https://placeholder.com"
            },
            "download_url": "https://via.placeholder.com/1200x800?text=Featured+Image",
            "width": 1200,
            "height": 800
        }
        
    except Exception as e:
        logger.error(f"Error getting featured image: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Return a basic placeholder on error
        return {
            "url": "https://via.placeholder.com/1200x800?text=Featured+Image",
            "alt_text": "Featured image",
            "attribution": {
                "name": "Placeholder",
                "url": "https://placeholder.com"
            },
            "download_url": "https://via.placeholder.com/1200x800?text=Featured+Image",
            "width": 1200,
            "height": 800
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
    try:
        # Combine title and keywords to create a good search query
        query_terms = [title] + keywords[:5]  # Use title and top 5 keywords
        
        # Shuffle the terms to get variety (except keep title first)
        query_terms_shuffled = [query_terms[0]] + random.sample(query_terms[1:], min(len(query_terms[1:]), 4))
        
        # Try to get one image with the full query
        full_query = " ".join(query_terms_shuffled[:3])  # Use first 3 shuffled terms
        images = search_unsplash_images(full_query, 1)
        
        # If we need more images, try individual keywords
        if len(images) < count and keywords:
            for keyword in keywords[:count]:
                # Skip if we already have enough images
                if len(images) >= count:
                    break
                    
                keyword_images = search_unsplash_images(keyword, 1)
                
                # Only add if we got a result and it's not already in our list
                if keyword_images and all(img["url"] != keyword_images[0]["url"] for img in images):
                    images.append(keyword_images[0])
        
        # If we still need more images, use title
        if len(images) < count:
            title_images = search_unsplash_images(title, count - len(images))
            
            # Filter out duplicates
            for img in title_images:
                if all(existing["url"] != img["url"] for existing in images):
                    images.append(img)
        
        # If we don't have enough images, fill with alternative sources
        if len(images) < count:
            alternative_images = search_alternative_images(title, count - len(images))
            images.extend(alternative_images)
        
        return images[:count]  # Return requested number of images
        
    except Exception as e:
        logger.error(f"Error getting multiple images: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Return basic placeholders on error
        placeholders = []
        for i in range(count):
            placeholders.append({
                "url": f"https://via.placeholder.com/1200x800?text=Image+{i+1}",
                "alt_text": f"Article image {i+1}",
                "attribution": {
                    "name": "Placeholder",
                    "url": "https://placeholder.com"
                },
                "download_url": f"https://via.placeholder.com/1200x800?text=Image+{i+1}",
                "width": 1200,
                "height": 800
            })
        return placeholders