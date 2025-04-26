"""
WordPress API client for interacting with WordPress sites
"""
import requests
import logging
import json
import os
import re
from datetime import datetime
from typing import Tuple, Dict, Any, List, Optional, Union

# Setup logging
logger = logging.getLogger(__name__)

def normalize_wp_api_url(api_url: str) -> str:
    """
    Normalize a WordPress API URL to ensure consistent formatting
    
    Args:
        api_url: The API URL to normalize
        
    Returns:
        Normalized API URL
    """
    # Remove trailing slashes
    api_url = api_url.rstrip('/')
    
    # Replace multiple consecutive slashes with a single slash
    api_url = re.sub(r'([^:])//+', r'\1/', api_url)
    
    return api_url

def build_wp_api_url(api_url: str, endpoint: str) -> str:
    """
    Build a WordPress API URL for a specific endpoint
    
    Args:
        api_url: The base API URL
        endpoint: The API endpoint (e.g., 'categories', 'posts')
        
    Returns:
        Full WordPress API URL
    """
    # First normalize the base URL
    api_url = normalize_wp_api_url(api_url)
    
    # Determine if the URL already has wp-json/wp/v2
    if '/wp-json/wp/v2' in api_url:
        # URL already has the full path
        base_url = api_url
    elif '/wp-json' in api_url:
        # URL has wp-json but needs wp/v2
        base_url = f"{api_url}/wp/v2"
    else:
        # URL needs the full path
        base_url = f"{api_url}/wp-json/wp/v2"
    
    # Remove any leading slash from the endpoint
    endpoint = endpoint.lstrip('/')
    
    # Construct the final URL
    url = f"{base_url}/{endpoint}"
    
    # Log the URL for debugging
    logger.info(f"WordPress API URL: {url} (from base: {api_url})")
    
    return url

def get_wordpress_client(blog_id: int) -> Tuple[str, str, str, str]:
    """
    Get WordPress API client configuration for a blog
    
    Args:
        blog_id: ID of the blog
        
    Returns:
        Tuple of (api_url, username, api_token, blog name)
    """
    from app import db
    from models import Blog
    
    blog = db.session.get(Blog, blog_id)
    if not blog:
        raise ValueError(f"Blog with ID {blog_id} not found")
    
    return blog.api_url, blog.username, blog.api_token, blog.name

def get_wordpress_categories(blog_id: int) -> List[Dict[str, Any]]:
    """
    Get categories from WordPress
    
    Args:
        blog_id: ID of the blog
        
    Returns:
        List of categories
    """
    api_url, username, token, blog_name = get_wordpress_client(blog_id)
    
    # Use our helper function to build the URL correctly
    url = build_wp_api_url(api_url, "categories")
    
    logger.info(f"Fetching WordPress categories for blog '{blog_name}' (ID: {blog_id})")
    auth = (username, token)
    
    try:
        response = requests.get(url, auth=auth, params={"per_page": 100})
        response.raise_for_status()
        
        categories = response.json()
        
        # Store categories in the database
        from app import db
        from models import Category
        
        for cat in categories:
            existing = Category.query.filter_by(
                blog_id=blog_id, 
                wordpress_id=cat['id']
            ).first()
            
            if not existing:
                new_cat = Category(
                    blog_id=blog_id,
                    name=cat['name'],
                    wordpress_id=cat['id'],
                    parent_id=None if cat['parent'] == 0 else cat['parent'],
                    description=cat.get('description', '')
                )
                db.session.add(new_cat)
        
        db.session.commit()
        
        return categories
    
    except Exception as e:
        logger.error(f"Error getting WordPress categories: {str(e)}")
        return []

def get_wordpress_tags(blog_id: int) -> List[Dict[str, Any]]:
    """
    Get tags from WordPress
    
    Args:
        blog_id: ID of the blog
        
    Returns:
        List of tags
    """
    api_url, username, token, blog_name = get_wordpress_client(blog_id)
    
    # Use our helper function to build the URL correctly
    url = build_wp_api_url(api_url, "tags")
    
    logger.info(f"Fetching WordPress tags for blog '{blog_name}' (ID: {blog_id})")
    auth = (username, token)
    
    try:
        response = requests.get(url, auth=auth, params={"per_page": 100})
        response.raise_for_status()
        
        tags = response.json()
        
        # Store tags in the database
        from app import db
        from models import Tag
        
        for tag in tags:
            existing = Tag.query.filter_by(
                blog_id=blog_id, 
                wordpress_id=tag['id']
            ).first()
            
            if not existing:
                new_tag = Tag(
                    blog_id=blog_id,
                    name=tag['name'],
                    wordpress_id=tag['id']
                )
                db.session.add(new_tag)
        
        db.session.commit()
        
        return tags
    
    except Exception as e:
        logger.error(f"Error getting WordPress tags: {str(e)}")
        return []

