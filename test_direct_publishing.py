#!/usr/bin/env python3
"""
Direct test of WordPress publishing with metadata
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Blog, ContentLog
from utils.automation.workflow_engine import WorkflowEngine

def test_direct_publishing():
    """Test publishing existing article with metadata"""
    
    with app.app_context():
        print("🚀 Testing direct publishing with metadata...")
        
        blog = Blog.query.first()
        if not blog:
            print("❌ No blog found")
            return
        
        # Get latest unpublished article or create a simple one
        article = ContentLog.query.filter_by(status='draft').first()
        
        if not article:
            # Create a simple test article
            article = ContentLog(
                title="Test artykułu z metadanymi",
                content="<p>To jest testowy artykuł sprawdzający czy metadane (kategorie, tagi, obrazy) są właściwie przypisywane podczas publikacji.</p><p>Artykuł powinien zostać opublikowany z kategorią 'Planowanie ciąży' i odpowiednimi tagami.</p>",
                meta_description="Test artykułu z automatycznymi metadanymi",
                category="Planowanie ciąży",
                status='draft',
                blog_id=blog.id
            )
            db.session.add(article)
            db.session.commit()
            print("✅ Created test article")
        
        print(f"📝 Article: {article.title}")
        # Get category name from ID
        category_name = "Planowanie ciąży"  # Default for testing
        if hasattr(article, 'category_name') and article.category_name:
            category_name = article.category_name
        
        print(f"📂 Category: {category_name}")
        
        # Test publishing with metadata
        engine = WorkflowEngine()
        
        # Test metadata functions first
        print("\n🔍 Testing metadata functions...")
        category_id = engine._get_wordpress_category_id(blog, category_name)
        tags = engine._generate_tags_for_category(category_name)
        
        print(f"✓ Category ID: {category_id}")
        print(f"✓ Tags: {tags}")
        
        if category_id and tags:
            print("\n📤 Publishing to WordPress with metadata...")
            
            # Mock article object for publishing
            class MockArticle:
                def __init__(self, content_log, category_name):
                    self.title = content_log.title
                    self.content = content_log.content
                    self.meta_description = content_log.meta_description
                    self.category = category_name
                    self.featured_image = None
            
            mock_article = MockArticle(article, category_name)
            
            # Test publishing
            success = engine._execute_wordpress_publishing(mock_article, blog)
            
            if success:
                print("🎉 Article published successfully with metadata!")
                print("🔍 Check WordPress to verify categories, tags, and featured image")
                
                # Update article status
                article.status = 'published'
                db.session.commit()
            else:
                print("❌ Publishing failed")
        else:
            print("❌ Metadata functions failed")

if __name__ == "__main__":
    test_direct_publishing()