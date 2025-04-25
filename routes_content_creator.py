"""
Content Creator Routes Module
"""
import json
import logging
import re
from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from sqlalchemy import desc, and_, or_, func

from app import db
from models import Blog, ArticleTopic, ContentLog, AutomationRule
from utils.writing import content_generator
from utils.automation import content_automation

# Create Blueprint
content_creator_bp = Blueprint('content_creator', __name__)
logger = logging.getLogger(__name__)

# Custom Jinja filters
@content_creator_bp.app_template_filter('split')
def split_filter(value, delimiter=' '):
    """Split a string into a list based on delimiter"""
    if not value:
        return []
    return value.split(delimiter)


@content_creator_bp.route('/content-creator')
def content_dashboard():
    """Content creation dashboard view"""
    # Get all blogs
    blogs = Blog.query.filter_by(active=True).all()
    
    # Get status filter
    status_filter = request.args.get('status', 'pending')
    
    # Get blog filter (optional)
    blog_filter = request.args.get('blog_id')
    if blog_filter:
        try:
            blog_filter = int(blog_filter)
        except (ValueError, TypeError):
            blog_filter = None
    
    # Get all approved topics for the selected blogs
    query = ArticleTopic.query.filter(ArticleTopic.status == 'approved')
    
    if blog_filter:
        query = query.filter(ArticleTopic.blog_id == blog_filter)
    
    # Get approved topics ordered by score (high to low)
    approved_topics = query.order_by(desc(ArticleTopic.score)).limit(10).all()
    
    # Get recent content logs
    content_query = ContentLog.query
    
    if blog_filter:
        content_query = content_query.filter(ContentLog.blog_id == blog_filter)
    
    # Get the latest content logs
    recent_content = content_query.order_by(desc(ContentLog.created_at)).limit(10).all()
    
    # Get any drafts in progress
    draft_query = ContentLog.query.filter(ContentLog.status == 'draft')
    
    if blog_filter:
        draft_query = draft_query.filter(ContentLog.blog_id == blog_filter)
    
    drafts = draft_query.all()
    
    return render_template(
        'content/dashboard.html',
        blogs=blogs,
        approved_topics=approved_topics,
        recent_content=recent_content,
        drafts=drafts,
        active_blog=blog_filter,
        title="Content Creator"
    )

@content_creator_bp.route('/content-generator')
def content_generator_page():
    """Content generator page with static topic selection and dynamic editor"""
    # Get all blogs for dropdown
    blogs = Blog.query.filter_by(active=True).all()
    
    # Check if there are any blogs
    if not blogs:
        flash('No active blogs found. Please create a blog first.', 'warning')
        return redirect(url_for('content_creator.content_dashboard'))
    
    return render_template('content/simple_topic_selector.html', 
                          title="Content Generator",
                          blogs=blogs)

@content_creator_bp.route('/standard-editor')
def standard_editor_page():
    """Standard editor page with WYSIWYG editor"""
    # Get all blogs for dropdown
    blogs = Blog.query.filter_by(active=True).all()
    
    # Check if there are any blogs
    if not blogs:
        flash('No active blogs found. Please create a blog first.', 'warning')
        return redirect(url_for('content_creator.content_dashboard'))
    
    # Get topic ID if passed as query parameter
    topic_id = request.args.get('topic_id')
    topic = None
    if topic_id:
        try:
            topic = ArticleTopic.query.get(int(topic_id))
        except (ValueError, TypeError):
            flash('Invalid topic ID', 'warning')
    
    # Create a blank content log for the editor
    content_log = None
    if topic:
        content_log = ContentLog(
            blog_id=topic.blog_id,
            title=topic.title,
            status='draft',
            created_at=datetime.utcnow()
        )
        db.session.add(content_log)
        db.session.commit()
        logger.info(f"Created new draft for standard editor: {content_log.id}")
    
    return render_template('content/standard_editor.html', 
                          title="Standard Editor",
                          blogs=blogs,
                          topic=topic,
                          content_log=content_log)


@content_creator_bp.route('/content-creator/generate', methods=['POST'])
def generate_content():
    """Generate content from a topic"""
    topic_id = request.form.get('topic_id')
    style = request.form.get('style', 'informative')
    paragraph_count = request.form.get('paragraph_count', '4')
    auto_generate = request.form.get('auto_generate', '0')
    
    # Ensure paragraph_count is a valid integer between 3 and 6
    try:
        paragraph_count = int(paragraph_count)
        if paragraph_count < 3:
            paragraph_count = 3
        elif paragraph_count > 6:
            paragraph_count = 6
    except (ValueError, TypeError):
        paragraph_count = 4  # Default to 4 paragraphs if invalid
    
    # Convert auto_generate to integer
    try:
        auto_generate = int(auto_generate)
    except (ValueError, TypeError):
        auto_generate = 0
    
    if not topic_id:
        flash('Topic ID is required', 'danger')
        return redirect(url_for('content_creator.content_dashboard'))
    
    try:
        # Get the topic
        topic = ArticleTopic.query.get(topic_id)
        
        if not topic:
            flash('Topic not found', 'danger')
            return redirect(url_for('content_creator.content_dashboard'))
        
        # Create a draft content log
        content_log = ContentLog(
            blog_id=topic.blog_id,
            title=topic.title,
            status='draft',
            created_at=datetime.utcnow()
        )
        
        db.session.add(content_log)
        db.session.commit()
        
        # Redirect to the content generation page with auto_generate flag
        return redirect(url_for('content_creator.edit_content', 
                                content_id=content_log.id, 
                                topic_id=topic_id, 
                                style=style, 
                                paragraph_count=paragraph_count,
                                auto_generate=auto_generate))
        
    except Exception as e:
        logger.error(f"Error starting content generation: {str(e)}")
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('content_creator.content_dashboard'))


