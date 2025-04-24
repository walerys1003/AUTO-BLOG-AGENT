"""
Newsletter content generator
"""
import os
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from jinja2 import Template

from app import db
from models import Blog, Newsletter, ContentLog, NewsletterConfig

logger = logging.getLogger(__name__)

class NewsletterGenerator:
    """Generator for newsletter content"""
    
    def __init__(self, blog_id: Optional[int] = None):
        """
        Initialize newsletter generator
        
        Args:
            blog_id: Optional blog ID to generate for
        """
        self.blog_id = blog_id
        self.default_template = """
<!DOCTYPE html>
<html>
<head>
    <title>{{ newsletter.title }}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }
        h1 {
            color: #2c3e50;
            font-size: 24px;
        }
        h2 {
            color: #3498db;
            font-size: 20px;
        }
        .article {
            margin-bottom: 30px;
            border-bottom: 1px solid #eee;
            padding-bottom: 20px;
        }
        .article h3 {
            margin-bottom: 10px;
        }
        .article-meta {
            color: #7f8c8d;
            font-size: 14px;
            margin-bottom: 10px;
        }
        .read-more {
            display: inline-block;
            background-color: #3498db;
            color: white;
            padding: 8px 15px;
            text-decoration: none;
            border-radius: 4px;
            font-size: 14px;
        }
        .footer {
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            font-size: 12px;
            color: #7f8c8d;
        }
        .unsubscribe {
            color: #7f8c8d;
        }
    </style>
</head>
<body>
    <h1>{{ newsletter.title }}</h1>
    
    <p>Here are the latest articles from {{ blog.name }}:</p>
    
    {% for article in articles %}
    <div class="article">
        <h3>{{ article.title }}</h3>
        <div class="article-meta">Published on {{ article.published_at }}</div>
        <p>{{ article.excerpt }}</p>
        <a href="{{ article.url }}" class="read-more">Read More</a>
    </div>
    {% endfor %}
    
    <div class="footer">
        <p>You're receiving this email because you subscribed to updates from {{ blog.name }}.</p>
        <p><a href="{{ unsubscribe_url }}" class="unsubscribe">Unsubscribe</a></p>
    </div>
</body>
</html>
"""
    
    def get_recent_articles(self, blog_id: Optional[int] = None, days: int = 7, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get recent articles for a blog
        
        Args:
            blog_id: Blog ID (defaults to self.blog_id)
            days: Number of days to look back
            limit: Maximum number of articles to return
            
        Returns:
            List of article data
        """
        blog_id = blog_id or self.blog_id
        if not blog_id:
            logger.error("Blog ID not provided")
            return []
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Query recent published articles
        recent_posts = ContentLog.query.filter(
            ContentLog.blog_id == blog_id,
            ContentLog.status == 'published',
            ContentLog.published_at >= start_date,
            ContentLog.published_at <= end_date
        ).order_by(ContentLog.published_at.desc()).limit(limit).all()
        
        articles = []
        for post in recent_posts:
            # Extract excerpt from content if available
            excerpt = ""
            try:
                if post.content:
                    excerpt = post.content[:150] + "..."
            except:
                excerpt = "Read the full article..."
            
            # Get the URL
            post_url = ""
            blog = Blog.query.get(blog_id)
            if blog and post.post_id:
                post_url = f"{blog.url.rstrip('/')}/p/{post.post_id}"
            
            articles.append({
                'title': post.title,
                'excerpt': excerpt,
                'published_at': post.published_at.strftime('%B %d, %Y') if post.published_at else "Recently",
                'url': post_url,
                'post_id': post.post_id
            })
        
        return articles
    
    def generate_newsletter_content(
        self, 
        blog_id: Optional[int] = None,
        title: Optional[str] = None,
        custom_template: Optional[str] = None,
        days: int = 7,
        article_limit: int = 5,
        extra_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        Generate newsletter content with recent articles
        
        Args:
            blog_id: Blog ID (defaults to self.blog_id)
            title: Newsletter title (defaults to "Weekly Newsletter")
            custom_template: Custom HTML template
            days: Number of days to look back for articles
            article_limit: Maximum number of articles to include
            extra_context: Additional context for template rendering
            
        Returns:
            Dictionary with HTML and text content
        """
        blog_id = blog_id or self.blog_id
        if not blog_id:
            logger.error("Blog ID not provided")
            return {"html": "", "text": ""}
        
        # Get blog details
        blog = Blog.query.get(blog_id)
        if not blog:
            logger.error(f"Blog with ID {blog_id} not found")
            return {"html": "", "text": ""}
        
        # Set default title if not provided
        title = title or f"{blog.name} Weekly Newsletter"
        
        # Get recent articles
        articles = self.get_recent_articles(blog_id, days, article_limit)
        
        if not articles:
            logger.warning(f"No recent articles found for blog {blog.name}")
            return {"html": "", "text": ""}
        
        # Prepare template context
        context = {
            'blog': {
                'id': blog.id,
                'name': blog.name,
                'url': blog.url
            },
            'newsletter': {
                'title': title,
                'date': datetime.utcnow().strftime('%B %d, %Y')
            },
            'articles': articles,
            'unsubscribe_url': f"{blog.url.rstrip('/')}/unsubscribe"
        }
        
        # Add any extra context
        if extra_context:
            context.update(extra_context)
        
        # Use custom template if provided, otherwise use default
        template_html = custom_template or self.default_template
        
        # Render HTML content
        try:
            template = Template(template_html)
            html_content = template.render(**context)
        except Exception as e:
            logger.error(f"Error rendering newsletter template: {str(e)}")
            return {"html": "", "text": ""}
        
        # Generate simple text version
        text_content = f"{title}\n\n"
        text_content += f"Latest articles from {blog.name}:\n\n"
        
        for article in articles:
            text_content += f"* {article['title']}\n"
            text_content += f"  Published on {article['published_at']}\n"
            text_content += f"  {article['url']}\n\n"
        
        text_content += f"\nYou're receiving this email because you subscribed to updates from {blog.name}.\n"
        text_content += f"To unsubscribe, visit: {context['unsubscribe_url']}"
        
        return {
            "html": html_content,
            "text": text_content
        }
    
    def create_scheduled_newsletter(
        self,
        blog_id: Optional[int] = None,
        title: Optional[str] = None,
        subject: Optional[str] = None,
        scheduled_for: Optional[datetime] = None,
        days: int = 7,
        article_limit: int = 5
    ) -> Dict[str, Any]:
        """
        Create a new newsletter and schedule it
        
        Args:
            blog_id: Blog ID (defaults to self.blog_id)
            title: Newsletter title (defaults to "Weekly Newsletter")
            subject: Email subject (defaults to title)
            scheduled_for: When to send the newsletter
            days: Number of days to look back for articles
            article_limit: Maximum number of articles to include
            
        Returns:
            Dictionary with result information
        """
        blog_id = blog_id or self.blog_id
        if not blog_id:
            return {"error": "Blog ID not provided"}
        
        # Get blog and newsletter config
        blog = Blog.query.get(blog_id)
        if not blog:
            return {"error": f"Blog with ID {blog_id} not found"}
        
        # Get newsletter configuration
        config = NewsletterConfig.query.filter_by(blog_id=blog_id).first()
        if not config:
            return {"error": f"Newsletter configuration not found for blog {blog.name}"}
        
        if not config.enabled:
            return {"error": f"Newsletter is disabled for blog {blog.name}"}
        
        # Set default title and subject
        title = title or f"{blog.name} Newsletter - {datetime.utcnow().strftime('%B %d, %Y')}"
        subject = subject or title
        
        # Generate content
        content = self.generate_newsletter_content(
            blog_id=blog_id,
            title=title,
            days=days,
            article_limit=article_limit
        )
        
        if not content["html"]:
            return {"error": "Failed to generate newsletter content or no recent articles found"}
        
        try:
            # Create new newsletter
            newsletter = Newsletter(
                title=title,
                subject=subject,
                content_html=content["html"],
                content_text=content["text"],
                status="scheduled" if scheduled_for else "draft",
                scheduled_for=scheduled_for,
                blog_id=blog_id
            )
            
            db.session.add(newsletter)
            db.session.commit()
            
            return {
                "success": True,
                "newsletter_id": newsletter.id,
                "status": newsletter.status
            }
            
        except Exception as e:
            logger.error(f"Error creating newsletter: {str(e)}")
            return {"error": str(e)}