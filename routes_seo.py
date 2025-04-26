"""
SEO Routes Module

This module provides routes for SEO-related functionality, including trend analysis,
keyword research, topic generation, and content optimization.
"""
import logging
import json
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from models import ArticleTopic, Blog, db
from datetime import datetime
from utils.seo.trends import get_daily_trends, get_trending_topics
from utils.seo.serp import get_serp_data, get_keyword_competition, analyze_serp_results
from utils.seo.analyzer import analyze_content, get_keyword_suggestions
from utils.seo.optimizer import seo_optimizer, generate_title_variations
from utils.seo.topic_generator import generate_topics_from_trends

# Setup logging
logger = logging.getLogger(__name__)

# Create blueprint
seo_bp = Blueprint('seo', __name__, url_prefix='/seo')

@seo_bp.route('/')
def index():
    """SEO dashboard page"""
    # Get stats for topics
    try:
        from datetime import datetime, timedelta
        
        stats = {}
        
        # Count topics by status
        stats['pending_count'] = ArticleTopic.query.filter_by(status='pending').count()
        stats['approved_count'] = ArticleTopic.query.filter_by(status='approved').count()
        stats['rejected_count'] = ArticleTopic.query.filter_by(status='rejected').count()
        
        # Count topics for today
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        stats['today_count'] = ArticleTopic.query.filter(
            ArticleTopic.created_at >= today_start
        ).count()
        
        # Count topics for this week
        week_start = today_start - timedelta(days=today_start.weekday())
        stats['week_count'] = ArticleTopic.query.filter(
            ArticleTopic.created_at >= week_start
        ).count()
        
        # Get recent topics
        topics_query = db.session.query(
            ArticleTopic, Blog
        ).join(
            Blog, ArticleTopic.blog_id == Blog.id
        ).order_by(
            ArticleTopic.created_at.desc()
        ).limit(5)
        
        recent_topics = []
        for topic, blog in topics_query:
            recent_topics.append({
                'id': topic.id,
                'title': topic.title,
                'status': topic.status,
                'blog_name': blog.name,
                'created_at': topic.created_at
            })
        
        # Get trending keywords
        from utils.seo.trends import get_daily_trends
        trends = get_daily_trends()
        
        return render_template(
            'seo/dashboard.html',
            stats=stats,
            topics=recent_topics,
            trends=trends
        )
    
    except Exception as e:
        logger.error(f"Error loading SEO dashboard: {str(e)}")
        return render_template('seo/dashboard.html')

@seo_bp.route('/trends')
def trends():
    """View current trends"""
    try:
        daily_trends = get_daily_trends()
        return render_template('seo/trends.html', trends=daily_trends)
    except Exception as e:
        logger.error(f"Error loading trends: {str(e)}")
        flash(f"Error loading trends: {str(e)}", "danger")
        return render_template('seo/trends.html', trends=[])

@seo_bp.route('/keywords')
def keywords():
    """Keyword research and analysis"""
    return render_template('seo/keywords.html')

@seo_bp.route('/topics')
def topics():
    """View and manage article topics"""
    # Get topics with join to Blog
    topics = db.session.query(ArticleTopic, Blog).join(Blog, ArticleTopic.blog_id == Blog.id).all()
    
    # Organize topics by status
    organized_topics = {
        'pending': [],
        'approved': [],
        'rejected': []
    }
    
    for topic, blog in topics:
        topic_data = {
            'id': topic.id,
            'title': topic.title,
            'description': topic.description,
            'keywords': json.loads(topic.keywords) if topic.keywords else [],
            'category': topic.category,
            'blog': blog.name,
            'blog_id': blog.id,
            'created_at': topic.created_at
        }
        
        if topic.status in organized_topics:
            organized_topics[topic.status].append(topic_data)
    
    # Get blogs for the generator form
    blogs = Blog.query.filter_by(active=True).all()
    
    return render_template(
        'seo/topics.html',
        topics=organized_topics,
        blogs=blogs
    )

