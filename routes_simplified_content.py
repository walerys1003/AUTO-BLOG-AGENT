"""
Simplified Content Creator Routes
Independent Content Creation System
"""
import os
import logging
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from sqlalchemy import desc, asc
from app import db
from models import Blog, Content, ArticleTopic

# Setup logging
logger = logging.getLogger(__name__)

# Create blueprint
simplified_content_bp = Blueprint('simplified_content', __name__, url_prefix='/simple-content')

@simplified_content_bp.route('/')
def content_creator():
    """Main simplified content creator view"""
    # Get all content with blogs joined
    contents = Content.query.order_by(Content.created_at.desc()).all()
    return render_template('content/simplified_content.html', contents=contents)

@simplified_content_bp.route('/topics')
def topic_selector():
    """Select from available topics"""
    # Filter by blog_id if provided
    blog_id = request.args.get('blog_id', 'all')
    
    # Get approved topics
    query = ArticleTopic.query.filter_by(status='approved')
    
    # Apply blog filter if provided
    if blog_id != 'all':
        query = query.filter_by(blog_id=blog_id)
    
    # Get topics with pagination
    topics = query.order_by(ArticleTopic.created_at.desc()).all()
    
    # Get all blogs for filter
    blogs = Blog.query.filter_by(active=True).all()
    
    return render_template('content/simple_topic_selector.html', 
                          topics=topics, 
                          blogs=blogs, 
                          blog_id=blog_id)

@simplified_content_bp.route('/topics/<int:topic_id>/use', methods=['POST'])
def use_topic(topic_id):
    """Use a topic for content creation"""
    topic = ArticleTopic.query.get_or_404(topic_id)
    
    # Redirect to content editor with topic
    return redirect(url_for('simplified_content.content_editor', topic_id=topic.id))

@simplified_content_bp.route('/editor', methods=['GET', 'POST'])
@simplified_content_bp.route('/editor/<int:content_id>', methods=['GET', 'POST'])
def content_editor(content_id=None):
    """Content editor view for creating and editing content"""
    # Get active blogs
    blogs = Blog.query.filter_by(active=True).all()
    if not blogs:
        flash('You need to add at least one active blog first', 'warning')
        return redirect(url_for('blogs_list'))
    
    # Get topic_id from query params if present
    topic_id = request.args.get('topic_id')
    topic = None
    if topic_id:
        topic = ArticleTopic.query.get_or_404(topic_id)
    
    # Get blog_id from query params if present
    blog_id = request.args.get('blog_id')
    
    # Get existing content if editing
    content = None
    if content_id:
        content = Content.query.get_or_404(content_id)
    
    # Handle POST request
    if request.method == 'POST':
        action = request.form.get('action', 'save')
        
        # Get form data
        title = request.form.get('title')
        body = request.form.get('body')
        blog_id = request.form.get('blog_id')
        topic_text = request.form.get('topic')
        
        if not all([title, body, blog_id]):
            flash('Title, content, and blog are required', 'danger')
            return render_template('content/simplified_editor.html', 
                                  content=content, 
                                  blogs=blogs, 
                                  topic=topic,
                                  blog_id=blog_id)
        
        # Determine status based on action
        status = 'published' if action == 'publish' else 'draft'
        
        try:
            # Update existing content or create new one
            if content:
                content.title = title
                content.body = body
                content.blog_id = blog_id
                content.topic = topic_text
                
                # Update status if publishing
                if status == 'published' and content.status != 'published':
                    content.status = 'published'
                    content.published_at = datetime.utcnow()
            else:
                content = Content(
                    title=title,
                    body=body,
                    blog_id=blog_id,
                    status=status,
                    topic=topic_text
                )
                
                # Set published_at if publishing
                if status == 'published':
                    content.published_at = datetime.utcnow()
                
                db.session.add(content)
            
            db.session.commit()
            
            # Determine appropriate message
            action_text = 'published' if status == 'published' else 'saved as draft'
            flash(f'Content {action_text} successfully', 'success')
            
            # Redirect to content list or edit page based on action
            if action == 'save_continue':
                return redirect(url_for('simplified_content.content_editor', content_id=content.id))
            else:
                return redirect(url_for('simplified_content.content_creator'))
                
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving content: {str(e)}")
            flash(f'Error saving content: {str(e)}', 'danger')
    
    # Render the editor template
    return render_template('content/simplified_editor.html', 
                          content=content, 
                          blogs=blogs, 
                          topic=topic,
                          blog_id=blog_id)

@simplified_content_bp.route('/content/<int:content_id>/publish', methods=['POST'])
def publish_content(content_id):
    """Publish a draft content"""
    content = Content.query.get_or_404(content_id)
    
    if content.status == 'published':
        flash('Content is already published', 'info')
        return redirect(url_for('simplified_content.content_creator'))
    
    try:
        content.status = 'published'
        content.published_at = datetime.utcnow()
        db.session.commit()
        
        flash('Content published successfully', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error publishing content: {str(e)}")
        flash(f'Error publishing content: {str(e)}', 'danger')
    
    return redirect(url_for('simplified_content.content_creator'))

@simplified_content_bp.route('/content/<int:content_id>/delete', methods=['POST'])
def delete_content(content_id):
    """Delete a content"""
    content = Content.query.get_or_404(content_id)
    
    try:
        db.session.delete(content)
        db.session.commit()
        
        flash('Content deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting content: {str(e)}")
        flash(f'Error deleting content: {str(e)}', 'danger')
    
    return redirect(url_for('simplified_content.content_creator'))