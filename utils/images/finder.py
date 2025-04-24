"""
Image Finder Module

This module provides a unified interface for fetching images from multiple sources.
"""
import logging
import os
import json
from typing import Dict, List, Any, Optional

from . import unsplash
from . import google

logger = logging.getLogger(__name__)

def find_images_for_topic(topic: str, keywords: List[str] = None, count: int = 5, 
                         source: str = "unsplash", orientation: str = None) -> List[Dict[str, Any]]:
    """
    Find images for a given topic from specified source
    
    Args:
        topic (str): Main topic
        keywords (list, optional): Additional keywords
        count (int): Number of images to fetch
        source (str): Source to use ('unsplash', 'google', 'all')
        orientation (str, optional): Image orientation preference
        
    Returns:
        list: List of image data dictionaries
    """
    # Build a search query from the topic and keywords
    query = topic
    if keywords and len(keywords) > 0:
        # Add up to 3 keywords to avoid over-specific queries
        query = f"{topic} {' '.join(keywords[:3])}"
    
    logger.info(f"Searching for images with query: {query} from source: {source}")
    
    results = []
    
    if source.lower() == "unsplash" or source.lower() == "all":
        # Fetch from Unsplash
        unsplash_images = unsplash.fetch_images(query, count=count, orientation=orientation)
        for img in unsplash_images:
            img['source'] = 'unsplash'
        results.extend(unsplash_images)
    
    if source.lower() == "google" or source.lower() == "all":
        # Fetch from Google Images
        google_images = google.fetch_images(query, count=count)
        for img in google_images:
            img['source'] = 'google'
        results.extend(google_images)
    
    # Return the top 'count' images
    return results[:count]


def get_featured_image(topic: str, keywords: List[str] = None, 
                      source: str = "unsplash", orientation: str = "landscape") -> Optional[Dict[str, Any]]:
    """
    Get a single featured image for an article
    
    Args:
        topic (str): Article topic
        keywords (list, optional): Article keywords
        source (str): Source to use ('unsplash', 'google')
        orientation (str): Preferred orientation
        
    Returns:
        dict: Image data or None if no suitable image is found
    """
    # Try to get multiple images to choose the best one
    images = find_images_for_topic(
        topic=topic,
        keywords=keywords,
        count=3,  # Get a few options to choose from
        source=source,
        orientation=orientation
    )
    
    if not images or len(images) == 0:
        logger.warning(f"No images found for topic: {topic}")
        
        # Fall back to a random image from Unsplash if the query fails
        if source.lower() == "unsplash":
            return unsplash.get_random_image(orientation=orientation)
            
        return None
    
    # Return the first (usually best match) image
    return images[0]


def download_featured_image(image_data: Dict[str, Any], path: str) -> bool:
    """
    Download a featured image
    
    Args:
        image_data (dict): Image data dictionary
        path (str): Path to save the image
        
    Returns:
        bool: True if successful, False otherwise
    """
    source = image_data.get('source', '').lower()
    
    if source == 'unsplash':
        image_id = image_data.get('id')
        if image_id:
            return unsplash.download_image(image_id, path)
    
    # For other sources or if no ID is available, download directly from URL
    try:
        import requests
        url = image_data.get('url')
        if not url:
            logger.error("No URL found in image data")
            return False
            
        response = requests.get(url)
        if response.status_code != 200:
            logger.error(f"Error downloading image: {response.status_code}")
            return False
            
        with open(path, 'wb') as f:
            f.write(response.content)
            
        return True
    
    except Exception as e:
        logger.error(f"Error downloading image: {str(e)}")
        return False