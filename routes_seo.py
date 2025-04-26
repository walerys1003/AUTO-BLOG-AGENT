"""
SEO Routes

Routes for SEO analyzer and topic generator functionality
"""
import logging
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from models import ArticleTopic, Blog
from app import db
from utils.seo.trends import get_daily_trends, get_related_topics
from utils.seo.analyzer import run_seo_analysis
from utils.seo.topic_generator import generate_topics_from_trends

# Setup logging
logger = logging.getLogger(__name__)

# Create blueprint
seo_bp = Blueprint('seo', __name__, url_prefix='/seo')

@seo_bp.route('/')
def seo_dashboard():
    """SEO Dashboard main view"""
    # Get all topics
    topics = ArticleTopic.query.order_by(ArticleTopic.created_at.desc()).all()
    
    return render_template('seo/dashboard.html', topics=topics)

@seo_bp.route('/run-analysis', methods=['POST'])
def run_analysis():
    """Run SEO analysis manually"""
    try:
        # Get selected categories from form
        categories = request.form.getlist('categories')
        
        if not categories:
            # Use default categories if none selected
            categories = ['medycyna', 'transport', 'IT', 'biznes', 'technologia', 'zdrowie', 'finanse', 'edukacja', 'rozrywka']
        
        logger.info(f"Running SEO analysis for categories: {categories}")
        
        # Get blogs
        blogs = Blog.query.filter_by(active=True).all()
        
        if not blogs:
            flash("No active blogs found to generate topics for", "warning")
            return redirect(url_for('seo.seo_dashboard'))
        
        # Run analysis for each blog
        topics_generated = 0
        
        for blog in blogs:
            # Get blog categories
            blog_categories = []
            try:
                if blog.categories:
                    import json
                    blog_categories = json.loads(blog.categories)
            except Exception as e:
                logger.error(f"Error parsing blog categories: {str(e)}")
                blog_categories = []
            
            # If blog has no categories, use all selected categories
            if not blog_categories:
                blog_categories = categories
            
            # Generate topics
            generated = run_seo_analysis(blog.id, blog_categories)
            
            if generated:
                topics_generated += len(generated)
        
        if topics_generated > 0:
            flash(f"Generated {topics_generated} new topics based on trending keywords", "success")
        else:
            flash("No new topics were generated. Try different categories or try again later.", "info")
            
    except Exception as e:
        logger.error(f"Error running SEO analysis: {str(e)}")
        flash(f"Error running SEO analysis: {str(e)}", "danger")
    
    return redirect(url_for('seo.seo_dashboard'))

@seo_bp.route('/approve/<int:topic_id>', methods=['POST'])
def approve_topic(topic_id):
    """Approve a topic"""
    topic = ArticleTopic.query.get_or_404(topic_id)
    
    try:
        topic.status = 'approved'
        db.session.commit()
        
        flash(f"Topic '{topic.title}' approved successfully", "success")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error approving topic: {str(e)}")
        flash(f"Error approving topic: {str(e)}", "danger")
    
    return redirect(url_for('seo.seo_dashboard'))

@seo_bp.route('/reject/<int:topic_id>', methods=['POST'])
def reject_topic(topic_id):
    """Reject a topic"""
    topic = ArticleTopic.query.get_or_404(topic_id)
    
    try:
        topic.status = 'rejected'
        db.session.commit()
        
        flash(f"Topic '{topic.title}' rejected", "success")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error rejecting topic: {str(e)}")
        flash(f"Error rejecting topic: {str(e)}", "danger")
    
    return redirect(url_for('seo.seo_dashboard'))

@seo_bp.route('/delete/<int:topic_id>', methods=['POST'])
def delete_topic(topic_id):
    """Delete a topic"""
    topic = ArticleTopic.query.get_or_404(topic_id)
    
    try:
        db.session.delete(topic)
        db.session.commit()
        
        flash(f"Topic '{topic.title}' deleted", "success")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting topic: {str(e)}")
        flash(f"Error deleting topic: {str(e)}", "danger")
    
    return redirect(url_for('seo.seo_dashboard'))

@seo_bp.route('/use/<int:topic_id>', methods=['POST'])
def use_topic(topic_id):
    """Use a topic for content creation"""
    topic = ArticleTopic.query.get_or_404(topic_id)
    
    try:
        # Redirect to content creation with this topic
        return redirect(url_for('simplified_content.content_creator', topic_title=topic.title))
        
    except Exception as e:
        logger.error(f"Error using topic: {str(e)}")
        flash(f"Error using topic: {str(e)}", "danger")
        return redirect(url_for('seo.seo_dashboard'))

@seo_bp.route('/api/trends')
def get_trends_api():
    """API endpoint to get current trends"""
    try:
        # Get daily trends
        trends = get_daily_trends(geo='PL')
        
        if trends:
            return jsonify({
                'success': True,
                'trends': trends
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No trends available'
            })
            
    except Exception as e:
        logger.error(f"Error fetching trends: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })