"""
Simplified Content Creator Module
"""
import json
import logging
from datetime import datetime

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from sqlalchemy import desc

from app import db
from models import Blog, ArticleTopic, Content
from utils.openrouter import openrouter

# Create Blueprint
simplified_content_bp = Blueprint('simplified_content', __name__)
logger = logging.getLogger(__name__)


@simplified_content_bp.route('/content-creator')
def content_creator():
    """Main content creator view - simplified version"""
    # Get all blogs for dropdown
    blogs = Blog.query.filter_by(active=True).all()
    
    # Check if there are any blogs
    if not blogs:
        flash('No active blogs found. Please create a blog first.', 'warning')
        return redirect(url_for('dashboard'))
    
    # Get all content items for display
    contents = Content.query.order_by(desc(Content.created_at)).limit(20).all()
    
    return render_template(
        'content/simplified_content.html',
        title="Content Creator",
        blogs=blogs,
        contents=contents
    )


@simplified_content_bp.route('/content-creator/topics')
def topic_selector():
    """Simple topic selector view"""
    # Get all blogs for reference
    blogs = Blog.query.filter_by(active=True).all()
    
    if not blogs:
        flash('No active blogs found. Please create a blog first.', 'warning')
        return redirect(url_for('dashboard'))
    
    return render_template(
        'content/simple_topic_selector.html',
        title="Select a Topic",
        blogs=blogs
    )


@simplified_content_bp.route('/content-creator/editor', methods=['GET', 'POST'])
def content_editor():
    """Content editor view"""
    # Get topic ID if provided
    topic_id = request.args.get('topic_id')
    content_id = request.args.get('content_id')
    blog_id = request.args.get('blog_id')
    
    # Get blogs for dropdown
    blogs = Blog.query.filter_by(active=True).all()
    
    # Default variables
    topic = None
    content = None
    
    # If we have a content_id, load existing content
    if content_id:
        content = Content.query.get_or_404(content_id)
        blog_id = content.blog_id
    
    # If we have a topic_id, load the topic for reference
    if topic_id:
        topic = ArticleTopic.query.get(topic_id)
        if topic:
            blog_id = topic.blog_id
    
    # Default to first blog if none provided
    if not blog_id and blogs:
        blog_id = blogs[0].id
    
    # Handle POST submission
    if request.method == 'POST':
        title = request.form.get('title', '')
        body = request.form.get('body', '')
        blog_id = request.form.get('blog_id', blog_id)
        topic_text = request.form.get('topic', '')
        action = request.form.get('action', 'save')
        
        if not title:
            flash('Title is required', 'danger')
            return render_template(
                'content/simplified_editor.html',
                topic=topic,
                content=content,
                blogs=blogs,
                blog_id=blog_id
            )
        
        # Create or update content
        if content_id:
            # Update existing content
            content.title = title
            content.body = body
            if action == 'publish':
                content.status = 'published'
            else:
                content.status = 'draft'
            
            db.session.commit()
            
            flash('Content updated successfully', 'success')
        else:
            # Create new content
            content = Content(
                title=title,
                body=body,
                topic=topic_text if topic_text else (topic.title if topic else ""),
                blog_id=blog_id,
                status='published' if action == 'publish' else 'draft'
            )
            
            db.session.add(content)
            db.session.commit()
            
            flash('Content created successfully', 'success')
        
        # Redirect based on action
        if action == 'publish':
            flash('Content published!', 'success')
            return redirect(url_for('simplified_content.content_creator'))
        else:
            return redirect(url_for('simplified_content.content_editor', content_id=content.id))
    
    # Handle GET request
    return render_template(
        'content/simplified_editor.html',
        title="Content Editor",
        topic=topic,
        content=content,
        blogs=blogs,
        blog_id=blog_id
    )