@seo_bp.route('/generate-topics', methods=['POST'])
def generate_topics():
    """Generate new topics from trends and keywords"""
    try:
        blog_id = request.form.get('blog_id')
        category = request.form.get('category')
        count = int(request.form.get('count', 5))
        
        if not blog_id:
            flash("Please select a blog to generate topics for", "danger")
            return redirect(url_for('seo.topics'))
        
        # Get blog
        blog = Blog.query.get(blog_id)
        if not blog:
            flash("Blog not found", "danger")
            return redirect(url_for('seo.topics'))
        
        # Get available categories
        available_categories = json.loads(blog.categories) if blog.categories else []
        
        # Get trends
        trends = get_trending_topics(limit=10)
        
        # Generate topics
        topic_list = generate_topics_from_trends(
            trends=trends,
            categories=available_categories if not category else [category],
            blog_id=int(blog_id),
            limit=count
        )
        
        if topic_list:
            flash(f"Generated {len(topic_list)} new topics for {blog.name}", "success")
        else:
            flash("No topics could be generated. Try changing the category or increasing the count.", "warning")
        
        return redirect(url_for('seo.topics'))
        
    except Exception as e:
        logger.error(f"Error generating topics: {str(e)}")
        flash(f"Error generating topics: {str(e)}", "danger")
        return redirect(url_for('seo.topics'))

@seo_bp.route('/approve-topic/<int:topic_id>', methods=['POST'])
def approve_topic(topic_id):
    """Approve a pending topic"""
    try:
        topic = ArticleTopic.query.get_or_404(topic_id)
        
        if topic.status != 'pending':
            flash("Only pending topics can be approved", "warning")
            return redirect(url_for('seo.topics'))
        
        topic.status = 'approved'
        db.session.commit()
        
        flash(f"Topic '{topic.title}' approved", "success")
        return redirect(url_for('seo.topics'))
        
    except Exception as e:
        logger.error(f"Error approving topic: {str(e)}")
        flash(f"Error approving topic: {str(e)}", "danger")
        return redirect(url_for('seo.topics'))

@seo_bp.route('/approve-all-topics', methods=['POST'])
def approve_all_topics():
    """Approve all pending topics for a specific blog"""
    try:
        blog_id = request.form.get('blog_id')
        
        if not blog_id:
            flash("Please select a blog", "danger")
            return redirect(url_for('seo.topics'))
        
        # Get pending topics for this blog
        pending_topics = ArticleTopic.query.filter_by(
            blog_id=blog_id,
            status='pending'
        ).all()
        
        if not pending_topics:
            flash("No pending topics found for this blog", "info")
            return redirect(url_for('seo.topics'))
        
        # Approve all pending topics
        for topic in pending_topics:
            topic.status = 'approved'
        
        db.session.commit()
        
        flash(f"Approved {len(pending_topics)} pending topics", "success")
        return redirect(url_for('seo.topics'))
        
    except Exception as e:
        logger.error(f"Error approving all topics: {str(e)}")
        flash(f"Error approving all topics: {str(e)}", "danger")
        return redirect(url_for('seo.topics'))

@seo_bp.route('/reject-topic/<int:topic_id>', methods=['POST'])
def reject_topic(topic_id):
    """Reject a pending topic"""
    try:
        topic = ArticleTopic.query.get_or_404(topic_id)
        
        if topic.status != 'pending':
            flash("Only pending topics can be rejected", "warning")
            return redirect(url_for('seo.topics'))
        
        topic.status = 'rejected'
        db.session.commit()
        
        flash(f"Topic '{topic.title}' rejected", "success")
        return redirect(url_for('seo.topics'))
        
    except Exception as e:
        logger.error(f"Error rejecting topic: {str(e)}")
        flash(f"Error rejecting topic: {str(e)}", "danger")
        return redirect(url_for('seo.topics'))

