"""
Publication management routes
Handle content publication scheduling, review, and management
"""
import logging
import json
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from sqlalchemy import or_, and_, desc
from app import db
from models import Blog, ContentLog, Category, Tag, PublishingSchedule, AutomationRule, SystemSettings, Notification
from utils.wordpress.client import get_wordpress_post, update_wordpress_post
from utils.notifications import send_notification

# Setup logging
logger = logging.getLogger(__name__)

# Create blueprint
publishing_bp = Blueprint('publishing', __name__, url_prefix='/publishing')

@publishing_bp.route('/')
def publishing_dashboard():
    """Publishing dashboard - overview of publication status"""
    # Get blogs for filter
    blogs = Blog.query.all()
    selected_blog_id = request.args.get('blog_id', type=int)
    
    # Get statistics
    pending_count = ContentLog.query.filter_by(status='scheduled').count()
    published_count = ContentLog.query.filter_by(status='published').count()
    failed_count = ContentLog.query.filter_by(status='failed').count()
    
    # Get latest published articles
    query = ContentLog.query.order_by(ContentLog.publish_date.desc())
    
    # Filter by blog if selected
    if selected_blog_id:
        query = query.filter_by(blog_id=selected_blog_id)
    
    # Get recent articles
    recent_articles = query.limit(5).all()
    
    # Get publishing schedule summary
    today = datetime.now().date()
    next_week = today + timedelta(days=7)
    
    schedule_query = PublishingSchedule.query.filter(
        PublishingSchedule.publish_date >= today,
        PublishingSchedule.publish_date <= next_week
    )
    
    if selected_blog_id:
        schedule_query = schedule_query.filter_by(blog_id=selected_blog_id)
    
    schedule_summary = schedule_query.all()
    
    # Group by date for the chart
    schedule_by_date = {}
    for item in schedule_summary:
        date_str = item.publish_date.strftime('%Y-%m-%d')
        if date_str not in schedule_by_date:
            schedule_by_date[date_str] = 0
        schedule_by_date[date_str] += 1
    
    return render_template(
        'publishing/dashboard.html',
        blogs=blogs,
        selected_blog_id=selected_blog_id,
        pending_count=pending_count,
        published_count=published_count,
        failed_count=failed_count,
        recent_articles=recent_articles,
        schedule_summary=schedule_summary,
        schedule_by_date=schedule_by_date
    )

@publishing_bp.route('/schedule')
def publishing_schedule():
    """View and manage publishing schedule"""
    # Get blogs for filter
    blogs = Blog.query.all()
    selected_blog_id = request.args.get('blog_id', type=int)
    
    # Get date range - default to current month
    today = datetime.now().date()
    start_date = request.args.get('start_date', 
                               (today.replace(day=1)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', 
                             (today.replace(day=1) + timedelta(days=31)).strftime('%Y-%m-%d'))
    
    # Parse dates
    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid date format. Using default date range.', 'warning')
        start_date = today.replace(day=1)
        end_date = (today.replace(day=1) + timedelta(days=31))
    
    # Build query
    query = PublishingSchedule.query.filter(
        PublishingSchedule.publish_date >= start_date,
        PublishingSchedule.publish_date <= end_date
    ).order_by(PublishingSchedule.publish_date)
    
    # Filter by blog if selected
    if selected_blog_id:
        query = query.filter_by(blog_id=selected_blog_id)
    
    # Get schedule items
    schedule_items = query.all()
    
    # Format for calendar
    calendar_events = []
    for item in schedule_items:
        # Get associated content
        content = ContentLog.query.filter_by(id=item.content_id).first()
        title = content.title if content else "Untitled"
        status = content.status if content else "unknown"
        
        # Color coding based on status
        color = "#3788d8"  # Default blue
        if status == "published":
            color = "#28a745"  # Green
        elif status == "failed":
            color = "#dc3545"  # Red
        elif status == "scheduled":
            color = "#17a2b8"  # Cyan
        elif status == "draft":
            color = "#6c757d"  # Gray
        
        # Create event object
        event = {
            "id": item.id,
            "title": title,
            "start": item.publish_date.strftime('%Y-%m-%d') + "T" + item.publish_time.strftime('%H:%M:%S'),
            "color": color,
            "extendedProps": {
                "content_id": item.content_id,
                "blog_id": item.blog_id,
                "status": status
            }
        }
        calendar_events.append(event)
    
    # Get automation status
    automation_status = {}
    for blog in blogs:
        active_rules = AutomationRule.query.filter_by(
            blog_id=blog.id, 
            is_active=True
        ).count()
        
        automation_status[blog.id] = {
            "active": active_rules > 0,
            "rule_count": active_rules
        }
    
    return render_template(
        'publishing/schedule.html',
        blogs=blogs,
        selected_blog_id=selected_blog_id,
        start_date=start_date,
        end_date=end_date,
        calendar_events=json.dumps(calendar_events),
        automation_status=automation_status
    )

@publishing_bp.route('/schedule/update', methods=['POST'])
def update_schedule():
    """Update publishing schedule item"""
    try:
        data = request.json
        schedule_id = data.get('id')
        new_date = data.get('date')
        new_time = data.get('time')
        
        # Get schedule item
        schedule_item = PublishingSchedule.query.get_or_404(schedule_id)
        
        # Update date and time
        if new_date:
            schedule_item.publish_date = datetime.strptime(new_date, '%Y-%m-%d').date()
        
        if new_time:
            schedule_item.publish_time = datetime.strptime(new_time, '%H:%M').time()
        
        # Save changes
        db.session.commit()
        
        # Also update content log if it exists
        content = ContentLog.query.filter_by(id=schedule_item.content_id).first()
        if content:
            # Combine date and time
            publish_datetime = datetime.combine(
                schedule_item.publish_date, 
                schedule_item.publish_time
            )
            content.publish_date = publish_datetime
            db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Schedule updated successfully'
        })
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating schedule: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@publishing_bp.route('/schedule/toggle-automation', methods=['POST'])
def toggle_automation():
    """Toggle automation for a blog"""
    try:
        data = request.json
        blog_id = data.get('blog_id')
        status = data.get('status', False)
        
        # Get all automation rules for the blog
        rules = AutomationRule.query.filter_by(blog_id=blog_id).all()
        
        # Update status
        for rule in rules:
            rule.is_active = status
        
        # Save changes
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Automation {"enabled" if status else "disabled"} successfully'
        })
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error toggling automation: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@publishing_bp.route('/pending')
def pending_articles():
    """View and manage pending articles"""
    # Get blogs for filter
    blogs = Blog.query.all()
    selected_blog_id = request.args.get('blog_id', type=int)
    status_filter = request.args.get('status', 'scheduled')
    
    # Build query
    query = ContentLog.query
    
    # Filter by status
    if status_filter == 'all':
        # No status filter
        pass
    else:
        query = query.filter_by(status=status_filter)
    
    # Filter by blog if selected
    if selected_blog_id:
        query = query.filter_by(blog_id=selected_blog_id)
    
    # Order by publish date
    query = query.order_by(ContentLog.publish_date)
    
    # Get articles
    articles = query.all()
    
    return render_template(
        'publishing/pending.html',
        blogs=blogs,
        selected_blog_id=selected_blog_id,
        status_filter=status_filter,
        articles=articles
    )

