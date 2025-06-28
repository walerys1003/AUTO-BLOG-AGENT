"""
Routes for Automation Management

REST API endpoints dla zarządzania systemem automatyzacji treści.
Obsługuje workflow engine, topic manager i scheduler.
"""
import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for

from app import db
from models import AutomationRule, ArticleTopic, Blog, ContentMetrics, Notification
from utils.automation.workflow_engine import WorkflowEngine, execute_automation_rule
from utils.automation.topic_manager import get_topic_manager
from utils.automation.scheduler import get_automation_scheduler

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
automation_bp = Blueprint('automation', __name__, url_prefix='/automation')

@automation_bp.route('/dashboard')
def dashboard():
    """Dashboard automatyzacji treści"""
    try:
        # Pobierz statystyki
        total_rules = AutomationRule.query.count()
        active_rules = AutomationRule.query.filter_by(is_active=True).count()
        pending_topics = ArticleTopic.query.filter_by(status='pending').count()
        approved_topics = ArticleTopic.query.filter_by(status='approved', used=False).count()
        
        # Ostatnie wykonania
        recent_executions = AutomationRule.query.filter(
            AutomationRule.last_execution_at.isnot(None)
        ).order_by(AutomationRule.last_execution_at.desc()).limit(10).all()
        
        # Status schedulera
        scheduler = get_automation_scheduler()
        scheduler_status = scheduler.get_scheduler_status()
        
        # Statystyki po blogach
        blogs = Blog.query.filter_by(active=True).all()
        blog_stats = {}
        
        for blog in blogs:
            blog_stats[blog.id] = {
                'name': blog.name,
                'rules': AutomationRule.query.filter_by(blog_id=blog.id, is_active=True).count(),
                'topics': ArticleTopic.query.filter_by(blog_id=blog.id, status='approved', used=False).count(),
                'articles_today': 0  # Simplified for now - can be implemented later
            }
        
        return render_template('automation/dashboard.html',
                             total_rules=total_rules,
                             active_rules=active_rules,
                             pending_topics=pending_topics,
                             approved_topics=approved_topics,
                             recent_executions=recent_executions,
                             scheduler_status=scheduler_status,
                             blog_stats=blog_stats,
                             blogs=blogs)
                             
    except Exception as e:
        logger.error(f"Error loading automation dashboard: {str(e)}")
        flash('Error loading dashboard', 'error')
        return redirect(url_for('index'))

