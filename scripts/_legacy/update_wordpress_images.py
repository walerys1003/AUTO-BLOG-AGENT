#!/usr/bin/env python3
"""
Zaktualizuj featured images na WordPress dla artykułów 238-243
"""
import sys
sys.path.insert(0, '.')

import json
import base64
import requests
from app import app, db
from models import ContentLog, Blog

def update_wp_images():
    with app.app_context():
        # Artykuły które były już published ale bez zdjęć
        articles_to_update = ContentLog.query.filter(
            ContentLog.id.in_([238, 239, 240, 241, 242, 243]),
            ContentLog.featured_image_data != None
        ).all()
        
        print(f"Found {len(articles_to_update)} articles to update on WordPress")
        
        for article in articles_to_update:
            print(f"\n📸 Updating WP image for: {article.title[:60]}")
            print(f"   Article ID: {article.id}, Blog: {article.blog_id}, WP Post ID: {article.post_id}")
            
            if not article.post_id:
                print(f"   ⚠️  No WordPress ID - skipping")
                continue
                
            # Parsuj featured image data
            try:
                image_data = json.loads(article.featured_image_data)
                image_url = image_data.get('url')
                if not image_url:
                    print(f"   ⚠️  No image URL found")
                    continue
                    
                print(f"   Image URL: {image_url[:80]}")
                
                # Pobierz blog
                blog = db.session.get(Blog, article.blog_id)
                if not blog:
                    print(f"   ❌ Blog not found")
                    continue
                
                # Przygotuj credentials
                credentials = f"{blog.username}:{blog.api_token}"
                auth_token = base64.b64encode(credentials.encode()).decode('utf-8')
                
                # Upload image to WordPress
                print(f"   Uploading to WordPress...")
                img_response = requests.get(image_url, timeout=30)
                if img_response.status_code != 200:
                    print(f"   ❌ Failed to download image: {img_response.status_code}")
                    continue
                
                # Upload do WP
                upload_url = f"{blog.url}/wp-json/wp/v2/media"
                headers = {
                    'Authorization': f'Basic {auth_token}',
                    'Content-Disposition': f'attachment; filename=featured-{article.id}.jpg',
                    'Content-Type': img_response.headers.get('Content-Type', 'image/jpeg')
                }
                
                upload_response = requests.post(
                    upload_url,
                    headers=headers,
                    data=img_response.content,
                    timeout=60
                )
                
                if upload_response.status_code in [200, 201]:
                    media_id = upload_response.json().get('id')
                    print(f"   ✅ Image uploaded, media ID: {media_id}")
                    
                    # Ustaw jako featured image
                    update_url = f"{blog.url}/wp-json/wp/v2/posts/{article.post_id}"
                    update_response = requests.post(
                        update_url,
                        headers={'Authorization': f'Basic {auth_token}'},
                        json={'featured_media': media_id},
                        timeout=30
                    )
                    
                    if update_response.status_code == 200:
                        print(f"   ✅ Featured image updated on WordPress!")
                    else:
                        print(f"   ⚠️  Failed to set featured image: {update_response.status_code}")
                        print(f"   Response: {update_response.text[:200]}")
                else:
                    print(f"   ❌ Failed to upload: {upload_response.status_code}")
                    print(f"   Response: {upload_response.text[:200]}")
                    
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
                import traceback
                print(f"   Traceback: {traceback.format_exc()[:300]}")
        
        print("\n✅ Done updating WordPress images")

if __name__ == "__main__":
    update_wp_images()
