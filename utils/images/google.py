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
from googleapiclient.discovery import build
from config import Config

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

def search_google_images_api(
    query: str,
    per_page: int = 20,
    page: int = 1,
    orientation: Optional[str] = None,
    safe_search: bool = True
) -> List[Dict[str, Any]]:
    """
    Search for images using Google Custom Search API
    
    Args:
        query: Search query
        per_page: Number of results per page (max 10 for free tier, max 100 for paid)
        page: Page number
        orientation: Optional orientation filter (landscape, portrait, square)
        safe_search: Whether to enable safe search
        
    Returns:
        List of image data dictionaries
    """
    # Get API key and CSE ID from config
    api_key = Config.GOOGLE_API_KEY
    cse_id = Config.GOOGLE_CSE_ID
    
    if not api_key or not cse_id:
        logger.error("Google Custom Search API key or CSE ID not found")
        return []
    
    try:
        # Initialize Google Custom Search API
        service = build("customsearch", "v1", developerKey=api_key)
        
        # Set up search parameters
        search_params = {
            'q': query,
            'cx': cse_id,
            'searchType': 'image',
            'num': min(per_page, 10),  # Max 10 per page for free tier
            'start': (page - 1) * 10 + 1,  # Pagination start at 1
            'imgSize': 'LARGE'  # Default to large images
        }
        
        # Add safe search if enabled
        if safe_search:
            search_params['safe'] = 'high'
        
        # Add orientation if provided
        if orientation:
            if orientation == 'landscape':
                search_params['imgType'] = 'photo'
                search_params['imgSize'] = 'XLARGE'
            elif orientation == 'portrait':
                search_params['imgType'] = 'photo'
                search_params['imgSize'] = 'LARGE'
            elif orientation == 'square':
                search_params['imgType'] = 'photo'
                search_params['imgSize'] = 'MEDIUM'
        
        # Execute search
        logger.info(f"Searching Google Images API for: {query}")
        results = service.cse().list(**search_params).execute()
        
        # Process results
        images = []
        if 'items' in results:
            for item in results['items']:
                image = {
                    'id': item.get('link', ''),  # Use link as ID
                    'url': item.get('link', ''),
                    'thumb_url': item.get('image', {}).get('thumbnailLink', item.get('link', '')),
                    'width': item.get('image', {}).get('width'),
                    'height': item.get('image', {}).get('height'),
                    'description': item.get('title', ''),
                    'source': 'google_api',
                    'attribution_text': f"Image from {item.get('displayLink', 'Google Images')}",
                    'attribution_url': item.get('image', {}).get('contextLink', ''),
                    'user': {
                        'name': item.get('displayLink', 'Unknown'),
                        'profile_url': item.get('image', {}).get('contextLink', '')
                    }
                }
                images.append(image)
        
        return images
        
    except Exception as e:
        logger.error(f"Error searching Google Images API: {str(e)}")
        return []

def get_google_image_details(image_id: str) -> Dict[str, Any]:
    """
    Get details for a specific Google image
    
    Args:
        image_id: Google image ID (URL in this case)
        
    Returns:
        Image data dictionary
    """
    # Since Google Custom Search API doesn't provide a direct endpoint for image details
    # We return a simple response with the available information
    return {
        'id': image_id,
        'url': image_id,  # The ID is the URL for Google images
        'thumb_url': image_id,
        'description': 'Google image',
        'source': 'google_api',
        'attribution_text': 'Image from Google Images',
        'attribution_url': '',
        'user': {
            'name': 'Unknown',
            'profile_url': ''
        }
    }