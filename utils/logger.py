import logging
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
from logging.handlers import RotatingFileHandler

# Configure logger
logger = logging.getLogger("zyga")
logger.setLevel(logging.DEBUG)

# Create log directory if it doesn't exist
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Configure file handler with rotation
file_handler = RotatingFileHandler(
    os.path.join(log_dir, "zyga.log"),
    maxBytes=10485760,  # 10MB
    backupCount=5
)
file_handler.setLevel(logging.INFO)

# Configure formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(file_handler)

# Configure console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

def log_event(event_type: str, data: Dict[str, Any], level: str = "info") -> None:
    """
    Log an event with structured data
    
    Args:
        event_type: Type of event (e.g., "content_generation", "wordpress_publish")
        data: Event data dictionary
        level: Log level (debug, info, warning, error)
    """
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "data": data
    }
    
    log_json = json.dumps(log_data)
    
    if level == "debug":
        logger.debug(log_json)
    elif level == "info":
        logger.info(log_json)
    elif level == "warning":
        logger.warning(log_json)
    elif level == "error":
        logger.error(log_json)
    else:
        logger.info(log_json)

def log_api_request(api_name: str, request_data: Dict[str, Any], response: Optional[Dict[str, Any]] = None, error: Optional[str] = None) -> None:
    """
    Log an API request
    
    Args:
        api_name: Name of the API
        request_data: Request data
        response: Response data (optional)
        error: Error message (optional)
    """
    log_data = {
        "api": api_name,
        "request": request_data
    }
    
    if response:
        log_data["response"] = response
    
    if error:
        log_data["error"] = error
        log_event("api_request", log_data, "error")
    else:
        log_event("api_request", log_data, "info")

def log_content_generation(blog_id: int, title: str, success: bool, error: Optional[str] = None) -> None:
    """
    Log content generation
    
    Args:
        blog_id: Blog ID
        title: Article title
        success: Whether generation was successful
        error: Error message (optional)
    """
    log_data = {
        "blog_id": blog_id,
        "title": title,
        "success": success
    }
    
    if error:
        log_data["error"] = error
        log_event("content_generation", log_data, "error")
    else:
        log_event("content_generation", log_data, "info")

def log_wordpress_publish(blog_id: int, title: str, post_id: Optional[int], success: bool, error: Optional[str] = None) -> None:
    """
    Log WordPress publishing
    
    Args:
        blog_id: Blog ID
        title: Article title
        post_id: Post ID (optional)
        success: Whether publishing was successful
        error: Error message (optional)
    """
    log_data = {
        "blog_id": blog_id,
        "title": title,
        "success": success
    }
    
    if post_id:
        log_data["post_id"] = post_id
    
    if error:
        log_data["error"] = error
        log_event("wordpress_publish", log_data, "error")
    else:
        log_event("wordpress_publish", log_data, "info")

def log_social_media_post(blog_id: int, platform: str, post_id: Optional[str], success: bool, error: Optional[str] = None) -> None:
    """
    Log social media posting
    
    Args:
        blog_id: Blog ID
        platform: Social media platform
        post_id: Post ID (optional)
        success: Whether posting was successful
        error: Error message (optional)
    """
    log_data = {
        "blog_id": blog_id,
        "platform": platform,
        "success": success
    }
    
    if post_id:
        log_data["post_id"] = post_id
    
    if error:
        log_data["error"] = error
        log_event("social_media_post", log_data, "error")
    else:
        log_event("social_media_post", log_data, "info")
