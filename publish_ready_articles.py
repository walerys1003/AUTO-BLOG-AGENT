#!/usr/bin/env python3
"""
Opublikuj artykuły w statusie "ready"
"""
import sys
sys.path.insert(0, '.')

from app import app, db
from models import ContentLog, Blog, AutomationRule
from utils.automation.workflow_engine import WorkflowEngine

def publish_ready_articles():
    with app.app_context():
        # Pobierz artykuły w statusie ready z dzisiaj
        ready_articles = ContentLog.query.filter_by(status='ready').filter(
            db.func.date(ContentLog.created_at) == '2025-11-19'
        ).all()
        
        print(f"Found {len(ready_articles)} ready articles to publish")
        
        for article in ready_articles:
            print(f"\n📤 Publishing: {article.title[:60]}")
            print(f"   Article ID: {article.id}, Blog ID: {article.blog_id}")
            
            # Pobierz blog i automation rule
            blog = db.session.get(Blog, article.blog_id)
            if not blog:
                print(f"   ❌ Blog not found")
                continue
                
            automation_rule = AutomationRule.query.filter_by(blog_id=blog.id, is_active=True).first()
            if not automation_rule:
                print(f"   ❌ Automation rule not found")
                continue
            
            # Użyj workflow engine do publikacji
            engine = WorkflowEngine()
            
            # UWAGA: Musimy przekonwertować ContentLog -> Article
            # Ale workflow engine używa modelu Article, nie ContentLog
            # Więc zrobimy to ręcznie używając WordPress client
            
            from utils.wordpress.client import build_wp_api_url
            import requests
            import base64
            import json
            
            try:
                # Przygotuj dane do publikacji
                wp_url = build_wp_api_url(blog.url)
                credentials = f"{blog.username}:{blog.api_token}"
                auth_token = base64.b64encode(credentials.encode()).decode('utf-8')
                
                # Pobierz category_id
                category_id = article.category_id
                if not category_id:
                    print(f"   ⚠️  No category_id, using default")
                    category_id = 1
                
                # Parsuj tags
                tags = []
                if article.tags:
                    try:
                        tags = json.loads(article.tags)
                    except:
                        tags = article.tags.split(',') if article.tags else []
                
                # Upload featured image if available
                featured_media_id = None
                if article.featured_image_data:
                    image_data = json.loads(article.featured_image_data)
                    image_url = image_data.get('url')
                    
                    if image_url:
                        print(f"   Uploading featured image...")
                        img_response = requests.get(image_url, timeout=30)
                        if img_response.status_code == 200:
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
                                featured_media_id = upload_response.json().get('id')
                                print(f"   ✅ Image uploaded, media ID: {featured_media_id}")
                
                # Przygotuj dane postu
                post_data = {
                    'title': article.title,
                    'content': article.content,
                    'excerpt': article.excerpt or '',
                    'status': 'publish',
                    'categories': [category_id]
                }
                
                if featured_media_id:
                    post_data['featured_media'] = featured_media_id
                
                # Opublikuj post
                create_url = f"{blog.url}/wp-json/wp/v2/posts"
                headers = {'Authorization': f'Basic {auth_token}', 'Content-Type': 'application/json'}
                
                response = requests.post(
                    create_url,
                    headers=headers,
                    json=post_data,
                    timeout=60
                )
                
                if response.status_code in [200, 201]:
                    post_id = response.json().get('id')
                    print(f"   ✅ Published to WordPress! Post ID: {post_id}")
                    
                    # Zaktualizuj ContentLog
                    article.status = 'published'
                    article.post_id = post_id
                    article.published_at = db.func.now()
                    db.session.commit()
                else:
                    print(f"   ❌ Failed to publish: {response.status_code}")
                    print(f"   Response: {response.text[:200]}")
                    
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
                import traceback
                print(f"   Traceback: {traceback.format_exc()[:300]}")
        
        print("\n✅ Done publishing ready articles")

if __name__ == "__main__":
    publish_ready_articles()
