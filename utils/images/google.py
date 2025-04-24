import os
import requests
import logging
from typing import List, Dict, Any, Optional
import re
from bs4 import BeautifulSoup
import urllib.parse
import json
import random
import time

# Setup logging
logger = logging.getLogger(__name__)

# User agent list to rotate
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 11.5; rv:90.0) Gecko/20100101 Firefox/90.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_5_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
]

def get_random_user_agent():
    """Get a random user agent from the list"""
    return random.choice(USER_AGENTS)

def search_google_images(
    query: str,
    per_page: int = 20,
    page: int = 1,
    orientation: Optional[str] = None,
    safe_search: bool = True
) -> List[Dict[str, Any]]:
    """
    Search for images on Google Images using web scraping
    
    IMPORTANT: This function uses web scraping which might violate Google's terms of service.
    Users should verify they have the right to use any images before using them.
    
    Args:
        query: Search query
        per_page: Number of results per page (max 100)
        page: Page number
        orientation: Optional orientation filter (landscape, portrait, square)
        safe_search: Whether to enable safe search
        
    Returns:
        List of image data dictionaries
    """
    # Constrain per_page
    per_page = min(per_page, 100)
    
    # Build search URL
    search_url = "https://www.google.com/search"
    
    # Build parameters
    params = {
        'q': query,
        'tbm': 'isch',  # Image search
        'start': (page - 1) * per_page,  # Pagination
        'ijn': page - 1,  # Page number
        'safe': 'active' if safe_search else 'off'
    }
    
    # Add orientation if provided
    if orientation:
        if orientation == 'landscape':
            params['iar'] = 'w'  # Wide aspect ratio
        elif orientation == 'portrait':
            params['iar'] = 't'  # Tall aspect ratio
        elif orientation == 'square':
            params['iar'] = 's'  # Square aspect ratio
    
    # Headers with random User-Agent
    headers = {
        'User-Agent': get_random_user_agent(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0'
    }
    
    try:
        # Make request
        logger.info(f"Searching Google Images for: {query}")
        response = requests.get(search_url, params=params, headers=headers)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find image data in the page
        # Google stores image data in a JavaScript variable, we need to extract it
        script_tags = soup.find_all('script')
        image_data = []
        
        for script in script_tags:
            script_text = script.string
            if script_text and 'AF_initDataCallback' in script_text:
                # Google Images data is in JSON format inside script tags
                data_matches = re.findall(r'AF_initDataCallback\((.+?)\);', script_text, re.DOTALL)
                
                for data_match in data_matches:
                    try:
                        data = json.loads(data_match)
                        # Check if this is the image data we're looking for
                        if data and 'data' in data and isinstance(data['data'], list) and len(data['data']) > 1:
                            # Usually the image data is nested deeply
                            for item in data['data']:
                                if isinstance(item, list) and len(item) > 1:
                                    # This is likely the image grid
                                    for grid_item in item:
                                        if isinstance(grid_item, list) and len(grid_item) > 1:
                                            # Process each image in the grid
                                            image_data.extend(extract_image_data(grid_item))
                    except (json.JSONDecodeError, KeyError, IndexError) as e:
                        logger.debug(f"Error parsing script data: {str(e)}")
                        continue
        
        # Deduplicate and trim to per_page
        seen_urls = set()
        unique_images = []
        
        for image in image_data:
            if image['url'] not in seen_urls:
                seen_urls.add(image['url'])
                unique_images.append(image)
                
                if len(unique_images) >= per_page:
                    break
        
        return unique_images[:per_page]
    
    except Exception as e:
        logger.error(f"Error searching Google Images: {str(e)}")
        raise

def extract_image_data(grid_item):
    """Extract image data from Google's grid item data structure"""
    images = []
    
    try:
        # Google's structure is complex and may change, this is a best effort extraction
        if isinstance(grid_item, list) and len(grid_item) > 1:
            for item in grid_item:
                if isinstance(item, dict) and 'metadata' in item:
                    metadata = item['metadata']
                    if isinstance(metadata, list) and len(metadata) > 1:
                        img_data = metadata[1]
                        if isinstance(img_data, dict):
                            # Basic image data
                            image = {
                                'id': img_data.get('id', ''),
                                'url': img_data.get('url', ''),
                                'thumb_url': img_data.get('thumbnailUrl', img_data.get('url', '')),
                                'width': img_data.get('width'),
                                'height': img_data.get('height'),
                                'description': img_data.get('title', ''),
                                'source': 'google',
                                'attribution_text': f"Image from {img_data.get('sourceUrl', 'Google Images')}",
                                'attribution_url': img_data.get('sourceUrl', ''),
                                'user': {
                                    'name': img_data.get('sourceName', 'Unknown'),
                                    'profile_url': img_data.get('sourceUrl', '')
                                }
                            }
                            images.append(image)
                elif isinstance(item, list) and len(item) > 1:
                    # Recursive extraction for nested structures
                    images.extend(extract_image_data(item))
    except Exception as e:
        logger.debug(f"Error extracting image data: {str(e)}")
    
    return images

def get_google_image_details(image_id: str) -> Dict[str, Any]:
    """
    Get details for a specific Google image (placeholder)
    
    Args:
        image_id: Google image ID
        
    Returns:
        Image data dictionary
    """
    # This is a placeholder since Google doesn't provide a direct API for image details
    # In a real implementation, you might store the full details when performing the search
    # and retrieve them here
    raise NotImplementedError("Google Images detail retrieval not supported")