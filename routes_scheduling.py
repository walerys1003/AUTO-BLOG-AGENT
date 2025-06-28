"""
Routes for advanced publication scheduling system
"""
import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, render_template
from typing import Dict, List, Any

from app import db
from models import Blog, ScheduledPublication
from utils.scheduling.publication_scheduler import create_30_day_schedule

logger = logging.getLogger(__name__)

# Create blueprint for scheduling routes
scheduling_bp = Blueprint('scheduling', __name__, url_prefix='/scheduling')

@scheduling_bp.route('/dashboard')
def scheduling_dashboard():
    """Dashboard for publication scheduling management"""
    try:
        # Get all blogs
        blogs = Blog.query.filter_by(active=True).all()
        
        # Get current month schedule stats
        current_date = datetime.now()
        start_of_month = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_of_month = start_of_month + timedelta(days=32)
        end_of_month = end_of_month.replace(day=1) - timedelta(days=1)
        
        schedule_stats = {}
        for blog in blogs:
            scheduled_count = ScheduledPublication.query.filter(
                ScheduledPublication.blog_id == blog.id,
                ScheduledPublication.scheduled_date >= start_of_month,
                ScheduledPublication.scheduled_date <= end_of_month
            ).count()
            
            published_count = ScheduledPublication.query.filter(
                ScheduledPublication.blog_id == blog.id,
                ScheduledPublication.status == 'published',
                ScheduledPublication.scheduled_date >= start_of_month,
                ScheduledPublication.scheduled_date <= end_of_month
            ).count()
            
            schedule_stats[blog.id] = {
                'scheduled': scheduled_count,
                'published': published_count,
                'pending': scheduled_count - published_count
            }
        
        return render_template('scheduling/dashboard.html', 
                             blogs=blogs, 
                             schedule_stats=schedule_stats,
                             current_date=current_date)
        
    except Exception as e:
        logger.error(f"Error loading scheduling dashboard: {str(e)}")
        return render_template('error.html', 
                             error_message="Błąd podczas ładowania dashboardu harmonogramu")

