"""
Script to create test content for testing the publishing module
"""
import sys
import os
from datetime import datetime, timedelta
from app import db
from models import Blog, ContentLog, Category, PublishingSchedule

def create_test_data():
    """Create test blog and article for testing"""
    # Create a test blog if doesn't exist
    test_blog = Blog.query.filter_by(name="Test Blog").first()
    
    if not test_blog:
        print("Creating test blog...")
        test_blog = Blog(
            name="Test Blog",
            url="https://example.com/test-blog",
            api_url="https://example.com/wp-json/wp/v2",
            username="testuser",
            api_token="test-api-token",
            active=True
        )
        db.session.add(test_blog)
        db.session.commit()
        print(f"Test blog created with ID: {test_blog.id}")
    else:
        print(f"Test blog already exists with ID: {test_blog.id}")
    
    # Create a test category
    test_category = Category.query.filter_by(name="Test Category", blog_id=test_blog.id).first()
    
    if not test_category:
        print("Creating test category...")
        test_category = Category(
            name="Test Category",
            blog_id=test_blog.id,
            wordpress_id=1
        )
        db.session.add(test_category)
        db.session.commit()
        print(f"Test category created with ID: {test_category.id}")
    else:
        print(f"Test category already exists with ID: {test_category.id}")
    
    # Create a test article
    test_article = ContentLog.query.filter_by(title="Test Article for Preview").first()
    
    if not test_article:
        print("Creating test article...")
        test_article = ContentLog(
            title="Test Article for Preview",
            content="<h2>This is a test article for previewing and editing</h2><p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam auctor, nisl eget ultricies lacinia, nisl nisl aliquam nisl, eget aliquam nisl nisl eget nisl. Nullam auctor, nisl eget ultricies lacinia, nisl nisl aliquam nisl, eget aliquam nisl nisl eget nisl.</p><p>Second paragraph with some <strong>bold text</strong> and <em>italic text</em>.</p><h3>A subheading</h3><p>More content here to test the preview functionality.</p><ul><li>List item 1</li><li>List item 2</li><li>List item 3</li></ul>",
            excerpt="This is a test article for previewing and editing functionality",
            blog_id=test_blog.id,
            category_id=test_category.id,
            status="scheduled",
            created_at=datetime.now(),
            publish_date=datetime.now() + timedelta(days=1)
        )
        db.session.add(test_article)
        db.session.commit()
        print(f"Test article created with ID: {test_article.id}")
        
        # Create publishing schedule for this article
        test_schedule = PublishingSchedule(
            content_id=test_article.id,
            blog_id=test_blog.id,
            publish_date=(datetime.now() + timedelta(days=1)).date(),
            publish_time=datetime.now().time()
        )
        db.session.add(test_schedule)
        db.session.commit()
        print(f"Test schedule created with ID: {test_schedule.id}")
    else:
        print(f"Test article already exists with ID: {test_article.id}")
    
    print("Test data creation completed.")

if __name__ == "__main__":
    try:
        from main import app
        with app.app_context():
            create_test_data()
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)