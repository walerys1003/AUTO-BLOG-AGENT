"""
Social media management routes
"""
import logging
import json
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from sqlalchemy import desc

from app import db
from models import Blog, ContentLog, SocialAccount
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