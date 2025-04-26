"""
SEO Analyzer

Main entry point for SEO functionality
"""
import logging
from . import trends, serp, topic_generator, scheduler

# Setup logging
logger = logging.getLogger(__name__)

# Create the main analyzer object for importing
seo_analyzer = {
    'trends': trends,
    'serp': serp,
    'topics': topic_generator
}

def initialize_seo_module():
    """
    Initialize SEO module and start scheduler
    
    This function should be called during application startup
    """
    logger.info("Initializing SEO module")
    
    try:
        # Test Google Trends API
        test_trends = trends.get_daily_trends(limit=3)
        logger.info(f"Google Trends API test successful. Found {len(test_trends)} trends")
        
        # Test SerpAPI
        if test_trends:
            test_questions = serp.get_related_questions(test_trends[0], limit=2)
            logger.info(f"SerpAPI test successful. Found {len(test_questions)} related questions")
        
        # Initialize scheduler
        scheduler.init_scheduler()
        
        logger.info("SEO module initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing SEO module: {str(e)}")
        return False

def analyze_topics_now(categories=None, save_to_db=True):
    """
    Run SEO analysis and topic generation immediately
    
    Args:
        categories: List of categories (if None, uses defaults)
        save_to_db: Whether to save generated topics to database
        
    Returns:
        dict: Dictionary with generated topics by category
    """
    logger.info("Running immediate SEO analysis")
    return topic_generator.analyze_and_generate_topics(
        categories=categories,
        save_db=save_to_db
    )