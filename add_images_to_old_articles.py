#!/usr/bin/env python3
"""
Script do dodania zdjęć do starszych artykułów z dzisiaj (bez zdjęć)
"""
import sys
sys.path.insert(0, '.')

from app import app, db
from models import ContentLog
from utils.automation.workflow_engine import WorkflowEngine

def add_images():
    with app.app_context():
        # Pobierz artykuły bez zdjęć z dzisiaj
        articles_without_images = ContentLog.query.filter(
            db.func.date(ContentLog.created_at) == '2025-11-19',
            (ContentLog.featured_image_data == None) | (ContentLog.featured_image_data == '')
        ).all()
        
        print(f"Found {len(articles_without_images)} articles without images")
        
        engine = WorkflowEngine()
        
        for article in articles_without_images:
            print(f"\n📷 Adding images to: {article.title}")
            print(f"   Article ID: {article.id}, Blog ID: {article.blog_id}")
            
            # Dodaj zdjęcia
            result = engine._execute_image_acquisition(article, topic_category=None)
            
            if result.get("success"):
                print(f"   ✅ Images added! Found {result.get('images_found', 0)} images")
            else:
                print(f"   ❌ Failed: {result.get('error')}")
        
        print("\n✅ Done adding images")

if __name__ == "__main__":
    add_images()