@publishing_bp.route('/edit/<int:content_id>', methods=['GET', 'POST'])
def edit_article(content_id):
    """Edit article before publication"""
    # Get content
    content = ContentLog.query.get_or_404(content_id)
    
    # Get blog
    blog = Blog.query.get_or_404(content.blog_id)
    
    # Get categories
    categories = Category.query.filter_by(blog_id=blog.id).all()
    
    if request.method == 'POST':
        try:
            # Update content
            content.title = request.form.get('title')
            content.content = request.form.get('content')
            content.excerpt = request.form.get('excerpt', '')
            
            # Get featured image
            featured_image = request.form.get('featured_image')
            if featured_image:
                content.featured_image_data = featured_image
            
            # Update category
            category_id = request.form.get('category_id')
            if category_id:
                content.category_id = category_id
            
            # Update tags
            tags = request.form.get('tags', '')
            content.set_tags([tag.strip() for tag in tags.split(',')])
            
            # Update meta data
            meta_title = request.form.get('meta_title')
            meta_description = request.form.get('meta_description')
            
            if meta_title or meta_description:
                # Parse existing metadata or create new
                try:
                    metadata = json.loads(content.metadata or '{}')
                except:
                    metadata = {}
                
                if meta_title:
                    metadata['title'] = meta_title
                
                if meta_description:
                    metadata['description'] = meta_description
                
                content.metadata = json.dumps(metadata)
            
            # Save changes
            db.session.commit()
            
            # If the post is already published, update it on WordPress
            if content.status == 'published' and content.post_id:
                success, post_id, error = update_wordpress_post(
                    blog_id=content.blog_id,
                    post_id=content.post_id,
                    title=content.title,
                    content=content.content,
                    excerpt=content.excerpt,
                    category_id=content.category_id,
                    tags=content.get_tags()
                )
                
                if not success:
                    flash(f'Warning: Post updated locally but failed to update on WordPress: {error}', 'warning')
            
            flash('Article updated successfully', 'success')
            return redirect(url_for('publishing.pending_articles'))
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating article: {str(e)}")
            flash(f'Error updating article: {str(e)}', 'danger')
    
    # For GET request, show edit form
    # Parse metadata
    try:
        metadata = json.loads(content.metadata or '{}')
    except:
        metadata = {}
    
    # Render template
    return render_template(
        'publishing/edit.html',
        content=content,
        blog=blog,
        categories=categories,
        metadata=metadata,
        tags=', '.join(content.get_tags())
    )

