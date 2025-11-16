import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys and Configuration
class Config:
    # OpenRouter API Configuration
    OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")  # Direct Anthropic API fallback
    
    # Image API Configuration
    UNSPLASH_API_KEY = os.environ.get("UNSPLASH_API_KEY")
    BING_SEARCH_API_KEY = os.environ.get("BING_SEARCH_API_KEY")  # Azure Cognitive Services
    GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "AIzaSyAqIRfjsdiZrmDqap0Je8-YZPISawTsQSY")
    GOOGLE_CSE_ID = os.environ.get("GOOGLE_CSE_ID", "10400bb2536244d91")
    
    # SEO API Configuration
    SERPAPI_KEY = os.environ.get("SERPAPI_KEY", "57d393880136bab7d3159bf1d56d251fa3945bf56e6d1fa3448199e7c10e069c")
    
    # Social Media API Configuration
    FACEBOOK_APP_ID = os.environ.get("FACEBOOK_APP_ID")
    FACEBOOK_APP_SECRET = os.environ.get("FACEBOOK_APP_SECRET")
    TWITTER_API_KEY = os.environ.get("TWITTER_API_KEY")
    TWITTER_API_SECRET = os.environ.get("TWITTER_API_SECRET")
    LINKEDIN_CLIENT_ID = os.environ.get("LINKEDIN_CLIENT_ID")
    LINKEDIN_CLIENT_SECRET = os.environ.get("LINKEDIN_CLIENT_SECRET")
    
    # Application Configuration
    ARTICLES_PER_DAY_PER_BLOG = int(os.environ.get("ARTICLES_PER_DAY_PER_BLOG", 4))
    ARTICLE_MIN_LENGTH = int(os.environ.get("ARTICLE_MIN_LENGTH", 1200))
    ARTICLE_MAX_LENGTH = int(os.environ.get("ARTICLE_MAX_LENGTH", 1600))
    PUBLISHING_TIMES = os.environ.get("PUBLISHING_TIMES", "08:00,12:00,16:00,20:00").split(",")
    
    # Default models
    DEFAULT_TOPIC_MODEL = os.environ.get("DEFAULT_TOPIC_MODEL", "deepseek/deepseek-chat-v3-0324:free")
    DEFAULT_CONTENT_MODEL = os.environ.get("DEFAULT_CONTENT_MODEL", "deepseek/deepseek-chat-v3-0324:free")
    DEFAULT_SOCIAL_MODEL = os.environ.get("DEFAULT_SOCIAL_MODEL", "deepseek/deepseek-chat-v3-0324:free")
    
    # Database Retention (days)
    LOG_RETENTION_DAYS = int(os.environ.get("LOG_RETENTION_DAYS", 30))
    
    # Scheduler Configuration
    SCHEDULER_API_ENABLED = True
