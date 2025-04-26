"""
SEO Routes

Routes for SEO functionality and topic generation
"""
import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app import db
from models import ArticleTopic, Blog
from utils.seo.analyzer import analyze_topics_now

# Setup logging
logger = logging.getLogger(__name__)

# Create blueprint
seo_bp = Blueprint('seo', __name__, url_prefix='/seo')

@seo_bp.route('/')
def seo_dashboard():
    """SEO Dashboard main view"""
    topics = ArticleTopic.query.order_by(ArticleTopic.created_at.desc()).limit(20).all()
    blogs = Blog.query.filter_by(active=True).all()
    
    return render_template(
        'seo/dashboard.html',
        topics=topics,
        blogs=blogs
    )

@seo_bp.route('/analyze', methods=['POST'])
def run_analysis():
    """Run SEO analysis manually"""
    try:
        # Get selected categories from form
        selected_categories = request.form.getlist('categories')
        
        # Run analysis with selected categories
        results = analyze_topics_now(
            categories=selected_categories if selected_categories else None
        )
        
        # Count total topics generated
        total_topics = sum(len(topics) for topics in results.values())
        
        # Flash success message
        flash(f'Successfully generated {total_topics} topics for {len(results)} categories', 'success')
        
    except Exception as e:
        logger.error(f"Error running SEO analysis: {str(e)}")
        flash(f'Error running SEO analysis: {str(e)}', 'danger')
    
    return redirect(url_for('seo.seo_dashboard'))

@seo_bp.route('/topics/approve/<int:topic_id>', methods=['POST'])
def approve_topic(topic_id):
    """Approve a topic"""
    topic = ArticleTopic.query.get_or_404(topic_id)
    topic.status = 'approved'
    
    try:
        db.session.commit()
        flash('Topic approved successfully', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error approving topic: {str(e)}")
        flash(f'Error approving topic: {str(e)}', 'danger')
    
    return redirect(url_for('seo.seo_dashboard'))

@seo_bp.route('/topics/reject/<int:topic_id>', methods=['POST'])
def reject_topic(topic_id):
    """Reject a topic"""
    topic = ArticleTopic.query.get_or_404(topic_id)
    topic.status = 'rejected'
    
    try:
        db.session.commit()
        flash('Topic rejected successfully', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error rejecting topic: {str(e)}")
        flash(f'Error rejecting topic: {str(e)}', 'danger')
    
    return redirect(url_for('seo.seo_dashboard'))

@seo_bp.route('/topics/delete/<int:topic_id>', methods=['POST'])
def delete_topic(topic_id):
    """Delete a topic"""
    topic = ArticleTopic.query.get_or_404(topic_id)
    
    try:
        db.session.delete(topic)
        db.session.commit()
        flash('Topic deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting topic: {str(e)}")
        flash(f'Error deleting topic: {str(e)}', 'danger')
    
    return redirect(url_for('seo.seo_dashboard'))

@seo_bp.route('/topics/use/<int:topic_id>', methods=['POST'])
def use_topic(topic_id):
    """Use a topic for content creation"""
    topic = ArticleTopic.query.get_or_404(topic_id)
    
    # Redirect to content editor with topic
    return redirect(url_for('simplified_content.content_editor', topic_id=topic.id))

@seo_bp.route('/trends/api/get', methods=['GET'])
def get_trends_api():
    """API endpoint to get current trends"""
    try:
        from utils.seo.trends import get_daily_trends
        trends = get_daily_trends(limit=10)
        return jsonify({'success': True, 'trends': trends})
    except Exception as e:
        logger.error(f"Error getting trends: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})