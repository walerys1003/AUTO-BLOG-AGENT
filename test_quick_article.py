#!/usr/bin/env python3
"""
Quick test of article generation with metadata
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import ArticleTopic, Blog, AutomationRule
from utils.automation.workflow_engine import WorkflowEngine

def quick_article_test():
    """Test quick article generation"""
    
    with app.app_context():
        print("🚀 Quick article generation test...")
        
        # Get first available topic
        topic = ArticleTopic.query.filter_by(status='approved', used=False).first()
        if not topic:
            print("❌ No available topics")
            return
            
        print(f"📝 Topic: {topic.title}")
        
        # Get blog and automation rule
        blog = Blog.query.first()
        automation_rule = AutomationRule.query.filter_by(is_active=True).first()
        
        if not blog or not automation_rule:
            print("❌ Missing blog or automation rule")
            return
            
        # Execute just content generation
        engine = WorkflowEngine()
        
        print("🎯 Generating article content...")
        result = engine._execute_content_generation(automation_rule, topic)
        
        if result.get('success'):
            article = result.get('article')
            print(f"✅ Article generated: {article.title}")
            print(f"📍 Length: {len(article.content)} characters")
            
            # Test WordPress publishing with metadata
            print("📤 Publishing to WordPress...")
            publish_result = engine._execute_wordpress_publishing(article, automation_rule)
            
            if publish_result.get('success'):
                post_id = publish_result.get('post_id')
                print(f"🎉 Article published!")
                print(f"📍 Post ID: {post_id}")
                print(f"🏷️ Category assigned: {publish_result.get('category_assigned')}")
                print(f"🔖 Tags assigned: {publish_result.get('tags_assigned')}")
                print(f"🖼️ Featured image: {publish_result.get('featured_image')}")
                print(f"🔗 URL: https://mamatestuje.com/?p={post_id}")
                
                return post_id
            else:
                print(f"❌ Publishing failed: {publish_result.get('error')}")
        else:
            print(f"❌ Content generation failed: {result.get('error')}")

if __name__ == "__main__":
    post_id = quick_article_test()
    if post_id:
        print(f"✅ Test completed successfully! Post ID: {post_id}")
    else:
        print("❌ Test failed")