import os
import json
import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from app import db
from models import Blog, ContentLog, ImageLibrary
from werkzeug.utils import secure_filename
from datetime import datetime
from PIL import Image
import requests
from io import BytesIO
import base64
import uuid

# Setup logging
logger = logging.getLogger(__name__)

# Create blueprint
images_bp = Blueprint('images', __name__, url_prefix='/images')

# Import utility functions
from utils.images.unsplash import search_unsplash_images
from utils.images.finder import search_images, get_image_details

@images_bp.route('/')
def index():
    """Images dashboard"""
    return redirect(url_for('images.image_library'))

@images_bp.route('/search')
def search_images():
    """Search for images from various sources"""
    query = request.args.get('query', '')
    source = request.args.get('source', 'unsplash')
    orientation = request.args.get('orientation', None)
    
    images = []
    error = None
    sources = ['unsplash', 'google', 'all']
    
    if query:
        try:
            # Search for images
            images = search_images(
                query=query,
                source=source,
                orientation=orientation
            )
        except Exception as e:
            logger.error(f"Error searching images: {str(e)}")
            error = f"Error searching images: {str(e)}"
    
    return render_template(
        'images/search.html',
        images=images,
        query=query,
        selected_source=source,
        sources=sources,
        error=error
    )

@images_bp.route('/library')
def image_library():
    """View image library"""
    selected_blog_id = request.args.get('blog_id', '')
    
    # Get all blogs for filter
    blogs = Blog.query.all()
    
    # Build query
    query = ImageLibrary.query
    
    # Filter by blog if selected
    if selected_blog_id:
        query = query.filter_by(blog_id=int(selected_blog_id))
    
    # Get images
    images = query.order_by(ImageLibrary.created_at.desc()).all()
    
    return render_template(
        'images/library.html',
        images=images,
        blogs=blogs,
        selected_blog_id=selected_blog_id
    )

@images_bp.route('/library/add', methods=['GET', 'POST'])
def add_to_library():
    """Add image to library"""
    if request.method == 'POST':
        try:
            # Handle image source (search, upload)
            source_type = request.form.get('source_type', 'search')
            
            if source_type == 'search':
                # Get image data from form
                image_data = json.loads(request.form.get('image_data', '{}'))
                
                # Get blog ID - if not provided, use the first blog
                blog_id = request.form.get('blog_id')
                if not blog_id:
                    blog = Blog.query.first()
                    if blog:
                        blog_id = blog.id
                    else:
                        flash('No blogs available. Please add a blog first.', 'danger')
                        return redirect(url_for('images.add_to_library'))
                
                # Create image library entry
                image = ImageLibrary(
                    blog_id=blog_id,
                    title=request.form.get('title', image_data.get('description', 'Unnamed Image')),
                    url=image_data.get('url', ''),
                    thumbnail_url=image_data.get('thumb_url', ''),
                    width=image_data.get('width'),
                    height=image_data.get('height'),
                    source=image_data.get('source', 'unknown'),
                    source_id=image_data.get('id'),
                    attribution=image_data.get('attribution_text', ''),
                    attribution_url=image_data.get('attribution_url', '')
                )
                
                # Set tags if provided
                tags = request.form.get('tags', '')
                if tags:
                    image.set_tags([tag.strip() for tag in tags.split(',')])
                
                db.session.add(image)
                db.session.commit()
                
                flash('Image added to library successfully', 'success')
                return redirect(url_for('images.image_library'))
                
            elif source_type == 'upload':
                # Check if file was uploaded
                if 'image_file' not in request.files:
                    flash('No file uploaded', 'danger')
                    return redirect(url_for('images.add_to_library'))
                
                image_file = request.files['image_file']
                if not image_file.filename:
                    flash('No file selected', 'danger')
                    return redirect(url_for('images.add_to_library'))
                
                # Get blog ID
                blog_id = request.form.get('blog_id')
                if not blog_id:
                    flash('Please select a blog', 'danger')
                    return redirect(url_for('images.add_to_library'))
                
                # Process the uploaded image
                try:
                    # Read image
                    img = Image.open(image_file)
                    width, height = img.size
                    
                    # Generate a unique filename
                    filename = secure_filename(image_file.filename)
                    unique_id = str(uuid.uuid4())
                    filename = f"{unique_id}_{filename}"
                    
                    # TODO: Implement proper storage for uploaded images
                    # For now, we'll just get the raw data and save as URL
                    image_file.seek(0)
                    img_data = image_file.read()
                    img_base64 = base64.b64encode(img_data).decode('utf-8')
                    data_url = f"data:image/jpeg;base64,{img_base64}"
                    
                    # Create image library entry
                    image = ImageLibrary(
                        blog_id=blog_id,
                        title=request.form.get('title', 'Uploaded Image'),
                        url=data_url,
                        thumbnail_url=data_url,  # Using same URL for thumbnail for now
                        width=width,
                        height=height,
                        source='upload',
                        source_id=unique_id
                    )
                    
                    # Set tags if provided
                    tags = request.form.get('tags', '')
                    if tags:
                        image.set_tags([tag.strip() for tag in tags.split(',')])
                    
                    db.session.add(image)
                    db.session.commit()
                    
                    flash('Image uploaded and added to library successfully', 'success')
                    return redirect(url_for('images.image_library'))
                
                except Exception as e:
                    logger.error(f"Error processing uploaded image: {str(e)}")
                    flash(f'Error processing uploaded image: {str(e)}', 'danger')
                    return redirect(url_for('images.add_to_library'))
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding image to library: {str(e)}")
            flash(f'Error adding image to library: {str(e)}', 'danger')
            return redirect(url_for('images.add_to_library'))
    
    # GET request - show form
    blogs = Blog.query.all()
    return render_template('images/add_to_library.html', blogs=blogs)

