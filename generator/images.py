"""
Featured Image Generator Module
"""
import logging
import random
import json
from datetime import datetime

logger = logging.getLogger(__name__)


def get_featured_image_for_article(title, keywords=None):
    """
    Get a featured image for an article automatically using keywords or title
    
    Args:
        title (str): The article title
        keywords (list, optional): List of keywords to help find an image
    
    Returns:
        dict: Image data dictionary with URL and metadata
    """
    from utils.images.finder import search_images, clean_image_metadata
    
    logger.info(f"Auto-getting featured image for: {title}")
    
    # Use keywords and title to create search query
    if keywords and isinstance(keywords, list) and len(keywords) > 0:
        # Use first 3 keywords as the search term
        search_query = " ".join(keywords[:3])
    else:
        # Use title as search term (cleaning it up a bit)
        search_query = " ".join(title.split()[:3])
    
    # Try Bing Images first (1000 free/month), then Google Images (SerpAPI) and Unsplash as fallbacks
    try:
        # Search Bing Images API
        logger.info(f"Auto-searching for images with query '{search_query}' from Bing Image Search")
        images = search_images(
            query=search_query,
            source='bing',  # Use Bing as primary source
            per_page=5,     # Get a few options to choose from
            orientation='landscape'  # Prefer landscape for featured images
        )
        
        # If we found any images, use the first one
        if images and len(images) > 0:
            # Get the first image
            image = images[0]
            
            # Clean and return the image data
            cleaned_data = clean_image_metadata(image)
            logger.info(f"Found image from Bing for article '{title}'")
            return cleaned_data
            
    except Exception as e:
        logger.warning(f"Error searching for images on Bing: {str(e)}")
    
    # Try Google Images as fallback (100 free queries/month with SerpAPI)
    try:
        # Search Google Images via SerpAPI
        logger.info(f"Auto-searching for images with query '{search_query}' from Google (SerpAPI, fallback 1)")
        images = search_images(
            query=search_query,
            source='google',
            per_page=5,  # Get a few options to choose from
            orientation='landscape',  # Prefer landscape for featured images
            use_serpapi=True  # Use SerpAPI for better results
        )
        
        # If we found any images, use the first one
        if images and len(images) > 0:
            # Get the first image
            image = images[0]
            
            # Clean and return the image data
            cleaned_data = clean_image_metadata(image)
            logger.info(f"Found fallback image from Google for article '{title}'")
            return cleaned_data
            
    except Exception as e:
        logger.warning(f"Error searching for images on Google: {str(e)}")
    
    # Try Unsplash as final fallback
    try:
        # Search for images on Unsplash
        logger.info(f"Auto-searching for images with query '{search_query}' from Unsplash (fallback 2)")
        images = search_images(
            query=search_query,
            source='unsplash',
            per_page=5,  # Get a few options to choose from
            orientation='landscape'  # Prefer landscape for featured images
        )
        
        # If we found any images, use the first one
        if images and len(images) > 0:
            # Get the first image
            image = images[0]
            
            # Clean and return the image data
            cleaned_data = clean_image_metadata(image)
            logger.info(f"Found fallback image from Unsplash for article '{title}'")
            return cleaned_data
            
    except Exception as e:
        logger.warning(f"Error searching for images on Unsplash: {str(e)}")
        # Continue to fallback
    
    # If we didn't find any image, create a fallback
    logger.warning(f"No image found for article '{title}', using fallback")
    
    # Default image dimensions
    width = 1200
    height = 630
    
    # Generate a placeholder with the first few words of the title
    title_words = title.split()[:3]
    title_text = "+".join(title_words)
    
    # Use placeholder.com to create a placeholder image
    image_url = f"https://via.placeholder.com/{width}x{height}/007bff/ffffff?text={title_text}"
    
    # Create fallback image data
    fallback_data = {
        'url': image_url,
        'thumb_url': image_url,
        'width': width,
        'height': height,
        'description': title,
        'source': 'fallback',
        'source_id': 'placeholder',
        'attribution_text': 'Generated placeholder',
        'attribution_url': ''
    }
    
    logger.info(f"Using fallback image for: {title}")
    return fallback_data