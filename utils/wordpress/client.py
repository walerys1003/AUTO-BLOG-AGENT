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
        
        # First pass - create categories without parent relationships
        # to avoid foreign key violations
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
                    parent_id=None,  # Initially set to None to avoid FK constraint issues
                    description=cat.get('description', '')
                )
                db.session.add(new_cat)
        
        # First commit to ensure all categories exist
        db.session.commit()
        
        # Second pass - update parent relationships now that all categories exist
        for cat in categories:
            if cat['parent'] != 0:  # If this category has a parent
                child_cat = Category.query.filter_by(
                    blog_id=blog_id, 
                    wordpress_id=cat['id']
                ).first()
                
                if child_cat:
                    # Find the parent category by WordPress ID
                    parent_cat = Category.query.filter_by(
                        blog_id=blog_id, 
                        wordpress_id=cat['parent']
                    ).first()
                    
                    if parent_cat:
                        # Update the parent_id with the actual database ID (not WordPress ID)
                        child_cat.parent_id = parent_cat.id
                    else:
                        logger.warning(f"Parent category with WordPress ID {cat['parent']} not found for category {cat['name']}")
        
        # Second commit to update parent relationships
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

def get_or_create_tag_ids(blog_id: int, tag_names: List[str]) -> List[int]:
    """
    Convert tag names to WordPress tag IDs, creating tags if they don't exist
    
    Args:
        blog_id: ID of the blog
        tag_names: List of tag names
        
    Returns:
        List of WordPress tag IDs
    """
    api_url, username, token, blog_name = get_wordpress_client(blog_id)
    auth = (username, token)
    tag_ids = []
    
    for tag_name in tag_names:
        # Try to find existing tag
        url = build_wp_api_url(api_url, "tags")
        try:
            response = requests.get(url, auth=auth, params={"search": tag_name})
            response.raise_for_status()
            existing_tags = response.json()
            
            # Check for exact match
            exact_match = None
            for tag in existing_tags:
                if tag['name'].lower() == tag_name.lower():
                    exact_match = tag
                    break
            
            if exact_match:
                tag_ids.append(exact_match['id'])
                logger.info(f"Found existing tag '{tag_name}' with ID {exact_match['id']}")
            else:
                # Create new tag
                create_url = build_wp_api_url(api_url, "tags")
                create_response = requests.post(
                    create_url, 
                    auth=auth, 
                    json={"name": tag_name}
                )
                create_response.raise_for_status()
                new_tag = create_response.json()
                tag_ids.append(new_tag['id'])
                logger.info(f"Created new tag '{tag_name}' with ID {new_tag['id']}")
                
        except Exception as e:
            logger.error(f"Error processing tag '{tag_name}': {str(e)}")
            continue
    
    return tag_ids

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
        # Convert tag names to IDs
        tag_ids = get_or_create_tag_ids(blog_id, tags)
        if tag_ids:
            post_data["tags"] = tag_ids
    
    if featured_media_id:
        post_data["featured_media"] = featured_media_id
    
    try:
        response = requests.post(url, auth=auth, json=post_data)
        response.raise_for_status()
        
        post = response.json()
        
        return True, post["id"], None
    
    except requests.exceptions.HTTPError as e:
        # WordPress API zwraca szczegóły błędu w JSON
        error_details = "Unknown error"
        try:
            error_json = e.response.json()
            error_details = f"{error_json.get('code', 'unknown')}: {error_json.get('message', str(e))}"
            logger.error(f"WordPress API error: {error_details}")
            logger.error(f"Full error response: {error_json}")
        except:
            error_details = str(e)
            logger.error(f"Error creating WordPress post: {error_details}")
        
        return False, None, error_details
    
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
        # Convert tag names to IDs
        tag_ids = get_or_create_tag_ids(blog_id, tags)
        if tag_ids:
            post_data["tags"] = tag_ids
    
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

def download_image_from_url(image_url: str) -> bytes:
    """
    Download image binary data from URL (zgodnie z instrukcjami użytkownika)
    
    Args:
        image_url: URL of the image to download
        
    Returns:
        Binary image data
    """
    try:
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        return response.content
    except Exception as e:
        logger.error(f"Error downloading image from {image_url}: {str(e)}")
        raise

def upload_image_to_wordpress_media(
    blog_id: int, 
    image_data: bytes, 
    filename: str, 
    alt_text: str = ""
) -> Tuple[bool, Optional[int], Optional[str]]:
    """
    Upload image binary data to WordPress media library (zgodnie z instrukcjami)
    
    Args:
        blog_id: ID of the blog
        image_data: Binary image data
        filename: Name for the file
        alt_text: Alt text for the image
        
    Returns:
        Tuple of (success, media_id, error_message)
    """
    api_url, username, token, blog_name = get_wordpress_client(blog_id)
    
    # Build media upload URL
    url = build_wp_api_url(api_url, "media")
    
    logger.info(f"Uploading media '{filename}' to blog '{blog_name}' (ID: {blog_id})")
    
    # Prepare headers for media upload (zgodnie z instrukcjami)
    headers = {
        'Content-Disposition': f'attachment; filename="{filename}"',
        'Content-Type': 'image/jpeg'
    }
    
    # Basic auth
    auth = (username, token)
    
    try:
        # Upload image to WordPress media library
        response = requests.post(url, auth=auth, headers=headers, data=image_data)
        response.raise_for_status()
        
        media = response.json()
        media_id = media.get('id')
        
        # Update alt text if provided
        if alt_text and media_id:
            try:
                alt_text_data = {'alt_text': alt_text}
                alt_url = build_wp_api_url(api_url, f"media/{media_id}")
                requests.post(alt_url, auth=auth, json=alt_text_data)
            except:
                pass  # Alt text update failure shouldn't break the upload
        
        logger.info(f"Successfully uploaded image to WordPress media library: ID {media_id}")
        return True, media_id, None
        
    except Exception as e:
        logger.error(f"Error uploading media to WordPress: {str(e)}")
        return False, None, str(e)

def upload_media_to_wordpress(
    blog_id: int,
    image_url: str,
    image_name: str,
    alt_text: str = "",
) -> Tuple[bool, Optional[int], Optional[str]]:
    """
    Download and upload media to WordPress (implementacja zgodnie z instrukcjami)
    
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