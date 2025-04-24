"""
Routes for newsletter management
"""

from flask import (
    render_template, redirect, url_for, flash, request, jsonify, Blueprint,
    current_app as app
)
import json
from datetime import datetime, timedelta
from sqlalchemy import desc

from app import db
from models import Blog, Newsletter, Subscriber, NewsletterConfig
from utils.newsletter.generator import NewsletterGenerator
from utils.newsletter.distributor import NewsletterDistributor, create_weekly_newsletter_for_blog

def register_newsletter_routes(app):
    """Register newsletter routes with the Flask app"""
    
    # Create blueprint
    newsletter_bp = Blueprint('newsletter', __name__, url_prefix='/newsletter')
    
    app.register_blueprint(newsletter_bp)
    
    # Newsletter Dashboard
    @newsletter_bp.route('/')
    def dashboard():
        """Newsletter dashboard view"""
        # Get all blogs with newsletter config
        blogs = Blog.query.all()
        blogs_with_config = []
        
        for blog in blogs:
            config = NewsletterConfig.query.filter_by(blog_id=blog.id).first()
            enabled = config.enabled if config else False
            
            blogs_with_config.append({
                'id': blog.id,
                'name': blog.name,
                'enabled': enabled,
                'config': config
            })
        
        # Get recent newsletters
        newsletters = Newsletter.query.order_by(desc(Newsletter.created_at)).limit(10).all()
        
        # Get subscriber count
        total_subscribers = Subscriber.query.filter_by(status='active').count()
        
        # Weekly generation schedule
        weekly_blogs = []
        for blog in blogs:
            config = NewsletterConfig.query.filter_by(blog_id=blog.id).first()
            if config and config.enabled and config.frequency == 'weekly':
                day_name = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][config.send_day]
                weekly_blogs.append({
                    'id': blog.id,
                    'name': blog.name,
                    'day': day_name,
                    'time': config.send_time
                })
        
        return render_template(
            'newsletter/dashboard.html',
            blogs=blogs_with_config,
            newsletters=newsletters,
            total_subscribers=total_subscribers,
            weekly_blogs=weekly_blogs
        )
    
    # Subscribers Management
    @newsletter_bp.route('/subscribers')
    def subscribers():
        """View and manage subscribers"""
        subscribers = Subscriber.query.order_by(Subscriber.created_at.desc()).all()
        blogs = Blog.query.all()
        
        # Get count by status
        active_count = Subscriber.query.filter_by(status='active').count()
        unsubscribed_count = Subscriber.query.filter_by(status='unsubscribed').count()
        bounced_count = Subscriber.query.filter_by(status='bounced').count()
        
        return render_template(
            'newsletter/subscribers.html',
            subscribers=subscribers,
            blogs=blogs,
            active_count=active_count,
            unsubscribed_count=unsubscribed_count,
            bounced_count=bounced_count
        )
    
    @newsletter_bp.route('/subscribers/add', methods=['POST'])
    def add_subscriber():
        """Add a new subscriber"""
        try:
            email = request.form.get('email')
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            blog_id = request.form.get('blog_id')
            
            if not email:
                flash('Email is required', 'danger')
                return redirect(url_for('newsletter.subscribers'))
            
            # Check if subscriber already exists
            existing = Subscriber.query.filter_by(email=email).first()
            if existing:
                flash(f'Subscriber with email {email} already exists', 'warning')
                return redirect(url_for('newsletter.subscribers'))
            
            # Create new subscriber
            subscriber = Subscriber(
                email=email,
                first_name=first_name,
                last_name=last_name,
                status='active',
                blog_id=blog_id if blog_id else None
            )
            
            db.session.add(subscriber)
            db.session.commit()
            
            flash(f'Subscriber {email} added successfully', 'success')
            
            # If EmailOctopus is configured, also add to list
            if blog_id:
                try:
                    distributor = NewsletterDistributor()
                    client = distributor.get_email_client(int(blog_id))
                    if client:
                        fields = {
                            "FirstName": first_name or "",
                            "LastName": last_name or ""
                        }
                        client.add_subscriber(email=email, fields=fields)
                except Exception as e:
                    app.logger.error(f"Error adding subscriber to EmailOctopus: {str(e)}")
            
            return redirect(url_for('newsletter.subscribers'))
            
        except Exception as e:
            app.logger.error(f"Error adding subscriber: {str(e)}")
            flash(f'Error adding subscriber: {str(e)}', 'danger')
            return redirect(url_for('newsletter.subscribers'))
    
    @newsletter_bp.route('/subscribers/<int:subscriber_id>/edit', methods=['POST'])
    def edit_subscriber(subscriber_id):
        """Edit a subscriber"""
        try:
            subscriber = Subscriber.query.get(subscriber_id)
            if not subscriber:
                flash(f'Subscriber with ID {subscriber_id} not found', 'danger')
                return redirect(url_for('newsletter.subscribers'))
            
            subscriber.email = request.form.get('email')
            subscriber.first_name = request.form.get('first_name')
            subscriber.last_name = request.form.get('last_name')
            subscriber.status = request.form.get('status', 'active')
            
            blog_id = request.form.get('blog_id')
            subscriber.blog_id = blog_id if blog_id else None
            
            db.session.commit()
            flash('Subscriber updated successfully', 'success')
            return redirect(url_for('newsletter.subscribers'))
            
        except Exception as e:
            app.logger.error(f"Error updating subscriber: {str(e)}")
            flash(f'Error updating subscriber: {str(e)}', 'danger')
            return redirect(url_for('newsletter.subscribers'))
    
    @newsletter_bp.route('/subscribers/<int:subscriber_id>/delete', methods=['POST'])
    def delete_subscriber(subscriber_id):
        """Delete a subscriber"""
        try:
            subscriber = Subscriber.query.get(subscriber_id)
            if not subscriber:
                flash(f'Subscriber with ID {subscriber_id} not found', 'danger')
                return redirect(url_for('newsletter.subscribers'))
            
            db.session.delete(subscriber)
            db.session.commit()
            flash('Subscriber deleted successfully', 'success')
            return redirect(url_for('newsletter.subscribers'))
            
        except Exception as e:
            app.logger.error(f"Error deleting subscriber: {str(e)}")
            flash(f'Error deleting subscriber: {str(e)}', 'danger')
            return redirect(url_for('newsletter.subscribers'))
    
    # Newsletter Configuration
    @newsletter_bp.route('/config/<int:blog_id>', methods=['GET', 'POST'])
    def newsletter_config(blog_id):
        """Configure newsletter settings for a blog"""
        blog = Blog.query.get(blog_id)
        if not blog:
            flash(f'Blog with ID {blog_id} not found', 'danger')
            return redirect(url_for('newsletter.dashboard'))
        
        # Get or create config
        config = NewsletterConfig.query.filter_by(blog_id=blog_id).first()
        if not config:
            config = NewsletterConfig(blog_id=blog_id)
            db.session.add(config)
            db.session.commit()
        
        if request.method == 'POST':
            try:
                # Update config from form
                config.enabled = request.form.get('enabled') == 'on'
                config.frequency = request.form.get('frequency')
                config.send_day = int(request.form.get('send_day', 1))
                config.send_time = request.form.get('send_time', '10:00')
                config.from_name = request.form.get('from_name')
                config.from_email = request.form.get('from_email')
                config.reply_to = request.form.get('reply_to')
                config.email_octopus_api_key = request.form.get('email_octopus_api_key')
                config.email_octopus_list_id = request.form.get('email_octopus_list_id')
                
                # Save settings
                settings = {}
                for key in request.form:
                    if key.startswith('setting_'):
                        settings[key[8:]] = request.form.get(key)
                
                if settings:
                    config.set_settings(settings)
                
                db.session.commit()
                flash('Newsletter configuration saved successfully', 'success')
                return redirect(url_for('newsletter.dashboard'))
                
            except Exception as e:
                app.logger.error(f"Error updating newsletter config: {str(e)}")
                flash(f'Error updating configuration: {str(e)}', 'danger')
        
        # Render config form
        return render_template(
            'newsletter/config.html',
            blog=blog,
            config=config
        )
    
    # Newsletter Management
    @newsletter_bp.route('/newsletters')
    def newsletters():
        """View and manage newsletters"""
        newsletters = Newsletter.query.order_by(desc(Newsletter.created_at)).all()
        blogs = Blog.query.all()
        
        return render_template(
            'newsletter/newsletters.html',
            newsletters=newsletters,
            blogs=blogs
        )
    
    @newsletter_bp.route('/create/<int:blog_id>', methods=['GET', 'POST'])
    def create_newsletter(blog_id):
        """Create a new newsletter"""
        blog = Blog.query.get(blog_id)
        if not blog:
            flash(f'Blog with ID {blog_id} not found', 'danger')
            return redirect(url_for('newsletter.newsletters'))
        
        if request.method == 'POST':
            try:
                title = request.form.get('title')
                subject = request.form.get('subject')
                days = int(request.form.get('days', 7))
                article_limit = int(request.form.get('article_limit', 5))
                
                scheduled = request.form.get('scheduled') == 'on'
                scheduled_date = request.form.get('scheduled_date')
                scheduled_time = request.form.get('scheduled_time')
                
                if not title or not subject:
                    flash('Title and subject are required', 'danger')
                    return redirect(url_for('newsletter.create_newsletter', blog_id=blog_id))
                
                scheduled_for = None
                if scheduled and scheduled_date and scheduled_time:
                    try:
                        scheduled_date_obj = datetime.strptime(scheduled_date, '%Y-%m-%d')
                        hour, minute = map(int, scheduled_time.split(':'))
                        scheduled_for = scheduled_date_obj.replace(hour=hour, minute=minute)
                    except ValueError:
                        flash('Invalid date or time format', 'danger')
                        return redirect(url_for('newsletter.create_newsletter', blog_id=blog_id))
                
                # Generate newsletter content
                generator = NewsletterGenerator(blog_id)
                result = generator.create_scheduled_newsletter(
                    title=title,
                    subject=subject,
                    scheduled_for=scheduled_for,
                    days=days,
                    article_limit=article_limit
                )
                
                if "error" in result:
                    flash(f"Error creating newsletter: {result['error']}", 'danger')
                    return redirect(url_for('newsletter.create_newsletter', blog_id=blog_id))
                
                flash('Newsletter created successfully', 'success')
                return redirect(url_for('newsletter.newsletters'))
                
            except Exception as e:
                app.logger.error(f"Error creating newsletter: {str(e)}")
                flash(f'Error creating newsletter: {str(e)}', 'danger')
                return redirect(url_for('newsletter.create_newsletter', blog_id=blog_id))
        
        # Show newsletter creation form
        return render_template(
            'newsletter/create.html',
            blog=blog
        )
    
    @newsletter_bp.route('/preview/<int:newsletter_id>')
    def preview_newsletter(newsletter_id):
        """Preview a newsletter"""
        newsletter = Newsletter.query.get(newsletter_id)
        if not newsletter:
            flash(f'Newsletter with ID {newsletter_id} not found', 'danger')
            return redirect(url_for('newsletter.newsletters'))
        
        return render_template(
            'newsletter/preview.html',
            newsletter=newsletter
        )
    
    @newsletter_bp.route('/send/<int:newsletter_id>', methods=['POST'])
    def send_newsletter(newsletter_id):
        """Send a newsletter immediately"""
        newsletter = Newsletter.query.get(newsletter_id)
        if not newsletter:
            flash(f'Newsletter with ID {newsletter_id} not found', 'danger')
            return redirect(url_for('newsletter.newsletters'))
        
        # Check status
        if newsletter.status == 'sent':
            flash(f'Newsletter has already been sent on {newsletter.sent_at}', 'warning')
            return redirect(url_for('newsletter.newsletters'))
        
        try:
            # Send newsletter
            distributor = NewsletterDistributor()
            result = distributor.send_newsletter(newsletter_id)
            
            if "error" in result:
                flash(f"Error sending newsletter: {result['error']}", 'danger')
            else:
                flash('Newsletter sent successfully', 'success')
                
            return redirect(url_for('newsletter.newsletters'))
            
        except Exception as e:
            app.logger.error(f"Error sending newsletter: {str(e)}")
            flash(f'Error sending newsletter: {str(e)}', 'danger')
            return redirect(url_for('newsletter.newsletters'))
    
    @newsletter_bp.route('/delete/<int:newsletter_id>', methods=['POST'])
    def delete_newsletter(newsletter_id):
        """Delete a newsletter"""
        newsletter = Newsletter.query.get(newsletter_id)
        if not newsletter:
            flash(f'Newsletter with ID {newsletter_id} not found', 'danger')
            return redirect(url_for('newsletter.newsletters'))
        
        try:
            db.session.delete(newsletter)
            db.session.commit()
            flash('Newsletter deleted successfully', 'success')
            return redirect(url_for('newsletter.newsletters'))
            
        except Exception as e:
            app.logger.error(f"Error deleting newsletter: {str(e)}")
            flash(f'Error deleting newsletter: {str(e)}', 'danger')
            return redirect(url_for('newsletter.newsletters'))
    
    # API Routes
    @newsletter_bp.route('/api/process-pending', methods=['POST'])
    def api_process_pending():
        """API endpoint to process pending newsletters"""
        try:
            distributor = NewsletterDistributor()
            results = distributor.process_pending_newsletters()
            return jsonify(results)
            
        except Exception as e:
            app.logger.error(f"Error processing pending newsletters: {str(e)}")
            return jsonify({"error": str(e)}), 500
    
    @newsletter_bp.route('/api/create-weekly/<int:blog_id>', methods=['POST'])
    def api_create_weekly(blog_id):
        """API endpoint to create a weekly newsletter for a blog"""
        try:
            result = create_weekly_newsletter_for_blog(blog_id)
            return jsonify(result)
            
        except Exception as e:
            app.logger.error(f"Error creating weekly newsletter: {str(e)}")
            return jsonify({"error": str(e)}), 500
    
    @newsletter_bp.route('/api/upload-subscribers/<int:blog_id>', methods=['POST'])
    def api_upload_subscribers(blog_id):
        """API endpoint to upload subscribers to EmailOctopus"""
        try:
            distributor = NewsletterDistributor()
            result = distributor.upload_subscribers(blog_id)
            return jsonify(result)
            
        except Exception as e:
            app.logger.error(f"Error uploading subscribers: {str(e)}")
            return jsonify({"error": str(e)}), 500