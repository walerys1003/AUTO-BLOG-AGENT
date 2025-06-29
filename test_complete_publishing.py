#!/usr/bin/env python3
"""
Test complete publishing workflow with categories, tags, and featured image
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import ArticleTopic, Blog, AutomationRule
from utils.automation.workflow_engine import WorkflowEngine
from datetime import datetime

def test_complete_publishing():
    """Test complete publishing with all features"""
    
    with app.app_context():
        print("🚀 Testing complete publishing workflow...")
        
        # Find available topic
        topic = ArticleTopic.query.filter_by(
            status='approved',
            used=False
        ).first()
        
        if not topic:
            print("❌ No approved topics available")
            return
            
        print(f"📝 Using topic: {topic.title}")
        print(f"🏷️ Category: {topic.category}")
        
        # Get blog and automation rule
        blog = Blog.query.first()
        automation_rule = AutomationRule.query.filter_by(is_active=True).first()
        
        if not blog or not automation_rule:
            print("❌ Missing blog or automation rule")
            return
            
        # Initialize workflow engine
        engine = WorkflowEngine()
        
        # Execute content generation
        print("🎯 Generating article...")
        content_result = engine._execute_content_generation(automation_rule, topic)
        
        if not content_result.get('success'):
            print(f"❌ Content generation failed: {content_result.get('error')}")
            return
            
        article = content_result.get('article')
        print(f"✅ Article generated: {article.title}")
        
        # Execute image acquisition  
        print("🖼️ Finding images...")
        image_result = engine._execute_image_acquisition(article)
        
        if image_result.get('success'):
            print(f"✅ Found {image_result.get('images_found', 0)} images")
        else:
            print(f"⚠️ Image search failed: {image_result.get('error')}")
            
        # Execute WordPress publishing with categories, tags, and featured image
        print("📤 Publishing to WordPress...")
        publish_result = engine._execute_wordpress_publishing(article, automation_rule)
        
        if publish_result.get('success'):
            post_id = publish_result.get('post_id')
            print(f"🎉 Article published successfully!")
            print(f"📍 WordPress Post ID: {post_id}")
            print(f"🔗 URL: https://mamatestuje.com/?p={post_id}")
            
            # Check WordPress post details
            print("\n📊 Checking post details...")
            import requests
            
            wp_url = f"https://mamatestuje.com/wp-json/wp/v2/posts/{post_id}"
            response = requests.get(wp_url)
            
            if response.status_code == 200:
                post_data = response.json()
                
                print(f"✅ Title: {post_data.get('title', {}).get('rendered', 'N/A')}")
                print(f"✅ Categories: {post_data.get('categories', [])}")
                print(f"✅ Tags: {post_data.get('tags', [])}")
                print(f"✅ Featured Media: {post_data.get('featured_media', 'None')}")
                print(f"✅ Author: {post_data.get('author', 'N/A')}")
                
        else:
            print(f"❌ Publishing failed: {publish_result.get('error')}")

if __name__ == "__main__":
    test_complete_publishing()