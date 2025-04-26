from app import db
from datetime import datetime, timedelta
import json
from sqlalchemy.ext.hybrid import hybrid_property
from typing import List, Optional, Dict, Any
import os

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

class Article(db.Model):
    """Model for article content with long paragraphs"""
    id = db.Column(db.Integer, primary_key=True)
    blog_id = db.Column(db.Integer, db.ForeignKey('blog.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)  # Full article content
    excerpt = db.Column(db.Text, nullable=True)  # Article excerpt/summary
    status = db.Column(db.String(50), default="draft")  # draft, ready, published, archived
    post_id = db.Column(db.Integer, nullable=True)  # WordPress post ID if published
    category_id = db.Column(db.Integer, nullable=True)  # Category ID
    tags = db.Column(db.Text, nullable=True)  # JSON string of tags
    token_count = db.Column(db.Integer, nullable=True)  # Total token count
    paragraph_count = db.Column(db.Integer, nullable=True)  # Number of paragraphs
    metrics_data = db.Column(db.Text, nullable=True)  # JSON string of metrics
    featured_image_url = db.Column(db.String(512), nullable=True)  # URL to featured image
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = db.Column(db.DateTime, nullable=True)  # When the article was published
    
    # Define relationship with Blog
    blog = db.relationship('Blog', backref=db.backref('articles', lazy=True))
    
    def __repr__(self):
        return f"<Article {self.title} - {self.status}>"
    
    def get_tags(self):
        """Returns tags as a Python list"""
        if self.tags:
            return json.loads(self.tags)
        return []
    
    def set_tags(self, tags_list):
        """Sets tags from a Python list"""
        self.tags = json.dumps(tags_list)
    
    def get_metrics(self):
        """Returns metrics as a Python dict"""
        if self.metrics_data:
            return json.loads(self.metrics_data)
        return {}
    
    def set_metrics(self, metrics_dict):
        """Sets metrics from a Python dict"""
        self.metrics_data = json.dumps(metrics_dict)

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

class SystemSettings(db.Model):
    """Model for system-wide settings"""
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), nullable=False, unique=True)
    value = db.Column(db.Text, nullable=True)
    description = db.Column(db.String(255), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """Get a setting value by key with optional default"""
        setting = cls.query.filter_by(key=key).first()
        if setting and setting.value:
            try:
                return json.loads(setting.value)
            except:
                return setting.value
        return default
    
    @classmethod
    def set(cls, key: str, value: Any, description: str = None) -> 'SystemSettings':
        """Set a setting value by key"""
        setting = cls.query.filter_by(key=key).first()
        
        if not setting:
            setting = cls(key=key, description=description)
            
        if isinstance(value, (dict, list, set, tuple)):
            setting.value = json.dumps(value)
        else:
            setting.value = str(value)
            
        db.session.add(setting)
        db.session.commit()
        return setting
    
    @classmethod
    def get_publishing_times(cls) -> List[str]:
        """Get the default publishing times"""
        times = cls.get('default_publishing_times', ["08:00", "12:00", "16:00", "20:00"])
        return sorted(times)  # Ensure the times are sorted
    
    @classmethod
    def get_articles_per_day(cls) -> int:
        """Get the default number of articles per day"""
        return int(cls.get('default_articles_per_day', 4))


class Notification(db.Model):
    """Model for system notifications"""
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)  # info, warning, error, success
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    is_email_sent = db.Column(db.Boolean, default=False)
    blog_id = db.Column(db.Integer, db.ForeignKey('blog.id'), nullable=True)
    content_id = db.Column(db.Integer, db.ForeignKey('content_log.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Define relationships
    blog = db.relationship('Blog', backref=db.backref('notifications', lazy=True))
    content = db.relationship('ContentLog', backref=db.backref('notifications', lazy=True))
    
    def __repr__(self):
        return f"<Notification {self.type} - {self.title}>"


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
    description = db.Column(db.Text, nullable=True)  # Added description field
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


class ImageLibrary(db.Model):
    """Model for storing saved images"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=True)
    url = db.Column(db.String(512), nullable=False)
    thumbnail_url = db.Column(db.String(512), nullable=True)
    source = db.Column(db.String(50), nullable=True)  # unsplash, google, upload, etc.
    source_id = db.Column(db.String(100), nullable=True)
    width = db.Column(db.Integer, nullable=True)
    height = db.Column(db.Integer, nullable=True)
    attribution = db.Column(db.String(255), nullable=True)  # Attribution text
    attribution_url = db.Column(db.String(512), nullable=True)  # Attribution link
    tags = db.Column(db.Text, nullable=True)  # JSON string of tags
    image_metadata = db.Column(db.Text, nullable=True)  # JSON string of additional metadata
    blog_id = db.Column(db.Integer, db.ForeignKey('blog.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Define relationship with Blog if applicable
    blog = db.relationship('Blog', backref=db.backref('images', lazy=True))
    
    def __repr__(self):
        return f"<ImageLibrary {self.title or 'untitled'}>"
    
    def get_tags(self):
        """Returns tags as a Python list"""
        if self.tags:
            return json.loads(self.tags)
        return []
    
    def set_tags(self, tags_list):
        """Sets tags from a Python list"""
        self.tags = json.dumps(tags_list)
    
    def get_image_metadata(self):
        """Returns image metadata as a Python dict"""
        if self.image_metadata:
            return json.loads(self.image_metadata)
        return {}
    
    def set_image_metadata(self, metadata_dict):
        """Sets image metadata from a Python dict"""
        self.image_metadata = json.dumps(metadata_dict)




class SocialMediaTemplate(db.Model):
    """Model for storing social media content templates"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    platform = db.Column(db.String(50), nullable=False)  # facebook, twitter, linkedin, instagram
    type = db.Column(db.String(50), nullable=False)  # article_promotion, quote, question, etc.
    content = db.Column(db.Text, nullable=False)
    hashtags = db.Column(db.Text, nullable=True)  # JSON string of hashtags
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<SocialMediaTemplate {self.name} - {self.platform}>"
    
    def get_hashtags(self):
        """Returns hashtags as a Python list"""
        if self.hashtags:
            return json.loads(self.hashtags)
        return []
        
    def set_hashtags(self, hashtags_list):
        """Sets hashtags from a Python list"""
        self.hashtags = json.dumps(hashtags_list)


class ScheduledSocialPost(db.Model):
    """Model for scheduled social media posts"""
    id = db.Column(db.Integer, primary_key=True)
    content_id = db.Column(db.Integer, db.ForeignKey('content_log.id'), nullable=True)
    platform = db.Column(db.String(50), nullable=False)  # facebook, twitter, linkedin, instagram
    content = db.Column(db.Text, nullable=False)
    hashtags = db.Column(db.Text, nullable=True)  # JSON string of hashtags
    image_url = db.Column(db.String(255), nullable=True)
    scheduled_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(50), default="scheduled")  # scheduled, published, error
    result_data = db.Column(db.Text, nullable=True)  # JSON string of API response data
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Define relationship with ContentLog (optional association)
    content = db.relationship('ContentLog', backref=db.backref('scheduled_social_posts', lazy=True))
    
    def __repr__(self):
        return f"<ScheduledSocialPost {self.platform} - {self.scheduled_date}>"
    
    def get_hashtags(self):
        """Returns hashtags as a Python list"""
        if self.hashtags:
            return json.loads(self.hashtags)
        return []
        
    def set_hashtags(self, hashtags_list):
        """Sets hashtags from a Python list"""
        self.hashtags = json.dumps(hashtags_list)
        
    def get_result_data(self):
        """Returns result data as a Python dict"""
        if self.result_data:
            return json.loads(self.result_data)
        return {}
        
    def set_result_data(self, result_dict):
        """Sets result data from a Python dict"""
        self.result_data = json.dumps(result_dict)


class SocialMediaScheduleSettings(db.Model):
    """Model for storing social media publishing schedule settings"""
    id = db.Column(db.Integer, primary_key=True)
    blog_id = db.Column(db.Integer, db.ForeignKey('blog.id'), nullable=True)  # NULL means global settings
    optimal_times = db.Column(db.Text, nullable=True)  # JSON string of optimal posting times
    platform_settings = db.Column(db.Text, nullable=True)  # JSON string of platform-specific settings
    auto_distribute = db.Column(db.Boolean, default=True)
    platform_rotation = db.Column(db.Boolean, default=True)
    content_variety = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Define relationship with Blog (optional)
    blog = db.relationship('Blog', backref=db.backref('social_schedule_settings', uselist=False))
    
    def __repr__(self):
        blog_name = self.blog.name if self.blog else "Global"
        return f"<SocialMediaScheduleSettings {blog_name}>"
    
    def get_optimal_times(self):
        """Returns optimal times as a Python list"""
        if self.optimal_times:
            return json.loads(self.optimal_times)
        return ["08:00", "12:00", "16:00", "20:00"]
        
    def set_optimal_times(self, times_list):
        """Sets optimal times from a Python list"""
        self.optimal_times = json.dumps(times_list)
        
    def get_platform_settings(self):
        """Returns platform settings as a Python dict"""
        if self.platform_settings:
            return json.loads(self.platform_settings)
        return {
            "facebook": {"frequency": 3, "days": ["mon", "wed", "fri"]},
            "twitter": {"frequency": 5, "days": ["mon", "tue", "wed", "thu", "fri"]},
            "linkedin": {"frequency": 2, "days": ["tue", "thu"]},
            "instagram": {"frequency": 2, "days": ["mon", "fri"]}
        }
        
    def set_platform_settings(self, settings_dict):
        """Sets platform settings from a Python dict"""
        self.platform_settings = json.dumps(settings_dict)


class SocialMediaPostMetrics(db.Model):
    """Model for storing social media post performance metrics"""
    id = db.Column(db.Integer, primary_key=True)
    content_id = db.Column(db.Integer, db.ForeignKey('content_log.id'), nullable=True)
    scheduled_post_id = db.Column(db.Integer, db.ForeignKey('scheduled_social_post.id'), nullable=True)
    platform = db.Column(db.String(50), nullable=False)  # facebook, twitter, linkedin, instagram
    post_url = db.Column(db.String(255), nullable=True)
    post_id = db.Column(db.String(100), nullable=True)  # ID from the social media platform
    likes = db.Column(db.Integer, default=0)
    comments = db.Column(db.Integer, default=0)
    shares = db.Column(db.Integer, default=0)
    clicks = db.Column(db.Integer, default=0)
    impressions = db.Column(db.Integer, default=0)
    engagement_rate = db.Column(db.Float, default=0.0)  # Percentage
    post_date = db.Column(db.DateTime, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    raw_data = db.Column(db.Text, nullable=True)  # JSON string of additional metrics
    
    # Define relationships
    content = db.relationship('ContentLog', backref=db.backref('social_metrics', lazy=True))
    scheduled_post = db.relationship('ScheduledSocialPost', backref=db.backref('metrics', lazy=True))
    
    def __repr__(self):
        return f"<SocialMediaPostMetrics {self.platform} - likes:{self.likes}, shares:{self.shares}>"
    
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

class Content(db.Model):
    """Model for simple content storage and editing"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    topic = db.Column(db.String(255), nullable=True)
    body = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='draft')  # draft / published
    blog_id = db.Column(db.Integer, db.ForeignKey('blog.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = db.Column(db.DateTime, nullable=True)
    featured_image_url = db.Column(db.String(500), nullable=True)
    wordpress_post_id = db.Column(db.Integer, nullable=True)
    
    # Define relationship with Blog
    blog = db.relationship('Blog', backref=db.backref('contents', lazy=True))
    
    def __repr__(self):
        return f"<Content {self.title} - {self.status}>"
    
    def to_dict(self):
        """Convert content to dictionary"""
        return {
            'id': self.id,
            'blog_id': self.blog_id,
            'title': self.title,
            'topic': self.topic,
            'body': self.body,
            'status': self.status,
            'featured_image_url': self.featured_image_url,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'wordpress_post_id': self.wordpress_post_id
        }
        
    def publish(self):
        """Mark content as published"""
        self.status = 'published'
        self.published_at = datetime.utcnow()
        return True


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
    unsubscribe_count = db.Column(db.Integer, default=0)
    
    # Template and design settings
    template_id = db.Column(db.String(100), nullable=True)
    design_settings = db.Column(db.Text, nullable=True)  # JSON string of design settings
    
    # Foreign key to blog if this is a blog-specific newsletter
    blog_id = db.Column(db.Integer, db.ForeignKey('blog.id'), nullable=True)
    blog = db.relationship('Blog', backref=db.backref('newsletters', lazy=True))
    
    def __repr__(self):
        return f"<Newsletter {self.title}>"
    
    def get_design_settings(self):
        """Returns design settings as a Python dict"""
        if not self.design_settings:
            return {}
        try:
            return json.loads(self.design_settings)
        except Exception:
            return {}
    
    def set_design_settings(self, settings_dict):
        """Sets design settings from a Python dict"""
        self.design_settings = json.dumps(settings_dict)

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
        """Returns additional settings as a Python dict"""
        if not self.settings:
            return {}
        try:
            return json.loads(self.settings)
        except Exception:
            return {}
    
    def set_settings(self, settings_dict):
        """Sets additional settings from a Python dict"""
        self.settings = json.dumps(settings_dict)

class AutomationRule(db.Model):
    """Model for content automation rules"""
    id = db.Column(db.Integer, primary_key=True)
    blog_id = db.Column(db.Integer, db.ForeignKey('blog.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)  # Reverted back to is_active to match database schema
    
    # Schedule settings
    days_of_week = db.Column(db.String(20), default="0,1,2,3,4")  # Monday=0, Sunday=6
    publishing_time = db.Column(db.String(5), default="12:00")  # Default publishing time in format HH:MM
    time_slots = db.Column(db.Text, nullable=True)  # JSON string of time slots
    posts_per_day = db.Column(db.Integer, default=1)
    min_interval_hours = db.Column(db.Integer, default=4)  # Minimum hours between posts
    
    # Content settings
    min_word_count = db.Column(db.Integer, default=1200)
    max_word_count = db.Column(db.Integer, default=1600)
    content_length = db.Column(db.String(20), default="medium")  # short, medium, long
    paragraph_count = db.Column(db.Integer, default=4)  # Number of paragraphs for paragraph-based generation
    use_paragraph_mode = db.Column(db.Boolean, default=False)  # Whether to use paragraph-based generation
    content_tone = db.Column(db.String(50), default="informative")  # Changed back to content_tone to match database schema
    topic_categories = db.Column(db.Text, nullable=True)  # JSON string of category IDs to focus on
    topic_min_score = db.Column(db.Float, default=0.7)  # Minimum score for auto-enabling topics
    
    # Approval settings
    require_approval = db.Column(db.Boolean, default=False)
    
    # Publication settings
    publish_immediately = db.Column(db.Boolean, default=False)
    apply_featured_image = db.Column(db.Boolean, default=True)
    auto_enable_topics = db.Column(db.Boolean, default=True)  # Automatically enable topics that meet minimum score
    auto_promote_content = db.Column(db.Boolean, default=False)  # Automatically promote content to social media
    
    # Priority (higher number = higher priority)
    priority = db.Column(db.Integer, default=10)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Define relationship with Blog
    blog = db.relationship('Blog', backref=db.backref('automation_rules', lazy=True))
    
    def __repr__(self):
        status = "active" if self.is_active else "inactive"
        return f"<AutomationRule {self.name} ({status})>"
    
    def get_time_slots(self):
        """Returns time slots as a Python list"""
        if self.time_slots:
            return json.loads(self.time_slots)
        return []
    
    def set_time_slots(self, slots_list):
        """Sets time slots from a Python list"""
        self.time_slots = json.dumps(slots_list)
    
    def get_topic_categories(self):
        """Returns topic categories as a Python list"""
        if self.topic_categories:
            return json.loads(self.topic_categories)
        return []
    
    def set_topic_categories(self, categories_list):
        """Sets topic categories from a Python list"""
        self.topic_categories = json.dumps(categories_list)
    
    def get_days_list(self):
        """Returns days of week as a Python list of integers"""
        if not self.days_of_week:
            return []
        try:
            return [int(day) for day in self.days_of_week.split(',')]
        except ValueError:
            return []
    
    def set_days_list(self, days_list):
        """Sets days of week from a Python list of integers"""
        self.days_of_week = ','.join([str(day) for day in days_list])
        
    # Alias methods for template compatibility
    def get_publishing_days(self):
        """Alias for get_days_list, returns days of week as a Python list of integers"""
        return self.get_days_list()
        
    def set_publishing_days(self, days_list):
        """Alias for set_days_list, sets days of week from a Python list of integers"""
        self.set_days_list(days_list)
        
    def get_categories(self):
        """Alias for get_topic_categories, returns categories as a Python list"""
        return self.get_topic_categories()
        
    def set_categories(self, categories_list):
        """Alias for set_topic_categories, sets categories from a Python list"""
        self.set_topic_categories(categories_list)