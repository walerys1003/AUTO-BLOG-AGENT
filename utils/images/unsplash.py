"""
Unsplash Image API Module

This module handles fetching images from Unsplash using their API.
"""
import logging
import os
import requests
import json
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# Get API credentials from environment
UNSPLASH_API_KEY = os.environ.get('UNSPLASH_API_KEY')
UNSPLASH_SECRET_KEY = os.environ.get('UNSPLASH_SECRET_KEY')

def fetch_images(query: str, count: int = 5, orientation: str = None) -> List[Dict[str, Any]]:
    """
    Fetch images from Unsplash API based on search query
    
    Args:
        query (str): Search query (keywords)
        count (int): Number of images to fetch (max 30)
        orientation (str, optional): Filter by orientation (landscape, portrait, squarish)
        
    Returns:
        list: List of image data dictionaries with URLs, attribution, etc.
    """
    if not UNSPLASH_API_KEY:
        logger.error("Unsplash API key not set")
        return []
    
    try:
        # Build the API request URL with parameters
        url = "https://api.unsplash.com/search/photos"
        params = {
            "query": query,
            "per_page": min(count, 30),  # API limit is 30 per request
        }
        
        if orientation and orientation in ['landscape', 'portrait', 'squarish']:
            params["orientation"] = orientation
            
        headers = {
            "Authorization": f"Client-ID {UNSPLASH_API_KEY}"
        }
        
        # Make the API request
        response = requests.get(url, params=params, headers=headers)
        
        # Check if the request was successful
        if response.status_code != 200:
            logger.error(f"Unsplash API error: {response.status_code} - {response.text}")
            return []
        
        # Parse the response JSON
        data = response.json()
        
        # Extract the relevant image data
        images = []
        for image in data.get("results", []):
            images.append({
                "id": image.get("id"),
                "url": image.get("urls", {}).get("regular"),
                "small_url": image.get("urls", {}).get("small"),
                "thumb_url": image.get("urls", {}).get("thumb"),
                "download_url": image.get("links", {}).get("download"),
                "width": image.get("width"),
                "height": image.get("height"),
                "color": image.get("color"),
                "description": image.get("description") or image.get("alt_description"),
                "user": {
                    "name": image.get("user", {}).get("name"),
                    "username": image.get("user", {}).get("username"),
                    "profile_url": image.get("user", {}).get("links", {}).get("html")
                },
                "attribution_text": f"Photo by {image.get('user', {}).get('name')} on Unsplash",
                "attribution_url": image.get("links", {}).get("html")
            })
        
        return images
        
    except Exception as e:
        logger.error(f"Error fetching images from Unsplash: {str(e)}")
        return []


def get_random_image(query: str = None, orientation: str = None) -> Optional[Dict[str, Any]]:
    """
    Get a random image from Unsplash
    
    Args:
        query (str, optional): Topic for the image
        orientation (str, optional): Preferred orientation
        
    Returns:
        dict: Image data or None if error occurs
    """
    try:
        # Build the API request URL
        url = "https://api.unsplash.com/photos/random"
        params = {}
        
        if query:
            params["query"] = query
            
        if orientation and orientation in ['landscape', 'portrait', 'squarish']:
            params["orientation"] = orientation
            
        headers = {
            "Authorization": f"Client-ID {UNSPLASH_API_KEY}"
        }
        
        # Make the API request
        response = requests.get(url, params=params, headers=headers)
        
        # Check if the request was successful
        if response.status_code != 200:
            logger.error(f"Unsplash random image API error: {response.status_code} - {response.text}")
            return None
        
        # Parse the response JSON
        image = response.json()
        
        # Extract the relevant image data
        return {
            "id": image.get("id"),
            "url": image.get("urls", {}).get("regular"),
            "small_url": image.get("urls", {}).get("small"),
            "thumb_url": image.get("urls", {}).get("thumb"),
            "download_url": image.get("links", {}).get("download"),
            "width": image.get("width"),
            "height": image.get("height"),
            "color": image.get("color"),
            "description": image.get("description") or image.get("alt_description"),
            "user": {
                "name": image.get("user", {}).get("name"),
                "username": image.get("user", {}).get("username"),
                "profile_url": image.get("user", {}).get("links", {}).get("html")
            },
            "attribution_text": f"Photo by {image.get('user', {}).get('name')} on Unsplash",
            "attribution_url": image.get("links", {}).get("html")
        }
        
    except Exception as e:
        logger.error(f"Error fetching random image from Unsplash: {str(e)}")
        return None


def download_image(image_id: str, path: str) -> bool:
    """
    Download an image from Unsplash by ID
    
    Args:
        image_id (str): The Unsplash image ID
        path (str): The path to save the image
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not UNSPLASH_API_KEY:
        logger.error("Unsplash API key not set")
        return False
    
    try:
        # Build the API request URL
        url = f"https://api.unsplash.com/photos/{image_id}/download"
        headers = {
            "Authorization": f"Client-ID {UNSPLASH_API_KEY}"
        }
        
        # Get the download URL
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            logger.error(f"Unsplash download API error: {response.status_code} - {response.text}")
            return False
        
        # Get the actual download URL from the response
        download_url = response.json().get("url")
        
        if not download_url:
            logger.error("No download URL found in Unsplash response")
            return False
        
        # Download the image
        img_response = requests.get(download_url)
        
        if img_response.status_code != 200:
            logger.error(f"Error downloading image: {img_response.status_code}")
            return False
        
        # Save the image to the specified path
        with open(path, 'wb') as f:
            f.write(img_response.content)
            
        return True
        
    except Exception as e:
        logger.error(f"Error downloading image from Unsplash: {str(e)}")
        return False