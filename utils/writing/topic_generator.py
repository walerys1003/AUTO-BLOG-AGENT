"""
Topic Generator Utility Module
"""
import json
import random
import logging
from datetime import datetime, timedelta
import re

import requests
import anthropic
from anthropic import Anthropic
from app import db
from models import ArticleTopic
from utils.seo import seo_analyzer
import os

logger = logging.getLogger(__name__)

# Define topic structures based on blog categories
TOPIC_STRUCTURES = {
    "technology": [
        "The Future of {technology}: What's Coming in {year}",
        "{number} {technology} Trends That Will Transform {industry}",
        "How {technology} is Revolutionizing the {industry} Industry",
        "Why {technology} Matters for Your Business in {year}",
        "The Complete Guide to {technology} for Beginners",
    ],
    "health": [
        "{number} Ways to Improve Your {health_aspect} Naturally",
        "The Science Behind {health_technique}: Does It Really Work?",
        "How to Optimize Your {health_aspect} in Just {number} Minutes a Day",
        "{health_technique} vs {alternative_technique}: Which is Better for {goal}?",
        "The Ultimate Guide to {health_aspect} for {demographic}",
    ],
    "finance": [
        "How to Build a {finance_goal} Strategy That Actually Works",
        "{number} {finance_method} Tips Every {demographic} Should Know",
        "The Truth About {finance_topic}: What the Experts Won't Tell You",
        "Why {finance_method} Is the Key to {finance_goal} in {year}",
        "From {starting_point} to {goal}: A {timeframe} {finance_goal} Plan",
    ],
    "marketing": [
        "{number} {marketing_tactic} Strategies That Drove {result} in {timeframe}",
        "How to Create a {marketing_channel} Strategy That Converts",
        "The Ultimate Guide to {marketing_tactic} for {business_type}",
        "Why Your {marketing_tactic} Strategy Isn't Working (And How to Fix It)",
        "{marketing_tactic} vs {alternative_tactic}: Which Works Better for {goal}?",
    ],
    "travel": [
        "{number} Hidden Gems in {destination} Most Tourists Miss",
        "How to Experience {destination} Like a Local: The Ultimate Guide",
        "The Best Time to Visit {destination}: A Seasonal Guide",
        "{destination} on a Budget: How to Travel for Less Than ${amount}",
        "The Ultimate {timeframe} Itinerary for {destination}",
    ],
    "general": [
        "The Ultimate Guide to {topic} in {year}",
        "{number} {topic} Techniques That Will Change Your {area}",
        "How to Master {topic} in {timeframe}",
        "Why {topic} Matters More Than Ever in {year}",
        "{topic} 101: Everything You Need to Know to Get Started",
    ]
}