@scheduling_bp.route('/api/create-schedule', methods=['POST'])
def create_schedule_api():
    """API endpoint to create 30-day publication schedule"""
    try:
        data = request.get_json()
        blog_name = data.get('blog_name', 'MamaTestuje.com')
        start_date = data.get('start_date')
        
        # Parse start date if provided
        if start_date:
            start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        
        # Generate schedule
        result = create_30_day_schedule(blog_name, export_csv=True)
        
        if result['success']:
            # Save to database if blog exists
            blog = Blog.query.filter_by(name=blog_name).first()
            if blog:
                # Clear existing scheduled publications for next 30 days
                future_date = datetime.now() + timedelta(days=30)
                ScheduledPublication.query.filter(
                    ScheduledPublication.blog_id == blog.id,
                    ScheduledPublication.scheduled_date >= datetime.now(),
                    ScheduledPublication.scheduled_date <= future_date,
                    ScheduledPublication.status == 'scheduled'
                ).delete()
                
                # Save new schedule
                for article in result['schedule']:
                    scheduled_pub = ScheduledPublication(
                        blog_id=blog.id,
                        title=article['title'],
                        main_category=article['main_category'],
                        subcategory=article['subcategory'],
                        description=article['description'],
                        scheduled_date=article['datetime'],
                        priority=article['priority'],
                        status='scheduled'
                    )
                    scheduled_pub.set_keywords_list(article['keywords'])
                    db.session.add(scheduled_pub)
                
                db.session.commit()
                result['saved_to_database'] = True
            
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error creating schedule: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@scheduling_bp.route('/api/schedule/<int:blog_id>')
def get_schedule_api(blog_id: int):
    """Get current schedule for a blog"""
    try:
        # Get upcoming scheduled publications
        upcoming_schedule = ScheduledPublication.query.filter(
            ScheduledPublication.blog_id == blog_id,
            ScheduledPublication.scheduled_date >= datetime.now()
        ).order_by(ScheduledPublication.scheduled_date.asc()).limit(100).all()
        
        schedule_data = [pub.to_dict() for pub in upcoming_schedule]
        
        # Generate statistics
        stats = _generate_schedule_api_stats(upcoming_schedule)
        
        return jsonify({
            'success': True,
            'blog_id': blog_id,
            'schedule': schedule_data,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting schedule for blog {blog_id}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@scheduling_bp.route('/api/schedule/<int:schedule_id>', methods=['PUT'])
def update_scheduled_publication(schedule_id: int):
    """Update a scheduled publication"""
    try:
        scheduled_pub = ScheduledPublication.query.get_or_404(schedule_id)
        data = request.get_json()
        
        # Update allowed fields
        if 'title' in data:
            scheduled_pub.title = data['title']
        if 'description' in data:
            scheduled_pub.description = data['description']
        if 'scheduled_date' in data:
            scheduled_pub.scheduled_date = datetime.fromisoformat(data['scheduled_date'])
        if 'priority' in data:
            scheduled_pub.priority = data['priority']
        if 'keywords' in data:
            scheduled_pub.set_keywords_list(data['keywords'])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Harmonogram zaktualizowany pomyślnie',
            'publication': scheduled_pub.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error updating scheduled publication {schedule_id}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@scheduling_bp.route('/api/schedule/<int:schedule_id>', methods=['DELETE'])
def delete_scheduled_publication(schedule_id: int):
    """Delete a scheduled publication"""
    try:
        scheduled_pub = ScheduledPublication.query.get_or_404(schedule_id)
        
        # Only allow deletion if not yet published
        if scheduled_pub.status == 'published':
            return jsonify({
                'success': False, 
                'error': 'Nie można usunąć już opublikowanego artykułu'
            }), 400
        
        db.session.delete(scheduled_pub)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Zaplanowany artykuł został usunięty'
        })
        
    except Exception as e:
        logger.error(f"Error deleting scheduled publication {schedule_id}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@scheduling_bp.route('/api/analytics/<int:blog_id>')
def get_scheduling_analytics(blog_id: int):
    """Get detailed analytics for publication scheduling"""
    try:
        # Get last 30 days of data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # Published articles in last 30 days
        published_articles = ScheduledPublication.query.filter(
            ScheduledPublication.blog_id == blog_id,
            ScheduledPublication.status == 'published',
            ScheduledPublication.published_at >= start_date,
            ScheduledPublication.published_at <= end_date
        ).all()
        
        # Upcoming articles (next 30 days)
        future_date = end_date + timedelta(days=30)
        upcoming_articles = ScheduledPublication.query.filter(
            ScheduledPublication.blog_id == blog_id,
            ScheduledPublication.status == 'scheduled',
            ScheduledPublication.scheduled_date >= end_date,
            ScheduledPublication.scheduled_date <= future_date
        ).all()
        
        # Generate analytics
        analytics = {
            'published_last_30_days': len(published_articles),
            'scheduled_next_30_days': len(upcoming_articles),
            'category_distribution': _analyze_category_distribution(published_articles + upcoming_articles),
            'daily_publishing_pattern': _analyze_daily_pattern(published_articles),
            'priority_distribution': _analyze_priority_distribution(upcoming_articles),
            'performance_metrics': {
                'avg_articles_per_day': len(published_articles) / 30,
                'most_productive_hour': _find_most_productive_hour(published_articles),
                'category_balance_score': _calculate_category_balance(upcoming_articles)
            }
        }
        
        return jsonify({
            'success': True,
            'blog_id': blog_id,
            'analytics': analytics
        })
        
    except Exception as e:
        logger.error(f"Error generating analytics for blog {blog_id}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@scheduling_bp.route('/calendar/<int:blog_id>')
def calendar_view(blog_id: int):
    """Calendar view of scheduled publications"""
    try:
        blog = Blog.query.get_or_404(blog_id)
        
        # Get current month data
        current_date = datetime.now()
        start_of_month = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_of_month = start_of_month + timedelta(days=32)
        end_of_month = end_of_month.replace(day=1) - timedelta(days=1)
        
        # Get scheduled publications for the month
        scheduled_pubs = ScheduledPublication.query.filter(
            ScheduledPublication.blog_id == blog_id,
            ScheduledPublication.scheduled_date >= start_of_month,
            ScheduledPublication.scheduled_date <= end_of_month
        ).order_by(ScheduledPublication.scheduled_date.asc()).all()
        
        # Group by date for calendar display
        calendar_data = {}
        for pub in scheduled_pubs:
            date_key = pub.scheduled_date.strftime('%Y-%m-%d')
            if date_key not in calendar_data:
                calendar_data[date_key] = []
            calendar_data[date_key].append({
                'id': pub.id,
                'title': pub.title,
                'time': pub.scheduled_date.strftime('%H:%M'),
                'category': pub.main_category,
                'subcategory': pub.subcategory,
                'status': pub.status,
                'priority': pub.priority
            })
        
        return render_template('scheduling/calendar.html',
                             blog=blog,
                             calendar_data=calendar_data,
                             current_date=current_date,
                             start_of_month=start_of_month,
                             end_of_month=end_of_month)
        
    except Exception as e:
        logger.error(f"Error loading calendar for blog {blog_id}: {str(e)}")
        return render_template('error.html',
                             error_message="Błąd podczas ładowania kalendarza publikacji")

# Helper functions for analytics

def _generate_schedule_api_stats(scheduled_publications: List[ScheduledPublication]) -> Dict[str, Any]:
    """Generate statistics for scheduled publications"""
    if not scheduled_publications:
        return {'total': 0}
    
    stats = {
        'total': len(scheduled_publications),
        'by_status': {},
        'by_category': {},
        'by_priority': {},
        'next_publication': None
    }
    
    # Count by status
    for pub in scheduled_publications:
        stats['by_status'][pub.status] = stats['by_status'].get(pub.status, 0) + 1
        stats['by_category'][pub.main_category] = stats['by_category'].get(pub.main_category, 0) + 1
        stats['by_priority'][str(pub.priority)] = stats['by_priority'].get(str(pub.priority), 0) + 1
    
    # Find next publication
    next_pub = min(scheduled_publications, key=lambda x: x.scheduled_date)
    stats['next_publication'] = {
        'title': next_pub.title,
        'date': next_pub.scheduled_date.isoformat(),
        'category': next_pub.main_category
    }
    
    return stats

def _analyze_category_distribution(publications: List[ScheduledPublication]) -> Dict[str, int]:
    """Analyze distribution of articles across categories"""
    distribution = {}
    for pub in publications:
        distribution[pub.main_category] = distribution.get(pub.main_category, 0) + 1
    return distribution

def _analyze_daily_pattern(publications: List[ScheduledPublication]) -> Dict[str, int]:
    """Analyze which days of week are most active"""
    pattern = {}
    days = ['Poniedziałek', 'Wtorek', 'Środa', 'Czwartek', 'Piątek', 'Sobota', 'Niedziela']
    
    for pub in publications:
        day_name = days[pub.published_at.weekday()] if pub.published_at else days[pub.scheduled_date.weekday()]
        pattern[day_name] = pattern.get(day_name, 0) + 1
    
    return pattern

def _analyze_priority_distribution(publications: List[ScheduledPublication]) -> Dict[str, int]:
    """Analyze priority distribution of upcoming articles"""
    distribution = {}
    for pub in publications:
        priority_label = f"Priorytet {pub.priority}"
        distribution[priority_label] = distribution.get(priority_label, 0) + 1
    return distribution

def _find_most_productive_hour(publications: List[ScheduledPublication]) -> str:
    """Find the hour with most publications"""
    if not publications:
        return "Brak danych"
    
    hour_counts = {}
    for pub in publications:
        hour = pub.published_at.hour if pub.published_at else pub.scheduled_date.hour
        hour_counts[hour] = hour_counts.get(hour, 0) + 1
    
    most_productive_hour = max(hour_counts, key=hour_counts.get)
    return f"{most_productive_hour:02d}:00"

def _calculate_category_balance(publications: List[ScheduledPublication]) -> float:
    """Calculate how balanced the category distribution is (0-100)"""
    if not publications:
        return 0.0
    
    category_counts = _analyze_category_distribution(publications)
    
    if len(category_counts) <= 1:
        return 0.0
    
    # Calculate coefficient of variation (lower = more balanced)
    counts = list(category_counts.values())
    mean_count = sum(counts) / len(counts)
    variance = sum((x - mean_count) ** 2 for x in counts) / len(counts)
    cv = (variance ** 0.5) / mean_count if mean_count > 0 else 0
    
    # Convert to balance score (0-100, where 100 is perfectly balanced)
    balance_score = max(0, 100 - (cv * 50))
    return round(balance_score, 1)