import logging
from typing import List, Dict, Any, Optional, Union
import urllib.parse

from utils.images.unsplash import search_unsplash_images, get_unsplash_photo

# Setup logging
logger = logging.getLogger(__name__)

def search_images(
    query: str,
    source: str = 'unsplash',
    per_page: int = 20,
    page: int = 1,
    orientation: Optional[str] = None,
    tags: Optional[List[str]] = None,
    color: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Search for images from various sources
    
    Args:
        query: Search query
        source: Source to search (unsplash, google, all)
        per_page: Number of results per page
        page: Page number
        orientation: Optional orientation filter (landscape, portrait, squarish)
        tags: Optional list of tags to filter by
        color: Optional color to filter by
        
    Returns:
        List of image data dictionaries
    """
    # Default empty results
    results = []
    
    # Log search
    logger.info(f"Searching for images with query '{query}', source: {source}")
    
    # Search based on source
    if source == 'unsplash' or source == 'all':
        try:
            unsplash_results = search_unsplash_images(
                query=query,
                per_page=per_page,
                page=page,
                orientation=orientation
            )
            results.extend(unsplash_results)
        except Exception as e:
            logger.warning(f"Error searching Unsplash: {str(e)}")
    
    if source == 'google' or source == 'all':
        # TODO: Implement Google Images search
        # Since there's no official API for Google Images, a custom solution would be needed
        # Potentially using a library like serpapi or a custom scraper
        # For now, only show a placeholder message
        logger.warning("Google Images search not implemented yet")
    
    # Filter results by tags if provided
    if tags and len(tags) > 0:
        filtered_results = []
        for image in results:
            # For now, just do simple keyword matching in the description
            description = image.get('description', '').lower()
            if any(tag.lower() in description for tag in tags):
                filtered_results.append(image)
        
        results = filtered_results
    
    return results

def get_image_details(image_id: str, source: str) -> Dict[str, Any]:
    """
    Get details for a specific image
    
    Args:
        image_id: Image ID
        source: Source of the image (unsplash, google, upload)
        
    Returns:
        Image data dictionary
    """
    if source == 'unsplash':
        return get_unsplash_photo(photo_id=image_id)
    elif source == 'google':
        # TODO: Implement Google Images detail retrieval
        logger.warning("Google Images detail retrieval not implemented yet")
        raise NotImplementedError("Google Images detail retrieval not implemented yet")
    else:
        raise ValueError(f"Unknown image source: {source}")

def clean_image_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean and sanitize image metadata for storage
    
    Args:
        metadata: Raw image metadata
        
    Returns:
        Cleaned metadata dictionary
    """
    # Basic fields to keep
    cleaned = {
        'url': metadata.get('url', ''),
        'thumb_url': metadata.get('thumb_url', ''),
        'width': metadata.get('width'),
        'height': metadata.get('height'),
        'description': metadata.get('description', ''),
        'source': metadata.get('source', 'unknown'),
        'source_id': metadata.get('id'),
        'attribution_text': metadata.get('attribution_text', ''),
        'attribution_url': metadata.get('attribution_url', '')
    }
    
    # Add user data if available
    user = metadata.get('user')
    if user and isinstance(user, dict):
        cleaned['user'] = {
            'name': user.get('name', ''),
            'username': user.get('username', ''),
            'profile_url': user.get('profile_url', '')
        }
    
    return cleaned