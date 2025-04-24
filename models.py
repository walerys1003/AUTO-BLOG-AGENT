from app import db
from datetime import datetime, timedelta
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

class ContentMetrics(db.Model):
    """Model for storing content performance metrics from Google Analytics"""
    id = db.Column(db.Integer, primary_key=True)
    blog_id = db.Column(db.Integer, db.ForeignKey('blog.id'), nullable=False)
    post_id = db.Column(db.Integer, nullable=False)  # WordPress post ID
    title = db.Column(db.String(255), nullable=True)
    url = db.Column(db.String(512), nullable=False)
    page_views = db.Column(db.Integer, default=0)
    unique_visitors = db.Column(db.Integer, default=0)
    avg_time_on_page = db.Column(db.Float, default=0.0)  # In seconds
    bounce_rate = db.Column(db.Float, default=0.0)  # Percentage
    conversion_rate = db.Column(db.Float, default=0.0)  # Percentage
    social_shares = db.Column(db.Integer, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    raw_data = db.Column(db.Text, nullable=True)  # JSON string of additional metrics
    
    # Define relationship with Blog
    blog = db.relationship('Blog', backref=db.backref('content_metrics', lazy=True))
    
    def __repr__(self):
        return f"<ContentMetrics {self.title} - views:{self.page_views}>"
    
    def set_raw_data(self, data_dict):
        """Sets raw data from a Python dict"""
        self.raw_data = json.dumps(data_dict)
    
    def get_raw_data(self):
        """Returns raw data as a Python dict"""
        if self.raw_data:
            return json.loads(self.raw_data)
        return {}

class PerformanceReport(db.Model):
    """Model for storing aggregated performance reports"""
    id = db.Column(db.Integer, primary_key=True)
    blog_id = db.Column(db.Integer, db.ForeignKey('blog.id'), nullable=False)
    report_type = db.Column(db.String(50), nullable=False)  # daily, weekly, monthly, custom
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    total_views = db.Column(db.Integer, default=0)
    total_visitors = db.Column(db.Integer, default=0)
    avg_bounce_rate = db.Column(db.Float, default=0.0)
    top_posts = db.Column(db.Text, nullable=True)  # JSON string of top performing posts
    insights = db.Column(db.Text, nullable=True)  # AI-generated insights
    recommendations = db.Column(db.Text, nullable=True)  # AI-generated recommendations
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Define relationship with Blog
    blog = db.relationship('Blog', backref=db.backref('performance_reports', lazy=True))
    
    def __repr__(self):
        return f"<PerformanceReport {self.blog.name} - {self.report_type} - {self.start_date.strftime('%Y-%m-%d')}>"
    
    def set_top_posts(self, posts_list):
        """Sets top posts from a Python list"""
        self.top_posts = json.dumps(posts_list)
    
    def get_top_posts(self):
        """Returns top posts as a Python list"""
        if self.top_posts:
            return json.loads(self.top_posts)
        return []
    
    def set_insights(self, insights_list):
        """Sets insights from a Python list"""
        self.insights = json.dumps(insights_list)
    
    def get_insights(self):
        """Returns insights as a Python list"""
        if self.insights:
            return json.loads(self.insights)
        return []
    
    def set_recommendations(self, recommendations_list):
        """Sets recommendations from a Python list"""
        self.recommendations = json.dumps(recommendations_list)
    
    def get_recommendations(self):
        """Returns recommendations as a Python list"""
        if self.recommendations:
            return json.loads(self.recommendations)
        return []

class ContentCalendar(db.Model):
    """Model for content planning and scheduling"""
    id = db.Column(db.Integer, primary_key=True)
    blog_id = db.Column(db.Integer, db.ForeignKey('blog.id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('article_topic.id'), nullable=True)
    title = db.Column(db.String(255), nullable=True)
    scheduled_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(50), default="planned")  # planned, in_progress, published, cancelled
    priority = db.Column(db.Integer, default=3)  # 1-5 (5 highest)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Define relationships
    blog = db.relationship('Blog', backref=db.backref('content_calendar', lazy=True))
    topic = db.relationship('ArticleTopic', backref=db.backref('calendar_entries', lazy=True))
    
    def __repr__(self):
        return f"<ContentCalendar {self.title} - {self.scheduled_date.strftime('%Y-%m-%d')}>"

class AnalyticsConfig(db.Model):
    """Model for storing Google Analytics configuration per blog"""
    id = db.Column(db.Integer, primary_key=True)
    blog_id = db.Column(db.Integer, db.ForeignKey('blog.id'), nullable=False, unique=True)
    property_id = db.Column(db.String(255), nullable=True)  # GA4 property ID
    view_id = db.Column(db.String(255), nullable=True)  # Legacy view ID
    measurement_id = db.Column(db.String(255), nullable=True)  # GA4 measurement ID (G-XXXXXXXXXX)
    tracking_code = db.Column(db.Text, nullable=True)  # Custom tracking code if needed
    last_sync = db.Column(db.DateTime, nullable=True)
    sync_frequency = db.Column(db.Integer, default=24)  # Hours
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Define relationship with Blog
    blog = db.relationship('Blog', backref=db.backref('analytics_config', uselist=False))
    
    def __repr__(self):
        return f"<AnalyticsConfig {self.blog.name}>"
