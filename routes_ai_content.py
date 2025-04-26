"""
Routes for AI-Driven Content Strategy

This module provides routes for managing AI-generated content, including:
- Generating topics for categories
- Generating articles from topics
- Managing categories and topics
"""

import os
import json
import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from datetime import datetime
from models import db, Blog, ArticleCategory, ArticleTopic, Article, ContentLog

from utils.ai_content_strategy import topic_generator, article_generator

# Create a blueprint for the AI content routes
ai_content = Blueprint('ai_content', __name__)

# Setup logging
logger = logging.getLogger(__name__)

# Data directory for storing AI-generated content
DATA_DIR = "data"
TOPICS_FILE = os.path.join(DATA_DIR, "ai_topics.json")

@ai_content.route("/ai-content", methods=["GET"])
def index():
    """AI Content Strategy Dashboard"""
    # Get all blogs
    blogs = Blog.query.all()
    
    # Get categories from database
    categories = ArticleCategory.query.all()
    
    # Load AI-generated topics
    ai_topics = {}
    if os.path.exists(TOPICS_FILE):
        try:
            with open(TOPICS_FILE, 'r', encoding='utf-8') as f:
                ai_topics_data = json.load(f)
                # Remove metadata keys
                ai_topics = {k: v for k, v in ai_topics_data.items() if not k.startswith('_')}
        except Exception as e:
            logger.error(f"Error loading AI topics: {str(e)}")
    
    # Get last update timestamp
    last_updated = None
    if os.path.exists(TOPICS_FILE):
        try:
            with open(TOPICS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if '_last_updated' in data:
                    last_updated = data['_last_updated']
        except Exception:
            pass
    
    # Recent articles generated with AI
    recent_articles = Article.query.filter_by(source='ai').order_by(Article.created_at.desc()).limit(5).all()
    
    return render_template(
        "ai_content/dashboard.html",
        blogs=blogs,
        categories=categories,
        ai_topics=ai_topics,
        last_updated=last_updated,
        recent_articles=recent_articles
    )

@ai_content.route("/ai-content/generate-topics", methods=["POST"])
def generate_topics():
    """Generate topics for a category"""
    category_name = request.form.get("category")
    count = int(request.form.get("count", 40))
    
    if not category_name:
        flash("Category name is required", "error")
        return redirect(url_for("ai_content.index"))
    
    try:
        # Generate topics for the category
        topics = topic_generator.generate_topics_for_category(category_name, count)
        
        # Save topics to the JSON file
        topic_generator.save_topics_to_json({category_name: topics}, TOPICS_FILE)
        
        flash(f"Successfully generated {len(topics)} topics for category '{category_name}'", "success")
    except Exception as e:
        logger.error(f"Error generating topics: {str(e)}")
        flash(f"Error generating topics: {str(e)}", "error")
    
    return redirect(url_for("ai_content.index"))

@ai_content.route("/ai-content/generate-article", methods=["POST"])
def generate_article():
    """Generate an article for a selected topic"""
    category = request.form.get("category")
    topic = request.form.get("topic")
    blog_id = request.form.get("blog_id")
    
    if not category or not topic:
        flash("Category and topic are required", "error")
        return redirect(url_for("ai_content.index"))
    
    try:
        # Generate the article
        article_data = article_generator.generate_article(topic, category)
        
        # Save the article to file
        article_path = article_generator.save_article(article_data)
        
        # Save to database if blog_id is provided
        if blog_id:
            try:
                blog = Blog.query.get(blog_id)
                
                # Find or create the category
                db_category = ArticleCategory.query.filter_by(name=category).first()
                if not db_category:
                    db_category = ArticleCategory(name=category)
                    db.session.add(db_category)
                    db.session.flush()
                
                # Create an article record
                article = Article(
                    title=article_data['title'],
                    content=article_data['content'],
                    meta_title=article_data['meta_title'],
                    meta_description=article_data['meta_description'],
                    category_id=db_category.id,
                    blog_id=blog_id,
                    status='draft',
                    source='ai',
                    keywords=",".join(article_data['keywords']),
                    file_path=article_path
                )
                db.session.add(article)
                
                # Log the content generation
                log = ContentLog(
                    title=article_data['title'],
                    prompt=f"Generate article for '{topic}' in category '{category}'",
                    content=article_data['content'],
                    tokens=len(article_data['content']) // 4,  # Rough estimate
                    status='success',
                    source='openrouter',
                    model='anthropic/claude-3-5-sonnet-20241022'
                )
                db.session.add(log)
                
                db.session.commit()
                flash(f"Article '{article_data['title']}' generated and saved to database!", "success")
                
                # Redirect to article edit page if available
                return redirect(url_for("content.edit_article", article_id=article.id))
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error saving article to database: {str(e)}")
                flash(f"Article generated but could not be saved to database: {str(e)}", "warning")
        else:
            flash(f"Article '{article_data['title']}' generated and saved to '{article_path}'", "success")
        
    except Exception as e:
        logger.error(f"Error generating article: {str(e)}")
        flash(f"Error generating article: {str(e)}", "error")
    
    return redirect(url_for("ai_content.index"))

@ai_content.route("/ai-content/categories", methods=["GET"])
def list_categories():
    """List all categories with topic counts"""
    # Get categories from database
    db_categories = ArticleCategory.query.all()
    
    # Load AI-generated topics
    ai_topics = {}
    if os.path.exists(TOPICS_FILE):
        try:
            with open(TOPICS_FILE, 'r', encoding='utf-8') as f:
                ai_topics_data = json.load(f)
                # Remove metadata keys
                ai_topics = {k: v for k, v in ai_topics_data.items() if not k.startswith('_')}
        except Exception as e:
            logger.error(f"Error loading AI topics: {str(e)}")
    
    # Combine database categories with AI topics
    categories = []
    
    # Add database categories
    for cat in db_categories:
        topic_count = ArticleTopic.query.filter_by(category_id=cat.id).count()
        ai_topic_count = len(ai_topics.get(cat.name, []))
        categories.append({
            'id': cat.id,
            'name': cat.name,
            'db_topic_count': topic_count,
            'ai_topic_count': ai_topic_count,
            'total_topic_count': topic_count + ai_topic_count
        })
    
    # Add AI topics that aren't in database
    for cat_name, topics in ai_topics.items():
        if not any(c['name'] == cat_name for c in categories):
            categories.append({
                'id': None,
                'name': cat_name,
                'db_topic_count': 0,
                'ai_topic_count': len(topics),
                'total_topic_count': len(topics)
            })
    
    return render_template(
        "ai_content/categories.html",
        categories=categories
    )

@ai_content.route("/ai-content/topics/<category>", methods=["GET"])
def list_topics(category):
    """List all topics for a category"""
    # Load AI-generated topics
    ai_topics = []
    if os.path.exists(TOPICS_FILE):
        try:
            with open(TOPICS_FILE, 'r', encoding='utf-8') as f:
                ai_topics_data = json.load(f)
                ai_topics = ai_topics_data.get(category, [])
        except Exception as e:
            logger.error(f"Error loading AI topics: {str(e)}")
    
    # Get database topics for this category
    db_category = ArticleCategory.query.filter_by(name=category).first()
    db_topics = []
    if db_category:
        db_topics = ArticleTopic.query.filter_by(category_id=db_category.id).all()
    
    return render_template(
        "ai_content/topics.html",
        category=category,
        ai_topics=ai_topics,
        db_topics=db_topics
    )

@ai_content.route("/ai-content/random-topics-by-category", methods=["GET"])
def api_random_topics():
    """API endpoint to get random topics by category"""
    result = {}
    
    # Load AI-generated topics
    ai_topics = {}
    if os.path.exists(TOPICS_FILE):
        try:
            with open(TOPICS_FILE, 'r', encoding='utf-8') as f:
                ai_topics_data = json.load(f)
                # Remove metadata keys
                ai_topics = {k: v for k, v in ai_topics_data.items() if not k.startswith('_')}
        except Exception as e:
            logger.error(f"Error loading AI topics: {str(e)}")
    
    # Get a random topic for each category
    for category, topics in ai_topics.items():
        if topics:
            import random
            result[category] = random.choice(topics)
    
    return jsonify(result)

@ai_content.route("/ai-content/get-topics/<category>", methods=["GET"])
def api_get_topics(category):
    """API endpoint to get topics for a category"""
    # Load AI-generated topics
    ai_topics = []
    if os.path.exists(TOPICS_FILE):
        try:
            with open(TOPICS_FILE, 'r', encoding='utf-8') as f:
                ai_topics_data = json.load(f)
                ai_topics = ai_topics_data.get(category, [])
        except Exception as e:
            logger.error(f"Error loading AI topics: {str(e)}")
    
    return jsonify(ai_topics)

@ai_content.route("/ai-content/bulk-generate", methods=["POST"])
def bulk_generate():
    """Bulk generate topics for multiple categories"""
    categories = request.form.getlist("categories[]")
    count = int(request.form.get("count", 40))
    
    if not categories:
        flash("No categories selected", "error")
        return redirect(url_for("ai_content.list_categories"))
    
    results = {}
    for category in categories:
        try:
            # Generate topics for the category
            topics = topic_generator.generate_topics_for_category(category, count)
            results[category] = len(topics)
            
            # Save topics to the JSON file (one by one to avoid race conditions)
            topic_generator.save_topics_to_json({category: topics}, TOPICS_FILE)
            
        except Exception as e:
            logger.error(f"Error generating topics for '{category}': {str(e)}")
            results[category] = f"Error: {str(e)}"
    
    # Prepare a flash message with results
    msg = "Bulk generation results:<br>"
    for category, result in results.items():
        msg += f"- {category}: {result} topics<br>"
    
    flash(msg, "success")
    return redirect(url_for("ai_content.list_categories"))

def register_routes(app):
    """Register the AI content routes with the Flask app"""
    app.register_blueprint(ai_content)