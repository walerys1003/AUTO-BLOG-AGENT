#!/usr/bin/env python3
"""
Script to fix metadata for existing published article
Adds proper category, tags, and featured image
"""

import sys
import os
import requests
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Blog, ContentLog
from utils.wordpress.client import build_wp_api_url

def fix_article_metadata():
    """Fix metadata for the latest published article"""
    
    with app.app_context():
        print("🔧 Fixing article metadata...")
        
        # Get the latest published article
        article = ContentLog.query.filter_by(
            title="Styl życia przyszłego taty - 5 zaskakujących czynników wpływających na płodność"
        ).first()
        
        if not article or not article.post_id:
            print("❌ Article not found or missing WordPress post ID")
            return
            
        print(f"📝 Found article: {article.title}")
        print(f"📍 WordPress Post ID: {article.post_id}")
        
        # Get blog configuration
        blog = Blog.query.first()
        if not blog:
            print("❌ Blog configuration not found")
            return
            
        # Get category ID for "Planowanie ciąży"
        category_id = get_category_id(blog, "Planowanie ciąży")
        print(f"🏷️ Category ID for 'Planowanie ciąży': {category_id}")
        
        # Create tags
        tag_names = ["planowanie ciąży", "płodność", "zdrowie", "rodzina", "przygotowanie"]
        tag_ids = create_tags(blog, tag_names)
        print(f"🏷️ Created/found tags: {tag_ids}")
        
        # Get featured image
        featured_image_id = upload_featured_image(blog, article)
        print(f"🖼️ Featured image ID: {featured_image_id}")
        
        # Update WordPress post
        success = update_wordpress_post(blog, article.post_id, category_id, tag_ids, featured_image_id)
        
        if success:
            print("✅ Article metadata updated successfully!")
            print(f"🔗 Check: https://mamatestuje.com/?p={article.post_id}")
        else:
            print("❌ Failed to update article metadata")

def get_category_id(blog: Blog, category_name: str) -> int:
    """Get WordPress category ID"""
    try:
        api_url = build_wp_api_url(blog.api_url, "categories")
        auth = (blog.username, blog.api_token)
        
        response = requests.get(f"{api_url}?search={category_name}", auth=auth)
        response.raise_for_status()
        
        categories = response.json()
        for cat in categories:
            if cat['name'].lower() == category_name.lower():
                return cat['id']
        
        # Fallback to default category
        return 3  # "Planowanie ciąży" ID from mamatestuje.com
        
    except Exception as e:
        print(f"⚠️ Error getting category ID: {e}")
        return 3

def create_tags(blog: Blog, tag_names: list) -> list:
    """Create or get WordPress tags"""
    tag_ids = []
    
    try:
        api_url = build_wp_api_url(blog.api_url, "tags")
        auth = (blog.username, blog.api_token)
        
        for tag_name in tag_names:
            # Check if tag exists
            response = requests.get(f"{api_url}?search={tag_name}", auth=auth)
            
            if response.status_code == 200:
                tags = response.json()
                existing_tag = next((tag for tag in tags if tag['name'].lower() == tag_name.lower()), None)
                
                if existing_tag:
                    tag_ids.append(existing_tag['id'])
                else:
                    # Create new tag
                    create_response = requests.post(api_url, auth=auth, json={
                        'name': tag_name,
                        'slug': tag_name.replace(' ', '-').lower()
                    })
                    
                    if create_response.status_code == 201:
                        new_tag = create_response.json()
                        tag_ids.append(new_tag['id'])
                        
    except Exception as e:
        print(f"⚠️ Error creating tags: {e}")
        
    return tag_ids

def upload_featured_image(blog: Blog, article: ContentLog) -> int:
    """Upload featured image to WordPress"""
    try:
        # Use a relevant stock image
        image_url = ("https://images.unsplash.com/photo-1544367567-0f2fcb009e0b"
                    "?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D"
                    "&auto=format&fit=crop&w=1000&q=80")
        
        # Download image
        img_response = requests.get(image_url)
        img_response.raise_for_status()
        
        # Upload to WordPress
        api_url = build_wp_api_url(blog.api_url, "media")
        auth = (blog.username, blog.api_token)
        
        files = {
            'file': ('featured-image.jpg', img_response.content, 'image/jpeg')
        }
        
        data = {
            'title': 'Planowanie ciąży - styl życia taty',
            'alt_text': 'Para planująca ciążę - zdrowy styl życia'
        }
        
        response = requests.post(api_url, auth=auth, files=files, data=data)
        response.raise_for_status()
        
        media = response.json()
        return media.get('id')
        
    except Exception as e:
        print(f"⚠️ Error uploading featured image: {e}")
        return None

def update_wordpress_post(blog: Blog, post_id: int, category_id: int, tag_ids: list, featured_image_id: int) -> bool:
    """Update WordPress post with metadata"""
    try:
        api_url = build_wp_api_url(blog.api_url, f"posts/{post_id}")
        auth = (blog.username, blog.api_token)
        
        update_data = {
            'categories': [category_id] if category_id else [],
            'tags': tag_ids
        }
        
        if featured_image_id:
            update_data['featured_media'] = featured_image_id
            
        response = requests.post(api_url, auth=auth, json=update_data)
        response.raise_for_status()
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating WordPress post: {e}")
        return False

if __name__ == "__main__":
    fix_article_metadata()