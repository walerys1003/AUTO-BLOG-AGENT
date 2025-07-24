"""
Pexels API integration for high-quality stock photos
"""
import os
import requests
import logging
from typing import List, Dict, Any, Optional

# Setup logging
logger = logging.getLogger(__name__)

# Pexels API configuration
PEXELS_API_KEY = os.environ.get('PEXELS_API_KEY')
PEXELS_API_URL = 'https://api.pexels.com/v1'

def search_pexels_images(
    query: str,
    per_page: int = 20,
    page: int = 1,
    orientation: Optional[str] = None,
    size: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Search for images on Pexels
    
    Args:
        query: Search query
        per_page: Number of results per page (1-80)
        page: Page number
        orientation: Optional orientation filter (landscape, portrait, square)
        size: Optional size filter (large, medium, small)
        
    Returns:
        List of image data dictionaries
    """
    if not PEXELS_API_KEY:
        raise ValueError("PEXELS_API_KEY environment variable not set")
    
    # Build URL
    url = f"{PEXELS_API_URL}/search"
    
    # Build headers
    headers = {
        'Authorization': PEXELS_API_KEY
    }
    
    # Build params
    params = {
        'query': query,
        'per_page': min(per_page, 80),  # Pexels limit
        'page': page
    }
    
    # Add optional filters
    if orientation:
        params['orientation'] = orientation
    if size:
        params['size'] = size
    
    try:
        # Make request
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        # Parse response
        data = response.json()
        photos = data.get('photos', [])
        
        # Transform results
        images = []
        for photo in photos:
            photographer = photo.get('photographer', 'Unknown')
            
            image = {
                'id': photo.get('id'),
                'url': photo.get('src', {}).get('original'),
                'large_url': photo.get('src', {}).get('large2x'),
                'medium_url': photo.get('src', {}).get('large'),
                'small_url': photo.get('src', {}).get('medium'),
                'thumb_url': photo.get('src', {}).get('small'),
                'tiny_url': photo.get('src', {}).get('tiny'),
                'width': photo.get('width'),
                'height': photo.get('height'),
                'description': photo.get('alt', f'Photo by {photographer}'),
                'source': 'pexels',
                'photographer': {
                    'name': photographer,
                    'url': photo.get('photographer_url'),
                    'id': photo.get('photographer_id')
                },
                'attribution_text': f"Photo by {photographer} on Pexels",
                'attribution_url': photo.get('url'),
                'pexels_url': photo.get('url')
            }
            
            images.append(image)
            
        return images
    
    except Exception as e:
        logger.error(f"Error searching Pexels: {str(e)}")
        raise

def get_pexels_photo(photo_id: str) -> Dict[str, Any]:
    """
    Get details for a specific Pexels photo
    
    Args:
        photo_id: Pexels photo ID
        
    Returns:
        Photo data dictionary
    """
    if not PEXELS_API_KEY:
        raise ValueError("PEXELS_API_KEY environment variable not set")
    
    # Build URL
    url = f"{PEXELS_API_URL}/photos/{photo_id}"
    
    # Build headers
    headers = {
        'Authorization': PEXELS_API_KEY
    }
    
    try:
        # Make request
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Parse response
        photo = response.json()
        
        photographer = photo.get('photographer', 'Unknown')
        
        # Transform result
        image = {
            'id': photo.get('id'),
            'url': photo.get('src', {}).get('original'),
            'large_url': photo.get('src', {}).get('large2x'),
            'medium_url': photo.get('src', {}).get('large'),
            'small_url': photo.get('src', {}).get('medium'),
            'thumb_url': photo.get('src', {}).get('small'),
            'tiny_url': photo.get('src', {}).get('tiny'),
            'width': photo.get('width'),
            'height': photo.get('height'),
            'description': photo.get('alt', f'Photo by {photographer}'),
            'source': 'pexels',
            'photographer': {
                'name': photographer,
                'url': photo.get('photographer_url'),
                'id': photo.get('photographer_id')
            },
            'attribution_text': f"Photo by {photographer} on Pexels",
            'attribution_url': photo.get('url'),
            'pexels_url': photo.get('url')
        }
        
        return image
        
    except Exception as e:
        logger.error(f"Error getting Pexels photo: {str(e)}")
        raise

def get_curated_pexels_photos(per_page: int = 15, page: int = 1) -> List[Dict[str, Any]]:
    """
    Get curated Pexels photos
    
    Args:
        per_page: Number of results per page (1-80)
        page: Page number
        
    Returns:
        List of curated image data dictionaries
    """
    if not PEXELS_API_KEY:
        raise ValueError("PEXELS_API_KEY environment variable not set")
    
    # Build URL
    url = f"{PEXELS_API_URL}/curated"
    
    # Build headers
    headers = {
        'Authorization': PEXELS_API_KEY
    }
    
    # Build params
    params = {
        'per_page': min(per_page, 80),  # Pexels limit
        'page': page
    }
    
    try:
        # Make request
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        # Parse response
        data = response.json()
        photos = data.get('photos', [])
        
        # Transform results
        images = []
        for photo in photos:
            photographer = photo.get('photographer', 'Unknown')
            
            image = {
                'id': photo.get('id'),
                'url': photo.get('src', {}).get('original'),
                'large_url': photo.get('src', {}).get('large2x'),
                'medium_url': photo.get('src', {}).get('large'),
                'small_url': photo.get('src', {}).get('medium'),
                'thumb_url': photo.get('src', {}).get('small'),
                'tiny_url': photo.get('src', {}).get('tiny'),
                'width': photo.get('width'),
                'height': photo.get('height'),
                'description': photo.get('alt', f'Photo by {photographer}'),
                'source': 'pexels',
                'photographer': {
                    'name': photographer,
                    'url': photo.get('photographer_url'),
                    'id': photo.get('photographer_id')
                },
                'attribution_text': f"Photo by {photographer} on Pexels",
                'attribution_url': photo.get('url'),
                'pexels_url': photo.get('url')
            }
            
            images.append(image)
            
        return images
    
    except Exception as e:
        logger.error(f"Error getting curated Pexels photos: {str(e)}")
        raise

# Test function for API connectivity
def test_pexels_api() -> bool:
    """
    Test if Pexels API is working
    
    Returns:
        True if API is working, False otherwise
    """
    try:
        images = search_pexels_images("nature", per_page=1)
        return len(images) > 0
    except:
        return False