#!/usr/bin/env python3
"""
Script do wygenerowania brakujących artykułów z dzisiaj
"""
import sys
sys.path.insert(0, '.')

from app import app, db
from models import AutomationRule, Blog
from utils.automation.workflow_engine import WorkflowEngine, execute_automation_rule

def generate_missing_articles():
    with app.app_context():
        # MamaTestuje - brakuje 1 artykuł
        print("=" * 80)
        print("🔧 Generating missing article for MAMATESTUJE")
        print("=" * 80)
        
        rule_mt = AutomationRule.query.filter_by(blog_id=2, is_active=True).first()
        if rule_mt:
            engine_mt = WorkflowEngine()
            result = execute_automation_rule(rule_mt.id, engine=engine_mt)
            
            if result.get("success"):
                print(f"✅ MamaTestuje article generated successfully!")
                print(f"   Article ID: {result.get('article_id')}")
                print(f"   WordPress ID: {result.get('wordpress_post_id')}")
            else:
                print(f"❌ MamaTestuje failed: {result.get('error')}")
        
        # ZnaneKosmetyki - brakuje 2 artykuły
        print("\n" + "=" * 80)
        print("🔧 Generating 2 missing articles for ZNANEKOSMETYKI")
        print("=" * 80)
        
        rule_zk = AutomationRule.query.filter_by(blog_id=3, is_active=True).first()
        if rule_zk:
            engine_zk = WorkflowEngine()
            
            for i in range(2):
                print(f"\n📝 Article {i+1}/2 for ZnaneKosmetyki")
                result = execute_automation_rule(rule_zk.id, engine=engine_zk)
                
                if result.get("success"):
                    print(f"   ✅ Article {i+1} generated successfully!")
                    print(f"   Article ID: {result.get('article_id')}")
                    print(f"   WordPress ID: {result.get('wordpress_post_id')}")
                else:
                    print(f"   ❌ Article {i+1} failed: {result.get('error')}")
        
        print("\n" + "=" * 80)
        print("✅ DONE - Check results above")
        print("=" * 80)

if __name__ == "__main__":
    generate_missing_articles()
