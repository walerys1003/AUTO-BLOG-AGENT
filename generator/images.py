"""
Featured Image Generator Module
"""
import logging
import random
from datetime import datetime

logger = logging.getLogger(__name__)


def get_featured_image_for_article(title, keywords=None):
    """
    Get a featured image for an article
    
    Args:
        title (str): The article title
        keywords (list, optional): List of keywords to help find an image
    
    Returns:
        str: URL to a featured image
    """
    logger.info(f"Getting featured image for: {title}")
    
    # In a real implementation, this would use an image API or library
    # For now, we'll return a placeholder URL for simulation
    
    # Default image dimensions
    width = 1200
    height = 630
    
    # Generate a placeholder with the first few words of the title
    title_words = title.split()[:3]
    title_text = "+".join(title_words)
    
    # Use placeholder.com to create a placeholder image
    image_url = f"https://via.placeholder.com/{width}x{height}/007bff/ffffff?text={title_text}"
    
    logger.info(f"Using featured image URL: {image_url}")
    return image_url