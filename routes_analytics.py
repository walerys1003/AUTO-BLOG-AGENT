import os
import json
import logging
import calendar
from datetime import datetime, timedelta, date
from typing import Dict, List, Any, Optional, Union, Tuple

from flask import render_template, request, redirect, url_for, flash, jsonify, abort
from sqlalchemy import desc, func

from app import db
from models import (
    Blog, ContentLog, ArticleTopic, ContentMetrics, 
    PerformanceReport, ContentCalendar, AnalyticsConfig
)
from utils.analytics.client import GA4Client
from utils.analytics.collector import AnalyticsCollector

logger = logging.getLogger(__name__)

def register_analytics_routes(app):
    """Register analytics routes with the Flask app"""
    
    @app.route('/analytics')
    def analytics_dashboard():
        """Analytics dashboard homepage"""
        # Get all blogs with analytics data
        blogs = Blog.query.all()
        
        blog_data = []
        for blog in blogs:
            # Get analytics config
            config = AnalyticsConfig.query.filter_by(blog_id=blog.id).first()
            
            # Get latest metrics
            metrics = ContentMetrics.query.filter_by(blog_id=blog.id).all()
            
            # Calculate total views and visitors
            total_views = sum(m.page_views for m in metrics) if metrics else 0
            total_visitors = sum(m.unique_visitors for m in metrics) if metrics else 0
            
            # Calculate engagement rate
            if total_views > 0:
                bounce_sum = sum(m.bounce_rate * m.page_views for m in metrics)
                avg_bounce = bounce_sum / total_views
                engagement_rate = 100 - avg_bounce
                engagement_percent = min(100, max(0, int(engagement_rate)))
            else:
                engagement_rate = 0
                engagement_percent = 0
            
            # Get post counts
            total_posts = ContentLog.query.filter_by(blog_id=blog.id, status='published').count()
            posts_with_metrics = len(metrics)
            
            blog_data.append({
                'id': blog.id,
                'name': blog.name,
                'analytics_configured': config is not None and config.active,
                'total_views': total_views,
                'total_visitors': total_visitors,
                'engagement_rate': f"{engagement_rate:.1f}%",
                'engagement_percent': engagement_percent,
                'last_sync': config.last_sync if config and config.active else None,
                'posts_with_metrics': posts_with_metrics,
                'total_posts': total_posts
            })
        
        # Get overall statistics
        total_stats = None
        top_posts = []
        recent_reports = []
        ai_insights = None
        
        if blogs:
            # Calculate total stats
            all_metrics = ContentMetrics.query.filter(
                ContentMetrics.updated_at >= datetime.utcnow() - timedelta(days=30)
            ).all()
            
            if all_metrics:
                total_views = sum(m.page_views for m in all_metrics)
                total_visitors = sum(m.unique_visitors for m in all_metrics)
                
                # Calculate weighted averages
                total_weighted_time = sum(m.avg_time_on_page * m.page_views for m in all_metrics)
                avg_time = total_weighted_time / total_views if total_views > 0 else 0
                
                total_weighted_bounce = sum(m.bounce_rate * m.page_views for m in all_metrics)
                avg_bounce = total_weighted_bounce / total_views if total_views > 0 else 0
                
                total_stats = {
                    'total_views': total_views,
                    'total_visitors': total_visitors,
                    'avg_time': avg_time,
                    'avg_bounce': avg_bounce
                }
            
            # Get top posts
            top_metrics = ContentMetrics.query.order_by(ContentMetrics.page_views.desc()).limit(5).all()
            for metric in top_metrics:
                blog_name = Blog.query.get(metric.blog_id).name if Blog.query.get(metric.blog_id) else "Unknown"
                top_posts.append({
                    'title': metric.title,
                    'blog_name': blog_name,
                    'views': metric.page_views,
                    'url': metric.url
                })
            
            # Get recent reports
            recent_reports = PerformanceReport.query.order_by(PerformanceReport.created_at.desc()).limit(5).all()
            
            # Get AI insights
            latest_report = PerformanceReport.query.order_by(PerformanceReport.created_at.desc()).first()
            if latest_report:
                ai_insights = {
                    'insights': latest_report.get_insights(),
                    'recommendations': latest_report.get_recommendations()
                }
        
        return render_template('analytics/dashboard.html', 
                              blogs=blog_data, 
                              total_stats=total_stats,
                              top_posts=top_posts,
                              recent_reports=recent_reports,
                              ai_insights=ai_insights)
    
    @app.route('/analytics/config')
    def analytics_config():
        """Google Analytics configuration page"""
        # Get all blogs
        blogs = Blog.query.all()
        
        # Get global config
        global_config = {
            'measurement_id': os.environ.get('GA4_MEASUREMENT_ID', ''),
            'api_secret': os.environ.get('GA4_API_SECRET', ''),
            'sync_frequency': 24,  # Default: daily
            'enabled': True
        }
        
        # Add analytics config to each blog
        for blog in blogs:
            blog.config = AnalyticsConfig.query.filter_by(blog_id=blog.id).first()
        
        return render_template('analytics/config.html', blogs=blogs, global_config=global_config)
    
    @app.route('/analytics/save-global', methods=['POST'])
    def save_global_analytics():
        """Save global Google Analytics configuration"""
        try:
            measurement_id = request.form.get('ga4_measurement_id', '')
            api_secret = request.form.get('ga4_api_secret', '')
            sync_frequency = int(request.form.get('sync_frequency', 24))
            enable_global = 'enable_global' in request.form
            
            # Save environment variables
            if enable_global and measurement_id:
                os.environ['GA4_MEASUREMENT_ID'] = measurement_id
                
                if api_secret:
                    os.environ['GA4_API_SECRET'] = api_secret
                
                flash('Globalna konfiguracja Google Analytics została zapisana.', 'success')
            else:
                # Optionally remove from environment if disabled
                if 'GA4_MEASUREMENT_ID' in os.environ:
                    del os.environ['GA4_MEASUREMENT_ID']
                
                flash('Globalna konfiguracja Google Analytics została wyłączona.', 'warning')
            
            return redirect(url_for('analytics_config'))
        
        except Exception as e:
            logger.error(f"Error saving global analytics config: {str(e)}")
            flash(f'Błąd podczas zapisywania globalnej konfiguracji: {str(e)}', 'danger')
            return redirect(url_for('analytics_config'))
    
    @app.route('/analytics/save-blog/<int:blog_id>', methods=['POST'])
    def save_blog_analytics(blog_id):
        """Save blog-specific Google Analytics configuration"""
        try:
            blog = Blog.query.get_or_404(blog_id)
            
            property_id = request.form.get('property_id', '')
            measurement_id = request.form.get('measurement_id', '')
            tracking_code = request.form.get('tracking_code', '')
            active = 'active' in request.form
            
            sync_frequency_str = request.form.get('sync_frequency', '0')
            sync_frequency = int(sync_frequency_str) if sync_frequency_str and sync_frequency_str != '0' else None
            
            # Find or create config
            config = AnalyticsConfig.query.filter_by(blog_id=blog_id).first()
            if not config:
                config = AnalyticsConfig(blog_id=blog_id)
                db.session.add(config)
            
            # Update config
            config.property_id = property_id
            config.measurement_id = measurement_id
            config.tracking_code = tracking_code
            config.active = active
            
            if sync_frequency is not None:
                config.sync_frequency = sync_frequency
            
            db.session.commit()
            
            flash(f'Konfiguracja Google Analytics dla bloga {blog.name} została zapisana.', 'success')
            return redirect(url_for('analytics_config'))
        
        except Exception as e:
            logger.error(f"Error saving blog analytics config: {str(e)}")
            db.session.rollback()
            flash(f'Błąd podczas zapisywania konfiguracji: {str(e)}', 'danger')
            return redirect(url_for('analytics_config'))
    
    @app.route('/analytics/sync/<blog_id>')
    def sync_analytics(blog_id):
        """Sync analytics data for a blog or all blogs"""
        try:
            # Create client and collector
            ga4_client = GA4Client()
            collector = AnalyticsCollector(ga4_client)
            
            if blog_id == 'all':
                # Sync all blogs
                blogs = Blog.query.filter_by(active=True).all()
                results = []
                
                for blog in blogs:
                    config = AnalyticsConfig.query.filter_by(blog_id=blog.id, active=True).first()
                    if config:
                        result = collector.sync_blog_metrics(blog.id)
                        results.append(result)
                
                # Check results
                success_count = len([r for r in results if 'error' not in r])
                if success_count == 0 and results:
                    flash('Nie udało się zsynchronizować danych dla żadnego bloga.', 'danger')
                elif success_count < len(results):
                    flash(f'Zsynchronizowano dane dla {success_count} z {len(results)} blogów.', 'warning')
                else:
                    flash(f'Zsynchronizowano dane dla wszystkich {len(results)} blogów.', 'success')
            else:
                # Sync specific blog
                blog_id = int(blog_id)
                blog = Blog.query.get_or_404(blog_id)
                
                result = collector.sync_blog_metrics(blog_id)
                
                if 'error' in result:
                    flash(f'Błąd synchronizacji danych dla bloga {blog.name}: {result["error"]}', 'danger')
                elif result.get('status') == 'no_posts':
                    flash(f'Brak opublikowanych postów do synchronizacji dla bloga {blog.name}.', 'warning')
                else:
                    flash(f'Zsynchronizowano dane dla {result.get("synced_posts", 0)} postów z bloga {blog.name}.', 'success')
            
            # Redirect back to referring page or dashboard
            return redirect(request.referrer or url_for('analytics_dashboard'))
        
        except Exception as e:
            logger.error(f"Error syncing analytics: {str(e)}")
            flash(f'Błąd podczas synchronizacji analityki: {str(e)}', 'danger')
            return redirect(url_for('analytics_dashboard'))
    
    @app.route('/analytics/blog/<int:blog_id>')
    def blog_analytics(blog_id):
        """View detailed analytics for a specific blog"""
        blog = Blog.query.get_or_404(blog_id)
        
        # Get all metrics for this blog
        metrics = ContentMetrics.query.filter_by(blog_id=blog_id).all()
        
        # Get content logs
        logs = ContentLog.query.filter_by(blog_id=blog_id, status='published').all()
        
        # Build content statistics
        total_posts = len(logs)
        posts_with_metrics = len(metrics)
        total_views = sum(m.page_views for m in metrics) if metrics else 0
        total_visitors = sum(m.unique_visitors for m in metrics) if metrics else 0
        
        # Calculate bounce and engagement rates
        if total_views > 0:
            total_weighted_bounce = sum(m.bounce_rate * m.page_views for m in metrics)
            avg_bounce_rate = total_weighted_bounce / total_views
            engagement_rate = 100 - avg_bounce_rate
        else:
            avg_bounce_rate = 0
            engagement_rate = 0
        
        # Get top posts
        top_posts = sorted(metrics, key=lambda m: m.page_views, reverse=True)[:10]
        
        # Get recent reports
        reports = PerformanceReport.query.filter_by(blog_id=blog_id).order_by(PerformanceReport.created_at.desc()).limit(5).all()
        
        # Get analytics config
        config = AnalyticsConfig.query.filter_by(blog_id=blog_id).first()
        
        stats = {
            'blog': blog,
            'total_posts': total_posts,
            'posts_with_metrics': posts_with_metrics,
            'total_views': total_views,
            'total_visitors': total_visitors,
            'avg_bounce_rate': avg_bounce_rate,
            'engagement_rate': engagement_rate,
            'config': config,
            'top_posts': top_posts,
            'reports': reports
        }
        
        return render_template('analytics/blog.html', **stats)
    
    @app.route('/analytics/reports')
    def analytics_reports():
        """View all performance reports"""
        # Get filter parameters
        selected_blog_id = request.args.get('blog_id', 'all')
        selected_type = request.args.get('report_type', 'all')
        days = int(request.args.get('date_range', 30))
        page = request.args.get('page', 1, type=int)
        
        # Base query
        query = PerformanceReport.query
        
        # Apply blog filter
        if selected_blog_id != 'all':
            query = query.filter_by(blog_id=int(selected_blog_id))
        
        # Apply report type filter
        if selected_type != 'all':
            query = query.filter_by(report_type=selected_type)
        
        # Apply date filter
        start_date = datetime.utcnow() - timedelta(days=days)
        query = query.filter(PerformanceReport.created_at >= start_date)
        
        # Paginate results
        per_page = 15
        reports = query.order_by(PerformanceReport.created_at.desc()).paginate(page=page, per_page=per_page)
        
        # Get all blogs for filter dropdown
        blogs = Blog.query.all()
        
        return render_template('analytics/reports.html', 
                              reports=reports, 
                              blogs=blogs,
                              selected_blog_id=selected_blog_id,
                              selected_type=selected_type,
                              days=days)
    
    @app.route('/analytics/reports/<int:report_id>')
    def view_report(report_id):
        """View a specific performance report"""
        report = PerformanceReport.query.get_or_404(report_id)
        
        # Get report data
        top_posts = report.get_top_posts()
        insights = report.get_insights()
        recommendations = report.get_recommendations()
        
        return render_template('analytics/report.html', 
                              report=report,
                              top_posts=top_posts,
                              insights=insights,
                              recommendations=recommendations)
    
    @app.route('/analytics/reports/generate/<int:blog_id>/<report_type>')
    def generate_report(blog_id, report_type):
        """Generate a new performance report"""
        try:
            blog = Blog.query.get_or_404(blog_id)
            
            # Validate report type
            valid_types = ['daily', 'weekly', 'monthly', 'quarterly']
            if report_type not in valid_types:
                flash(f'Nieprawidłowy typ raportu: {report_type}', 'danger')
                return redirect(url_for('analytics_reports'))
            
            # Create analytics collector
            collector = AnalyticsCollector()
            
            # Generate report
            report = collector.generate_performance_report(blog_id, report_type)
            
            if isinstance(report, dict) and 'error' in report:
                flash(f'Błąd generowania raportu: {report["error"]}', 'danger')
                return redirect(url_for('analytics_reports'))
            
            flash(f'Raport {report_type} dla bloga {blog.name} został wygenerowany pomyślnie.', 'success')
            return redirect(url_for('view_report', report_id=report.id))
        
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            flash(f'Błąd podczas generowania raportu: {str(e)}', 'danger')
            return redirect(url_for('analytics_reports'))
    
    @app.route('/analytics/reports/custom', methods=['GET', 'POST'])
    def custom_report():
        """Generate a custom performance report"""
        if request.method == 'POST':
            try:
                blog_id = request.form.get('blog_id', type=int)
                start_date_str = request.form.get('start_date')
                end_date_str = request.form.get('end_date')
                
                if not blog_id or not start_date_str or not end_date_str:
                    flash('Wszystkie pola są wymagane', 'danger')
                    return redirect(url_for('custom_report'))
                
                blog = Blog.query.get_or_404(blog_id)
                
                # Parse dates
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                
                # Validate date range
                if end_date < start_date:
                    flash('Data końcowa musi być późniejsza niż data początkowa', 'danger')
                    return redirect(url_for('custom_report'))
                
                # Create analytics collector
                collector = AnalyticsCollector()
                
                # Generate custom report
                report = collector.generate_performance_report(
                    blog_id=blog_id,
                    report_type='custom',
                    start_date=start_date,
                    end_date=end_date
                )
                
                if isinstance(report, dict) and 'error' in report:
                    flash(f'Błąd generowania raportu: {report["error"]}', 'danger')
                    return redirect(url_for('custom_report'))
                
                flash(f'Niestandardowy raport dla bloga {blog.name} został wygenerowany pomyślnie.', 'success')
                return redirect(url_for('view_report', report_id=report.id))
            
            except Exception as e:
                logger.error(f"Error generating custom report: {str(e)}")
                flash(f'Błąd podczas generowania raportu: {str(e)}', 'danger')
                return redirect(url_for('custom_report'))
        
        # GET request - show form
        blogs = Blog.query.all()
        
        return render_template('analytics/custom_report.html', blogs=blogs)
    
    @app.route('/analytics/reports/download/<int:report_id>/<format>')
    def download_report(report_id, format):
        """Download a report in a specific format"""
        # This is a placeholder that would be implemented with a PDF generation library
        report = PerformanceReport.query.get_or_404(report_id)
        
        if format != 'pdf':
            flash(f'Format {format} nie jest obsługiwany.', 'danger')
            return redirect(url_for('view_report', report_id=report_id))
        
        # Placeholder for PDF generation
        flash('Eksport do PDF nie jest jeszcze zaimplementowany.', 'warning')
        return redirect(url_for('view_report', report_id=report_id))
    
    @app.route('/analytics/reports/delete', methods=['POST'])
    def delete_report():
        """Delete a performance report"""
        try:
            report_id = request.form.get('report_id', type=int)
            if not report_id:
                flash('ID raportu jest wymagane', 'danger')
                return redirect(url_for('analytics_reports'))
            
            report = PerformanceReport.query.get_or_404(report_id)
            blog_name = report.blog.name
            
            db.session.delete(report)
            db.session.commit()
            
            flash(f'Raport dla bloga {blog_name} został usunięty.', 'success')
            return redirect(url_for('analytics_reports'))
        
        except Exception as e:
            logger.error(f"Error deleting report: {str(e)}")
            db.session.rollback()
            flash(f'Błąd podczas usuwania raportu: {str(e)}', 'danger')
            return redirect(url_for('analytics_reports'))
    
    @app.route('/analytics/calendar')
    def content_calendar():
        """View content calendar"""
        # Get filter parameters
        selected_blog_id = request.args.get('blog_id', 'all')
        selected_status = request.args.get('status', 'all')
        
        # Get year and month
        today = datetime.utcnow()
        year = int(request.args.get('year', today.year))
        month = int(request.args.get('month', today.month))
        
        # Create calendar date
        current_date = date(year, month, 1)
        
        # Get previous and next month
        prev_month = date(year, month - 1, 1) if month > 1 else date(year - 1, 12, 1)
        next_month = date(year, month + 1, 1) if month < 12 else date(year + 1, 1, 1)
        
        # Build calendar
        cal = calendar.monthcalendar(year, month)
        
        # Get all calendar entries
        query = ContentCalendar.query
        
        # Filter by blog if specified
        if selected_blog_id != 'all':
            query = query.filter_by(blog_id=int(selected_blog_id))
        
        # Filter by status if specified
        if selected_status != 'all':
            query = query.filter_by(status=selected_status)
        
        # Get all entries for current month and surrounding dates
        start_date = date(year, month, 1) - timedelta(days=7)  # Include previous month overflow
        end_date = date(year, month, calendar.monthrange(year, month)[1]) + timedelta(days=7)  # Include next month overflow
        
        entries = query.filter(
            ContentCalendar.scheduled_date >= datetime.combine(start_date, datetime.min.time()),
            ContentCalendar.scheduled_date <= datetime.combine(end_date, datetime.max.time())
        ).all()
        
        # Organize entries by date
        entries_by_date = {}
        for entry in entries:
            entry_date = entry.scheduled_date.date()
            if entry_date not in entries_by_date:
                entries_by_date[entry_date] = []
                
            # Get blog name
            blog_name = Blog.query.get(entry.blog_id).name if Blog.query.get(entry.blog_id) else "Unknown"
            
            # Format time
            entry_time = entry.scheduled_date.strftime('%H:%M') if entry.scheduled_date.hour or entry.scheduled_date.minute else None
            
            entries_by_date[entry_date].append({
                'id': entry.id,
                'title': entry.title,
                'blog_name': blog_name,
                'time': entry_time,
                'status': entry.status,
                'priority': entry.priority,
                'notes': entry.notes
            })
        
        # Build calendar weeks with entries
        calendar_weeks = []
        for week in cal:
            week_data = []
            for day in week:
                if day == 0:
                    # Day outside the month
                    week_data.append({'date': None})
                else:
                    day_date = date(year, month, day)
                    day_entries = entries_by_date.get(day_date, [])
                    
                    week_data.append({
                        'date': day_date,
                        'current_month': True,
                        'today': day_date == date.today(),
                        'weekday': day_date.weekday(),
                        'entries': day_entries
                    })
            calendar_weeks.append(week_data)
        
        # Add days from previous month
        first_day_weekday = date(year, month, 1).weekday()
        if first_day_weekday > 0:
            prev_month_days = calendar.monthrange(prev_month.year, prev_month.month)[1]
            for i in range(first_day_weekday):
                day = prev_month_days - first_day_weekday + i + 1
                day_date = date(prev_month.year, prev_month.month, day)
                day_entries = entries_by_date.get(day_date, [])
                
                calendar_weeks[0][i] = {
                    'date': day_date,
                    'current_month': False,
                    'today': day_date == date.today(),
                    'weekday': day_date.weekday(),
                    'entries': day_entries
                }
        
        # Add days from next month
        last_day_weekday = date(year, month, calendar.monthrange(year, month)[1]).weekday()
        if last_day_weekday < 6:
            for i in range(6 - last_day_weekday):
                day = i + 1
                day_date = date(next_month.year, next_month.month, day)
                day_entries = entries_by_date.get(day_date, [])
                
                calendar_weeks[-1][last_day_weekday + i + 1] = {
                    'date': day_date,
                    'current_month': False,
                    'today': day_date == date.today(),
                    'weekday': day_date.weekday(),
                    'entries': day_entries
                }
        
        # Get all blogs
        blogs = Blog.query.all()
        
        return render_template('analytics/calendar.html',
                              current_date=current_date,
                              prev_month=prev_month,
                              next_month=next_month,
                              calendar_weeks=calendar_weeks,
                              blogs=blogs,
                              selected_blog_id=selected_blog_id,
                              selected_status=selected_status)
    
    @app.route('/analytics/calendar/add', methods=['GET', 'POST'])
    def add_calendar_entry():
        """Add a new calendar entry"""
        if request.method == 'POST':
            try:
                blog_id = request.form.get('blog_id', type=int)
                title = request.form.get('title')
                scheduled_date_str = request.form.get('scheduled_date')
                scheduled_time_str = request.form.get('scheduled_time', '00:00')
                status = request.form.get('status')
                priority = request.form.get('priority', type=int)
                notes = request.form.get('notes')
                topic_id = request.form.get('topic_id', type=int)
                
                if not blog_id or not title or not scheduled_date_str or not status:
                    flash('Wszystkie wymagane pola muszą być wypełnione', 'danger')
                    return redirect(url_for('add_calendar_entry'))
                
                # Parse date and time
                scheduled_date = datetime.strptime(scheduled_date_str, '%Y-%m-%d')
                if scheduled_time_str:
                    time_parts = scheduled_time_str.split(':')
                    scheduled_date = scheduled_date.replace(
                        hour=int(time_parts[0]), 
                        minute=int(time_parts[1])
                    )
                
                # Create new entry
                entry = ContentCalendar(
                    blog_id=blog_id,
                    topic_id=topic_id if topic_id else None,
                    title=title,
                    scheduled_date=scheduled_date,
                    status=status,
                    priority=priority,
                    notes=notes
                )
                
                db.session.add(entry)
                
                # If this is linked to a topic, update topic status
                if topic_id:
                    topic = ArticleTopic.query.get(topic_id)
                    if topic and topic.status == 'approved':
                        topic.status = 'scheduled'
                
                db.session.commit()
                
                flash('Wpis dodany do kalendarza treści', 'success')
                return redirect(url_for('content_calendar'))
            
            except Exception as e:
                logger.error(f"Error adding calendar entry: {str(e)}")
                db.session.rollback()
                flash(f'Błąd podczas dodawania wpisu: {str(e)}', 'danger')
                return redirect(url_for('add_calendar_entry'))
        
        # GET request - show form
        blogs = Blog.query.all()
        
        # Get approved topics
        topics = ArticleTopic.query.filter_by(status='approved').all()
        
        return render_template('analytics/calendar_form.html',
                              entry=None,
                              blogs=blogs,
                              topics=topics,
                              today=datetime.utcnow())
    
    @app.route('/analytics/calendar/edit/<int:entry_id>', methods=['GET', 'POST'])
    def edit_calendar_entry(entry_id):
        """Edit a calendar entry"""
        entry = ContentCalendar.query.get_or_404(entry_id)
        
        if request.method == 'POST':
            try:
                blog_id = request.form.get('blog_id', type=int)
                title = request.form.get('title')
                scheduled_date_str = request.form.get('scheduled_date')
                scheduled_time_str = request.form.get('scheduled_time', '00:00')
                status = request.form.get('status')
                priority = request.form.get('priority', type=int)
                notes = request.form.get('notes')
                topic_id = request.form.get('topic_id', type=int)
                
                if not blog_id or not title or not scheduled_date_str or not status:
                    flash('Wszystkie wymagane pola muszą być wypełnione', 'danger')
                    return redirect(url_for('edit_calendar_entry', entry_id=entry_id))
                
                # Parse date and time
                scheduled_date = datetime.strptime(scheduled_date_str, '%Y-%m-%d')
                if scheduled_time_str:
                    time_parts = scheduled_time_str.split(':')
                    scheduled_date = scheduled_date.replace(
                        hour=int(time_parts[0]), 
                        minute=int(time_parts[1])
                    )
                
                # Update entry
                entry.blog_id = blog_id
                entry.topic_id = topic_id if topic_id else None
                entry.title = title
                entry.scheduled_date = scheduled_date
                entry.status = status
                entry.priority = priority
                entry.notes = notes
                
                # Update topic status if needed
                old_topic_id = entry.topic_id
                if old_topic_id and old_topic_id != topic_id:
                    old_topic = ArticleTopic.query.get(old_topic_id)
                    if old_topic and old_topic.status == 'scheduled':
                        old_topic.status = 'approved'
                
                if topic_id and topic_id != old_topic_id:
                    new_topic = ArticleTopic.query.get(topic_id)
                    if new_topic and new_topic.status == 'approved':
                        new_topic.status = 'scheduled'
                
                db.session.commit()
                
                flash('Wpis w kalendarzu został zaktualizowany', 'success')
                return redirect(url_for('content_calendar'))
            
            except Exception as e:
                logger.error(f"Error updating calendar entry: {str(e)}")
                db.session.rollback()
                flash(f'Błąd podczas aktualizacji wpisu: {str(e)}', 'danger')
                return redirect(url_for('edit_calendar_entry', entry_id=entry_id))
        
        # GET request - show form
        blogs = Blog.query.all()
        
        # Get topics
        topics = ArticleTopic.query.filter(
            (ArticleTopic.status == 'approved') | 
            (ArticleTopic.id == entry.topic_id)
        ).all()
        
        return render_template('analytics/calendar_form.html',
                              entry=entry,
                              blogs=blogs,
                              topics=topics,
                              today=datetime.utcnow())
    
    @app.route('/analytics/calendar/delete', methods=['POST'])
    def delete_calendar_entry():
        """Delete a calendar entry"""
        try:
            entry_id = request.form.get('entry_id', type=int)
            if not entry_id:
                flash('ID wpisu jest wymagane', 'danger')
                return redirect(url_for('content_calendar'))
            
            entry = ContentCalendar.query.get_or_404(entry_id)
            
            # Update topic status if linked
            if entry.topic_id:
                topic = ArticleTopic.query.get(entry.topic_id)
                if topic and topic.status == 'scheduled':
                    topic.status = 'approved'
            
            db.session.delete(entry)
            db.session.commit()
            
            flash('Wpis został usunięty z kalendarza', 'success')
            return redirect(url_for('content_calendar'))
        
        except Exception as e:
            logger.error(f"Error deleting calendar entry: {str(e)}")
            db.session.rollback()
            flash(f'Błąd podczas usuwania wpisu: {str(e)}', 'danger')
            return redirect(url_for('content_calendar'))
    
    @app.route('/analytics/plan', methods=['GET', 'POST'])
    def generate_content_plan():
        """Generate content plan based on analytics"""
        if request.method == 'POST':
            try:
                blog_id = request.form.get('blog_id', type=int)
                days_ahead = request.form.get('days_ahead', type=int, default=30)
                posts_per_day = request.form.get('posts_per_day', type=int)
                
                if not blog_id:
                    flash('Blog jest wymagany', 'danger')
                    return redirect(url_for('generate_content_plan'))
                
                # Make sure blog exists
                blog = Blog.query.get_or_404(blog_id)
                
                # Create collector
                collector = AnalyticsCollector()
                
                # Generate plan
                result = collector.schedule_content_based_on_performance(
                    blog_id=blog_id,
                    days_ahead=days_ahead,
                    posts_per_day=posts_per_day if posts_per_day else None
                )
                
                if 'error' in result:
                    flash(f'Błąd generowania planu: {result["error"]}', 'danger')
                    return redirect(url_for('generate_content_plan'))
                
                flash(f'Plan treści dla bloga {blog.name} został wygenerowany. Zaplanowano {result["total_scheduled"]} wpisów.', 'success')
                return redirect(url_for('content_calendar'))
            
            except Exception as e:
                logger.error(f"Error generating content plan: {str(e)}")
                flash(f'Błąd podczas generowania planu treści: {str(e)}', 'danger')
                return redirect(url_for('generate_content_plan'))
        
        # GET request - show form
        blogs = Blog.query.all()
        
        # Get topic counts
        topic_counts = {}
        for blog in blogs:
            topic_counts[blog.id] = ArticleTopic.query.filter_by(
                blog_id=blog.id, 
                status='approved'
            ).count()
        
        return render_template('analytics/plan.html',
                              blogs=blogs,
                              topic_counts=topic_counts)