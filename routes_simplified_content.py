"""
Simplified Content Creator Routes
Independent Content Creation System
"""
import os
import logging
import json
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from sqlalchemy import desc, asc
from app import db
from models import Blog, Content, ArticleTopic
from config import Config
import requests

# Setup logging
logger = logging.getLogger(__name__)

# Writing styles for AI content generation
WRITING_STYLES = {
    'professional': 'professional and formal',
    'conversational': 'friendly and conversational',
    'persuasive': 'persuasive and compelling',
    'educational': 'educational and informative',
    'creative': 'creative and engaging',
    'humorous': 'light-hearted and humorous'
}

def generate_article_with_ai(title, paragraphs, style):
    """
    Generate an article using OpenRouter AI API
    
    Args:
        title (str): Article title
        paragraphs (int): Number of paragraphs to generate
        style (str): Writing style from WRITING_STYLES
    
    Returns:
        str: Generated article content or error message
    """
    try:
        api_key = Config.OPENROUTER_API_KEY
        if not api_key:
            return "OpenRouter API key is missing. Please configure it in your environment variables."
        
        style_description = WRITING_STYLES.get(style, 'professional and formal')
        
        prompt = f"""Write a detailed, well-structured article titled "{title}".
        
The article should be:
- Written in a {style_description} tone
- Consist of exactly {paragraphs} paragraphs
- Include a compelling introduction, well-developed body, and clear conclusion
- Be factually accurate and well-researched
- Use proper headings and subheadings where appropriate
- Be easy to read with good flow between paragraphs
- Be comprehensive and self-contained

Format the article with proper Markdown formatting.
"""
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": Config.DEFAULT_CONTENT_MODEL,
            "messages": [
                {"role": "system", "content": "You are a professional content writer who creates high-quality, engaging articles."},
                {"role": "user", "content": prompt}
            ]
        }
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            data=json.dumps(data),
            timeout=60  # Increased timeout for longer content generation
        )
        
        if response.status_code == 200:
            response_data = response.json()
            generated_content = response_data['choices'][0]['message']['content']
            return generated_content
        else:
            logger.error(f"API Error: {response.status_code} - {response.text}")
            return f"Error: API returned status code {response.status_code}"
            
    except Exception as e:
        logger.error(f"Error generating content with AI: {str(e)}")
        return f"Error generating content: {str(e)}"

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

@simplified_content_bp.route('/generate-content', methods=['POST'])
def generate_content():
    """Generate content using AI"""
    try:
        # Get form data
        title = request.form.get('title')
        paragraphs = int(request.form.get('paragraphs', 5))
        style = request.form.get('style', 'professional')
        
        # Validate input
        if not title:
            return jsonify({'success': False, 'error': 'Title is required'})
        
        # Limit paragraph count for reasonable response times
        if paragraphs < 3:
            paragraphs = 3
        elif paragraphs > 15:
            paragraphs = 15
            
        # Generate content with AI
        generated_content = generate_article_with_ai(title, paragraphs, style)
        
        # Return response
        return jsonify({
            'success': True,
            'content': generated_content
        })
    except Exception as e:
        logger.error(f"Error in generate_content: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})