@publishing_bp.route('/publish-now/<int:content_id>', methods=['POST'])
def publish_now(content_id):
    """Publish article immediately"""
    from utils.wordpress.client import publish_wordpress_post
    
    # Get content
    content = ContentLog.query.get_or_404(content_id)
    
    try:
        # Update status
        content.status = 'pending_publish'
        content.publish_date = datetime.now()
        db.session.commit()
        
        # Publish to WordPress
        success, post_id, error = publish_wordpress_post(
            blog_id=content.blog_id,
            post_id=content.post_id if content.post_id else None,
            title=content.title,
            content=content.content,
            excerpt=content.excerpt,
            category_id=content.category_id,
            tags=content.get_tags(),
            featured_image=json.loads(content.featured_image_data) if content.featured_image_data else None
        )
        
        if success:
            # Update status
            content.status = 'published'
            content.post_id = post_id
            db.session.commit()
            
            flash('Article published successfully', 'success')
        else:
            # Update status
            content.status = 'failed'
            content.error_message = error
            db.session.commit()
            
            flash(f'Failed to publish article: {error}', 'danger')
        
        return redirect(url_for('publishing.pending_articles'))
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error publishing article: {str(e)}")
        flash(f'Error publishing article: {str(e)}', 'danger')
        return redirect(url_for('publishing.pending_articles'))

@publishing_bp.route('/cancel/<int:content_id>', methods=['POST'])
def cancel_publication(content_id):
    """Cancel scheduled publication"""
    # Get content
    content = ContentLog.query.get_or_404(content_id)
    
    try:
        # Check if there's a schedule entry
        schedule = PublishingSchedule.query.filter_by(content_id=content.id).first()
        
        if schedule:
            # Remove from schedule
            db.session.delete(schedule)
        
        # Update status
        content.status = 'draft'
        db.session.commit()
        
        flash('Publication cancelled successfully', 'success')
        return redirect(url_for('publishing.pending_articles'))
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error cancelling publication: {str(e)}")
        flash(f'Error cancelling publication: {str(e)}', 'danger')
        return redirect(url_for('publishing.pending_articles'))

@publishing_bp.route('/history')
def publication_history():
    """View publication history and logs"""
    # Get blogs for filter
    blogs = Blog.query.all()
    selected_blog_id = request.args.get('blog_id', type=int)
    status_filter = request.args.get('status', 'all')
    
    # Date range for filter
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    
    # Build query
    query = ContentLog.query
    
    # Apply filters
    if selected_blog_id:
        query = query.filter_by(blog_id=selected_blog_id)
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    if from_date:
        try:
            from_date_obj = datetime.strptime(from_date, '%Y-%m-%d')
            query = query.filter(ContentLog.publish_date >= from_date_obj)
        except ValueError:
            flash('Invalid from date format', 'warning')
    
    if to_date:
        try:
            to_date_obj = datetime.strptime(to_date, '%Y-%m-%d')
            # Add one day to include the to_date
            to_date_obj = to_date_obj + timedelta(days=1)
            query = query.filter(ContentLog.publish_date <= to_date_obj)
        except ValueError:
            flash('Invalid to date format', 'warning')
    
    # Order by publish date (newest first)
    query = query.order_by(desc(ContentLog.publish_date))
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = 20
    pagination = query.paginate(page=page, per_page=per_page)
    
    # Get success rate data for chart
    success_data = {}
    
    # If blog is selected, get data for that blog only
    if selected_blog_id:
        blogs_to_check = [b for b in blogs if b.id == selected_blog_id]
    else:
        blogs_to_check = blogs
    
    for blog in blogs_to_check:
        total = ContentLog.query.filter_by(blog_id=blog.id).count()
        published = ContentLog.query.filter_by(blog_id=blog.id, status='published').count()
        failed = ContentLog.query.filter_by(blog_id=blog.id, status='failed').count()
        
        if total > 0:
            success_rate = round((published / total) * 100, 1)
        else:
            success_rate = 0
        
        success_data[blog.name] = {
            'total': total,
            'published': published,
            'failed': failed,
            'success_rate': success_rate
        }
    
    return render_template(
        'publishing/history.html',
        blogs=blogs,
        selected_blog_id=selected_blog_id,
        status_filter=status_filter,
        from_date=from_date,
        to_date=to_date,
        pagination=pagination,
        success_data=success_data
    )

@publishing_bp.route('/settings')
def publishing_settings():
    """Publication settings"""
    # Get blogs
    blogs = Blog.query.all()
    
    # Get automation rules
    automation_rules = {}
    for blog in blogs:
        rules = AutomationRule.query.filter_by(blog_id=blog.id).all()
        automation_rules[blog.id] = rules
    
    return render_template(
        'publishing/settings.html',
        blogs=blogs,
        automation_rules=automation_rules
    )

@publishing_bp.route('/settings/update', methods=['POST'])
def update_settings():
    """Update publication settings"""
    try:
        # Get form data
        data = request.form
        
        # Process each blog's settings
        for key, value in data.items():
            if key.startswith('approval_required_'):
                # Extract blog_id
                blog_id = int(key.split('_')[-1])
                
                # Get blog
                blog = Blog.query.get_or_404(blog_id)
                
                # Update approval setting
                blog.approval_required = value == 'on'
        
        # Save changes
        db.session.commit()
        
        flash('Publication settings updated successfully', 'success')
        return redirect(url_for('publishing.publishing_settings'))
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating publication settings: {str(e)}")
        flash(f'Error updating settings: {str(e)}', 'danger')
        return redirect(url_for('publishing.publishing_settings'))