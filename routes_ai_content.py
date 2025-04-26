"""
Routes for AI-Driven Content Strategy

This module provides routes for managing AI-generated content, including:
- Generating topics for categories
- Generating articles from topics
- Managing categories and topics
"""
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy import desc
from models import db, Blog, ArticleTopic, ContentLog, Article
from utils.ai_content_strategy.topic_generator import generate_ai_topics_for_category
from utils.ai_content_strategy.article_generator import generate_article_from_topic

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
ai_content = Blueprint('ai_content', __name__, url_prefix='/ai-content')

# In-memory storage for AI-generated topics
# Format: {"category": ["topic1", "topic2", ...]}
ai_topics: Dict[str, List[str]] = {}


@ai_content.route('/')
def index():
    """AI Content Strategy Dashboard"""
    # Get all blogs for the dropdown
    blogs = Blog.query.all()
    
    # Get recent articles (from database)
    recent_articles = Article.query.order_by(Article.created_at.desc()).limit(10).all()
    
    # Get last updated timestamp
    last_updated = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    return render_template(
        'ai_content/dashboard.html',
        ai_topics=ai_topics,
        blogs=blogs,
        recent_articles=recent_articles,
        last_updated=last_updated
    )


@ai_content.route('/generate-topics', methods=['POST'])
def generate_topics():
    """Generate topics for a category"""
    category = request.form.get('category')
    count = int(request.form.get('count', 20))
    
    if not category:
        flash('Kategoria jest wymagana', 'danger')
        return redirect(url_for('ai_content.index'))
    
    try:
        # Generate topics using AI
        new_topics = generate_ai_topics_for_category(category, count)
        
        # Update in-memory topics store
        if category in ai_topics:
            ai_topics[category].extend(new_topics)
            # Remove duplicates
            ai_topics[category] = list(set(ai_topics[category]))
        else:
            ai_topics[category] = new_topics
        
        flash(f'Wygenerowano {len(new_topics)} nowych tematów dla kategorii "{category}"', 'success')
        return redirect(url_for('ai_content.list_topics', category=category))
        
    except Exception as e:
        logger.error(f"Error generating topics: {str(e)}")
        flash(f'Błąd generowania tematów: {str(e)}', 'danger')
        return redirect(url_for('ai_content.index'))


@ai_content.route('/generate-article', methods=['POST'])
def generate_article():
    """Generate an article for a selected topic"""
    category = request.form.get('category')
    topic = request.form.get('topic')
    blog_id = request.form.get('blog_id')
    
    if not category or not topic:
        flash('Kategoria i temat są wymagane', 'danger')
        return redirect(url_for('ai_content.index'))
    
    try:
        # Generate article content using AI
        article_data = generate_article_from_topic(category, topic)
        
        if blog_id:
            # Save to database if blog selected
            blog = Blog.query.get(blog_id)
            if blog:
                article = Article(
                    title=article_data['title'],
                    content=article_data['content'],
                    blog_id=blog_id,
                    status='draft',
                    metrics_data=json.dumps({
                        'category': category,
                        'original_topic': topic,
                        'generation_method': 'claude_3.5_sonnet',
                        'generated_at': datetime.now().isoformat()
                    })
                )
                db.session.add(article)
                db.session.commit()
                
                flash(f'Artykuł "{article_data["title"]}" został wygenerowany i zapisany', 'success')
        else:
            flash(f'Artykuł "{article_data["title"]}" został wygenerowany. Wybierz blog, aby zapisać', 'info')
        
        # Pass the generated content to template to display
        return render_template(
            'ai_content/article_preview.html',
            article=article_data,
            category=category,
            topic=topic,
            blog_id=blog_id
        )
        
    except Exception as e:
        logger.error(f"Error generating article: {str(e)}")
        flash(f'Błąd generowania artykułu: {str(e)}', 'danger')
        return redirect(url_for('ai_content.index'))


@ai_content.route('/categories')
def list_categories():
    """List all categories with topic counts"""
    categories_data = []
    
    # Prepare data for each category
    for category, topics in ai_topics.items():
        # Check database for topics with this category
        db_topic_count = ArticleTopic.query.filter_by(category=category).count()
        
        categories_data.append({
            'name': category,
            'ai_topic_count': len(topics),
            'db_topic_count': db_topic_count,
            'total_topic_count': len(topics) + db_topic_count
        })
    
    return render_template('ai_content/categories.html', categories=categories_data)


@ai_content.route('/topics/<category>')
def list_topics(category):
    """List all topics for a category"""
    # Get AI-generated topics
    category_topics = ai_topics.get(category, [])
    
    # Get database topics
    db_topics = ArticleTopic.query.filter_by(category=category).all()
    
    return render_template(
        'ai_content/topics.html',
        category=category,
        ai_topics=category_topics,
        db_topics=db_topics
    )


@ai_content.route('/get-topics/<category>')
def api_get_topics(category):
    """API endpoint to get topics for a category"""
    topics = ai_topics.get(category, [])
    return jsonify(topics)


@ai_content.route('/random-topics')
def api_random_topics():
    """API endpoint to get random topics by category"""
    import random
    
    result = {}
    for category, topics in ai_topics.items():
        # Get up to 5 random topics per category
        if topics:
            sample_size = min(5, len(topics))
            result[category] = random.sample(topics, sample_size)
    
    return jsonify(result)


@ai_content.route('/bulk-generate', methods=['POST'])
def bulk_generate():
    """Bulk generate topics for multiple categories"""
    categories = request.form.getlist('categories[]')
    count = int(request.form.get('count', 40))
    
    if not categories:
        flash('Wybierz co najmniej jedną kategorię', 'danger')
        return redirect(url_for('ai_content.list_categories'))
    
    success_count = 0
    for category in categories:
        try:
            # Generate topics for this category
            new_topics = generate_ai_topics_for_category(category, count)
            
            # Update in-memory topics store
            if category in ai_topics:
                ai_topics[category].extend(new_topics)
                # Remove duplicates
                ai_topics[category] = list(set(ai_topics[category]))
            else:
                ai_topics[category] = new_topics
            
            success_count += 1
        except Exception as e:
            logger.error(f"Error generating topics for {category}: {str(e)}")
            continue
    
    if success_count == len(categories):
        flash(f'Wygenerowano tematy dla wszystkich {len(categories)} kategorii', 'success')
    else:
        flash(f'Wygenerowano tematy dla {success_count} z {len(categories)} kategorii', 'warning')
    
    return redirect(url_for('ai_content.list_categories'))


def register_routes(app):
    """Register the AI content routes with the Flask app"""
    app.register_blueprint(ai_content)