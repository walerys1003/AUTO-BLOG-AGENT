#!/usr/bin/env python3
"""
Quick test of article publishing with metadata
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Blog, ArticleTopic
from utils.ai_content_strategy.article_generator import ArticleGenerationStrategy
from utils.automation.workflow_engine import WorkflowEngine

def test_quick_article():
    """Test quick article generation and publishing with metadata"""
    
    with app.app_context():
        print("🚀 Testing quick article with metadata...")
        
        blog = Blog.query.first()
        if not blog:
            print("❌ No blog found")
            return
        
        # Get an approved topic
        topic = ArticleTopic.query.filter_by(approval_status='approved').first()
        if not topic:
            print("❌ No approved topics found")
            return
            
        print(f"📝 Using topic: {topic.title}")
        print(f"📂 Category: {topic.category}")
        
        # Generate short article quickly
        strategy = ArticleGenerationStrategy()
        
        # Override for quick test - just 2 paragraphs
        article = strategy.generate_article(
            title=topic.title,
            category=topic.category,
            description=topic.description or f"Artykuł o {topic.title}",
            min_paragraphs=2,
            max_paragraphs=2
        )
        
        if not article or not hasattr(article, 'title'):
            print("❌ Article generation failed")
            return
            
        print(f"✅ Article generated: {article.title}")
        print(f"📄 Content length: {len(article.content)} chars")
        
        # Test publishing with metadata
        engine = WorkflowEngine()
        
        # Publish to WordPress
        success = engine._execute_wordpress_publishing(article, blog)
        
        if success:
            print("🎉 Article published successfully with metadata!")
            print("🔍 Check WordPress to verify categories, tags, and featured image")
        else:
            print("❌ Publishing failed")

if __name__ == "__main__":
    test_quick_article()