# Define topic variables for templates
TOPIC_VARIABLES = {
    "technology": ["artificial intelligence", "blockchain", "cloud computing", "cybersecurity", "data science", 
                  "machine learning", "augmented reality", "internet of things", "5G", "robotics"],
    "industry": ["healthcare", "finance", "retail", "education", "manufacturing", "transportation", "agriculture", 
                "energy", "entertainment", "real estate"],
    "health_aspect": ["sleep", "nutrition", "fitness", "mental health", "immune system", "digestion", "energy levels", 
                     "skin health", "heart health", "brain function"],
    "health_technique": ["intermittent fasting", "meditation", "yoga", "high-intensity interval training", "ketogenic diet", 
                        "plant-based diet", "mindfulness", "strength training", "cardio", "supplements"],
    "alternative_technique": ["traditional diet", "steady-state cardio", "weightlifting", "paleo diet", "therapy", 
                             "medication", "surgery", "conventional medicine", "rest days", "stretching"],
    "goal": ["weight loss", "muscle gain", "better sleep", "stress reduction", "productivity", "retirement", 
            "financial freedom", "passive income", "work-life balance", "mental clarity"],
    "demographic": ["beginners", "professionals", "entrepreneurs", "parents", "seniors", "students", "millennials", 
                   "Gen Z", "remote workers", "busy professionals"],
    "finance_goal": ["retirement", "investment", "saving", "passive income", "wealth building", "tax optimization", 
                    "debt reduction", "budgeting", "financial independence", "credit improvement"],
    "finance_method": ["index investing", "real estate", "cryptocurrency", "side hustle", "budgeting", "tax planning", 
                      "debt snowball", "automation", "dividend investing", "value investing"],
    "finance_topic": ["stock market", "real estate investing", "cryptocurrency", "retirement planning", "index funds", 
                     "401(k)", "IRA", "life insurance", "estate planning", "tax deductions"],
    "starting_point": ["zero savings", "debt", "average income", "good credit", "bad credit", "no experience", 
                      "beginner", "middle class", "minimum wage", "entry-level"],
    "timeframe": ["30-day", "60-day", "90-day", "6-month", "1-year", "5-year", "10-year", "weekend", "weekly", "monthly"],
    "marketing_tactic": ["content marketing", "email marketing", "social media marketing", "SEO", "PPC", "influencer marketing", 
                        "affiliate marketing", "video marketing", "podcast marketing", "SMS marketing"],
    "marketing_channel": ["Instagram", "TikTok", "YouTube", "LinkedIn", "Facebook", "Twitter", "email", "blog", "podcast", "webinar"],
    "alternative_tactic": ["traditional advertising", "print media", "television", "radio", "direct mail", "billboards", 
                          "trade shows", "cold calling", "networking events", "public relations"],
    "business_type": ["small business", "startup", "e-commerce", "local business", "SaaS", "B2B", "B2C", "service business", 
                     "nonprofit", "personal brand"],
    "result": ["500% ROI", "10x revenue", "1 million subscribers", "record sales", "viral growth", "100k followers", 
              "market dominance", "industry recognition", "customer loyalty", "brand awareness"],
    "destination": ["Paris", "Tokyo", "Bali", "New York City", "Thailand", "Italy", "Greece", "Australia", "London", 
                   "Costa Rica", "Mexico City", "Barcelona", "Amsterdam", "Marrakech", "Cape Town"],
    "amount": ["500", "1000", "1500", "2000", "2500", "3000", "3500", "4000", "5000"],
    "topic": ["productivity", "leadership", "communication", "public speaking", "writing", "negotiation", "creativity", 
             "problem-solving", "decision-making", "time management", "design thinking", "project management"],
    "area": ["career", "personal life", "relationships", "business", "education", "health", "finances", "creativity", 
            "productivity", "wellbeing"],
    "number": ["5", "7", "10", "12", "15", "20", "25", "30"],
    "year": ["2024", "2025", "2026"]
}

def get_variable(variable_type):
    """Get a random variable of the specified type"""
    if variable_type in TOPIC_VARIABLES:
        return random.choice(TOPIC_VARIABLES[variable_type])
    return variable_type

def format_topic_template(template):
    """Format a topic template by replacing variables with actual values"""
    # Find all variables in the template - they are in {curly_braces}
    variables = re.findall(r'\{([^}]+)\}', template)
    
    # Replace each variable with a random value from the corresponding list
    for var in variables:
        template = template.replace('{' + var + '}', get_variable(var))
    
    return template

def generate_topics_from_template(category, count=3):
    """Generate topics based on predefined templates for a category"""
    if category not in TOPIC_STRUCTURES:
        category = "general"
    
    templates = TOPIC_STRUCTURES[category]
    
    # Ensure we don't try to generate more topics than we have templates
    count = min(count, len(templates))
    
    # Randomly select templates and format them
    selected_templates = random.sample(templates, count)
    topics = [format_topic_template(template) for template in selected_templates]
    
    return topics