@images_bp.route('/library/delete/<int:image_id>', methods=['POST'])
def delete_from_library(image_id):
    """Delete image from library"""
    image = ImageLibrary.query.get_or_404(image_id)
    
    try:
        db.session.delete(image)
        db.session.commit()
        
        flash('Image deleted from library successfully', 'success')
        return redirect(url_for('images.image_library'))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting image from library: {str(e)}")
        flash(f'Error deleting image: {str(e)}', 'danger')
        return redirect(url_for('images.image_library'))

@images_bp.route('/article/<int:content_id>')
def preview_article_image(content_id):
    """Preview article image"""
    content = ContentLog.query.get_or_404(content_id)
    
    # Get image data from content if available
    image = None
    if content.featured_image_data:
        try:
            image = json.loads(content.featured_image_data)
        except:
            image = None
    
    return render_template('images/preview.html', content=content, image=image)

@images_bp.route('/article/<int:content_id>/change', methods=['GET', 'POST'])
def change_article_image(content_id):
    """Change article image"""
    content = ContentLog.query.get_or_404(content_id)
    
    if request.method == 'POST':
        try:
            image_type = request.form.get('image_type', 'search')
            
            if image_type == 'search':
                # Get image data from form
                image_data = json.loads(request.form.get('image_data', '{}'))
                
                # Save to content
                content.featured_image_data = json.dumps(image_data)
                
                # Add to library if requested
                if request.form.get('add_to_library', '') == 'yes':
                    # Create image library entry
                    image = ImageLibrary(
                        blog_id=content.blog_id,
                        title=request.form.get('title', image_data.get('description', 'Unnamed Image')),
                        url=image_data.get('url', ''),
                        thumbnail_url=image_data.get('thumb_url', ''),
                        width=image_data.get('width'),
                        height=image_data.get('height'),
                        source=image_data.get('source', 'unknown'),
                        source_id=image_data.get('id'),
                        attribution=image_data.get('attribution_text', ''),
                        attribution_url=image_data.get('attribution_url', '')
                    )
                    
                    # Set tags if provided
                    tags = request.form.get('tags', '')
                    if tags:
                        image.set_tags([tag.strip() for tag in tags.split(',')])
                    
                    db.session.add(image)
            
            elif image_type == 'library':
                # Get image from library
                image_id = request.form.get('image_id')
                if not image_id:
                    flash('No image selected', 'danger')
                    return redirect(url_for('images.change_article_image', content_id=content_id))
                
                image = ImageLibrary.query.get_or_404(image_id)
                
                # Convert to dictionary for storage
                image_data = {
                    'url': image.url,
                    'thumb_url': image.thumbnail_url,
                    'width': image.width,
                    'height': image.height,
                    'source': image.source,
                    'source_id': image.source_id,
                    'attribution_text': image.attribution,
                    'attribution_url': image.attribution_url,
                    'description': image.title
                }
                
                # Save to content
                content.featured_image_data = json.dumps(image_data)
                
            elif image_type == 'upload':
                # Check if file was uploaded
                if 'image_file' not in request.files:
                    flash('No file uploaded', 'danger')
                    return redirect(url_for('images.change_article_image', content_id=content_id))
                
                image_file = request.files['image_file']
                if not image_file.filename:
                    flash('No file selected', 'danger')
                    return redirect(url_for('images.change_article_image', content_id=content_id))
                
                # Process the uploaded image
                try:
                    # Read image
                    img = Image.open(image_file)
                    width, height = img.size
                    
                    # Generate a unique filename
                    filename = secure_filename(image_file.filename)
                    unique_id = str(uuid.uuid4())
                    filename = f"{unique_id}_{filename}"
                    
                    # TODO: Implement proper storage for uploaded images
                    # For now, we'll just get the raw data and save as URL
                    image_file.seek(0)
                    img_data = image_file.read()
                    img_base64 = base64.b64encode(img_data).decode('utf-8')
                    data_url = f"data:image/jpeg;base64,{img_base64}"
                    
                    # Create image data
                    image_data = {
                        'url': data_url,
                        'thumb_url': data_url,
                        'width': width,
                        'height': height,
                        'source': 'upload',
                        'source_id': unique_id,
                        'description': request.form.get('title', 'Uploaded Image')
                    }
                    
                    # Save to content
                    content.featured_image_data = json.dumps(image_data)
                    
                    # Add to library if requested
                    if request.form.get('add_to_library', 'off') == 'on':
                        # Create image library entry
                        image = ImageLibrary(
                            blog_id=content.blog_id,
                            title=request.form.get('title', 'Uploaded Image'),
                            url=data_url,
                            thumbnail_url=data_url,
                            width=width,
                            height=height,
                            source='upload',
                            source_id=unique_id
                        )
                        
                        # Set tags if provided
                        tags = request.form.get('tags', '')
                        if tags:
                            image.set_tags([tag.strip() for tag in tags.split(',')])
                        
                        db.session.add(image)
                
                except Exception as e:
                    logger.error(f"Error processing uploaded image: {str(e)}")
                    flash(f'Error processing uploaded image: {str(e)}', 'danger')
                    return redirect(url_for('images.change_article_image', content_id=content_id))
            
            db.session.commit()
            
            flash('Article image updated successfully', 'success')
            return redirect(url_for('images.preview_article_image', content_id=content_id))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error changing article image: {str(e)}")
            flash(f'Error changing article image: {str(e)}', 'danger')
            return redirect(url_for('images.change_article_image', content_id=content_id))
    
    # GET request - show form
    # Get images from library for this blog
    library_images = ImageLibrary.query.filter_by(blog_id=content.blog_id).order_by(ImageLibrary.created_at.desc()).all()
    
    return render_template('images/change.html', content=content, library_images=library_images)

def register_image_routes(app):
    app.register_blueprint(images_bp)