@seo_bp.route('/delete-topic/<int:topic_id>', methods=['POST'])
def delete_topic(topic_id):
    """Delete a topic"""
    try:
        topic = ArticleTopic.query.get_or_404(topic_id)
        title = topic.title
        
        db.session.delete(topic)
        db.session.commit()
        
        flash(f"Topic '{title}' deleted", "success")
        return redirect(url_for('seo.topics'))
        
    except Exception as e:
        logger.error(f"Error deleting topic: {str(e)}")
        flash(f"Error deleting topic: {str(e)}", "danger")
        return redirect(url_for('seo.topics'))

@seo_bp.route('/analyze-content', methods=['GET', 'POST'])
def analyze_content_page():
    """Analyze content for SEO optimization"""
    if request.method == 'POST':
        try:
            content = request.form.get('content')
            primary_keyword = request.form.get('primary_keyword')
            secondary_keywords = request.form.get('secondary_keywords', '').split(',')
            secondary_keywords = [k.strip() for k in secondary_keywords if k.strip()]
            
            if not content or not primary_keyword:
                flash("Content and primary keyword are required", "danger")
                return render_template('seo/analyze_content.html')
            
            # Perform analysis
            analysis = analyze_content(
                content=content, 
                primary_keyword=primary_keyword,
                secondary_keywords=secondary_keywords
            )
            
            return render_template(
                'seo/analyze_content.html',
                content=content,
                primary_keyword=primary_keyword,
                secondary_keywords=','.join(secondary_keywords),
                analysis=analysis
            )
            
        except Exception as e:
            logger.error(f"Error analyzing content: {str(e)}")
            flash(f"Error analyzing content: {str(e)}", "danger")
            return render_template('seo/analyze_content.html')
    
    return render_template('seo/analyze_content.html')

@seo_bp.route('/api/trends')
def api_trends():
    """API endpoint to get current trends"""
    try:
        country = request.args.get('country', 'pl')
        limit = int(request.args.get('limit', 10))
        
        trends = get_daily_trends(country=country)
        
        return jsonify({
            'status': 'success',
            'trends': trends[:limit] if trends else []
        })
        
    except Exception as e:
        logger.error(f"Error getting trends API: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@seo_bp.route('/api/keyword-competition', methods=['POST'])
def api_keyword_competition():
    """API endpoint to analyze keyword competition"""
    try:
        data = request.json
        
        if not data or 'keyword' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Keyword is required'
            }), 400
        
        keyword = data['keyword']
        country = data.get('country', 'pl')
        
        competition = get_keyword_competition(
            keyword=keyword,
            country=country
        )
        
        return jsonify({
            'status': 'success',
            'competition': competition
        })
        
    except Exception as e:
        logger.error(f"Error getting keyword competition API: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@seo_bp.route('/api/keyword-suggestions', methods=['GET'])
def api_keyword_suggestions():
    """API endpoint to get keyword suggestions"""
    try:
        topic = request.args.get('topic')
        limit = int(request.args.get('limit', 5))
        
        if not topic:
            return jsonify({
                'status': 'error',
                'message': 'Topic is required'
            }), 400
        
        suggestions = get_keyword_suggestions(
            topic=topic,
            limit=limit
        )
        
        return jsonify({
            'status': 'success',
            'suggestions': suggestions
        })
        
    except Exception as e:
        logger.error(f"Error getting keyword suggestions API: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@seo_bp.route('/api/title-variations', methods=['POST'])
def api_title_variations():
    """API endpoint to generate title variations"""
    try:
        data = request.json
        
        if not data or 'title' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Title is required'
            }), 400
        
        title = data['title']
        keywords = data.get('keywords', [])
        limit = data.get('limit', 5)
        
        variations = generate_title_variations(
            title=title,
            keywords=keywords,
            limit=limit
        )
        
        return jsonify({
            'status': 'success',
            'variations': variations
        })
        
    except Exception as e:
        logger.error(f"Error generating title variations API: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500