def get_wordpress_post(blog_id: int, post_id: int) -> Dict[str, Any]:
    """
    Get a post from WordPress
    
    Args:
        blog_id: ID of the blog
        post_id: ID of the post
        
    Returns:
        Post data
    """
    api_url, username, token, blog_name = get_wordpress_client(blog_id)
    
    # Use our helper function to build the URL correctly with the post ID
    url = build_wp_api_url(api_url, f"posts/{post_id}")
    
    logger.info(f"Fetching WordPress post (ID: {post_id}) from blog '{blog_name}' (ID: {blog_id})")
    auth = (username, token)
    
    try:
        response = requests.get(url, auth=auth)
        response.raise_for_status()
        
        return response.json()
    
    except Exception as e:
        logger.error(f"Error getting WordPress post: {str(e)}")
        return {}

def create_wordpress_post(
    blog_id: int,
    title: str,
    content: str,
    excerpt: str = "",
    status: str = "draft",
    category_id: Optional[int] = None,
    tags: Optional[List[str]] = None,
    featured_media_id: Optional[int] = None,
) -> Tuple[bool, Optional[int], Optional[str]]:
    """
    Create a new post in WordPress
    
    Args:
        blog_id: ID of the blog
        title: Post title
        content: Post content
        excerpt: Post excerpt
        status: Post status (draft, publish, future, etc.)
        category_id: Category ID
        tags: List of tag names
        featured_media_id: Featured media ID
        
    Returns:
        Tuple of (success, post_id, error_message)
    """
    api_url, username, token, blog_name = get_wordpress_client(blog_id)
    
    # Use our helper function to build the URL correctly
    url = build_wp_api_url(api_url, "posts")
    
    logger.info(f"Creating WordPress post titled '{title}' on blog '{blog_name}' (ID: {blog_id})")
    auth = (username, token)
    
    # Prepare post data
    post_data = {
        "title": title,
        "content": content,
        "status": status
    }
    
    if excerpt:
        post_data["excerpt"] = excerpt
    
    if category_id:
        post_data["categories"] = [category_id]
    
    if tags:
        post_data["tags"] = tags
    
    if featured_media_id:
        post_data["featured_media"] = featured_media_id
    
    try:
        response = requests.post(url, auth=auth, json=post_data)
        response.raise_for_status()
        
        post = response.json()
        
        return True, post["id"], None
    
    except Exception as e:
        logger.error(f"Error creating WordPress post: {str(e)}")
        return False, None, str(e)

def update_wordpress_post(
    blog_id: int,
    post_id: int,
    title: Optional[str] = None,
    content: Optional[str] = None,
    excerpt: Optional[str] = None,
    status: Optional[str] = None,
    category_id: Optional[int] = None,
    tags: Optional[List[str]] = None,
    featured_media_id: Optional[int] = None,
) -> Tuple[bool, Optional[int], Optional[str]]:
    """
    Update an existing post in WordPress
    
    Args:
        blog_id: ID of the blog
        post_id: ID of the post to update
        title: Post title
        content: Post content
        excerpt: Post excerpt
        status: Post status (draft, publish, future, etc.)
        category_id: Category ID
        tags: List of tag names
        featured_media_id: Featured media ID
        
    Returns:
        Tuple of (success, post_id, error_message)
    """
    api_url, username, token, blog_name = get_wordpress_client(blog_id)
    
    # Use our helper function to build the URL correctly with the post ID
    url = build_wp_api_url(api_url, f"posts/{post_id}")
    
    logger.info(f"Updating WordPress post (ID: {post_id}) on blog '{blog_name}' (ID: {blog_id})")
    auth = (username, token)
    
    # Prepare post data
    post_data = {}
    
    if title is not None:
        post_data["title"] = title
    
    if content is not None:
        post_data["content"] = content
    
    if excerpt is not None:
        post_data["excerpt"] = excerpt
    
    if status is not None:
        post_data["status"] = status
    
    if category_id is not None:
        post_data["categories"] = [category_id]
    
    if tags is not None:
        post_data["tags"] = tags
    
    if featured_media_id is not None:
        post_data["featured_media"] = featured_media_id
    
    try:
        response = requests.post(url, auth=auth, json=post_data)
        response.raise_for_status()
        
        post = response.json()
        
        return True, post["id"], None
    
    except Exception as e:
        logger.error(f"Error updating WordPress post: {str(e)}")
        return False, None, str(e)

