from app import db
from datetime import datetime, timedelta
import json
from sqlalchemy.ext.hybrid import hybrid_property

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
    approval_required = db.Column(db.Boolean, default=False)  # Require approval before publishing
    
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

class Category(db.Model):
    """Model for WordPress categories"""
    id = db.Column(db.Integer, primary_key=True)
    blog_id = db.Column(db.Integer, db.ForeignKey('blog.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    wordpress_id = db.Column(db.Integer, nullable=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Define relationships
    blog = db.relationship('Blog', backref=db.backref('categories_list', lazy=True))
    parent = db.relationship('Category', remote_side=[id], backref=db.backref('subcategories', lazy=True))
    
    def __repr__(self):
        return f"<Category {self.name}>"

class Tag(db.Model):
    """Model for WordPress tags"""
    id = db.Column(db.Integer, primary_key=True)
    blog_id = db.Column(db.Integer, db.ForeignKey('blog.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    wordpress_id = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Define relationship with Blog
    blog = db.relationship('Blog', backref=db.backref('tags_list', lazy=True))
    
    def __repr__(self):
        return f"<Tag {self.name}>"

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
    content = db.Column(db.Text, nullable=True)  # Full article content
    excerpt = db.Column(db.Text, nullable=True)  # Article excerpt/summary
    status = db.Column(db.String(50), nullable=False)  # draft, scheduled, pending_review, published, failed
    post_id = db.Column(db.Integer, nullable=True)
    category_id = db.Column(db.Integer, nullable=True)  # WordPress category ID
    tags = db.Column(db.Text, nullable=True)  # JSON string of tags
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    publish_date = db.Column(db.DateTime, nullable=True)  # When the post should be published
    published_at = db.Column(db.DateTime, nullable=True)  # When the post was actually published
    social_media_posts = db.Column(db.Text, nullable=True)  # JSON string of social media post URLs
    featured_image_data = db.Column(db.Text, nullable=True)  # JSON string of featured image data
    seo_metadata = db.Column(db.Text, nullable=True)  # JSON string of SEO metadata
    
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
        
    def set_featured_image(self, image_data):
        """Sets featured image data from a Python dict"""
        self.featured_image_data = json.dumps(image_data)
    
    def get_featured_image(self):
        """Returns featured image data as a Python dict"""
        if self.featured_image_data:
            return json.loads(self.featured_image_data)
        return None
    
    def set_tags(self, tags_list):
        """Sets tags from a Python list"""
        self.tags = json.dumps(tags_list)
    
    def get_tags(self):
        """Returns tags as a Python list"""
        if self.tags:
            return json.loads(self.tags)
        return []
    
    def set_seo_metadata(self, metadata_dict):
        """Sets SEO metadata from a Python dict"""
        self.seo_metadata = json.dumps(metadata_dict)
    
    def get_seo_metadata(self):
        """Returns SEO metadata as a Python dict"""
        if self.seo_metadata:
            return json.loads(self.seo_metadata)
        return {}

class PublishingSchedule(db.Model):
    """Model for managing publication schedule"""
    id = db.Column(db.Integer, primary_key=True)
    blog_id = db.Column(db.Integer, db.ForeignKey('blog.id'), nullable=False)
    content_id = db.Column(db.Integer, db.ForeignKey('content_log.id'), nullable=False)
    publish_date = db.Column(db.Date, nullable=False)
    publish_time = db.Column(db.Time, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Define relationships
    blog = db.relationship('Blog', backref=db.backref('publishing_schedule', lazy=True))
    content = db.relationship('ContentLog', backref=db.backref('schedule', uselist=False))
    
    def __repr__(self):
        return f"<PublishingSchedule {self.publish_date} {self.publish_time}>"
    
    @hybrid_property
    def full_datetime(self):
        """Returns combined datetime of publish_date and publish_time"""
        if self.publish_date and self.publish_time:
            return datetime.combine(self.publish_date, self.publish_time)
        return None

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

class Subscriber(db.Model):
    """Model for newsletter subscribers"""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), default='active')  # active, unsubscribed, bounced
    preferences = db.Column(db.Text, nullable=True)  # JSON string of preferences
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_activity = db.Column(db.DateTime, nullable=True)
    
    # Foreign key to blog if relevant
    blog_id = db.Column(db.Integer, db.ForeignKey('blog.id'), nullable=True)
    blog = db.relationship('Blog', backref=db.backref('subscribers', lazy=True))
    
    def __repr__(self):
        return f"<Subscriber {self.email}>"
    
    def get_preferences(self):
        """Returns preferences as a Python dict"""
        if not self.preferences:
            return {}
        try:
            return json.loads(self.preferences)
        except Exception:
            return {}
    
    def set_preferences(self, preferences_dict):
        """Sets preferences from a Python dict"""
        self.preferences = json.dumps(preferences_dict)

class Newsletter(db.Model):
    """Model for newsletter campaigns"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    content_html = db.Column(db.Text, nullable=False)
    content_text = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='draft')  # draft, scheduled, sent, cancelled
    scheduled_for = db.Column(db.DateTime, nullable=True)
    sent_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Campaign metrics
    recipients_count = db.Column(db.Integer, default=0)
    open_count = db.Column(db.Integer, default=0)
    click_count = db.Column(db.Integer, default=0)
    bounce_count = db.Column(db.Integer, default=0)
    unsubscribe_count = db.Column(db.Integer, default=0)
    
    # Foreign key to blog if relevant
    blog_id = db.Column(db.Integer, db.ForeignKey('blog.id'), nullable=True)
    blog = db.relationship('Blog', backref=db.backref('newsletters', lazy=True))
    
    def __repr__(self):
        return f"<Newsletter {self.title}>"

class NewsletterConfig(db.Model):
    """Model for newsletter configuration settings"""
    id = db.Column(db.Integer, primary_key=True)
    blog_id = db.Column(db.Integer, db.ForeignKey('blog.id'), nullable=False, unique=True)
    enabled = db.Column(db.Boolean, default=False)
    frequency = db.Column(db.String(20), default='weekly')  # daily, weekly, monthly
    send_day = db.Column(db.Integer, default=1)  # 0-6 for weekly (Monday=0), 1-31 for monthly
    send_time = db.Column(db.String(5), default='10:00')  # HH:MM format
    template_id = db.Column(db.String(100), nullable=True)  # EmailOctopus template ID if used
    from_name = db.Column(db.String(100), nullable=True)
    from_email = db.Column(db.String(255), nullable=True)
    reply_to = db.Column(db.String(255), nullable=True)
    
    # Email service settings
    email_octopus_api_key = db.Column(db.String(255), nullable=True)
    email_octopus_list_id = db.Column(db.String(255), nullable=True)
    aws_ses_region = db.Column(db.String(50), default='us-east-1')
    
    # Additional settings as JSON
    settings = db.Column(db.Text, nullable=True)  # JSON string of additional settings
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Define relationship with Blog
    blog = db.relationship('Blog', backref=db.backref('newsletter_config', uselist=False))
    
    def __repr__(self):
        return f"<NewsletterConfig {self.blog.name}>"
    
    def get_settings(self):
        """Returns settings as a Python dict"""
        if self.settings:
            try:
                return json.loads(self.settings)
            except Exception:
                return {}
        return {}
    
    def set_settings(self, settings_dict):
        """Sets settings from a Python dict"""
        self.settings = json.dumps(settings_dict)

class ImageLibrary(db.Model):
    """Model for storing images for reuse across articles"""
    id = db.Column(db.Integer, primary_key=True)
    blog_id = db.Column(db.Integer, db.ForeignKey('blog.id'), nullable=False)
    title = db.Column(db.String(255), nullable=True)
    url = db.Column(db.String(512), nullable=False)
    thumbnail_url = db.Column(db.String(512), nullable=True)
    width = db.Column(db.Integer, nullable=True)
    height = db.Column(db.Integer, nullable=True)
    source = db.Column(db.String(50), nullable=True)  # unsplash, google, upload
    source_id = db.Column(db.String(100), nullable=True)  # original ID from source
    attribution = db.Column(db.String(255), nullable=True)  # attribution text
    attribution_url = db.Column(db.String(512), nullable=True)  # attribution URL
    tags = db.Column(db.Text, nullable=True)  # JSON string of tags
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    image_metadata = db.Column(db.Text, nullable=True)  # JSON string of additional metadata
    
    # Define relationship with Blog
    blog = db.relationship('Blog', backref=db.backref('image_library', lazy=True))
    
    def __repr__(self):
        return f"<ImageLibrary {self.title or self.url[:30]}>"
    
    def get_tags(self):
        """Returns tags as a Python list"""
        if self.tags:
            return json.loads(self.tags)
        return []
    
    def set_tags(self, tags_list):
        """Sets tags from a Python list"""
        self.tags = json.dumps(tags_list)
    
    def get_metadata(self):
        """Returns metadata as a Python dict"""
        if self.image_metadata:
            try:
                return json.loads(self.image_metadata)
            except Exception:
                return {}
        return {}
    
    def set_metadata(self, metadata_dict):
        """Sets metadata from a Python dict"""
        self.image_metadata = json.dumps(metadata_dict)

class AutomationRule(db.Model):
    """Content automation rules"""
    id = db.Column(db.Integer, primary_key=True)
    blog_id = db.Column(db.Integer, db.ForeignKey('blog.id'))
    name = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    
    # Content Generation Settings
    writing_style = db.Column(db.String(50), default='informative')  # informative, conversational, professional, storytelling, persuasive
    content_length = db.Column(db.String(50), default='medium')  # short, medium, long
    
    # Publishing Settings
    publishing_days = db.Column(db.String(255), default='0,1,2,3,4,5,6')  # Days of week (0=Monday, 6=Sunday)
    publishing_time = db.Column(db.String(50), default='12:00')  # Time of day for publishing
    posts_per_day = db.Column(db.Integer, default=1)  # Number of posts to publish per day
    
    # Topic Selection Criteria
    topic_min_score = db.Column(db.Float, default=0.7)  # Minimum topic score to consider
    categories = db.Column(db.Text, nullable=True)  # JSON list of categories to publish to
    
    # Auto-scheduling Settings
    auto_enable_topics = db.Column(db.Boolean, default=False)  # Auto-approve topics
    auto_promote_content = db.Column(db.Boolean, default=True)  # Auto-promote to social media
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Define relationship with Blog
    blog = db.relationship('Blog', backref=db.backref('automation_rules', lazy=True))
    
    def get_categories(self):
        """Returns categories as a Python list"""
        if self.categories:
            return json.loads(self.categories)
        return []
    
    def set_categories(self, categories_list):
        """Sets categories from a Python list"""
        self.categories = json.dumps(categories_list)
    
    def get_publishing_days(self):
        """Returns publishing days as a list of integers"""
        if self.publishing_days:
            return [int(day) for day in self.publishing_days.split(',')]
        return [0, 1, 2, 3, 4, 5, 6]  # Default to all days
    
    def set_publishing_days(self, days_list):
        """Sets publishing days from a list of integers"""
        self.publishing_days = ','.join([str(day) for day in days_list])