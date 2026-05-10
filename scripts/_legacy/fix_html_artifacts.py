#!/usr/bin/env python3
"""
Napraw artykuły z dzisiaj - usuń znaczniki markdown ```html
"""
import sys
sys.path.insert(0, '.')

import re
from app import app, db
from models import ContentLog, Blog
import requests
import base64
from datetime import datetime

def clean_markdown_artifacts(content: str) -> str:
    """Remove markdown code block artifacts"""
    if not content:
        return content
    
    # Remove markdown code blocks
    content = re.sub(r'^```html\s*\n?', '', content, flags=re.MULTILINE)
    content = re.sub(r'\n?```\s*$', '', content, flags=re.MULTILINE) 
    content = re.sub(r'^```\s*\n?', '', content, flags=re.MULTILINE)
    
    return content.strip()

def fix_articles():
    with app.app_context():
        # Pobierz artykuły z dzisiaj
        articles = ContentLog.query.filter(
            db.func.date(ContentLog.created_at) == datetime.utcnow().date()
        ).all()
        
        print(f"Found {len(articles)} articles from today")
        
        for article in articles:
            # Sprawdź czy ma znaczniki markdown
            if article.content and ('```html' in article.content or article.content.startswith('```')):
                print(f"\n🔧 Fixing article {article.id}: {article.title[:60]}")
                
                # Wyczyść content
                old_length = len(article.content)
                article.content = clean_markdown_artifacts(article.content)
                new_length = len(article.content)
                
                print(f"   Cleaned: {old_length} → {new_length} chars (removed {old_length - new_length} chars)")
                
                # Zaktualizuj w WordPress jeśli opublikowane
                if article.post_id and article.status == 'published':
                    blog = db.session.get(Blog, article.blog_id)
                    if blog:
                        try:
                            credentials = f"{blog.username}:{blog.api_token}"
                            auth_token = base64.b64encode(credentials.encode()).decode('utf-8')
                            
                            update_url = f"{blog.url}/wp-json/wp/v2/posts/{article.post_id}"
                            update_data = {'content': article.content}
                            
                            response = requests.post(
                                update_url,
                                headers={'Authorization': f'Basic {auth_token}', 'Content-Type': 'application/json'},
                                json=update_data,
                                timeout=30
                            )
                            
                            if response.status_code == 200:
                                print(f"   ✅ Updated on WordPress (Post ID: {article.post_id})")
                            else:
                                print(f"   ⚠️  WordPress update failed: {response.status_code}")
                        except Exception as e:
                            print(f"   ❌ Error updating WordPress: {str(e)}")
            else:
                print(f"✓ Article {article.id} OK (no markdown artifacts)")
        
        # Zapisz zmiany w bazie
        db.session.commit()
        print("\n✅ All articles fixed!")

if __name__ == "__main__":
    fix_articles()
