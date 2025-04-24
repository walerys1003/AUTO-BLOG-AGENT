"""
SEO Inspiration Routes Module
"""
import json
from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from sqlalchemy import desc, and_, or_, func

from app import db
from models import Blog, ArticleTopic
from utils.seo import seo_analyzer
from utils.writing import topic_generator

# Create Blueprint
seo_inspiration_bp = Blueprint('seo_inspiration', __name__)


@seo_inspiration_bp.route('/seo-inspirations')
def seo_inspirations():
    """SEO inspirations dashboard view"""
    # Get all blogs
    blogs = Blog.query.filter_by(active=True).all()
    
    # Get status filter
    status_filter = request.args.get('status', 'pending')
    
    # Get blog filter
    blog_filter = request.args.get('blog_id', '')
    try:
        blog_filter = int(blog_filter) if blog_filter else None
    except ValueError:
        blog_filter = None
    
    # Build query
    query = ArticleTopic.query
    
    if status_filter != 'all':
        query = query.filter(ArticleTopic.status == status_filter)
    
    if blog_filter:
        query = query.filter(ArticleTopic.blog_id == blog_filter)
    
    # Get the topics ordered by creation date (newest first)
    topics = query.order_by(desc(ArticleTopic.created_at)).all()
    
    return render_template(
        'seo/inspirations.html',
        blogs=blogs,
        topics=topics,
        active_status=status_filter,
        active_blog=blog_filter,
        title="SEO Inspirations"
    )


@seo_inspiration_bp.route('/seo-inspirations/generate', methods=['POST'])
def generate_inspirations():
    """Generate new SEO inspirations for blogs"""
    blog_id = request.form.get('blog_id')
    count = request.form.get('count', '3')
    
    try:
        count = int(count)
        if count < 1 or count > 10:
            count = 3  # Default to 3 if out of range
    except ValueError:
        count = 3  # Default to 3 if not a valid number
    
    if blog_id:
        try:
            blog_id = int(blog_id)
            blog = Blog.query.get(blog_id)
            
            if not blog:
                flash('Blog not found.', 'danger')
                return redirect(url_for('seo_inspiration.seo_inspirations'))
            
            # Generate topics using the generator utility
            topics = topic_generator.generate_topics_for_blog(blog, count)
            
            if topics:
                flash(f'Successfully generated {len(topics)} SEO topic suggestions for {blog.name}.', 'success')
            else:
                flash('Unable to generate topics. Please try again later.', 'warning')
                
        except Exception as e:
            flash(f'Error generating topics: {str(e)}', 'danger')
    else:
        # Get all active blogs
        blogs = Blog.query.filter_by(active=True).all()
        
        generated_count = 0
        for blog in blogs:
            try:
                # Generate topics using the generator utility
                topics = topic_generator.generate_topics_for_blog(blog, count)
                generated_count += len(topics)
            except Exception as e:
                flash(f'Error generating topics for {blog.name}: {str(e)}', 'warning')
        
        if generated_count > 0:
            flash(f'Successfully generated {generated_count} SEO topic suggestions across all blogs.', 'success')
        else:
            flash('Unable to generate topics. Please try again later.', 'warning')
    
    return redirect(url_for('seo_inspiration.seo_inspirations'))


@seo_inspiration_bp.route('/seo-inspirations/update-status', methods=['POST'])
def update_topic_status():
    """Update the status of a topic"""
    topic_id = request.form.get('topic_id')
    new_status = request.form.get('status')
    
    if not topic_id or not new_status:
        return jsonify({'success': False, 'message': 'Missing required parameters'})
    
    try:
        topic = ArticleTopic.query.get(topic_id)
        
        if not topic:
            return jsonify({'success': False, 'message': 'Topic not found'})
        
        # Update the status
        if new_status in ['pending', 'approved', 'rejected', 'used']:
            topic.status = new_status
            db.session.commit()
            return jsonify({
                'success': True, 
                'message': f'Topic status updated to {new_status}',
                'topic_id': topic_id,
                'new_status': new_status
            })
        else:
            return jsonify({'success': False, 'message': 'Invalid status'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@seo_inspiration_bp.route('/seo-inspirations/edit-topic', methods=['POST'])
def edit_topic():
    """Edit a topic"""
    topic_id = request.form.get('topic_id')
    new_title = request.form.get('title')
    new_keywords = request.form.get('keywords')
    new_category = request.form.get('category')
    
    if not topic_id or not new_title:
        return jsonify({'success': False, 'message': 'Missing required parameters'})
    
    try:
        topic = ArticleTopic.query.get(topic_id)
        
        if not topic:
            return jsonify({'success': False, 'message': 'Topic not found'})
        
        # Update the topic
        topic.title = new_title
        
        if new_keywords:
            keywords_list = [k.strip() for k in new_keywords.split(',')]
            topic.set_keywords(keywords_list)
        
        if new_category:
            topic.category = new_category
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Topic updated successfully',
            'topic': {
                'id': topic.id,
                'title': topic.title,
                'keywords': topic.get_keywords(),
                'category': topic.category
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@seo_inspiration_bp.route('/seo-inspirations/add-manual-topic', methods=['POST'])
def add_manual_topic():
    """Add a manual topic"""
    blog_id = request.form.get('blog_id')
    title = request.form.get('title')
    keywords = request.form.get('keywords', '')
    category = request.form.get('category', '')
    
    if not blog_id or not title:
        flash('Blog and title are required.', 'danger')
        return redirect(url_for('seo_inspiration.seo_inspirations'))
    
    try:
        blog = Blog.query.get(blog_id)
        
        if not blog:
            flash('Blog not found.', 'danger')
            return redirect(url_for('seo_inspiration.seo_inspirations'))
        
        # Create new topic
        new_topic = ArticleTopic(
            blog_id=blog.id,
            title=title,
            category=category,
            status='approved'  # Manual topics are auto-approved
        )
        
        # Set keywords if provided
        if keywords:
            keywords_list = [k.strip() for k in keywords.split(',')]
            new_topic.set_keywords(keywords_list)
        
        db.session.add(new_topic)
        db.session.commit()
        
        flash('Manual topic added successfully.', 'success')
        
    except Exception as e:
        flash(f'Error adding topic: {str(e)}', 'danger')
    
    return redirect(url_for('seo_inspiration.seo_inspirations'))


@seo_inspiration_bp.route('/seo-inspirations/delete-topic/<int:topic_id>', methods=['POST'])
def delete_topic(topic_id):
    """Delete a topic"""
    try:
        topic = ArticleTopic.query.get(topic_id)
        
        if not topic:
            flash('Topic not found.', 'danger')
            return redirect(url_for('seo_inspiration.seo_inspirations'))
        
        db.session.delete(topic)
        db.session.commit()
        
        flash('Topic deleted successfully.', 'success')
        
    except Exception as e:
        flash(f'Error deleting topic: {str(e)}', 'danger')
    
    return redirect(url_for('seo_inspiration.seo_inspirations'))


@seo_inspiration_bp.route('/seo-inspirations/analyze-keyword', methods=['POST'])
def analyze_keyword():
    """Analyze a keyword for SEO potential"""
    keyword = request.form.get('keyword')
    
    if not keyword:
        return jsonify({'success': False, 'message': 'Keyword is required'})
    
    try:
        # Use SEO analyzer utility to get keyword metrics
        keyword_data = seo_analyzer.analyze_keyword(keyword)
        
        return jsonify({
            'success': True,
            'data': keyword_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error analyzing keyword: {str(e)}'})