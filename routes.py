import logging
import traceback
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from models import Blog, SocialAccount, ContentLog, ArticleTopic
from app import db
from utils.scheduler import start_scheduler, process_content_generation
from generator.seo import generate_article_topics
from generator.content import generate_article_content
from wordpress.publisher import publish_article, get_optimal_publish_time
from social.autopost import post_article_to_social_media
from utils.seo.analyzer import seo_analyzer
from utils.seo.optimizer import seo_optimizer
from utils.writing.assistant import writing_assistant
from routes_analytics import register_analytics_routes
from routes_seo_inspiration import seo_inspiration_bp
from routes_content_creator import content_creator_bp
from routes_images import register_image_routes
from newsletter import newsletter_bp
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
        
        # Add newsletter stats if available
        try:
            from models import Subscriber, Newsletter
            from datetime import datetime, timedelta
            
            # Active subscribers
            stats['subscribers'] = Subscriber.query.filter_by(status='active').count()
            
            # Recent newsletters - last 30 days
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            stats['newsletters'] = Newsletter.query.filter(
                Newsletter.status == 'sent',
                Newsletter.sent_at >= thirty_days_ago
            ).count()
        except Exception as e:
            logger.error(f"Error fetching newsletter stats: {str(e)}")
            stats['subscribers'] = 0
            stats['newsletters'] = 0
        
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
        
    @app.route('/seo-tools')
    def seo_tools():
        """SEO tools and content optimization page"""
        return render_template('seo_tools.html')
    
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
    
    # SEO API endpoints
    @app.route('/api/seo/analyze', methods=['POST'])
    def analyze_seo():
        """Analyze content for SEO optimization opportunities"""
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({"error": "Invalid JSON data"}), 400
                
            html_content = data.get('content')
            primary_keyword = data.get('primary_keyword')
            secondary_keywords = data.get('secondary_keywords', [])
            meta_title = data.get('meta_title')
            meta_description = data.get('meta_description')
            
            if not html_content or not primary_keyword:
                return jsonify({"error": "Content and primary keyword are required"}), 400
            
            # Perform SEO analysis
            analysis = seo_analyzer.analyze_content(
                html_content=html_content,
                primary_keyword=primary_keyword,
                secondary_keywords=secondary_keywords,
                meta_title=meta_title,
                meta_description=meta_description
            )
            
            # Return the analysis
            return jsonify(analysis)
            
        except Exception as e:
            logger.error(f"Error analyzing SEO: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/seo/optimize', methods=['POST'])
    def optimize_seo():
        """Optimize content for SEO based on analysis"""
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({"error": "Invalid JSON data"}), 400
                
            html_content = data.get('content')
            primary_keyword = data.get('primary_keyword')
            secondary_keywords = data.get('secondary_keywords', [])
            meta_title = data.get('meta_title')
            meta_description = data.get('meta_description')
            
            if not html_content or not primary_keyword:
                return jsonify({"error": "Content and primary keyword are required"}), 400
            
            # Optimize content for SEO
            optimization = seo_optimizer.optimize_article_content(
                html_content=html_content,
                primary_keyword=primary_keyword,
                secondary_keywords=secondary_keywords,
                meta_title=meta_title,
                meta_description=meta_description
            )
            
            # Return the optimized content
            return jsonify(optimization)
            
        except Exception as e:
            logger.error(f"Error optimizing SEO: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/seo/title-variations', methods=['POST'])
    def generate_title_variations():
        """Generate SEO-optimized title variations"""
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({"error": "Invalid JSON data"}), 400
                
            topic = data.get('topic')
            primary_keyword = data.get('primary_keyword')
            secondary_keywords = data.get('secondary_keywords', [])
            count = data.get('count', 5)
            
            if not topic or not primary_keyword:
                return jsonify({"error": "Topic and primary keyword are required"}), 400
            
            # Generate title variations
            titles = seo_optimizer.generate_seo_title_variations(
                topic=topic,
                primary_keyword=primary_keyword,
                secondary_keywords=secondary_keywords,
                count=count
            )
            
            # Return the titles
            return jsonify({"titles": titles})
            
        except Exception as e:
            logger.error(f"Error generating title variations: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/seo/meta-description', methods=['POST'])
    def optimize_meta_description():
        """Generate an optimized meta description"""
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({"error": "Invalid JSON data"}), 400
                
            content_snippet = data.get('content')
            primary_keyword = data.get('primary_keyword')
            max_length = data.get('max_length', 160)
            
            if not content_snippet or not primary_keyword:
                return jsonify({"error": "Content snippet and primary keyword are required"}), 400
            
            # Generate meta description
            description = seo_optimizer.optimize_meta_description(
                content_snippet=content_snippet,
                primary_keyword=primary_keyword,
                max_length=max_length
            )
            
            # Return the description
            return jsonify({"meta_description": description})
            
        except Exception as e:
            logger.error(f"Error generating meta description: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({"error": str(e)}), 500
            
    @app.route('/api/seo/keyword-competition', methods=['POST'])
    def analyze_keyword_competition():
        """Analyze competition for a keyword"""
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({"error": "Invalid JSON data"}), 400
                
            keyword = data.get('keyword')
            related_keywords = data.get('related_keywords')
            
            if not keyword:
                return jsonify({"error": "Keyword is required"}), 400
            
            # Analyze competition
            analysis = seo_analyzer.analyze_keyword_competition(
                keyword=keyword,
                related_keywords=related_keywords
            )
            
            # Return the analysis
            return jsonify(analysis)
            
        except Exception as e:
            logger.error(f"Error analyzing keyword competition: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({"error": str(e)}), 500
    
    # Writing assistant API endpoints
    @app.route('/api/writing/improve', methods=['POST'])
    def improve_content():
        """Improve content using AI writing assistant"""
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({"error": "Invalid JSON data"}), 400
                
            content = data.get('content')
            target_tone = data.get('tone', 'professional')
            improvement_type = data.get('improvement_type', 'comprehensive')
            keywords = data.get('keywords')
            context = data.get('context')
            
            if not content:
                return jsonify({"error": "Content is required"}), 400
            
            # Improve content
            improvement = writing_assistant.improve_content(
                content=content,
                target_tone=target_tone,
                improvement_type=improvement_type,
                keywords=keywords,
                context=context
            )
            
            # Return the improved content
            return jsonify(improvement)
            
        except Exception as e:
            logger.error(f"Error improving content: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/writing/suggest', methods=['POST'])
    def suggest_improvements():
        """Suggest improvements for content without changing it"""
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({"error": "Invalid JSON data"}), 400
                
            content = data.get('content')
            focus_areas = data.get('focus_areas')
            
            if not content:
                return jsonify({"error": "Content is required"}), 400
            
            # Get improvement suggestions
            suggestions = writing_assistant.suggest_improvements(
                content=content,
                focus_areas=focus_areas
            )
            
            # Return the suggestions
            return jsonify(suggestions)
            
        except Exception as e:
            logger.error(f"Error generating improvement suggestions: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/writing/rewrite', methods=['POST'])
    def rewrite_section():
        """Rewrite a specific section of content"""
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({"error": "Invalid JSON data"}), 400
                
            original_text = data.get('text')
            instructions = data.get('instructions')
            context = data.get('context')
            tone = data.get('tone', 'professional')
            
            if not original_text or not instructions:
                return jsonify({"error": "Text and instructions are required"}), 400
            
            # Rewrite section
            rewrite = writing_assistant.rewrite_section(
                original_text=original_text,
                instructions=instructions,
                context=context,
                tone=tone
            )
            
            # Return the rewritten section
            return jsonify(rewrite)
            
        except Exception as e:
            logger.error(f"Error rewriting section: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/writing/variations', methods=['POST'])
    def content_variations():
        """Generate variations of content"""
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({"error": "Invalid JSON data"}), 400
                
            content = data.get('content')
            variation_count = data.get('count', 3)
            instruction = data.get('instruction')
            
            if not content:
                return jsonify({"error": "Content is required"}), 400
            
            # Generate variations
            variations = writing_assistant.generate_content_variations(
                content=content,
                variation_count=variation_count,
                instruction=instruction
            )
            
            # Return the variations
            return jsonify({"variations": variations})
            
        except Exception as e:
            logger.error(f"Error generating content variations: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/writing/check-grammar', methods=['POST'])
    def check_grammar():
        """Check content for grammar and style issues"""
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({"error": "Invalid JSON data"}), 400
                
            content = data.get('content')
            
            if not content:
                return jsonify({"error": "Content is required"}), 400
            
            # Check grammar
            check_results = writing_assistant.check_grammar_and_style(content=content)
            
            # Return the check results
            return jsonify(check_results)
            
        except Exception as e:
            logger.error(f"Error checking grammar: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({"error": str(e)}), 500
    
    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('error.html', error_code=404, error_message='Page not found'), 404
    
    @app.errorhandler(500)
    def server_error(e):
        return render_template('error.html', error_code=500, error_message='Server error'), 500
        
    # Register analytics routes
    register_analytics_routes(app)
    
    # Register SEO Inspirations blueprint
    app.register_blueprint(seo_inspiration_bp)
    
    # Register Content Creator blueprint
    app.register_blueprint(content_creator_bp)
    
    # Register Images routes
    register_image_routes(app)
    
    # Register newsletter blueprint
    app.register_blueprint(newsletter_bp)
