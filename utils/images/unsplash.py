import os
import requests
import logging
from typing import List, Dict, Any, Optional

# Setup logging
logger = logging.getLogger(__name__)

# Get Unsplash API key from environment
UNSPLASH_API_KEY = os.environ.get('UNSPLASH_API_KEY')
UNSPLASH_API_URL = 'https://api.unsplash.com'

def search_unsplash_images(
    query: str,
    per_page: int = 20,
    page: int = 1,
    orientation: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Search for images on Unsplash
    
    Args:
        query: Search query
        per_page: Number of results per page
        page: Page number
        orientation: Optional orientation filter (landscape, portrait, squarish)
        
    Returns:
        List of image data dictionaries
    """
    if not UNSPLASH_API_KEY:
        raise ValueError("UNSPLASH_API_KEY environment variable not set")
    
    # Build URL
    url = f"{UNSPLASH_API_URL}/search/photos"
    
    # Build params
    params = {
        'query': query,
        'per_page': per_page,
        'page': page,
        'client_id': UNSPLASH_API_KEY
    }
    
    # Add orientation if provided
    if orientation:
        params['orientation'] = orientation
    
    try:
        # Make request
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        # Parse response
        data = response.json()
        results = data.get('results', [])
        
        # Transform results
        images = []
        for result in results:
            user = result.get('user', {})
            user_portfolio = user.get('portfolio_url') or user.get('links', {}).get('html', '')
            
            image = {
                'id': result.get('id'),
                'url': result.get('urls', {}).get('regular'),
                'thumb_url': result.get('urls', {}).get('thumb'),
                'width': result.get('width'),
                'height': result.get('height'),
                'description': result.get('description') or result.get('alt_description'),
                'source': 'unsplash',
                'user': {
                    'id': user.get('id'),
                    'name': user.get('name'),
                    'username': user.get('username'),
                    'profile_url': user.get('links', {}).get('html')
                },
                'attribution_text': f"Photo by {user.get('name')} on Unsplash",
                'attribution_url': result.get('links', {}).get('html')
            }
            
            images.append(image)
            
        return images
    
    except Exception as e:
        logger.error(f"Error searching Unsplash: {str(e)}")
        raise

def get_unsplash_photo(photo_id: str) -> Dict[str, Any]:
    """
    Get details for a specific Unsplash photo
    
    Args:
        photo_id: Unsplash photo ID
        
    Returns:
        Photo data dictionary
    """
    if not UNSPLASH_API_KEY:
        raise ValueError("UNSPLASH_API_KEY environment variable not set")
    
    # Build URL
    url = f"{UNSPLASH_API_URL}/photos/{photo_id}"
    
    # Build params
    params = {
        'client_id': UNSPLASH_API_KEY
    }
    
    try:
        # Make request
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        # Parse response
        result = response.json()
        
        user = result.get('user', {})
        
        # Transform result
        image = {
            'id': result.get('id'),
            'url': result.get('urls', {}).get('regular'),
            'thumb_url': result.get('urls', {}).get('thumb'),
            'width': result.get('width'),
            'height': result.get('height'),
            'description': result.get('description') or result.get('alt_description'),
            'source': 'unsplash',
            'user': {
                'id': user.get('id'),
                'name': user.get('name'),
                'username': user.get('username'),
                'profile_url': user.get('links', {}).get('html')
            },
            'attribution_text': f"Photo by {user.get('name')} on Unsplash",
            'attribution_url': result.get('links', {}).get('html')
        }
        
        return image
    
    except Exception as e:
        logger.error(f"Error getting Unsplash photo: {str(e)}")
        raise