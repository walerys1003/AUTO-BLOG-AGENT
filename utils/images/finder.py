import logging
from typing import List, Dict, Any, Optional, Union
import urllib.parse

from utils.images.unsplash import search_unsplash_images, get_unsplash_photo
from utils.images.pexels import search_pexels_images, get_pexels_photo
from utils.images.google import search_google_images, search_google_images_api, get_google_image_details
from utils.images.serpapi import search_google_images_serpapi
from utils.images.bing import search_bing_images, get_bing_image_details

# Setup logging
logger = logging.getLogger(__name__)

def search_images(
    query: str,
    source: str = 'google',  # Changed default to Google as main source
    per_page: int = 20,
    page: int = 1,
    orientation: Optional[str] = None,
    tags: Optional[List[str]] = None,
    color: Optional[str] = None,
    use_serpapi: bool = False  # Default to Google Custom Search API not SerpAPI
) -> List[Dict[str, Any]]:
    """
    Search for images from various sources
    
    Args:
        query: Search query
        source: Source to search (bing, google, unsplash, pexels, all)
        per_page: Number of results per page
        page: Page number
        orientation: Optional orientation filter (landscape, portrait, squarish)
        tags: Optional list of tags to filter by
        color: Optional color to filter by
        use_serpapi: Whether to use SerpAPI for Google Images (default True)
        
    Returns:
        List of image data dictionaries
    """
    # Default empty results
    results = []
    
    # Log search
    logger.info(f"Searching for images with query '{query}', source: {source}")
    
    # Search based on source, with Bing as first priority
    if source == 'bing' or source == 'all':
        try:
            # Try Bing Image Search API first
            bing_results = search_bing_images(
                query=query,
                per_page=per_page,
                page=page,
                orientation=orientation,
                safe_search="Moderate"
            )
            
            results.extend(bing_results)
            
            # If we got results from Bing, return them immediately
            if results and len(results) > 0:
                logger.info(f"Found {len(results)} images from Bing for '{query}'")
                # Skip other sources if we have results
                if source != 'all':
                    return results
        except Exception as e:
            logger.warning(f"Error searching Bing Images: {str(e)}")
    
    # Search Google if requested or as fallback
    if (source == 'google' or source == 'all') and (len(results) == 0 or source == 'google'):
        try:
            # Use Google Custom Search API by default
            if not use_serpapi:
                google_results = search_google_images_api(
                    query=query,
                    per_page=per_page,
                    page=page,
                    orientation=orientation,
                    safe_search=True
                )
            elif use_serpapi:
                # Use SerpAPI if requested
                google_results = search_google_images_serpapi(
                    query=query,
                    per_page=per_page,
                    page=page,
                    orientation=orientation,
                    safe_search=True
                )
            else:
                # Last fallback to web scraping method (avoid if possible)
                google_results = search_google_images(
                    query=query,
                    per_page=per_page,
                    page=page,
                    orientation=orientation,
                    safe_search=True
                )
            
            results.extend(google_results)
            
            # If we got results from Google, and specifically requested Google only
            if results and len(results) > 0:
                logger.info(f"Found {len(results)} images from Google for '{query}'")
                if source == 'google':
                    return results
        except Exception as e:
            logger.warning(f"Error searching Google Images: {str(e)}")
    
    # Only search Unsplash if specifically requested or as final fallback
    if (source == 'unsplash' or source == 'all') and (len(results) == 0 or source == 'unsplash'):
        try:
            unsplash_results = search_unsplash_images(
                query=query,
                per_page=per_page,
                page=page,
                orientation=orientation
            )
            results.extend(unsplash_results)
            logger.info(f"Found {len(unsplash_results)} images from Unsplash for '{query}'")
        except Exception as e:
            logger.warning(f"Error searching Unsplash: {str(e)}")
    
    # Search Pexels if specifically requested (NEW THIRD SOURCE)
    if (source == 'pexels' or source == 'all') and (len(results) == 0 or source == 'pexels'):
        try:
            pexels_results = search_pexels_images(
                query=query,
                per_page=per_page,
                page=page,
                orientation=orientation
            )
            results.extend(pexels_results)
            logger.info(f"Found {len(pexels_results)} images from Pexels for '{query}'")
        except Exception as e:
            logger.warning(f"Error searching Pexels: {str(e)}")
    
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
        source: Source of the image (bing, unsplash, google, upload)
        
    Returns:
        Image data dictionary
    """
    if source == 'bing':
        try:
            return get_bing_image_details(image_id=image_id)
        except NotImplementedError:
            # Fallback message for Bing Images detail retrieval
            logger.warning("Bing Images detail retrieval not fully implemented. Returning basic info.")
            # Create a minimal stub response with the ID
            return {
                'id': image_id,
                'url': '',
                'thumb_url': '',
                'description': 'Bing image details not available',
                'source': 'bing',
                'attribution_text': 'Bing Image Search',
                'attribution_url': ''
            }
    elif source == 'unsplash':
        return get_unsplash_photo(photo_id=image_id)
    elif source == 'pexels':
        return get_pexels_photo(photo_id=image_id)
    elif source == 'google':
        try:
            return get_google_image_details(image_id=image_id)
        except NotImplementedError:
            # Fallback message for Google Images detail retrieval
            logger.warning("Google Images detail retrieval not fully implemented. Returning basic info.")
            # Create a minimal stub response with the ID
            return {
                'id': image_id,
                'url': '',
                'thumb_url': '',
                'description': 'Google image details not available',
                'source': 'google',
                'attribution_text': 'Unknown source - verify licensing',
                'attribution_url': ''
            }
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