@automation_bp.route('/api/execute/<int:rule_id>', methods=['POST'])
def api_execute_rule(rule_id):
    """API endpoint do ręcznego wykonania reguły automatyzacji"""
    try:
        rule = AutomationRule.query.get_or_404(rule_id)
        
        if not rule.is_active:
            return jsonify({
                'success': False,
                'error': 'Rule is not active'
            }), 400
            
        # Wykonaj przez scheduler dla lepszej kontroli
        scheduler = get_automation_scheduler()
        result = scheduler.manual_execute_rule(rule_id)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': f'Rule "{rule.name}" execution started',
                'rule_id': rule_id
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        logger.error(f"Error executing rule {rule_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@automation_bp.route('/api/topics/pending')
def api_pending_topics():
    """API endpoint do pobierania tematów oczekujących na zatwierdzenie"""
    try:
        blog_id = request.args.get('blog_id', type=int)
        category = request.args.get('category')
        limit = request.args.get('limit', default=50, type=int)
        
        topic_manager = get_topic_manager()
        
        if blog_id:
            topics = topic_manager.get_topics_for_approval(blog_id, category, limit)
        else:
            # Pobierz dla wszystkich blogów
            topics = []
            blogs = Blog.query.filter_by(active=True).all()
            for blog in blogs:
                blog_topics = topic_manager.get_topics_for_approval(blog.id, category, limit//len(blogs) if blogs else limit)
                for topic in blog_topics:
                    topic['blog_name'] = blog.name
                topics.extend(blog_topics)
        
        return jsonify({
            'success': True,
            'topics': topics,
            'count': len(topics)
        })
        
    except Exception as e:
        logger.error(f"Error fetching pending topics: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@automation_bp.route('/api/topics/approve', methods=['POST'])
def api_approve_topics():
    """API endpoint do masowego zatwierdzania tematów"""
    try:
        data = request.get_json()
        topic_ids = data.get('topic_ids', [])
        
        if not topic_ids:
            return jsonify({
                'success': False,
                'error': 'No topic IDs provided'
            }), 400
            
        topic_manager = get_topic_manager()
        result = topic_manager.bulk_approve_topics(topic_ids)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error approving topics: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@automation_bp.route('/api/topics/reject', methods=['POST'])
def api_reject_topics():
    """API endpoint do masowego odrzucania tematów"""
    try:
        data = request.get_json()
        topic_ids = data.get('topic_ids', [])
        reason = data.get('reason', '')
        
        if not topic_ids:
            return jsonify({
                'success': False,
                'error': 'No topic IDs provided'
            }), 400
            
        topic_manager = get_topic_manager()
        result = topic_manager.bulk_reject_topics(topic_ids, reason)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error rejecting topics: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@automation_bp.route('/api/topics/refresh/<int:blog_id>', methods=['POST'])
def api_refresh_topics(blog_id):
    """API endpoint do odświeżania puli tematów dla bloga"""
    try:
        blog = Blog.query.get_or_404(blog_id)
        
        topic_manager = get_topic_manager()
        result = topic_manager.auto_refresh_topic_pool(blog_id)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error refreshing topics for blog {blog_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@automation_bp.route('/api/scheduler/status')
def api_scheduler_status():
    """API endpoint do pobierania statusu schedulera"""
    try:
        scheduler = get_automation_scheduler()
        status = scheduler.get_scheduler_status()
        
        return jsonify({
            'success': True,
            'status': status
        })
        
    except Exception as e:
        logger.error(f"Error getting scheduler status: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@automation_bp.route('/api/rules/<int:rule_id>/toggle', methods=['POST'])
def api_toggle_rule(rule_id):
    """API endpoint do przełączania aktywności reguły"""
    try:
        rule = AutomationRule.query.get_or_404(rule_id)
        
        rule.is_active = not rule.is_active
        rule.failure_count = 0  # Reset failure count when toggling
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'active': rule.is_active,
            'message': f'Rule "{rule.name}" {"activated" if rule.is_active else "deactivated"}'
        })
        
    except Exception as e:
        logger.error(f"Error toggling rule {rule_id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@automation_bp.route('/api/stats/overview')
def api_stats_overview():
    """API endpoint do pobierania statystyk systemu automatyzacji"""
    try:
        # Statystyki ogólne
        stats = {
            'rules': {
                'total': AutomationRule.query.count(),
                'active': AutomationRule.query.filter_by(is_active=True).count(),
                'failed': AutomationRule.query.filter(AutomationRule.failure_count > 0).count()
            },
            'topics': {
                'pending': ArticleTopic.query.filter_by(status='pending').count(),
                'approved': ArticleTopic.query.filter_by(status='approved', used=False).count(),
                'used': ArticleTopic.query.filter_by(status='used').count(),
                'rejected': ArticleTopic.query.filter_by(status='rejected').count()
            },
            'executions': {
                'today': AutomationRule.query.filter(
                    AutomationRule.last_execution_at >= datetime.utcnow().date()
                ).count(),
                'this_week': AutomationRule.query.filter(
                    AutomationRule.last_execution_at >= datetime.utcnow() - timedelta(days=7)
                ).count()
            }
        }
        
        # Statystyki po blogach
        blog_stats = []
        blogs = Blog.query.filter_by(active=True).all()
        
        for blog in blogs:
            topic_manager = get_topic_manager()
            blog_topic_stats = topic_manager.get_topic_statistics(blog.id)
            
            blog_stats.append({
                'blog_id': blog.id,
                'blog_name': blog.name,
                'rules': AutomationRule.query.filter_by(blog_id=blog.id, is_active=True).count(),
                'topics': blog_topic_stats
            })
        
        return jsonify({
            'success': True,
            'stats': stats,
            'blog_stats': blog_stats
        })
        
    except Exception as e:
        logger.error(f"Error getting automation stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@automation_bp.route('/topics')
def topics_management():
    """Strona zarządzania tematami"""
    try:
        blog_id = request.args.get('blog_id', type=int)
        status = request.args.get('status', 'pending')
        category = request.args.get('category')
        
        # Pobierz blogi
        blogs = Blog.query.filter_by(active=True).all()
        
        # Pobierz tematy
        query = ArticleTopic.query
        
        if blog_id:
            query = query.filter_by(blog_id=blog_id)
        if status:
            query = query.filter_by(status=status)
        if category:
            query = query.filter_by(category=category)
            
        topics = query.order_by(ArticleTopic.created_at.desc()).limit(100).all()
        
        # Pobierz kategorie dla filtra
        categories = db.session.query(ArticleTopic.category).distinct().all()
        categories = [cat[0] for cat in categories if cat[0]]
        
        return render_template('automation/topics.html',
                             topics=topics,
                             blogs=blogs,
                             categories=categories,
                             selected_blog=blog_id,
                             selected_status=status,
                             selected_category=category)
                             
    except Exception as e:
        logger.error(f"Error loading topics management: {str(e)}")
        flash('Error loading topics', 'error')
        return redirect(url_for('automation.dashboard'))

@automation_bp.route('/logs')
def execution_logs():
    """Strona logów wykonania automatyzacji"""
    try:
        # Pobierz ostatnie wykonania
        executions = AutomationRule.query.filter(
            AutomationRule.last_execution_at.isnot(None)
        ).order_by(AutomationRule.last_execution_at.desc()).limit(50).all()
        
        # Pobierz powiadomienia systemowe
        notifications = Notification.query.order_by(
            Notification.created_at.desc()
        ).limit(20).all()
        
        return render_template('automation/logs.html',
                             executions=executions,
                             notifications=notifications)
                             
    except Exception as e:
        logger.error(f"Error loading execution logs: {str(e)}")
        flash('Error loading logs', 'error')
        return redirect(url_for('automation.dashboard'))

@automation_bp.route('/api/workflow/test', methods=['POST'])
def api_test_workflow():
    """API endpoint do testowania workflow engine"""
    try:
        data = request.get_json()
        rule_id = data.get('rule_id')
        
        if not rule_id:
            return jsonify({
                'success': False,
                'error': 'Rule ID is required'
            }), 400
            
        rule = AutomationRule.query.get_or_404(rule_id)
        
        # Utwórz workflow engine i przetestuj
        engine = WorkflowEngine()
        result = engine.execute_full_cycle(rule)
        
        return jsonify({
            'success': True,
            'workflow_result': result
        })
        
    except Exception as e:
        logger.error(f"Error testing workflow: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500