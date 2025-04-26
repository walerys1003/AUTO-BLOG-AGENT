"""
SEO Topic Generator combining Google Trends and SerpAPI data
"""
import logging
import os
import pandas as pd
from datetime import datetime
from . import trends
from . import serp
from models import ArticleTopic, Blog
from app import db

# Setup logging
logger = logging.getLogger(__name__)

# Categories for blogs
DEFAULT_CATEGORIES = ['medycyna', 'transport', 'IT', 'biznes', 'technologia', 'zdrowie', 'finanse', 'edukacja', 'rozrywka']

# CSV file path for saving topics
CSV_FILE = os.path.join(os.getcwd(), 'data', 'tematy_blogowe.csv')

# Make sure the data directory exists
os.makedirs(os.path.dirname(CSV_FILE), exist_ok=True)

def generate_titles(keywords, category):
    """
    Generate article titles from keywords for a specific category
    
    Args:
        keywords: List of keywords/phrases
        category: Category name
        
    Returns:
        list: List of generated titles
    """
    titles = []
    
    # Various title templates for diversity
    templates = [
        f"Najlepsze porady dotyczące {{keyword}} w kategorii {category}",
        f"Jak {{keyword}} wpływa na rozwój w branży {category}?",
        f"{{keyword}} - wszystko co musisz wiedzieć w {category}",
        f"{category.capitalize()}: {{keyword}} - praktyczny poradnik",
        f"10 sposobów wykorzystania {{keyword}} w {category}"
    ]
    
    # Generate titles using different templates
    for keyword in keywords:
        for template in templates[:2]:  # Limit to first 2 templates to avoid too many titles
            title = template.format(keyword=keyword)
            titles.append(title)
    
    return titles

def prioritize_suggestions(titles, limit=5):
    """
    Prioritize title suggestions
    
    Args:
        titles: List of title suggestions
        limit: Maximum number of titles to return
        
    Returns:
        list: List of prioritized titles
    """
    return titles[:limit]

def save_to_csv(data):
    """
    Save topics data to CSV file
    
    Args:
        data: List of dictionaries with topic data
        
    Returns:
        bool: True if saved successfully, False otherwise
    """
    try:
        df = pd.DataFrame(data)
        
        # Check if file exists and append data
        try:
            if os.path.exists(CSV_FILE):
                existing_df = pd.read_csv(CSV_FILE)
                df = pd.concat([existing_df, df], ignore_index=True)
        except Exception as e:
            logger.warning(f"Error reading existing CSV: {str(e)}")
        
        # Save data to CSV
        df.to_csv(CSV_FILE, index=False)
        logger.info(f"Topics saved to {CSV_FILE}")
        return True
    except Exception as e:
        logger.error(f"Error saving to CSV: {str(e)}")
        return False

def save_to_database(data, auto_approve=True):
    """
    Save topics to database as ArticleTopic objects
    
    Args:
        data: List of dictionaries with topic data
        auto_approve: Whether to automatically approve topics (default: True)
        
    Returns:
        int: Number of topics saved to database
    """
    try:
        # Get all active blogs
        blogs = Blog.query.filter_by(active=True).all()
        if not blogs:
            logger.warning("No active blogs found, cannot save topics to database")
            return 0
        
        # Map category names to blog IDs (simple mapping for demo)
        blog_categories = {}
        for blog in blogs:
            # Extract first word from blog name as category
            category = blog.name.split()[0].lower()
            blog_categories[category] = blog.id
        
        # Default to first blog if no matching category
        default_blog_id = blogs[0].id
        
        saved_count = 0
        
        for item in data:
            category = item.get('Kategoria', '').lower()
            title = item.get('Tytuł', '')
            
            if not title:
                continue
            
            # Find matching blog_id or use default
            blog_id = blog_categories.get(category, default_blog_id)
            
            # Create new ArticleTopic
            topic = ArticleTopic(
                title=title,
                blog_id=blog_id,
                status='approved' if auto_approve else 'pending',
                created_at=datetime.now()
            )
            
            db.session.add(topic)
            saved_count += 1
        
        # Commit changes to database
        db.session.commit()
        logger.info(f"Saved {saved_count} topics to database")
        return saved_count
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving topics to database: {str(e)}")
        return 0

def analyze_and_generate_topics(categories=None, num_trends=10, questions_per_trend=2, save_csv=True, save_db=True):
    """
    Analyze SEO data and generate blog topics
    
    Args:
        categories: List of categories (default: DEFAULT_CATEGORIES)
        num_trends: Number of trends to fetch (default: 10)
        questions_per_trend: Number of questions to fetch per trend (default: 2)
        save_csv: Whether to save topics to CSV (default: True)
        save_db: Whether to save topics to database (default: True)
        
    Returns:
        dict: Dictionary with generated topics by category
    """
    logger.info("Starting SEO analysis and topic generation")
    
    # Use default categories if none provided
    if categories is None:
        categories = DEFAULT_CATEGORIES
    
    # Get trending searches from Google Trends
    google_trends = trends.get_daily_trends(country='poland', limit=num_trends)
    logger.info(f"Found {len(google_trends)} trending searches: {google_trends}")
    
    all_data = []
    results_by_category = {}
    
    for category in categories:
        logger.info(f"Generating topics for category: {category}")
        
        combined_keywords = []
        
        # Process each trend and get related questions
        for trend in google_trends:
            combined_keywords.append(trend)
            
            # Get related questions from SerpAPI
            related_questions = serp.get_related_questions(
                trend, 
                limit=questions_per_trend
            )
            combined_keywords.extend(related_questions)
        
        # Generate titles from keywords
        titles = generate_titles(combined_keywords, category)
        
        # Prioritize suggestions
        prioritized = prioritize_suggestions(titles)
        results_by_category[category] = prioritized
        
        # Prepare data for CSV and database
        for title in prioritized:
            all_data.append({
                'Data': datetime.now().strftime('%Y-%m-%d'),
                'Kategoria': category,
                'Tytuł': title
            })
        
        # Log generated topics
        logger.info(f"Generated {len(prioritized)} topics for {category}")
        for title in prioritized:
            logger.info(f"- {title}")
    
    # Save data to CSV if requested
    if save_csv and all_data:
        save_to_csv(all_data)
    
    # Save data to database if requested
    if save_db and all_data:
        save_to_database(all_data)
    
    return results_by_category

def daily_analysis_job():
    """
    Run daily analysis job to generate topics
    This function can be scheduled to run daily
    """
    logger.info("Running daily SEO analysis job")
    results = analyze_and_generate_topics()
    logger.info(f"Daily analysis job completed. Generated topics for {len(results)} categories")
    return results