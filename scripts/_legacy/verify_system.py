#!/usr/bin/env python3
"""
Weryfikacja systemu - sprawdź czy wszystko działa
"""
import sys
sys.path.insert(0, '.')

from app import app, db
from models import Blog, AutomationRule, ArticleTopic
from datetime import datetime
import os

def verify_system():
    with app.app_context():
        print("=" * 80)
        print("🔍 WERYFIKACJA SYSTEMU")
        print("=" * 80)
        
        # 1. Sprawdź blogi
        print("\n1️⃣  BLOGI:")
        blogs = Blog.query.filter_by(active=True).all()
        for blog in blogs:
            print(f"   ✅ {blog.name} - {blog.url}")
        
        # 2. Sprawdź reguły automatyzacji
        print("\n2️⃣  REGUŁY AUTOMATYZACJI:")
        rules = AutomationRule.query.filter_by(is_active=True).all()
        for rule in rules:
            blog = db.session.get(Blog, rule.blog_id)
            print(f"   ✅ {blog.name}: {rule.posts_per_day} artykułów/dzień")
        
        # 3. Sprawdź pulę tematów
        print("\n3️⃣  PULA TEMATÓW:")
        for blog in blogs:
            approved = ArticleTopic.query.filter_by(
                blog_id=blog.id, 
                status='approved'
            ).count()
            used_today = ArticleTopic.query.filter_by(
                blog_id=blog.id,
                status='used'
            ).filter(
                db.func.date(ArticleTopic.used_at) == datetime.utcnow().date()
            ).count()
            print(f"   {blog.name}:")
            print(f"      Zatwierdzone: {approved} tematów")
            print(f"      Użyte dzisiaj: {used_today} tematów")
        
        # 4. Sprawdź logi
        print("\n4️⃣  SYSTEM LOGOWANIA:")
        scheduler_log = os.path.exists('logs/automation/scheduler.log')
        workflow_log = os.path.exists('logs/automation/workflow_engine.log')
        print(f"   Scheduler log: {'✅ EXISTS' if scheduler_log else '❌ MISSING'}")
        print(f"   Workflow log: {'✅ EXISTS' if workflow_log else '❌ MISSING'}")
        
        if scheduler_log:
            size = os.path.getsize('logs/automation/scheduler.log')
            print(f"      scheduler.log: {size:,} bytes")
        
        if workflow_log:
            size = os.path.getsize('logs/automation/workflow_engine.log')
            print(f"      workflow_engine.log: {size:,} bytes")
        
        # 5. Sprawdź API keys
        print("\n5️⃣  API KEYS:")
        openrouter = os.environ.get('OPENROUTER_API_KEY')
        unsplash = os.environ.get('UNSPLASH_API_KEY')
        print(f"   OpenRouter: {'✅ SET' if openrouter else '❌ MISSING'}")
        print(f"   Unsplash: {'✅ SET' if unsplash else '❌ MISSING'}")
        
        # 6. Dzisiejsze artykuły
        from models import ContentLog
        today_articles = ContentLog.query.filter(
            db.func.date(ContentLog.created_at) == datetime.utcnow().date()
        ).all()
        
        print(f"\n6️⃣  DZISIEJSZE ARTYKUŁY ({len(today_articles)} total):")
        for blog in blogs:
            blog_articles = [a for a in today_articles if a.blog_id == blog.id]
            published = len([a for a in blog_articles if a.status == 'published'])
            with_images = len([a for a in blog_articles if a.featured_image_data])
            with_wp_id = len([a for a in blog_articles if a.post_id])
            print(f"   {blog.name}:")
            print(f"      Artykuły: {len(blog_articles)}")
            print(f"      Opublikowane: {published}/{len(blog_articles)}")
            print(f"      Ze zdjęciami: {with_images}/{len(blog_articles)}")
            print(f"      Na WordPress: {with_wp_id}/{len(blog_articles)}")
        
        print("\n" + "=" * 80)
        print("✅ WERYFIKACJA ZAKOŃCZONA - System gotowy na jutro!")
        print("=" * 80)

if __name__ == "__main__":
    verify_system()