@content_creator_bp.route('/content-creator/edit/<int:content_id>', methods=['GET', 'POST'])
def edit_content(content_id):
    """Edit content before publishing"""
    content_log = ContentLog.query.get_or_404(content_id)
    topic_id = request.args.get('topic_id')
    style = request.args.get('style', 'informative')
    paragraph_count = request.args.get('paragraph_count', 4)
    auto_generate = request.args.get('auto_generate', '0') == '1'
    
    # Ensure paragraph_count is a valid integer between 3 and 6
    try:
        paragraph_count = int(paragraph_count)
        if paragraph_count < 3:
            paragraph_count = 3
        elif paragraph_count > 6:
            paragraph_count = 6
    except (ValueError, TypeError):
        paragraph_count = 4  # Default to 4 paragraphs if invalid
    
    # If this is a POST request, update the content and metadata
    if request.method == 'POST':
        try:
            content_log.title = request.form.get('title', content_log.title)
            
            # Store the content and metadata in the error_message field temporarily
            # In a production system, there would be a better structure for this
            content_data = {
                'content': request.form.get('content', ''),
                'meta_description': request.form.get('meta_description', ''),
                'excerpt': request.form.get('excerpt', ''),
                'tags': request.form.get('tags', '').split(','),
                'featured_image_url': request.form.get('featured_image_url', ''),
                'topic_id': request.form.get('topic_id', topic_id)  # Zapisujemy topic_id w danych artykułu
            }
            
            content_log.error_message = json.dumps(content_data)
            
            # Update status based on action
            action = request.form.get('action', 'save')
            
            if action == 'publish':
                content_log.status = 'ready_to_publish'
                flash('Content marked as ready to publish', 'success')
            else:
                content_log.status = 'draft'
                flash('Draft saved successfully', 'success')
            
            db.session.commit()
            
            if action == 'publish':
                return redirect(url_for('content_creator.content_dashboard'))
            else:
                # Przekazujemy również topic_id przy przekierowaniu, aby nie zniknął
                stored_topic_id = content_data.get('topic_id')
                return redirect(url_for('content_creator.edit_content', content_id=content_id, topic_id=stored_topic_id))
                
        except Exception as e:
            logger.error(f"Error saving content: {str(e)}")
            flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('content_creator.edit_content', content_id=content_id))
    
    # For GET requests, show the edit form
    topic = None
    content_html = ''
    meta_description = ''
    excerpt = ''
    tags = []
    featured_image_url = ''
    stored_topic_id = None
    
    # Load content from the content_log if it exists
    if content_log.error_message:
        try:
            content_data = json.loads(content_log.error_message)
            content_html = content_data.get('content', '')
            meta_description = content_data.get('meta_description', '')
            excerpt = content_data.get('excerpt', '')
            tags = content_data.get('tags', [])
            featured_image_url = content_data.get('featured_image_url', '')
            stored_topic_id = content_data.get('topic_id')  # Wczytujemy zapisany topic_id
        except json.JSONDecodeError:
            # If the JSON is invalid, we'll just use the defaults
            pass
    
    # Używamy zapisanego topic_id jeśli dostępny, w przeciwnym razie użyj z parametrów URL
    topic_id = topic_id or stored_topic_id
    
    # If the content is empty and we have a topic, generate content
    if not content_html and topic_id:
        try:
            topic = ArticleTopic.query.get(topic_id)
            
            if topic:
                # Generate content using the paragraph-based approach
                generation_result = content_generator.generate_article_by_paragraphs(
                    topic=topic.title,
                    keywords=topic.get_keywords() if topic.get_keywords() else [],
                    style=style,
                    paragraph_count=paragraph_count
                )
                
                content_html = generation_result.get('content', '')
                meta_description = generation_result.get('meta_description', '')
                excerpt = generation_result.get('excerpt', '')
                tags = generation_result.get('tags', [])
                featured_image_url = generation_result.get('featured_image_url', '')
                
                # Save the generated content to the content_log
                content_data = {
                    'content': content_html,
                    'meta_description': meta_description,
                    'excerpt': excerpt,
                    'tags': tags,
                    'featured_image_url': featured_image_url,
                    'topic_id': topic_id  # Zapisujemy topic_id w danych artykułu
                }
                
                content_log.error_message = json.dumps(content_data)
                db.session.commit()
                
        except Exception as e:
            logger.error(f"Error generating content: {str(e)}")
            error_message = str(e)
            # Sprawdź, czy błąd jest związany z API OpenRouter
            if "openrouter" in error_message.lower() or "ai service" in error_message.lower():
                error_message = "Problem z połączeniem z usługą AI. Spróbuj ponownie za chwilę."
            elif "timeout" in error_message.lower():
                error_message = "Przekroczono czas oczekiwania na odpowiedź z usługi AI. Spróbuj ponownie."
            flash(f'Błąd generowania treści: {error_message}', 'danger')
            
            # Zapisz informację o błędzie w content_log
            content_data = {
                'content': '<p>Nie udało się wygenerować treści. Spróbuj ponownie.</p>',
                'meta_description': '',
                'excerpt': '',
                'tags': [],
                'featured_image_url': '',
                'topic_id': topic_id,
                'generation_error': error_message
            }
            content_log.error_message = json.dumps(content_data)
            db.session.commit()
    
    # If we don't have a topic object yet but we have a topic_id, get it
    if not topic and topic_id:
        topic = ArticleTopic.query.get(topic_id)
    
    # Get the blog
    blog = Blog.query.get(content_log.blog_id)
    
    return render_template(
        'content/editor.html',
        content_log=content_log,
        topic=topic,
        blog=blog,
        topic_id=topic_id,  # Przekazujemy topic_id do szablonu
        content_html=content_html,
        meta_description=meta_description,
        excerpt=excerpt,
        tags=tags,
        featured_image_url=featured_image_url,
        style=style,
        paragraph_count=paragraph_count,
        auto_generate=auto_generate  # Przekazujemy flagę auto_generate do szablonu
    )