def publish_wordpress_post(
    blog_id: int,
    title: str,
    content: str,
    excerpt: str = "",
    post_id: Optional[int] = None,
    category_id: Optional[int] = None,
    tags: Optional[List[str]] = None,
    featured_image: Optional[Dict[str, Any]] = None,
    scheduled_date: Optional[datetime] = None,
) -> Tuple[bool, Optional[int], Optional[str]]:
    """
    Publish a post to WordPress
    If post_id is provided, updates an existing post
    Otherwise creates a new post
    
    Args:
        blog_id: ID of the blog
        title: Post title
        content: Post content
        excerpt: Post excerpt
        post_id: Optional ID of existing post to update
        category_id: Category ID
        tags: List of tag names
        featured_image: Featured image data
        scheduled_date: Date to schedule the post for
        
    Returns:
        Tuple of (success, post_id, error_message)
    """
    # First upload the featured image if provided
    featured_media_id = None
    if featured_image:
        success, media_id, error = upload_media_to_wordpress(
            blog_id=blog_id,
            image_url=featured_image.get('url'),
            image_name=featured_image.get('name', 'featured-image.jpg'),
            alt_text=featured_image.get('alt_text', title)
        )
        
        if success:
            featured_media_id = media_id
        else:
            logger.warning(f"Failed to upload featured image: {error}")
    
    # Determine status and date
    status = "publish"
    if scheduled_date:
        if scheduled_date > datetime.now():
            status = "future"
    
    # Create or update the post
    if post_id:
        return update_wordpress_post(
            blog_id=blog_id,
            post_id=post_id,
            title=title,
            content=content,
            excerpt=excerpt,
            status=status,
            category_id=category_id,
            tags=tags,
            featured_media_id=featured_media_id
        )
    else:
        return create_wordpress_post(
            blog_id=blog_id,
            title=title,
            content=content,
            excerpt=excerpt,
            status=status,
            category_id=category_id,
            tags=tags,
            featured_media_id=featured_media_id
        )

def upload_media_to_wordpress(
    blog_id: int,
    image_url: str,
    image_name: str,
    alt_text: str = "",
) -> Tuple[bool, Optional[int], Optional[str]]:
    """
    Upload media to WordPress
    
    Args:
        blog_id: ID of the blog
        image_url: URL of the image
        image_name: Name of the image
        alt_text: Alt text for the image
        
    Returns:
        Tuple of (success, media_id, error_message)
    """
    api_url, username, token, blog_name = get_wordpress_client(blog_id)
    
    # Use our helper function to build the URL correctly
    url = build_wp_api_url(api_url, "media")
    
    logger.info(f"Uploading media '{image_name}' to blog '{blog_name}' (ID: {blog_id})")
    auth = (username, token)
    
    try:
        # Download the image
        image_response = requests.get(image_url)
        image_response.raise_for_status()
        
        # Upload to WordPress
        headers = {
            "Content-Disposition": f'attachment; filename="{image_name}"',
        }
        
        response = requests.post(
            url, 
            auth=auth, 
            headers=headers,
            data=image_response.content
        )
        response.raise_for_status()
        
        media = response.json()
        
        # Set alt text if provided
        if alt_text:
            # Use our helper function to build the URL correctly for the media update
            update_url = build_wp_api_url(api_url, f"media/{media['id']}")
            update_data = {
                "alt_text": alt_text
            }
            
            logger.info(f"Setting alt text for media ID {media['id']}")
            update_response = requests.post(update_url, auth=auth, json=update_data)
            update_response.raise_for_status()
        
        return True, media["id"], None
    
    except Exception as e:
        logger.error(f"Error uploading media to WordPress: {str(e)}")
        return False, None, str(e)

def delete_wordpress_post(blog_id: int, post_id: int) -> bool:
    """
    Delete a post from WordPress
    
    Args:
        blog_id: ID of the blog
        post_id: ID of the post
        
    Returns:
        Success status
    """
    api_url, username, token, blog_name = get_wordpress_client(blog_id)
    
    # Use our helper function to build the URL correctly with the post ID
    url = build_wp_api_url(api_url, f"posts/{post_id}")
    
    logger.info(f"Deleting WordPress post (ID: {post_id}) from blog '{blog_name}' (ID: {blog_id})")
    auth = (username, token)
    
    try:
        response = requests.delete(url, auth=auth, params={"force": True})
        response.raise_for_status()
        
        return True
    
    except Exception as e:
        logger.error(f"Error deleting WordPress post: {str(e)}")
        return False