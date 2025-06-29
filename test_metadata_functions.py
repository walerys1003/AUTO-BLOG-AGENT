#!/usr/bin/env python3
"""
Test metadata functions independently
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Blog
from utils.automation.workflow_engine import WorkflowEngine

def test_metadata_functions():
    """Test individual metadata functions"""
    
    with app.app_context():
        print("🧪 Testing metadata functions...")
        
        blog = Blog.query.first()
        if not blog:
            print("❌ No blog found")
            return
            
        engine = WorkflowEngine()
        
        # Test category ID detection
        print("\n🏷️ Testing category ID detection...")
        category_id = engine._get_wordpress_category_id(blog, "Planowanie ciąży")
        print(f"Category ID for 'Planowanie ciąży': {category_id}")
        
        # Test tag generation
        print("\n🔖 Testing tag generation...")
        tags = engine._generate_tags_for_category("Planowanie ciąży")
        print(f"Generated tags: {tags}")
        
        # Test if functions work
        if category_id and tags:
            print("\n✅ Metadata functions working correctly!")
            print(f"✓ Category mapping: 'Planowanie ciąży' → ID {category_id}")
            print(f"✓ Tag generation: {len(tags)} tags created")
            
            # Show what next article will have
            print(f"\n📊 Next article will be published with:")
            print(f"   Categories: [{category_id}]")
            print(f"   Tags: {tags}")
            print(f"   Featured image: Auto-uploaded from Google Images")
            
            return True
        else:
            print("❌ Metadata functions not working properly")
            return False

if __name__ == "__main__":
    success = test_metadata_functions()
    if success:
        print("\n🎉 Metadata system ready for next article!")
    else:
        print("\n❌ Metadata system needs fixes")