@content_creator_bp.route('/content-creator/preview/<int:content_id>')
def preview_content(content_id):
    """Preview content before publishing"""
    content_log = ContentLog.query.get_or_404(content_id)
    
    content_html = ''
    meta_description = ''
    excerpt = ''
    tags = []
    featured_image_url = ''
    
    # Load content from the content_log if it exists
    logger.info(f"Preview content for content_log.id={content_id}, status={content_log.status}")
    logger.info(f"Content log error_message length: {len(content_log.error_message) if content_log.error_message else 0}")
    
    if content_log.error_message:
        try:
            content_data = json.loads(content_log.error_message)
            logger.info(f"Content data keys: {list(content_data.keys())}")
            
            content_html = content_data.get('content', '')
            meta_description = content_data.get('meta_description', '')
            excerpt = content_data.get('excerpt', '')
            tags = content_data.get('tags', [])
            featured_image_url = content_data.get('featured_image_url', '')
            
            logger.info(f"Content HTML length: {len(content_html)}")
            logger.info(f"Meta description: {meta_description[:50]}...")
            logger.info(f"Excerpt: {excerpt[:50]}...")
        except json.JSONDecodeError as e:
            # If the JSON is invalid, we'll just use the defaults
            logger.error(f"JSONDecodeError in preview: {str(e)}")
            pass
    
    # Get the blog
    blog = Blog.query.get(content_log.blog_id)
    
    return render_template(
        'content/preview.html',
        content_log=content_log,
        blog=blog,
        content_html=content_html,
        meta_description=meta_description,
        excerpt=excerpt,
        tags=tags,
        featured_image_url=featured_image_url
    )


@content_creator_bp.route('/content-creator/publish/<int:content_id>', methods=['POST'])
def publish_content(content_id):
    """Publish content to WordPress"""
    content_log = ContentLog.query.get_or_404(content_id)
    
    # Only allow publishing of content that's marked as ready
    if content_log.status != 'ready_to_publish':
        flash('Content is not ready to publish', 'danger')
        return redirect(url_for('content_creator.content_dashboard'))
    
    try:
        # Load content from the content_log
        if not content_log.error_message:
            flash('No content found to publish', 'danger')
            return redirect(url_for('content_creator.content_dashboard'))
        
        content_data = json.loads(content_log.error_message)
        content_html = content_data.get('content', '')
        meta_description = content_data.get('meta_description', '')
        excerpt = content_data.get('excerpt', '')
        tags = content_data.get('tags', [])
        featured_image_url = content_data.get('featured_image_url', '')
        
        # Get the blog
        blog = Blog.query.get(content_log.blog_id)
        
        if not blog:
            flash('Blog not found', 'danger')
            return redirect(url_for('content_creator.content_dashboard'))
        
        # In a real implementation, this would publish to WordPress
        # For now, we'll just mark it as published
        content_log.status = 'published'
        content_log.published_at = datetime.utcnow()
        
        # Update the topic to mark it as used
        topic_id = request.form.get('topic_id')
        if topic_id:
            try:
                topic = ArticleTopic.query.get(topic_id)
                if topic and topic.status == 'approved':
                    topic.status = 'used'
                    db.session.commit()
            except Exception as e:
                logger.error(f"Error updating topic status: {str(e)}")
        
        db.session.commit()
        
        flash('Content published successfully', 'success')
        return redirect(url_for('content_creator.content_dashboard'))
        
    except Exception as e:
        logger.error(f"Error publishing content: {str(e)}")
        flash(f'Error publishing content: {str(e)}', 'danger')
        return redirect(url_for('content_creator.content_dashboard'))


@content_creator_bp.route('/content-creator/delete/<int:content_id>', methods=['POST'])
def delete_content(content_id):
    """Delete a draft content log"""
    content_log = ContentLog.query.get_or_404(content_id)
    
    # Only allow deletion of drafts
    if content_log.status not in ['draft', 'ready_to_publish']:
        flash('Only drafts can be deleted', 'danger')
        return redirect(url_for('content_creator.content_dashboard'))
    
    try:
        db.session.delete(content_log)
        db.session.commit()
        
        flash('Draft deleted successfully', 'success')
        return redirect(url_for('content_creator.content_dashboard'))
        
    except Exception as e:
        logger.error(f"Error deleting draft: {str(e)}")
        flash(f'Error deleting draft: {str(e)}', 'danger')
        return redirect(url_for('content_creator.content_dashboard'))