@simplified_content_bp.route('/content-creator/generate', methods=['POST'])
def generate_content():
    """Generate content from a topic"""
    topic_title = request.form.get('topic', '')
    blog_id = request.form.get('blog_id')
    
    if not topic_title:
        flash('Topic is required', 'danger')
        return redirect(url_for('simplified_content.topic_selector'))
    
    try:
        # Use the default blog if none provided
        if not blog_id:
            blog = Blog.query.filter_by(active=True).first()
            if not blog:
                flash('No active blog found', 'danger')
                return redirect(url_for('dashboard'))
            blog_id = blog.id
        
        # Generate content
        prompt = f"""Wygeneruj dobrej jakości artykuł na temat: {topic_title}.
        
        Artykuł powinien mieć 5 akapitów, w tym wstęp i zakończenie.
        
        Zwróć artykuł w formacie HTML z tagami <p> dla każdego akapitu.
        """
        
        model = "anthropic/claude-3.5-sonnet"
        logger.info(f"Generating content for topic: {topic_title} using model: {model}")
        
        response = openrouter.generate_completion(
            prompt=prompt,
            model=model,
            system_prompt="Jesteś pomocnym asystentem, który pisze profesjonalne artykuły na blog. Używaj paragrafów HTML.",
            temperature=0.7
        )
        
        if response and "choices" in response and len(response["choices"]) > 0:
            generated_content = response["choices"][0]["message"]["content"]
            
            # Create a new content entry
            content = Content(
                title=topic_title,
                body=generated_content,
                topic=topic_title,
                blog_id=blog_id,
                status='draft'
            )
            
            db.session.add(content)
            db.session.commit()
            
            flash('Content generated successfully', 'success')
            return redirect(url_for('simplified_content.content_editor', content_id=content.id))
        else:
            # Handle API error
            flash('Failed to generate content. Please try again.', 'danger')
            return redirect(url_for('simplified_content.topic_selector'))
            
    except Exception as e:
        logger.error(f"Error generating content: {str(e)}")
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('simplified_content.topic_selector'))


@simplified_content_bp.route('/content-creator/api/topics')
def get_all_topics():
    """API endpoint to get approved topics for all blogs or a specific blog"""
    logger.info("API endpoint get_all_topics called")
    
    blog_id = request.args.get('blog_id')
    
    try:
        # Build the query for approved topics
        query = ArticleTopic.query.filter_by(status='approved')
        
        # Add blog_id filter if provided
        if blog_id:
            query = query.filter_by(blog_id=blog_id)
        
        logger.info(f"Querying approved topics with blog_id filter: {blog_id}")
        
        # Get all approved topics
        topics = query.order_by(desc(ArticleTopic.score)).all()
        
        # Format the topics for the response
        topics_data = []
        for topic in topics:
            # Convert keywords to a list if available
            keywords = topic.get_keywords() if hasattr(topic, 'get_keywords') else []
            
            topics_data.append({
                'id': topic.id,
                'title': topic.title,
                'blog_id': topic.blog_id,
                'blog_name': topic.blog.name if topic.blog else None,
                'status': topic.status,
                'score': topic.score,
                'keywords': keywords,
                'created_at': topic.created_at.strftime('%Y-%m-%d') if topic.created_at else None
            })
        
        logger.info(f"Found {len(topics_data)} approved topics")
        return jsonify({
            'success': True,
            'topics': topics_data
        })
        
    except Exception as e:
        logger.error(f"Error getting topics: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@simplified_content_bp.route('/content-creator/delete/<int:content_id>', methods=['POST'])
def delete_content(content_id):
    """Delete content"""
    content = Content.query.get_or_404(content_id)
    
    try:
        db.session.delete(content)
        db.session.commit()
        flash('Content deleted successfully', 'success')
    except Exception as e:
        logger.error(f"Error deleting content: {str(e)}")
        flash(f'Error deleting content: {str(e)}', 'danger')
    
    return redirect(url_for('simplified_content.content_creator'))


@simplified_content_bp.route('/content-creator/publish/<int:content_id>', methods=['POST'])
def publish_content(content_id):
    """Publish content"""
    content = Content.query.get_or_404(content_id)
    
    try:
        content.status = 'published'
        db.session.commit()
        flash('Content published successfully', 'success')
    except Exception as e:
        logger.error(f"Error publishing content: {str(e)}")
        flash(f'Error publishing content: {str(e)}', 'danger')
    
    return redirect(url_for('simplified_content.content_creator'))