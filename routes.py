import logging
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from models import Blog, SocialAccount, ContentLog, ArticleTopic
from app import db
from utils.scheduler import start_scheduler, process_content_generation
from generator.seo import generate_article_topics
from generator.content import generate_article_content
from wordpress.publisher import publish_article, get_optimal_publish_time
from social.autopost import post_article_to_social_media
import json
from datetime import datetime, timedelta

# Setup logging
logger = logging.getLogger(__name__)

def register_routes(app: Flask):
    """Register all routes with the Flask app"""
    
    # Add template context processor for datetime
    @app.context_processor
    def inject_now():
        return {'now': datetime.now()}
    
    @app.route('/')
    def index():
        """Dashboard homepage"""
        return redirect(url_for('dashboard'))
    
    @app.route('/dashboard')
    def dashboard():
        """Main dashboard view"""
        # Get statistics
        stats = {
            'total_blogs': Blog.query.count(),
            'active_blogs': Blog.query.filter_by(active=True).count(),
            'total_posts': ContentLog.query.filter_by(status='published').count(),
            'pending_topics': ArticleTopic.query.filter_by(status='pending').count()
        }
        
        # Get recent posts
        recent_posts = ContentLog.query.filter_by(status='published').order_by(ContentLog.published_at.desc()).limit(10).all()
        
        # Get all blogs
        blogs = Blog.query.all()
        
        # Calculate posts per blog
        blog_stats = []
        for blog in blogs:
            posts_count = ContentLog.query.filter_by(blog_id=blog.id, status='published').count()
            posts_today = ContentLog.query.filter(
                ContentLog.blog_id == blog.id,
                ContentLog.status == 'published',
                ContentLog.published_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            ).count()
            
            blog_stats.append({
                'id': blog.id,
                'name': blog.name,
                'url': blog.url,
                'active': blog.active,
                'posts_count': posts_count,
                'posts_today': posts_today
            })
        
        return render_template('dashboard.html', stats=stats, recent_posts=recent_posts, blog_stats=blog_stats)
    
    @app.route('/blogs')
    def blogs_list():
        """List all blogs"""
        blogs = Blog.query.all()
        return render_template('blogs.html', blogs=blogs)
    
    @app.route('/blogs/add', methods=['GET', 'POST'])
    def add_blog():
        """Add a new blog"""
        if request.method == 'POST':
            try:
                name = request.form.get('name')
                url = request.form.get('url')
                api_url = request.form.get('api_url')
                username = request.form.get('username')
                api_token = request.form.get('api_token')
                categories = request.form.get('categories', '[]')
                
                if not all([name, url, api_url, username, api_token]):
                    flash('All fields are required', 'danger')
                    return redirect(url_for('add_blog'))
                
                # Create new blog
                blog = Blog(
                    name=name,
                    url=url,
                    api_url=api_url,
                    username=username,
                    api_token=api_token,
                    categories=categories,
                    active=True
                )
                
                db.session.add(blog)
                db.session.commit()
                
                flash(f'Blog {name} added successfully', 'success')
                return redirect(url_for('blogs_list'))
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error adding blog: {str(e)}")
                flash(f'Error adding blog: {str(e)}', 'danger')
                return redirect(url_for('add_blog'))
        
        return render_template('blog_form.html', blog=None, action='add')
    
    @app.route('/blogs/edit/<int:blog_id>', methods=['GET', 'POST'])
    def edit_blog(blog_id):
        """Edit a blog"""
        blog = Blog.query.get_or_404(blog_id)
        
        if request.method == 'POST':
            try:
                blog.name = request.form.get('name')
                blog.url = request.form.get('url')
                blog.api_url = request.form.get('api_url')
                blog.username = request.form.get('username')
                
                # Only update API token if provided
                new_token = request.form.get('api_token')
                if new_token:
                    blog.api_token = new_token
                
                blog.categories = request.form.get('categories', '[]')
                blog.active = 'active' in request.form
                
                db.session.commit()
                
                flash(f'Blog {blog.name} updated successfully', 'success')
                return redirect(url_for('blogs_list'))
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error updating blog: {str(e)}")
                flash(f'Error updating blog: {str(e)}', 'danger')
                return redirect(url_for('edit_blog', blog_id=blog_id))
        
        return render_template('blog_form.html', blog=blog, action='edit')
    
    @app.route('/blogs/delete/<int:blog_id>', methods=['POST'])
    def delete_blog(blog_id):
        """Delete a blog"""
        blog = Blog.query.get_or_404(blog_id)
        
        try:
            db.session.delete(blog)
            db.session.commit()
            
            flash(f'Blog {blog.name} deleted successfully', 'success')
            return redirect(url_for('blogs_list'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting blog: {str(e)}")
            flash(f'Error deleting blog: {str(e)}', 'danger')
            return redirect(url_for('blogs_list'))
    
    @app.route('/social')
    def social_accounts():
        """List all social media accounts"""
        accounts = SocialAccount.query.all()
        blogs = Blog.query.all()
        return render_template('social.html', accounts=accounts, blogs=blogs)
    
    @app.route('/social/add', methods=['GET', 'POST'])
    def add_social_account():
        """Add a new social media account"""
        if request.method == 'POST':
            try:
                platform = request.form.get('platform')
                name = request.form.get('name')
                api_token = request.form.get('api_token')
                api_secret = request.form.get('api_secret')
                account_id = request.form.get('account_id')
                blog_id = request.form.get('blog_id')
                
                if not all([platform, name, api_token, blog_id]):
                    flash('Platform, name, API token, and blog are required', 'danger')
                    return redirect(url_for('add_social_account'))
                
                # Create new social account
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
                
                flash(f'Social account {name} added successfully', 'success')
                return redirect(url_for('social_accounts'))
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error adding social account: {str(e)}")
                flash(f'Error adding social account: {str(e)}', 'danger')
                return redirect(url_for('add_social_account'))
        
        blogs = Blog.query.all()
        return render_template('social_form.html', account=None, blogs=blogs, action='add')
    
    @app.route('/social/edit/<int:account_id>', methods=['GET', 'POST'])
    def edit_social_account(account_id):
        """Edit a social media account"""
        account = SocialAccount.query.get_or_404(account_id)
        
        if request.method == 'POST':
            try:
                account.platform = request.form.get('platform')
                account.name = request.form.get('name')
                
                # Only update tokens if provided
                new_token = request.form.get('api_token')
                if new_token:
                    account.api_token = new_token
                
                new_secret = request.form.get('api_secret')
                if new_secret:
                    account.api_secret = new_secret
                
                account.account_id = request.form.get('account_id')
                account.blog_id = request.form.get('blog_id')
                account.active = 'active' in request.form
                
                db.session.commit()
                
                flash(f'Social account {account.name} updated successfully', 'success')
                return redirect(url_for('social_accounts'))
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error updating social account: {str(e)}")
                flash(f'Error updating social account: {str(e)}', 'danger')
                return redirect(url_for('edit_social_account', account_id=account_id))
        
        blogs = Blog.query.all()
        return render_template('social_form.html', account=account, blogs=blogs, action='edit')
    
    @app.route('/social/delete/<int:account_id>', methods=['POST'])
    def delete_social_account(account_id):
        """Delete a social media account"""
        account = SocialAccount.query.get_or_404(account_id)
        
        try:
            db.session.delete(account)
            db.session.commit()
            
            flash(f'Social account {account.name} deleted successfully', 'success')
            return redirect(url_for('social_accounts'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting social account: {str(e)}")
            flash(f'Error deleting social account: {str(e)}', 'danger')
            return redirect(url_for('social_accounts'))
    
    @app.route('/logs')
    def logs():
        """View content logs"""
        # Filter by status
        status = request.args.get('status', 'all')
        blog_id = request.args.get('blog_id', 'all')
        days = int(request.args.get('days', 7))
        
        # Base query
        query = ContentLog.query
        
        # Apply filters
        if status != 'all':
            query = query.filter_by(status=status)
        
        if blog_id != 'all':
            query = query.filter_by(blog_id=blog_id)
        
        # Filter by date range
        start_date = datetime.utcnow() - timedelta(days=days)
        query = query.filter(ContentLog.created_at >= start_date)
        
        # Get results with pagination
        page = request.args.get('page', 1, type=int)
        per_page = 20
        logs = query.order_by(ContentLog.created_at.desc()).paginate(page=page, per_page=per_page)
        
        # Get blogs for filter
        blogs = Blog.query.all()
        
        return render_template('logs.html', logs=logs, blogs=blogs, current_status=status, current_blog=blog_id, days=days)
    
    @app.route('/topics')
    def topics():
        """View and manage article topics"""
        # Filter by status
        status = request.args.get('status', 'pending')
        blog_id = request.args.get('blog_id', 'all')
        
        # Base query
        query = ArticleTopic.query
        
        # Apply filters
        if status != 'all':
            query = query.filter_by(status=status)
        
        if blog_id != 'all':
            query = query.filter_by(blog_id=blog_id)
        
        # Get results with pagination
        page = request.args.get('page', 1, type=int)
        per_page = 20
        topics = query.order_by(ArticleTopic.created_at.desc()).paginate(page=page, per_page=per_page)
        
        # Get blogs for filter
        blogs = Blog.query.all()
        
        return render_template('topics.html', topics=topics, blogs=blogs, current_status=status, current_blog=blog_id)
    
    @app.route('/topics/generate', methods=['POST'])
    def generate_topics():
        """Generate new topics for a blog"""
        blog_id = request.form.get('blog_id')
        category = request.form.get('category')
        count = int(request.form.get('count', 4))
        
        try:
            blog = Blog.query.get_or_404(blog_id)
            
            # Generate topics
            topics = generate_article_topics(
                blog_name=blog.name,
                categories=[category] if category else None,
                count=count
            )
            
            if topics:
                # Save topics to database
                for topic in topics:
                    article_topic = ArticleTopic(
                        blog_id=blog.id,
                        title=topic.get('title', ''),
                        category=category,
                        status='pending',
                        score=topic.get('score', 0)
                    )
                    
                    # Set keywords
                    keywords = topic.get('keywords', [])
                    if keywords:
                        article_topic.set_keywords(keywords)
                    
                    db.session.add(article_topic)
                
                db.session.commit()
                
                flash(f'Generated {len(topics)} topics for {blog.name}', 'success')
            else:
                flash('Failed to generate topics', 'danger')
                
            return redirect(url_for('topics'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error generating topics: {str(e)}")
            flash(f'Error generating topics: {str(e)}', 'danger')
            return redirect(url_for('topics'))
    
    @app.route('/topics/approve/<int:topic_id>', methods=['POST'])
    def approve_topic(topic_id):
        """Approve a pending topic"""
        topic = ArticleTopic.query.get_or_404(topic_id)
        
        try:
            topic.status = 'approved'
            db.session.commit()
            
            flash(f'Topic "{topic.title}" approved', 'success')
            return redirect(url_for('topics'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error approving topic: {str(e)}")
            flash(f'Error approving topic: {str(e)}', 'danger')
            return redirect(url_for('topics'))
    
    @app.route('/topics/reject/<int:topic_id>', methods=['POST'])
    def reject_topic(topic_id):
        """Reject a pending topic"""
        topic = ArticleTopic.query.get_or_404(topic_id)
        
        try:
            topic.status = 'rejected'
            db.session.commit()
            
            flash(f'Topic "{topic.title}" rejected', 'success')
            return redirect(url_for('topics'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error rejecting topic: {str(e)}")
            flash(f'Error rejecting topic: {str(e)}', 'danger')
            return redirect(url_for('topics'))
    
    @app.route('/topics/delete/<int:topic_id>', methods=['POST'])
    def delete_topic(topic_id):
        """Delete a topic"""
        topic = ArticleTopic.query.get_or_404(topic_id)
        
        try:
            db.session.delete(topic)
            db.session.commit()
            
            flash(f'Topic "{topic.title}" deleted', 'success')
            return redirect(url_for('topics'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting topic: {str(e)}")
            flash(f'Error deleting topic: {str(e)}', 'danger')
            return redirect(url_for('topics'))
    
    @app.route('/api/process_blog/<int:blog_id>', methods=['POST'])
    def api_process_blog(blog_id):
        """API endpoint to manually process a blog's content pipeline"""
        try:
            # Start the content pipeline for this blog
            process_content_generation()
            
            return jsonify({
                'success': True,
                'message': f'Content pipeline started for blog {blog_id}'
            })
            
        except Exception as e:
            logger.error(f"Error processing blog content: {str(e)}")
            
            return jsonify({
                'success': False,
                'message': f'Error: {str(e)}'
            }), 500
    
    @app.route('/api/health')
    def api_health():
        """API health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat()
        })
    
    @app.route('/openrouter')
    def openrouter_config():
        """OpenRouter configuration page"""
        from utils.openrouter import openrouter
        from config import Config
        
        models = []
        openrouter_api_key = Config.OPENROUTER_API_KEY
        
        # Only fetch models if we have an API key
        if openrouter_api_key:
            try:
                models = openrouter.get_available_models()
                
                # Add some additional information for the UI
                for model in models:
                    model['provider'] = model.get('id', '').split('/')[0] if '/' in model.get('id', '') else 'Unknown'
                    model['vision'] = 'vision' in model.get('capabilities', [])
                    model['json_output'] = 'json' in model.get('capabilities', [])
            except Exception as e:
                logger.error(f"Error fetching OpenRouter models: {str(e)}")
                flash('Error fetching models from OpenRouter API', 'danger')
        
        return render_template(
            'openrouter.html',
            models=models,
            openrouter_api_key=openrouter_api_key,
            default_topic_model=Config.DEFAULT_TOPIC_MODEL,
            default_content_model=Config.DEFAULT_CONTENT_MODEL,
            default_social_model=Config.DEFAULT_SOCIAL_MODEL
        )
    
    @app.route('/openrouter/set_model/<purpose>/<path:model_id>')
    def set_model(purpose, model_id):
        """Set a model for a specific purpose"""
        # This would normally update environment variables or database settings
        # For now, we'll store in session and show a message that this would modify the env in prod
        
        model_purposes = {
            'topic': 'Topic Generation',
            'content': 'Content Creation',
            'social': 'Social Media'
        }
        
        if purpose not in model_purposes:
            flash('Invalid model purpose', 'danger')
        else:
            session[f'DEFAULT_{purpose.upper()}_MODEL'] = model_id
            flash(f'{model_purposes[purpose]} model set to {model_id}', 'success')
            flash('Note: In production, this would update your environment variables.', 'info')
        
        return redirect(url_for('openrouter_config'))
    
    @app.route('/api/test_openrouter', methods=['POST'])
    def test_openrouter():
        """Test OpenRouter with a model and prompt"""
        import time
        from utils.openrouter import openrouter
        
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        model = data.get('model')
        prompt = data.get('prompt')
        temperature = data.get('temperature', 0.7)
        
        if not model or not prompt:
            return jsonify({"error": "Model and prompt are required"}), 400
        
        try:
            start_time = time.time()
            response = openrouter.generate_completion(
                prompt=prompt,
                model=model,
                temperature=temperature
            )
            end_time = time.time()
            
            time_taken = end_time - start_time
            
            return jsonify({
                "model": model,
                "content": response,
                "time_taken": time_taken
            })
        except Exception as e:
            logger.error(f"Error testing OpenRouter: {str(e)}")
            return jsonify({"error": str(e)}), 500
    
    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('error.html', error_code=404, error_message='Page not found'), 404
    
    @app.errorhandler(500)
    def server_error(e):
        return render_template('error.html', error_code=500, error_message='Server error'), 500