@content_creator_bp.route('/content-creator/regenerate/<int:content_id>', methods=['POST'])
def regenerate_content(content_id):
    """Regenerate content with different settings"""
    content_log = ContentLog.query.get_or_404(content_id)
    
    topic_id = request.form.get('topic_id')
    style = request.form.get('style', 'informative')
    paragraph_count = request.form.get('paragraph_count', '4')
    
    # Ensure paragraph_count is a valid integer between 3 and 6
    try:
        paragraph_count = int(paragraph_count)
        if paragraph_count < 3:
            paragraph_count = 3
        elif paragraph_count > 6:
            paragraph_count = 6
    except (ValueError, TypeError):
        paragraph_count = 4  # Default to 4 paragraphs if invalid
    
    if not topic_id:
        flash('Topic ID is required', 'danger')
        return redirect(url_for('content_creator.edit_content', content_id=content_id))
    
    try:
        # Get the topic
        topic = ArticleTopic.query.get(topic_id)
        
        if not topic:
            flash('Topic not found', 'danger')
            return redirect(url_for('content_creator.edit_content', content_id=content_id))
        
        # Clear existing content
        content_log.error_message = None
        db.session.commit()
        
        # Redirect to the content editor to trigger regeneration
        return redirect(url_for('content_creator.edit_content', content_id=content_id, topic_id=topic_id, style=style, paragraph_count=paragraph_count))
        
    except Exception as e:
        logger.error(f"Error regenerating content: {str(e)}")
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('content_creator.edit_content', content_id=content_id))