def generate_topics_using_ai(blog_name, blog_category, count=3):
    """Generate topics using AI via OpenRouter or direct anthropic"""
    try:
        # Try to use Anthropic directly if API key is available
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        
        if not api_key:
            # Fallback to manual generation if no API key
            logger.warning("No ANTHROPIC_API_KEY found, falling back to template-based generation")
            return generate_topics_from_template(blog_category, count)
        
        # Create Anthropic client
        client = Anthropic(api_key=api_key)
        
        # Current date information for context
        current_date = datetime.now().strftime("%B %d, %Y")
        current_year = datetime.now().year
        
        # Create prompt for topic generation
        prompt = f"""
        Today's date is {current_date}. I need to generate {count} blog post topics for a blog called "{blog_name}" focused on {blog_category}.

        Each topic should:
        1. Be SEO-friendly and have potential for organic traffic
        2. Be timely and relevant to current trends in {current_year}
        3. Be specific enough to cover in a 1200-1600 word article
        4. Include keywords that have search volume
        5. Be interesting to the target audience interested in {blog_category}

        For each topic, also suggest 3-5 related keywords that should be included in the article.

        Please format your response as a JSON array of objects with the following structure:
        [
            {
                "title": "The topic title formatted as a compelling headline",
                "keywords": ["keyword1", "keyword2", "keyword3"]
            }
        ]

        Generate {count} unique, high-quality topic ideas in this format.
        """
        
        # Send the request to Anthropic
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1000,
            temperature=0.7,
            system="You are an expert SEO content strategist helping to generate blog topics.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Parse the response
        ai_content = response.content[0].text
        
        # Extract JSON from the response
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', ai_content)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find JSON without code blocks
            json_match = re.search(r'\[\s*\{.*\}\s*\]', ai_content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                # Fallback to the entire response
                json_str = ai_content
        
        # Clean up the string to ensure it's valid JSON
        json_str = re.sub(r'(["\]}])\s*(?:[,;])\s*$', r'\1', json_str, flags=re.MULTILINE)
        
        try:
            topic_data = json.loads(json_str)
            
            # Ensure we got a list of topics
            if isinstance(topic_data, list) and len(topic_data) > 0:
                return topic_data
            else:
                logger.warning(f"Invalid topic data format: {type(topic_data)}")
                return generate_topics_from_template(blog_category, count)
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from AI response: {e}")
            logger.debug(f"JSON string attempted to parse: {json_str}")
            return generate_topics_from_template(blog_category, count)
            
    except Exception as e:
        logger.error(f"Error generating topics with AI: {str(e)}")
        return generate_topics_from_template(blog_category, count)

def generate_topics_for_blog(blog, count=3):
    """Generate topics for a specific blog and save them to the database"""
    logger.info(f"Generating {count} topics for blog: {blog.name}")
    
    # Determine the best category match for the blog
    # This would ideally be improved with a more sophisticated categorization algorithm
    categories = ["technology", "health", "finance", "marketing", "travel", "general"]
    
    # Simple matching based on blog name and existing categories
    blog_category = "general"
    blog_name_lower = blog.name.lower()
    
    for category in categories:
        if category in blog_name_lower:
            blog_category = category
            break
    
    # Get trends from SEO analyzer
    trending_topics = seo_analyzer.get_trending_topics(blog_category, limit=3)
    
    # Generate topics using AI (or fallback to templates)
    ai_topics = generate_topics_using_ai(blog.name, blog_category, count)
    
    # Create and save topics to database
    created_topics = []
    for topic_data in ai_topics:
        try:
            # Extract title and keywords
            if isinstance(topic_data, dict):
                title = topic_data.get("title", "")
                keywords = topic_data.get("keywords", [])
            else:
                # If AI returned plain strings instead of dictionaries
                title = str(topic_data)
                keywords = []
            
            # Create new topic
            new_topic = ArticleTopic(
                blog_id=blog.id,
                title=title,
                status="pending",
                created_at=datetime.now()
            )
            
            # Set keywords if available
            if keywords:
                new_topic.set_keywords(keywords)
                
            # Set a relevant category if found in blog categories
            if blog.get_categories():
                new_topic.category = random.choice(blog.get_categories())
            
            # Calculate a score based on keyword relevance and trends
            # This would be more sophisticated in a production system
            new_topic.score = random.uniform(3.0, 9.0)
            
            # Save to database
            db.session.add(new_topic)
            created_topics.append(new_topic)
            
        except Exception as e:
            logger.error(f"Error creating topic: {str(e)}")
    
    # Commit all topics at once
    try:
        db.session.commit()
        logger.info(f"Created {len(created_topics)} topics for {blog.name}")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error committing topics to database: {str(e)}")
        return []
    
    return created_topics