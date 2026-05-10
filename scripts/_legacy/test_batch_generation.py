#!/usr/bin/env python3
"""
Test batch generation for a specific blog
"""
from app import app, db
from models import Blog, AutomationRule
from utils.automation.workflow_engine import WorkflowEngine

def test_batch_for_blog(blog_name: str, num_articles: int):
    with app.app_context():
        print(f"\n{'='*70}")
        print(f"🚀 BATCH GENERATION TEST: {blog_name}")
        print(f"{'='*70}\n")
        
        # Find blog
        blog = Blog.query.filter_by(name=blog_name).first()
        if not blog:
            print(f"❌ Blog '{blog_name}' not found!")
            return
        
        print(f"✅ Found blog: {blog.name} (ID: {blog.id})")
        print(f"   URL: {blog.url}")
        
        # Find automation rule
        rule = AutomationRule.query.filter_by(blog_id=blog.id, is_active=True).first()
        if not rule:
            print(f"❌ No active automation rule found for {blog.name}!")
            return
        
        print(f"✅ Found automation rule: {rule.name}")
        print(f"   Auto-publish: {rule.auto_publish}")
        print(f"   Categories: {rule.get_categories()}")
        
        print(f"\n🔄 Starting batch generation ({num_articles} articles)...")
        print("-" * 70)
        
        try:
            # Create workflow engine
            engine = WorkflowEngine()
            
            # Execute batch generation for each article
            results = []
            for i in range(num_articles):
                print(f"\n📄 Generating article {i+1}/{num_articles}...")
                result = engine.execute_full_cycle(rule)
                results.append(result)
                
                if result.get('status') == 'completed':
                    print(f"   ✅ Article {i+1} completed successfully!")
                    if result.get('article_id'):
                        print(f"      Article ID: {result['article_id']}")
                    if result.get('wordpress_post_id'):
                        print(f"      WordPress Post ID: {result['wordpress_post_id']}")
                else:
                    print(f"   ❌ Article {i+1} failed!")
                    if result.get('errors'):
                        for error in result['errors']:
                            print(f"      Error: {error}")
            
            # Commit changes
            db.session.commit()
            
            print("\n" + "="*70)
            print("📊 BATCH GENERATION RESULTS")
            print("="*70)
            print(f"Total articles: {len(results)}")
            successful = sum(1 for r in results if r.get('status') == 'completed')
            failed = len(results) - successful
            print(f"Successful: {successful}")
            print(f"Failed: {failed}")
            
        except Exception as e:
            print(f"\n❌ Error during batch generation: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    import sys
    
    # Test HomosOnly with 2 articles
    test_batch_for_blog("HOMOSONLY.PL", 2)