@content_creator_bp.route('/content-creator/generate-metadata', methods=['POST'])
def generate_metadata():
    """Generate metadata from content"""
    content = request.form.get('content', '')
    
    if not content:
        return jsonify({'success': False, 'message': 'Content is required'})
    
    try:
        # Use the content generator to create metadata
        metadata = content_generator.generate_metadata(content)
        
        return jsonify({
            'success': True,
            'meta_description': metadata.get('meta_description', ''),
            'excerpt': metadata.get('excerpt', ''),
            'tags': metadata.get('tags', [])
        })
        
    except Exception as e:
        logger.error(f"Error generating metadata: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


# Dynamic Content Generation API Endpoints

@content_creator_bp.route('/content-creator/api/plan', methods=['POST'])
def generate_article_plan_api():
    """Generate article plan API endpoint for dynamic content generation"""
    logger.info("Article plan generation API called")
    
    # Log all form data
    logger.info("Form data: %s", dict(request.form))
    
    topic = request.form.get('topic', '')
    paragraph_count = request.form.get('paragraph_count', '4')
    style = request.form.get('style', 'informative')
    
    logger.info("Generating plan for topic: %s, paragraph_count: %s, style: %s", 
               topic, paragraph_count, style)
    
    # Validate inputs
    if not topic:
        return jsonify({
            'success': False,
            'message': 'No topic provided'
        })
    
    try:
        paragraph_count = int(paragraph_count)
        if paragraph_count < 3:
            paragraph_count = 3
        elif paragraph_count > 6:
            paragraph_count = 6
    except (ValueError, TypeError):
        paragraph_count = 4
    
    try:
        # Generate article plan
        plan_result = content_generator.generate_article_plan(topic, paragraph_count, style)
        
        # Log the plan generation
        logger.info(f"Generated article plan for '{topic}' with {paragraph_count} paragraphs")
        
        return jsonify({
            'success': True,
            'plan': plan_result.get('plan', [])
        })
    except Exception as e:
        logger.error(f"Error generating article plan: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        })

@content_creator_bp.route('/content-creator/api/create-draft-content', methods=['POST'])
def api_create_draft_content_v2():
    """Enhanced API endpoint to create a draft content entry and return its ID"""
    try:
        # Get request parameters - supports both JSON and form data
        if request.is_json:
            data = request.get_json()
            title = data.get('title')
            topic_id = data.get('topic_id')
        else:
            title = request.form.get('title')
            topic_id = request.form.get('topic_id')
        
        # Validate required parameters
        if not title and not topic_id:
            return jsonify({'success': False, 'message': 'Either title or topic_id is required'})
        
        # Get blog_id and title from topic_id if provided
        blog_id = None
        if topic_id:
            try:
                topic = ArticleTopic.query.get(topic_id)
                if topic:
                    blog_id = topic.blog_id
                    # Use topic title if no title was provided
                    if not title:
                        title = topic.title
                else:
                    return jsonify({'success': False, 'message': 'Topic not found'})
            except Exception as topic_error:
                logger.warning(f"Error getting topic: {str(topic_error)}")
                return jsonify({'success': False, 'message': f'Error getting topic: {str(topic_error)}'})
        
        # If we couldn't get blog_id from topic, use the first active blog
        if not blog_id:
            blog = Blog.query.filter_by(active=True).first()
            if blog:
                blog_id = blog.id
            else:
                return jsonify({'success': False, 'message': 'No active blogs found'})
        
        # Create a draft content log
        content_log = ContentLog(
            blog_id=blog_id,
            title=title,
            status='draft',
            created_at=datetime.utcnow()
        )
        
        db.session.add(content_log)
        db.session.commit()
        
        logger.info(f"Created draft content: ID={content_log.id}, Title='{title}'")
        
        # Return the content ID
        return jsonify({
            'success': True,
            'content_id': content_log.id,
            'title': title,
            'blog_id': blog_id,
            'topic_id': topic_id
        })
        
    except Exception as e:
        logger.error(f"Error creating draft content: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@content_creator_bp.route('/content-creator/api/paragraph', methods=['POST'])
def generate_single_paragraph_api():
    """Generate single paragraph API endpoint for dynamic content generation"""
    logger.info("Paragraph generation API called")
    
    # Log all form data
    logger.info("Form data: %s", dict(request.form))
    
    topic = request.form.get('topic', '')
    paragraph_topic = request.form.get('paragraph_topic', '')
    style = request.form.get('style', 'informative')
    paragraph_index = request.form.get('paragraph_index', '0')
    total_paragraphs = request.form.get('total_paragraphs', '4')
    
    # Log parsed values
    logger.info("Generating paragraph for topic: %s, paragraph_topic: %s, style: %s, index: %s/%s", 
               topic, paragraph_topic, style, paragraph_index, total_paragraphs)
    
    # Validate inputs
    if not topic or not paragraph_topic:
        return jsonify({
            'success': False,
            'message': 'Topic and paragraph topic are required'
        })
    
    try:
        paragraph_index = int(paragraph_index)
        total_paragraphs = int(total_paragraphs)
        is_introduction = paragraph_index == 0
        is_conclusion = paragraph_index == total_paragraphs - 1
    except (ValueError, TypeError):
        is_introduction = False
        is_conclusion = False
    
    try:
        # Generate paragraph
        result = content_generator.generate_paragraph(
            topic=topic,
            paragraph_topic=paragraph_topic,
            style=style,
            is_introduction=is_introduction,
            is_conclusion=is_conclusion
        )
        
        # Log the paragraph generation
        logger.info(f"Generated paragraph {paragraph_index+1}/{total_paragraphs} for '{topic}': {paragraph_topic}")
        
        return jsonify({
            'success': True,
            'content': result.get('content', '')
        })
    except Exception as e:
        logger.error(f"Error generating paragraph: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        })
    
@content_creator_bp.route('/api/dynamic/paragraph', methods=['POST'])
def generate_dynamic_paragraph():
    """API endpoint for dynamic paragraph generation with real-time updates"""
    topic = request.form.get('topic', '')
    paragraph_topic = request.form.get('paragraph_topic', '')
    style = request.form.get('style', 'informative')
    paragraph_index = request.form.get('paragraph_index', '0')
    total_paragraphs = request.form.get('total_paragraphs', '4')
    
    # Validate inputs
    if not topic or not paragraph_topic:
        return jsonify({
            'success': False,
            'message': 'Topic and paragraph topic are required'
        })
    
    try:
        paragraph_index = int(paragraph_index)
        total_paragraphs = int(total_paragraphs)
        is_introduction = paragraph_index == 0
        is_conclusion = paragraph_index == total_paragraphs - 1
    except (ValueError, TypeError):
        is_introduction = False
        is_conclusion = False
    
    try:
        # Generate paragraph
        result = content_generator.generate_paragraph(
            topic=topic,
            paragraph_topic=paragraph_topic,
            style=style,
            is_introduction=is_introduction,
            is_conclusion=is_conclusion
        )
        
        # Log the paragraph generation
        logger.info(f"Generated paragraph {paragraph_index+1}/{total_paragraphs} for '{topic}': {paragraph_topic}")
        
        return jsonify({
            'success': True,
            'content': result.get('content', '')
        })
    except Exception as e:
        logger.error(f"Error generating paragraph: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        })

# Implementation moved to the existing generate_dynamic_paragraph_v2 method below

# Automation routes

@content_creator_bp.route('/content-creator/automation')
def automation_dashboard():
    """Content automation dashboard view"""
    # Get all blogs
    blogs = Blog.query.filter_by(active=True).all()
    
    # Get active automation rules
    active_rules = AutomationRule.query.filter_by(is_active=True).all()
    
    # Get inactive automation rules
    inactive_rules = AutomationRule.query.filter_by(is_active=False).all()
    
    # Get automation logs from the utility function
    logs = content_automation.get_automation_logs(limit=20)
    
    # Render the automation dashboard
    return render_template(
        'content/automation.html',
        blogs=blogs,
        active_rules=active_rules,
        inactive_rules=inactive_rules,
        logs=logs,
        title="Content Automation"
    )


@content_creator_bp.route('/content-creator/automation/create', methods=['GET', 'POST'])
def create_automation_rule():
    """Create a new automation rule"""
    # If GET request, render the create form
    if request.method == 'GET':
        blogs = Blog.query.filter_by(active=True).all()
        return render_template(
            'content/edit_automation.html',
            rule=None,
            blogs=blogs,
            title="Create Automation Rule"
        )
    
    # If POST request, create a new rule
    try:
        # Get form data
        name = request.form.get('name', '')
        blog_id = request.form.get('blog_id')
        
        # Content settings
        content_tone = request.form.get('writing_style', 'informative')  # Get from form as writing_style but use content_tone in db
        content_length = request.form.get('content_length', 'medium')
        
        # Paragraph mode settings
        use_paragraph_mode = 'use_paragraph_mode' in request.form
        paragraph_count = int(request.form.get('paragraph_count', 4))
        
        # Schedule settings
        publishing_days = request.form.getlist('publishing_days')
        publishing_time = request.form.get('publishing_time', '12:00')
        posts_per_day = int(request.form.get('posts_per_day', 1))
        
        # Topic settings
        topic_min_score = float(request.form.get('topic_min_score', 0.7))
        categories = request.form.getlist('categories')
        
        # Advanced settings
        auto_enable_topics = 'auto_enable_topics' in request.form
        auto_promote_content = 'auto_promote_content' in request.form
        
        # Create a new automation rule
        new_rule = AutomationRule(
            name=name,
            blog_id=blog_id,
            content_tone=content_tone,  # Use content_tone instead of writing_style to match database schema
            content_length=content_length,
            use_paragraph_mode=use_paragraph_mode,
            paragraph_count=paragraph_count,
            publishing_time=publishing_time,
            posts_per_day=posts_per_day,
            topic_min_score=topic_min_score,
            auto_enable_topics=auto_enable_topics,
            auto_promote_content=auto_promote_content,
            is_active=True
        )
        
        # Set publishing days as JSON
        new_rule.set_publishing_days(publishing_days)
        
        # Set categories as JSON (if any)
        if categories and categories[0] != '':
            new_rule.set_categories(categories)
        
        db.session.add(new_rule)
        db.session.commit()
        
        flash(f'Automation rule "{name}" created successfully', 'success')
        
    except Exception as e:
        logger.error(f"Error creating automation rule: {str(e)}")
        flash(f'Error creating automation rule: {str(e)}', 'danger')
    
    return redirect(url_for('content_creator.automation_dashboard'))


@content_creator_bp.route('/content-creator/automation/edit/<int:rule_id>', methods=['GET', 'POST'])
def edit_automation_rule(rule_id):
    """Edit an existing automation rule"""
    rule = AutomationRule.query.get_or_404(rule_id)
    
    if request.method == 'POST':
        try:
            # Update rule data
            rule.name = request.form.get('name', rule.name)
            rule.content_tone = request.form.get('writing_style', rule.content_tone)  # Form uses writing_style but db uses content_tone
            rule.content_length = request.form.get('content_length', rule.content_length)
            rule.publishing_time = request.form.get('publishing_time', rule.publishing_time)
            rule.posts_per_day = int(request.form.get('posts_per_day', rule.posts_per_day))
            rule.topic_min_score = float(request.form.get('topic_min_score', rule.topic_min_score))
            rule.auto_enable_topics = 'auto_enable_topics' in request.form
            rule.auto_promote_content = 'auto_promote_content' in request.form
            
            # Paragraph mode settings
            rule.use_paragraph_mode = 'use_paragraph_mode' in request.form
            rule.paragraph_count = int(request.form.get('paragraph_count', 4))
            
            # Update publishing days
            publishing_days = request.form.getlist('publishing_days')
            rule.set_publishing_days(publishing_days)
            
            # Update categories
            categories = request.form.getlist('categories')
            if categories and categories[0] != '':
                rule.set_categories(categories)
            else:
                rule.set_categories([])
            
            db.session.commit()
            flash(f'Automation rule "{rule.name}" updated successfully', 'success')
            return redirect(url_for('content_creator.automation_dashboard'))
            
        except Exception as e:
            logger.error(f"Error updating automation rule: {str(e)}")
            flash(f'Error updating automation rule: {str(e)}', 'danger')
    
    # For GET requests, render the edit form
    blogs = Blog.query.filter_by(active=True).all()
    
    return render_template(
        'content/edit_automation.html',
        rule=rule,
        blogs=blogs,
        title=f"Edit Automation Rule - {rule.name}"
    )


@content_creator_bp.route('/content-creator/automation/toggle/<int:rule_id>', methods=['POST'])
def toggle_automation_rule(rule_id):
    """Toggle an automation rule active status"""
    rule = AutomationRule.query.get_or_404(rule_id)
    
    try:
        active = request.form.get('active', 'false').lower() == 'true'
        rule.is_active = active  # Use is_active to match database schema
        
        db.session.commit()
        
        status = 'activated' if active else 'deactivated'
        flash(f'Automation rule "{rule.name}" {status} successfully', 'success')
        
    except Exception as e:
        logger.error(f"Error toggling automation rule: {str(e)}")
        flash(f'Error toggling automation rule: {str(e)}', 'danger')
    
    return redirect(url_for('content_creator.automation_dashboard'))


@content_creator_bp.route('/content-creator/automation/delete/<int:rule_id>', methods=['POST'])
def delete_automation_rule(rule_id):
    """Delete an automation rule"""
    rule = AutomationRule.query.get_or_404(rule_id)
    
    try:
        rule_name = rule.name
        db.session.delete(rule)
        db.session.commit()
        
        flash(f'Automation rule "{rule_name}" deleted successfully', 'success')
        
    except Exception as e:
        logger.error(f"Error deleting automation rule: {str(e)}")
        flash(f'Error deleting automation rule: {str(e)}', 'danger')
    
    return redirect(url_for('content_creator.automation_dashboard'))


@content_creator_bp.route('/content-creator/automation/run/<int:rule_id>', methods=['POST'])
def run_automation_rule(rule_id):
    """Manually run an automation rule"""
    rule = AutomationRule.query.get_or_404(rule_id)
    
    try:
        # Run the automation rule
        result = content_automation.run_rule(rule.id)
        
        if result.get('success'):
            flash(f'Automation rule "{rule.name}" executed successfully. {result.get("message", "")}', 'success')
        else:
            flash(f'Automation rule execution failed: {result.get("message", "Unknown error")}', 'danger')
        
    except Exception as e:
        logger.error(f"Error running automation rule: {str(e)}")
        flash(f'Error running automation rule: {str(e)}', 'danger')
    
    return redirect(url_for('content_creator.automation_dashboard'))


@content_creator_bp.route('/api/blogs/<int:blog_id>/categories')
def get_blog_categories(blog_id):
    """API endpoint to get categories for a blog"""
    blog = Blog.query.get_or_404(blog_id)
    
    # Get categories from the blog
    categories = blog.get_categories()
    
    return jsonify({
        'success': True,
        'categories': categories
    })

@content_creator_bp.route('/content-creator/api/topics', endpoint='get_all_topics')
def get_all_topics():
    """API endpoint to get approved topics for all blogs or a specific blog"""
    logger.info("API endpoint get_all_topics called")
    blog_id = request.args.get('blog_id')
    
    try:
        query = ArticleTopic.query.filter_by(status='approved')
        logger.info(f"Querying approved topics with blog_id filter: {blog_id}")
        
        # Filter by blog_id if provided
        if blog_id:
            try:
                blog_id = int(blog_id)
                # Verify the blog exists
                blog = Blog.query.get_or_404(blog_id)
                query = query.filter_by(blog_id=blog_id)
            except (ValueError, TypeError):
                return jsonify({'success': False, 'message': 'Invalid blog ID'})
        
        # Get approved topics ordered by score
        topics = query.order_by(desc(ArticleTopic.score)).all()
        
        # Convert to JSON format
        topics_data = []
        for topic in topics:
            # Get blog name
            blog_name = None
            if topic.blog_id:
                blog = Blog.query.get(topic.blog_id)
                if blog:
                    blog_name = blog.name
            
            # Get keywords
            keywords = None
            try:
                keywords = topic.get_keywords()
                if keywords:
                    keywords = ','.join(keywords)
            except:
                keywords = None
            
            topics_data.append({
                'id': topic.id,
                'title': topic.title,
                'score': topic.score,
                'status': topic.status,
                'blog_id': topic.blog_id,
                'blog_name': blog_name,
                'keywords': keywords,
                'created_at': topic.created_at.strftime('%Y-%m-%d') if topic.created_at else None
            })
        
        return jsonify({
            'success': True,
            'topics': topics_data
        })
        
    except Exception as e:
        logger.error(f"Error getting topics: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@content_creator_bp.route('/content-creator/api/blog/<int:blog_id>/topics')
def get_blog_topics(blog_id):
    """API endpoint to get approved topics for a blog"""
    try:
        # Verify the blog exists
        blog = Blog.query.get_or_404(blog_id)
        
        # Get approved topics for this blog
        topics = ArticleTopic.query.filter_by(
            blog_id=blog_id,
            status='approved'
        ).order_by(desc(ArticleTopic.score)).all()
        
        # Convert to JSON format
        topics_data = []
        for topic in topics:
            # Get keywords
            keywords = None
            try:
                keywords = topic.get_keywords()
                if keywords:
                    keywords = ','.join(keywords)
            except:
                keywords = None
                
            topics_data.append({
                'id': topic.id,
                'title': topic.title,
                'score': topic.score,
                'status': topic.status,
                'blog_id': topic.blog_id,
                'blog_name': blog.name,  # We already have the blog object from blog_id
                'keywords': keywords,
                'created_at': topic.created_at.strftime('%Y-%m-%d') if topic.created_at else None
            })
        
        return jsonify({
            'success': True,
            'topics': topics_data
        })
        
    except Exception as e:
        logger.error(f"Error getting blog topics: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


# Note: This endpoint is replaced by /content-creator/api/create-draft-content
# But we're keeping it for backwards compatibility with a redirect
@content_creator_bp.route('/content-creator/api/create-draft', methods=['POST'])
def api_create_draft_content_legacy():
    """Legacy API endpoint for compatibility"""
    return redirect(url_for('content_creator.api_create_draft_content_v2'))


@content_creator_bp.route('/content-creator/api/generate-plan', methods=['POST'])
def generate_article_plan_existing():
    """API endpoint to generate an article plan with paragraph topics (existing endpoint)"""
    try:
        # Get request parameters
        topic = request.form.get('topic')
        paragraph_count = int(request.form.get('paragraph_count', 4))
        style = request.form.get('style', 'informative')
        keywords = request.form.get('keywords', '').split(',') if request.form.get('keywords') else []
        
        # Generate article plan
        # Generate plan without keywords
        plan = content_generator.generate_article_plan(
            topic=topic,
            paragraph_count=paragraph_count,
            style=style
        )
        
        return jsonify({
            'success': True,
            'plan': plan
        })
        
    except Exception as e:
        logger.error(f"Error generating article plan: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@content_creator_bp.route('/content-creator/api/generate-paragraph', methods=['POST'])
def generate_paragraph_existing():
    """API endpoint to generate a single paragraph for dynamic content creation (existing endpoint)"""
    try:
        # Get request parameters
        topic = request.form.get('topic')
        paragraph_topic = request.form.get('paragraph_topic')
        style = request.form.get('style', 'informative')
        paragraph_index = int(request.form.get('paragraph_index', 0))
        total_paragraphs = int(request.form.get('total_paragraphs', 4))
        keywords = request.form.get('keywords', '').split(',') if request.form.get('keywords') else []
        is_introduction = paragraph_index == 0
        is_conclusion = paragraph_index == total_paragraphs - 1
        
        # Generate the paragraph
        if is_introduction:
            paragraph_topic = "Introduction"
        elif is_conclusion:
            paragraph_topic = "Conclusion"
            
        # Generate the paragraph content
        paragraph_content = content_generator._generate_paragraph(
            topic=topic,
            paragraph_topic=paragraph_topic,
            style=style,
            is_introduction=is_introduction,
            is_conclusion=is_conclusion,
            keywords=keywords,
            prev_content_summary=None
        )
        
        return jsonify({
            'success': True,
            'content': paragraph_content,
            'paragraph_index': paragraph_index,
            'total_paragraphs': total_paragraphs,
            'is_introduction': is_introduction,
            'is_conclusion': is_conclusion
        })
        
    except Exception as e:
        logger.error(f"Error generating paragraph: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@content_creator_bp.route('/content-creator/api/dynamic-paragraph-v2', methods=['POST'])
def generate_dynamic_paragraph_v2():
    """Enhanced API endpoint for dynamic paragraph generation with real-time updates"""
    try:
        # Get request parameters
        topic = request.form.get('topic')
        paragraph_topic = request.form.get('paragraph_topic')
        style = request.form.get('style', 'informative')
        paragraph_index = int(request.form.get('paragraph_index', 0))
        total_paragraphs = int(request.form.get('total_paragraphs', 4))
        content_id = request.form.get('content_id')
        
        # Validate required parameters
        if not topic:
            return jsonify({'success': False, 'message': 'Topic is required'})
        
        if not paragraph_topic:
            return jsonify({'success': False, 'message': 'Paragraph topic is required'})
        
        # Log parameters for debugging
        logger.info(f"Generating paragraph: topic={topic}, paragraph_topic={paragraph_topic}, " +
                   f"style={style}, index={paragraph_index}, total={total_paragraphs}")
        
        # Determine if this is introduction or conclusion
        is_introduction = paragraph_index == 0
        is_conclusion = paragraph_index == total_paragraphs - 1
        
        # Override title if needed
        if is_introduction:
            paragraph_topic = "Introduction"
        elif is_conclusion:
            paragraph_topic = "Conclusion"
        
        # Get content log if content_id is provided
        content_log = None
        if content_id:
            content_log = ContentLog.query.get(content_id)
            if not content_log:
                logger.warning(f"Content log with ID {content_id} not found")
        
        # Generate the paragraph with improved error handling
        try:
            # Add additional logging for debugging
            logger.info(f"Calling content generator for paragraph {paragraph_index+1}/{total_paragraphs}")
            
            # Generate the paragraph
            paragraph_content = content_generator._generate_paragraph(
                topic=topic,
                paragraph_topic=paragraph_topic,
                style=style,
                is_introduction=is_introduction,
                is_conclusion=is_conclusion,
                keywords=[],  # No keywords for dynamic generation to reduce complexity
                prev_content_summary=None
            )
            
            logger.info(f"Successfully generated paragraph {paragraph_index+1}/{total_paragraphs}")
            
            # Update the content log if provided
            if content_log:
                try:
                    # Load existing content data or create new
                    content_data = {}
                    if content_log.error_message:
                        try:
                            content_data = json.loads(content_log.error_message)
                        except json.JSONDecodeError:
                            logger.warning("Could not parse existing content data, creating new")
                            content_data = {'content': '', 'paragraphs': {}}
                    else:
                        content_data = {'content': '', 'paragraphs': {}}
                    
                    # Update the paragraph data
                    paragraphs = content_data.get('paragraphs', {})
                    paragraphs[str(paragraph_index)] = paragraph_content
                    content_data['paragraphs'] = paragraphs
                    
                    # Rebuild the full content
                    full_content = []
                    for i in range(total_paragraphs):
                        if str(i) in paragraphs:
                            full_content.append(paragraphs[str(i)])
                    
                    content_data['content'] = '<p>' + '</p><p>'.join(full_content) + '</p>'
                    
                    # Save back to content log
                    content_log.error_message = json.dumps(content_data)
                    db.session.commit()
                    logger.info(f"Updated content log {content_id} with new paragraph {paragraph_index+1}")
                except Exception as e:
                    logger.error(f"Error updating content log: {str(e)}")
            
            return jsonify({
                'success': True,
                'content': paragraph_content,
                'paragraph_index': paragraph_index,
                'total_paragraphs': total_paragraphs,
                'is_introduction': is_introduction,
                'is_conclusion': is_conclusion
            })
            
        except Exception as inner_e:
            logger.error(f"Inner paragraph generation error: {str(inner_e)}")
            raise inner_e
        
    except Exception as e:
        logger.error(f"Error generating dynamic paragraph: {str(e)}")
        # Return more detailed error information for debugging
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Error details: {error_details}")
        return jsonify({
            'success': False, 
            'message': f'Error generating paragraph: {str(e)}',
            'details': error_details
        })