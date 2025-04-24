"""
Social media management routes
"""
import logging
import json
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from sqlalchemy import desc

from app import db
from models import Blog, ContentLog, SocialAccount, SocialMediaTemplate, ScheduledSocialPost, SocialMediaScheduleSettings, SocialMediaPostMetrics
from social.autopost import create_social_media_posts, post_article_to_social_media, update_social_post_content, SocialMediaPostError

# Create Blueprint
social_bp = Blueprint('social', __name__)

logger = logging.getLogger(__name__)

@social_bp.route('/social/dashboard')
def social_dashboard():
    """Social media dashboard"""
    # Get blogs for filter
    blogs = Blog.query.all()
    selected_blog_id = request.args.get('blog_id', type=int)
    
    # Get pending posts
    query = ContentLog.query.filter(ContentLog.social_media_posts.isnot(None))
    
    if selected_blog_id:
        query = query.filter_by(blog_id=selected_blog_id)
    
    # Get the latest content logs with social media posts
    recent_posts = query.order_by(desc(ContentLog.created_at)).limit(20).all()
    
    # Extract social media posts and statuses
    social_data = []
    platform_stats = {
        'facebook': {'total': 0, 'published': 0, 'error': 0, 'pending': 0},
        'twitter': {'total': 0, 'published': 0, 'error': 0, 'pending': 0},
        'linkedin': {'total': 0, 'published': 0, 'error': 0, 'pending': 0},
        'instagram': {'total': 0, 'published': 0, 'error': 0, 'pending': 0}
    }
    
    for content in recent_posts:
        social_posts = content.get_social_posts() or {}
        if not social_posts:
            continue
            
        for platform, post_data in social_posts.items():
            if platform in platform_stats:
                platform_stats[platform]['total'] += 1
                status = post_data.get('status', 'draft')
                
                if status == 'published':
                    platform_stats[platform]['published'] += 1
                elif status == 'error':
                    platform_stats[platform]['error'] += 1
                else:
                    platform_stats[platform]['pending'] += 1
        
        social_data.append({
            'content_id': content.id,
            'blog_id': content.blog_id,
            'blog_name': content.blog.name if content.blog else 'Unknown',
            'title': content.title,
            'created_at': content.created_at,
            'url': content.url,
            'social_posts': social_posts
        })
    
    # Get accounts for each blog
    social_accounts = {}
    for blog in blogs:
        accounts = SocialAccount.query.filter_by(blog_id=blog.id).all()
        social_accounts[blog.id] = accounts
    
    return render_template(
        'social/dashboard.html',
        blogs=blogs,
        selected_blog_id=selected_blog_id,
        social_data=social_data,
        platform_stats=platform_stats,
        social_accounts=social_accounts
    )

@social_bp.route('/social/accounts')
def social_accounts():
    """Social media accounts management"""
    # Get all social accounts
    accounts = SocialAccount.query.all()
    
    # Get blogs for account creation
    blogs = Blog.query.all()
    
    return render_template('social/accounts.html', accounts=accounts, blogs=blogs)

