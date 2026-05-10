#!/usr/bin/env python3
"""
Generuje pozostałe artykuły (po kolei, aby uniknąć timeoutów)
"""
import sys
import logging
from app import app, db
from models import AutomationRule, Blog
from utils.automation.workflow_engine import execute_automation_rule

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_single_article(blog_id: int, article_num: int):
    """Generuje jeden artykuł dla danego bloga"""
    logger.info(f"=== Generuję artykuł dla blog_id={blog_id} ===")
    
    with app.app_context():
        rule = AutomationRule.query.filter(
            AutomationRule.blog_id == blog_id,
            AutomationRule.is_active == True
        ).first()
        
        if not rule:
            logger.error(f"No active rule for blog {blog_id}")
            return False
            
        blog = Blog.query.get(blog_id)
        logger.info(f"Generating article {article_num} for {blog.name}")
        
        try:
            execute_automation_rule(rule.id)
            logger.info(f"✅ Article {article_num} completed for {blog.name}")
            return True
        except Exception as e:
            logger.error(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python generate_remaining.py <blog_id> <article_number>")
        print("Example: python generate_remaining.py 3 2")
        sys.exit(1)
    
    blog_id = int(sys.argv[1])
    article_num = int(sys.argv[2])
    
    success = generate_single_article(blog_id, article_num)
    sys.exit(0 if success else 1)
