from app import db
from datetime import datetime
import json

class Blog(db.Model):
    """Model for WordPress blog configuration"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    api_url = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(100), nullable=False)
    api_token = db.Column(db.String(255), nullable=False)
    categories = db.Column(db.Text, nullable=True)  # JSON string of categories
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f"<Blog {self.name}>"
    
    def get_categories(self):
        """Returns categories as a Python list"""
        if self.categories:
            return json.loads(self.categories)
        return []
    
    def set_categories(self, categories_list):
        """Sets categories from a Python list"""
        self.categories = json.dumps(categories_list)

class SocialAccount(db.Model):
    """Model for social media account configuration"""
    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(50), nullable=False)  # facebook, twitter, instagram, etc.
    name = db.Column(db.String(100), nullable=False)
    api_token = db.Column(db.String(255), nullable=False)
    api_secret = db.Column(db.String(255), nullable=True)
    account_id = db.Column(db.String(100), nullable=True)
    active = db.Column(db.Boolean, default=True)
    blog_id = db.Column(db.Integer, db.ForeignKey('blog.id'), nullable=False)
    
    # Define relationship with Blog
    blog = db.relationship('Blog', backref=db.backref('social_accounts', lazy=True))
    
    def __repr__(self):
        return f"<SocialAccount {self.platform} - {self.name}>"

class ContentLog(db.Model):
    """Model for logging content generation and publishing activities"""
    id = db.Column(db.Integer, primary_key=True)
    blog_id = db.Column(db.Integer, db.ForeignKey('blog.id'), nullable=False)
    title = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(50), nullable=False)  # generated, published, error
    post_id = db.Column(db.Integer, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    published_at = db.Column(db.DateTime, nullable=True)
    social_media_posts = db.Column(db.Text, nullable=True)  # JSON string of social media post URLs
    
    # Define relationship with Blog
    blog = db.relationship('Blog', backref=db.backref('content_logs', lazy=True))
    
    def __repr__(self):
        return f"<ContentLog {self.title} - {self.status}>"
    
    def set_social_posts(self, posts_dict):
        """Sets social media posts from a Python dict"""
        self.social_media_posts = json.dumps(posts_dict)
    
    def get_social_posts(self):
        """Returns social media posts as a Python dict"""
        if self.social_media_posts:
            return json.loads(self.social_media_posts)
        return {}

class ArticleTopic(db.Model):
    """Model for storing generated topics"""
    id = db.Column(db.Integer, primary_key=True)
    blog_id = db.Column(db.Integer, db.ForeignKey('blog.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    keywords = db.Column(db.Text, nullable=True)  # JSON string of keywords
    category = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(50), default="pending")  # pending, approved, rejected, used
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    score = db.Column(db.Float, default=0.0)  # SEO score or priority
    
    # Define relationship with Blog
    blog = db.relationship('Blog', backref=db.backref('article_topics', lazy=True))
    
    def __repr__(self):
        return f"<ArticleTopic {self.title}>"
    
    def get_keywords(self):
        """Returns keywords as a Python list"""
        if self.keywords:
            return json.loads(self.keywords)
        return []
    
    def set_keywords(self, keywords_list):
        """Sets keywords from a Python list"""
        self.keywords = json.dumps(keywords_list)