@social_bp.route('/social/accounts/add', methods=['GET', 'POST'])
def add_social_account():
    """Add a new social media account"""
    # Get blogs for dropdown
    blogs = Blog.query.all()
    if not blogs:
        flash('You need to create a blog first.', 'warning')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        try:
            # Get form data
            platform = request.form.get('platform')
            name = request.form.get('name')
            api_token = request.form.get('api_token')
            api_secret = request.form.get('api_secret')
            account_id = request.form.get('account_id')
            blog_id = request.form.get('blog_id', type=int)
            
            # Validate required fields
            if not all([platform, name, api_token, blog_id]):
                flash('Please fill in all required fields.', 'danger')
                return redirect(url_for('social.add_social_account'))
            
            # Create social account
            account = SocialAccount(
                platform=platform,
                name=name,
                api_token=api_token,
                api_secret=api_secret,
                account_id=account_id,
                blog_id=blog_id,
                active=True
            )
            
            db.session.add(account)
            db.session.commit()
            
            flash(f'Social media account "{name}" added successfully.', 'success')
            return redirect(url_for('social.social_accounts'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding social account: {str(e)}")
            flash(f'Error adding social account: {str(e)}', 'danger')
            return redirect(url_for('social.add_social_account'))
    
    return render_template('social/account_form.html', account=None, blogs=blogs, action='add')

@social_bp.route('/social/accounts/<int:account_id>/edit', methods=['GET', 'POST'])
def edit_social_account(account_id):
    """Edit a social media account"""
    # Get account
    account = SocialAccount.query.get_or_404(account_id)
    
    # Get blogs for dropdown
    blogs = Blog.query.all()
    
    if request.method == 'POST':
        try:
            # Get form data
            platform = request.form.get('platform')
            name = request.form.get('name')
            api_token = request.form.get('api_token')
            api_secret = request.form.get('api_secret')
            account_id_form = request.form.get('account_id')
            blog_id = request.form.get('blog_id', type=int)
            active = 'active' in request.form
            
            # Validate required fields
            if not all([platform, name, blog_id]):
                flash('Please fill in all required fields.', 'danger')
                return redirect(url_for('social.edit_social_account', account_id=account_id))
            
            # Update account
            account.platform = platform
            account.name = name
            if api_token:
                account.api_token = api_token
            if api_secret:
                account.api_secret = api_secret
            account.account_id = account_id_form
            account.blog_id = blog_id
            account.active = active
            
            db.session.commit()
            
            flash(f'Social media account "{name}" updated successfully.', 'success')
            return redirect(url_for('social.social_accounts'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating social account: {str(e)}")
            flash(f'Error updating social account: {str(e)}', 'danger')
            return redirect(url_for('social.edit_social_account', account_id=account_id))
    
    return render_template('social/account_form.html', account=account, blogs=blogs, action='edit')

@social_bp.route('/social/accounts/<int:account_id>/delete', methods=['POST'])
def delete_social_account(account_id):
    """Delete a social media account"""
    # Get account
    account = SocialAccount.query.get_or_404(account_id)
    
    try:
        name = account.name
        db.session.delete(account)
        db.session.commit()
        
        flash(f'Social media account "{name}" deleted successfully.', 'success')
        return redirect(url_for('social.social_accounts'))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting social account: {str(e)}")
        flash(f'Error deleting social account: {str(e)}', 'danger')
        return redirect(url_for('social.social_accounts'))

@social_bp.route('/social/posts/<int:content_id>/create', methods=['POST'])
def create_posts(content_id):
    """Create social media posts for content"""
    try:
        # Generate posts
        social_posts = create_social_media_posts(content_id)
        
        if social_posts:
            flash('Social media posts created successfully.', 'success')
        else:
            flash('No social media posts could be created. Please check social accounts.', 'warning')
            
        return redirect(url_for('social.social_dashboard'))
        
    except SocialMediaPostError as e:
        logger.error(f"Error creating social posts: {str(e)}")
        flash(f'Error creating social posts: {str(e)}', 'danger')
        return redirect(url_for('social.social_dashboard'))

@social_bp.route('/social/posts/<int:content_id>/edit/<platform>', methods=['GET', 'POST'])
def edit_post(content_id, platform):
    """Edit social media post content"""
    # Get content
    content = ContentLog.query.get_or_404(content_id)
    
    # Get social posts
    social_posts = content.get_social_posts() or {}
    
    if platform.lower() not in social_posts:
        flash(f'No {platform} post found for this content.', 'warning')
        return redirect(url_for('social.social_dashboard'))
    
    post_data = social_posts[platform.lower()]
    
    if request.method == 'POST':
        try:
            # Get form data
            new_content = request.form.get('content')
            new_hashtags = request.form.get('hashtags', '').split(',')
            new_hashtags = [tag.strip() for tag in new_hashtags if tag.strip()]
            
            # Update post content
            success = update_social_post_content(content_id, platform, new_content, new_hashtags)
            
            if success:
                flash(f'{platform} post updated successfully.', 'success')
                return redirect(url_for('social.social_dashboard'))
            else:
                flash('Failed to update post content.', 'danger')
                
        except Exception as e:
            logger.error(f"Error updating post content: {str(e)}")
            flash(f'Error updating post content: {str(e)}', 'danger')
    
    # Set platform color for styling
    platform_colors = {
        'facebook': 'primary',
        'twitter': 'info',
        'linkedin': 'success',
        'instagram': 'danger'
    }
    platform_color = platform_colors.get(platform.lower(), 'primary')
    
    return render_template(
        'social/edit_post.html',
        content=content,
        platform=platform,
        post_data=post_data,
        platform_color=platform_color
    )

@social_bp.route('/social/posts/<int:content_id>/publish', methods=['POST'])
def publish_posts(content_id):
    """Publish social media posts"""
    # Get selected platforms
    platforms = request.form.getlist('platforms')
    
    if not platforms:
        flash('Please select at least one platform.', 'warning')
        return redirect(url_for('social.social_dashboard'))
    
    # Get scheduled time if any
    scheduled_time_str = request.form.get('scheduled_time')
    scheduled_time = None
    
    if scheduled_time_str:
        try:
            scheduled_time = datetime.strptime(scheduled_time_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('Invalid scheduled time format.', 'danger')
            return redirect(url_for('social.social_dashboard'))
    
    try:
        # Publish or schedule posts
        result = post_article_to_social_media(content_id, platforms, scheduled_time)
        
        if not result:
            flash('No posts were published. Please check social accounts and post content.', 'warning')
        elif scheduled_time:
            flash(f'Social media posts scheduled successfully for {scheduled_time}.', 'success')
        else:
            # Count successful posts
            success_count = sum(1 for p in result.values() if p.get('status') == 'published')
            error_count = sum(1 for p in result.values() if p.get('status') == 'error')
            
            if success_count > 0:
                flash(f'{success_count} posts published successfully.', 'success')
            if error_count > 0:
                flash(f'{error_count} posts failed to publish. Check details below.', 'warning')
        
        return redirect(url_for('social.social_dashboard'))
        
    except SocialMediaPostError as e:
        logger.error(f"Error publishing social posts: {str(e)}")
        flash(f'Error publishing social posts: {str(e)}', 'danger')
        return redirect(url_for('social.social_dashboard'))

@social_bp.route('/social/posts/<int:content_id>/preview', methods=['GET'])
def preview_posts(content_id):
    """Preview social media posts"""
    # Get content
    content = ContentLog.query.get_or_404(content_id)
    
    # Get or generate social posts
    social_posts = content.get_social_posts()
    if not social_posts:
        try:
            social_posts = create_social_media_posts(content_id, preview_only=True)
        except SocialMediaPostError as e:
            flash(f'Error generating preview: {str(e)}', 'danger')
            return redirect(url_for('social.social_dashboard'))
    
    # Get blog
    blog = Blog.query.get(content.blog_id)
    
    return render_template(
        'social/preview.html',
        content=content,
        social_posts=social_posts,
        blog=blog
    )

@social_bp.route('/social/posts/<int:content_id>/regenerate/<platform>', methods=['POST'])
def regenerate_post(content_id, platform):
    """Regenerate social media post content for a specific platform"""
    try:
        # Get content log entry
        content_log = ContentLog.query.get_or_404(content_id)
        
        # Extract content data
        title = content_log.title
        excerpt = content_log.excerpt or ""
        url = content_log.url
        keywords = content_log.get_tags() if content_log.tags else []
        
        # Get featured image if available
        featured_image_data = content_log.get_featured_image()
        image_description = featured_image_data.get("alt_text", "") if featured_image_data else None
        
        # Generate content for specific platform
        from utils.openrouter.social import generate_social_media_content
        social_content = generate_social_media_content(
            title=title,
            excerpt=excerpt,
            url=url,
            platforms=[platform.lower()],
            keywords=keywords,
            image_description=image_description
        )
        
        if platform.lower() not in social_content:
            flash(f'Failed to regenerate {platform} post content.', 'danger')
            return redirect(url_for('social.edit_post', content_id=content_id, platform=platform))
        
        # Update post content
        new_content = social_content[platform.lower()]["content"]
        new_hashtags = social_content[platform.lower()]["hashtags"]
        
        success = update_social_post_content(content_id, platform, new_content, new_hashtags)
        
        if success:
            flash(f'{platform} post regenerated successfully.', 'success')
        else:
            flash('Failed to update post content.', 'danger')
            
        return redirect(url_for('social.edit_post', content_id=content_id, platform=platform))
        
    except Exception as e:
        logger.error(f"Error regenerating post content: {str(e)}")
        flash(f'Error regenerating post content: {str(e)}', 'danger')
        return redirect(url_for('social.edit_post', content_id=content_id, platform=platform))

# API routes for AJAX calls
@social_bp.route('/api/social/posts/<int:content_id>/status', methods=['GET'])
def get_post_status(content_id):
    """Get status of social media posts"""
    # Get content
    content = ContentLog.query.get_or_404(content_id)
    
    # Get social posts
    social_posts = content.get_social_posts() or {}
    
    # Format status data
    status_data = {}
    for platform, post_data in social_posts.items():
        status_data[platform] = {
            'status': post_data.get('status', 'draft'),
            'post_url': post_data.get('post_url'),
            'error': post_data.get('error')
        }
    
    return jsonify(status_data)


@social_bp.route('/social/statistics')
def social_statistics():
    """Social media statistics dashboard"""
    # Get date range parameters
    date_range = request.args.get('date_range', '30')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Calculate default dates if not provided
    today = datetime.now()
    if date_range != 'custom':
        # Convert date_range to integer days
        days = int(date_range)
        start_date = (today - timedelta(days=days)).strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
    
    # Get metrics from database
    metrics = SocialMediaPostMetrics.query.filter(
        SocialMediaPostMetrics.post_date >= start_date,
        SocialMediaPostMetrics.post_date <= end_date
    ).all()
    
    # Calculate statistics
    stats = {
        'total_posts': len(metrics),
        'total_engagements': sum(m.likes + m.comments + m.shares for m in metrics),
        'total_clicks': sum(m.clicks for m in metrics),
        'avg_engagement_rate': 0
    }
    
    if stats['total_posts'] > 0:
        stats['avg_engagement_rate'] = round(
            (stats['total_engagements'] / stats['total_posts']) * 100 / 
            (sum(m.impressions for m in metrics) / stats['total_posts']),
            1
        ) if sum(m.impressions for m in metrics) > 0 else 0
    
    # Platform performance data
    platform_data = {}
    for platform in ['facebook', 'twitter', 'linkedin', 'instagram']:
        platform_metrics = [m for m in metrics if m.platform == platform]
        if platform_metrics:
            total_engagements = sum(m.likes + m.comments + m.shares for m in platform_metrics)
            total_impressions = sum(m.impressions for m in platform_metrics)
            platform_data[platform] = {
                'engagement_rate': round((total_engagements / len(platform_metrics)) * 100 / 
                                       (total_impressions / len(platform_metrics)), 1) 
                                       if total_impressions > 0 else 0
            }
        else:
            platform_data[platform] = {'engagement_rate': 0}
    
    platform_labels = ['Facebook', 'Twitter', 'LinkedIn', 'Instagram']
    platform_engagement_rates = [
        platform_data.get('facebook', {}).get('engagement_rate', 0),
        platform_data.get('twitter', {}).get('engagement_rate', 0),
        platform_data.get('linkedin', {}).get('engagement_rate', 0),
        platform_data.get('instagram', {}).get('engagement_rate', 0)
    ]
    
    # Content type performance
    content_types = {}
    for metric in metrics:
        post = ScheduledSocialPost.query.get(metric.scheduled_post_id) if metric.scheduled_post_id else None
        if post and post.content_id:
            content = ContentLog.query.get(post.content_id)
            if content:
                content_type = content.get_seo_metadata().get('content_type', 'article')
                if content_type not in content_types:
                    content_types[content_type] = {
                        'engagements': 0,
                        'posts': 0
                    }
                content_types[content_type]['engagements'] += metric.likes + metric.comments + metric.shares
                content_types[content_type]['posts'] += 1
    
    content_type_labels = list(content_types.keys()) or ['Article', 'Question', 'Quote', 'Listicle', 'Video']
    content_type_engagement = [
        content_types.get(t, {}).get('engagements', 0) for t in content_type_labels
    ] or [45, 20, 15, 10, 10]  # Default values if no data
    
    # Time series data
    time_labels = []
    time_engagements = []
    time_clicks = []
    
    # Generate date range
    date_range = []
    current_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
    while current_date <= end_date_obj:
        date_range.append(current_date.strftime('%Y-%m-%d'))
        current_date += timedelta(days=1)
    
    # Populate time series data
    for date_str in date_range:
        time_labels.append(date_str[5:])  # Just month-day
        day_metrics = [m for m in metrics if m.post_date and m.post_date.strftime('%Y-%m-%d') == date_str]
        time_engagements.append(sum(m.likes + m.comments + m.shares for m in day_metrics))
        time_clicks.append(sum(m.clicks for m in day_metrics))
    
    # Get top performing posts
    top_posts = []
    for metric in sorted(metrics, key=lambda m: (m.likes + m.comments + m.shares), reverse=True)[:5]:
        post_data = {
            'platform': metric.platform,
            'post_date': metric.post_date or datetime.now(),
            'likes': metric.likes,
            'comments': metric.comments,
            'shares': metric.shares,
            'clicks': metric.clicks,
            'engagement_rate': round(
                (metric.likes + metric.comments + metric.shares) * 100 / metric.impressions, 1
            ) if metric.impressions > 0 else 0,
            'post_url': metric.post_url,
            'image_url': None,
            'title': f"Post on {metric.platform.capitalize()}"
        }
        
        # Get post details if available
        if metric.scheduled_post_id:
            post = ScheduledSocialPost.query.get(metric.scheduled_post_id)
            if post:
                post_data['image_url'] = post.image_url
                if post.content_id:
                    content = ContentLog.query.get(post.content_id)
                    if content:
                        post_data['title'] = content.title
        
        top_posts.append(post_data)
    
    return render_template(
        'social/statistics.html',
        date_range=date_range,
        start_date=start_date,
        end_date=end_date,
        stats=stats,
        platform_labels=platform_labels,
        platform_engagement_rates=platform_engagement_rates,
        content_type_labels=content_type_labels,
        content_type_engagement=content_type_engagement,
        time_labels=time_labels,
        time_engagements=time_engagements,
        time_clicks=time_clicks,
        top_posts=top_posts
    )

@social_bp.route('/social/templates')
def social_templates():
    """Social media content templates"""
    # Get templates from database
    templates = SocialMediaTemplate.query.all()
    
    return render_template(
        'social/templates.html',
        templates=templates
    )

@social_bp.route('/social/templates/add', methods=['POST'])
def add_template():
    """Add a new social media template"""
    try:
        # Get form data
        name = request.form.get('name')
        platform = request.form.get('platform')
        template_type = request.form.get('type')
        content = request.form.get('content')
        description = request.form.get('description', '')
        hashtags_str = request.form.get('hashtags', '')
        
        # Validate required fields
        if not all([name, platform, template_type, content]):
            flash('Please fill in all required fields.', 'danger')
            return redirect(url_for('social.social_templates'))
        
        # Process hashtags
        hashtags = [tag.strip() for tag in hashtags_str.split(',') if tag.strip()]
        
        # Create template
        template = SocialMediaTemplate(
            name=name,
            platform=platform,
            type=template_type,
            content=content,
            description=description
        )
        template.set_hashtags(hashtags)
        
        db.session.add(template)
        db.session.commit()
        
        flash('Template added successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding template: {str(e)}")
        flash(f'Error adding template: {str(e)}', 'danger')
    
    return redirect(url_for('social.social_templates'))

@social_bp.route('/social/templates/<int:template_id>/edit', methods=['POST'])
def edit_template(template_id):
    """Edit a social media template"""
    try:
        # Get template
        template = SocialMediaTemplate.query.get_or_404(template_id)
        
        # Get form data
        name = request.form.get('name')
        platform = request.form.get('platform')
        template_type = request.form.get('type')
        content = request.form.get('content')
        description = request.form.get('description', '')
        hashtags_str = request.form.get('hashtags', '')
        
        # Validate required fields
        if not all([name, platform, template_type, content]):
            flash('Please fill in all required fields.', 'danger')
            return redirect(url_for('social.social_templates'))
        
        # Process hashtags
        hashtags = [tag.strip() for tag in hashtags_str.split(',') if tag.strip()]
        
        # Update template
        template.name = name
        template.platform = platform
        template.type = template_type
        template.content = content
        template.description = description
        template.set_hashtags(hashtags)
        
        db.session.commit()
        
        flash('Template updated successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating template: {str(e)}")
        flash(f'Error updating template: {str(e)}', 'danger')
    
    return redirect(url_for('social.social_templates'))

@social_bp.route('/social/templates/<int:template_id>/delete', methods=['POST'])
def delete_template(template_id):
    """Delete a social media template"""
    try:
        # Get template
        template = SocialMediaTemplate.query.get_or_404(template_id)
        
        # Delete template
        db.session.delete(template)
        db.session.commit()
        
        flash('Template deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting template: {str(e)}")
        flash(f'Error deleting template: {str(e)}', 'danger')
    
    return redirect(url_for('social.social_templates'))

@social_bp.route('/social/schedule')
def social_schedule():
    """Social media scheduling calendar"""
    # Get scheduled posts
    scheduled_posts = ScheduledSocialPost.query.filter(
        ScheduledSocialPost.scheduled_date >= datetime.now()
    ).order_by(ScheduledSocialPost.scheduled_date).all()
    
    # Get schedule settings
    settings = SocialMediaScheduleSettings.query.filter_by(blog_id=None).first()
    if not settings:
        settings = SocialMediaScheduleSettings()
        db.session.add(settings)
        db.session.commit()
    
    # Get articles for dropdown
    articles = ContentLog.query.filter(
        ContentLog.status == 'published'
    ).order_by(ContentLog.created_at.desc()).limit(20).all()
    
    # Get templates for dropdown
    templates = SocialMediaTemplate.query.all()
    
    # Convert scheduled posts to JSON for calendar
    scheduled_posts_json = json.dumps([{
        'id': post.id,
        'content': post.content[:50] + '...' if len(post.content) > 50 else post.content,
        'platform': post.platform,
        'scheduled_date': post.scheduled_date.isoformat(),
        'status': post.status
    } for post in scheduled_posts])
    
    return render_template(
        'social/schedule.html',
        scheduled_posts=scheduled_posts,
        schedule_settings=settings,
        articles=articles,
        templates=templates,
        scheduled_posts_json=scheduled_posts_json
    )

@social_bp.route('/social/schedule/settings', methods=['POST'])
def update_schedule_settings():
    """Update social media schedule settings"""
    try:
        # Get settings
        settings = SocialMediaScheduleSettings.query.filter_by(blog_id=None).first()
        if not settings:
            settings = SocialMediaScheduleSettings()
            db.session.add(settings)
        
        # Process optimal times
        optimal_times = []
        for i in range(4):
            time_str = request.form.get(f'time{i}')
            if time_str:
                optimal_times.append(time_str)
        
        # Process platform settings
        platform_settings = {}
        for platform in ['facebook', 'twitter', 'linkedin', 'instagram']:
            frequency = int(request.form.get(f'{platform}_frequency', 0))
            days = request.form.getlist(f'{platform}_days')
            platform_settings[platform] = {
                'frequency': frequency,
                'days': days
            }
        
        # Process other settings
        auto_distribute = 'auto_distribute' in request.form
        platform_rotation = 'platform_rotation' in request.form
        content_variety = 'content_variety' in request.form
        
        # Update settings
        settings.set_optimal_times(optimal_times)
        settings.set_platform_settings(platform_settings)
        settings.auto_distribute = auto_distribute
        settings.platform_rotation = platform_rotation
        settings.content_variety = content_variety
        
        db.session.commit()
        
        flash('Schedule settings updated successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating schedule settings: {str(e)}")
        flash(f'Error updating schedule settings: {str(e)}', 'danger')
    
    return redirect(url_for('social.social_schedule'))

@social_bp.route('/social/schedule/post', methods=['POST'])
def schedule_post():
    """Schedule a new social media post"""
    try:
        # Get form data
        platform = request.form.get('platform')
        content_type = request.form.get('content_type')
        content = request.form.get('content')
        hashtags_str = request.form.get('hashtags', '')
        image_url = request.form.get('image_url')
        
        # Process content based on content type
        if content_type == 'article':
            article_id = request.form.get('article_id', type=int)
            if article_id:
                article = ContentLog.query.get_or_404(article_id)
                # Generate content for article
                content = f"Check out our latest article: {article.title}\n\n{article.url}"
                # Get article image if available
                if not image_url and article.get_featured_image():
                    image_url = article.get_featured_image().get('url')
        elif content_type == 'template':
            template_id = request.form.get('template_id', type=int)
            if template_id:
                template = SocialMediaTemplate.query.get_or_404(template_id)
                content = template.content
                hashtags_str = ', '.join(template.get_hashtags())
        
        # Process scheduling
        use_optimal_time = 'use_optimal_time' in request.form
        if use_optimal_time:
            # Get next optimal time
            settings = SocialMediaScheduleSettings.query.filter_by(blog_id=None).first()
            if settings:
                optimal_times = settings.get_optimal_times()
                if optimal_times:
                    now = datetime.now()
                    today_times = [
                        datetime.combine(now.date(), datetime.strptime(t, '%H:%M').time())
                        for t in optimal_times
                    ]
                    future_times = [t for t in today_times if t > now]
                    
                    if future_times:
                        scheduled_time = future_times[0]
                    else:
                        # Use first time tomorrow
                        tomorrow = now.date() + timedelta(days=1)
                        scheduled_time = datetime.combine(tomorrow, datetime.strptime(optimal_times[0], '%H:%M').time())
        else:
            scheduled_time_str = request.form.get('scheduled_time')
            if scheduled_time_str:
                scheduled_time = datetime.strptime(scheduled_time_str, '%Y-%m-%dT%H:%M')
            else:
                # Default to one hour from now
                scheduled_time = datetime.now() + timedelta(hours=1)
        
        # Process hashtags
        hashtags = [tag.strip() for tag in hashtags_str.split(',') if tag.strip()]
        
        # Create scheduled post
        post = ScheduledSocialPost(
            platform=platform,
            content=content,
            image_url=image_url,
            scheduled_date=scheduled_time,
            status='scheduled'
        )
        post.set_hashtags(hashtags)
        
        # Associate with article if applicable
        if content_type == 'article' and 'article_id' in request.form:
            post.content_id = request.form.get('article_id', type=int)
        
        db.session.add(post)
        db.session.commit()
        
        flash(f'Post scheduled successfully for {scheduled_time.strftime("%Y-%m-%d %H:%M")}.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error scheduling post: {str(e)}")
        flash(f'Error scheduling post: {str(e)}', 'danger')
    
    return redirect(url_for('social.social_schedule'))

@social_bp.route('/social/schedule/<int:post_id>/edit', methods=['GET', 'POST'])
def edit_scheduled_post(post_id):
    """Edit a scheduled social media post"""
    # Get scheduled post
    post = ScheduledSocialPost.query.get_or_404(post_id)
    
    if request.method == 'POST':
        try:
            # Get form data
            content = request.form.get('content')
            hashtags_str = request.form.get('hashtags', '')
            image_url = request.form.get('image_url')
            scheduled_time_str = request.form.get('scheduled_time')
            
            # Process hashtags
            hashtags = [tag.strip() for tag in hashtags_str.split(',') if tag.strip()]
            
            # Update post
            post.content = content
            post.image_url = image_url
            post.set_hashtags(hashtags)
            
            # Update scheduled time if provided
            if scheduled_time_str:
                post.scheduled_date = datetime.strptime(scheduled_time_str, '%Y-%m-%dT%H:%M')
            
            db.session.commit()
            
            flash('Scheduled post updated successfully.', 'success')
            return redirect(url_for('social.social_schedule'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating scheduled post: {str(e)}")
            flash(f'Error updating scheduled post: {str(e)}', 'danger')
    
    # Convert hashtags to string for form
    hashtags_str = ', '.join(post.get_hashtags())
    
    return render_template(
        'social/edit_scheduled_post.html',
        post=post,
        hashtags=hashtags_str
    )

@social_bp.route('/social/schedule/<int:post_id>/delete', methods=['POST'])
def delete_scheduled_post(post_id):
    """Delete a scheduled social media post"""
    try:
        # Get scheduled post
        post = ScheduledSocialPost.query.get_or_404(post_id)
        
        # Delete post
        db.session.delete(post)
        db.session.commit()
        
        flash('Scheduled post deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting scheduled post: {str(e)}")
        flash(f'Error deleting scheduled post: {str(e)}', 'danger')
    
    return redirect(url_for('social.social_schedule'))

# API endpoints for AJAX calls
@social_bp.route('/api/social/templates/<int:template_id>', methods=['GET'])
def get_template(template_id):
    """Get template data by ID"""
    template = SocialMediaTemplate.query.get_or_404(template_id)
    
    return jsonify({
        'id': template.id,
        'name': template.name,
        'platform': template.platform,
        'type': template.type,
        'content': template.content,
        'hashtags': template.get_hashtags(),
        'description': template.description
    })