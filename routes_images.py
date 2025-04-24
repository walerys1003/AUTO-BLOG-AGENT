"""
Image Management Routes

This module handles the routes for image management.
"""
import os
import json
from flask import Blueprint, request, jsonify, render_template, current_app, flash, redirect, url_for
from sqlalchemy import desc
from werkzeug.utils import secure_filename

from app import db
from models import Blog, ContentLog, ImageLibrary
from utils.images import finder, unsplash

# Create blueprint
images_bp = Blueprint('images', __name__)

# Constants
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
UPLOAD_FOLDER = 'static/uploads/images'

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@images_bp.route('/images/search', methods=['GET', 'POST'])
def search_images():
    """Search for images from external sources"""
    # Default parameters
    query = request.args.get('query', '') or request.form.get('query', '')
    count = int(request.args.get('count', 10)) or int(request.form.get('count', 10))
    source = request.args.get('source', 'unsplash') or request.form.get('source', 'unsplash')
    orientation = request.args.get('orientation') or request.form.get('orientation')
    
    if not query:
        # No query provided, return empty results
        if request.method == 'POST':
            return jsonify({'success': False, 'message': 'No search query provided', 'images': []})
        return render_template('images/search.html', images=[], query='', sources=['unsplash', 'google', 'all'])
    
    # Search for images
    try:
        images = finder.find_images_for_topic(
            topic=query,
            count=count,
            source=source,
            orientation=orientation
        )
        
        # Return the results
        if request.method == 'POST':
            return jsonify({'success': True, 'images': images})
        
        return render_template(
            'images/search.html', 
            images=images, 
            query=query,
            sources=['unsplash', 'google', 'all'],
            selected_source=source
        )
        
    except Exception as e:
        if request.method == 'POST':
            return jsonify({'success': False, 'message': str(e), 'images': []})
        
        flash(f"Error searching for images: {str(e)}", 'danger')
        return render_template('images/search.html', images=[], query=query, error=str(e))


@images_bp.route('/images/preview/<content_id>', methods=['GET'])
def preview_article_image(content_id):
    """Preview the featured image for an article"""
    try:
        # Get the content log
        content = ContentLog.query.get_or_404(content_id)
        
        # Get the featured image data
        image_data = content.get_featured_image()
        
        if not image_data:
            flash("No featured image found for this article", "warning")
            return render_template('images/preview.html', content=content, image=None)
        
        return render_template('images/preview.html', content=content, image=image_data)
        
    except Exception as e:
        flash(f"Error previewing image: {str(e)}", "danger")
        return redirect(url_for('content.dashboard'))


@images_bp.route('/images/change/<content_id>', methods=['GET', 'POST'])
def change_article_image(content_id):
    """Change the featured image for an article"""
    try:
        # Get the content log
        content = ContentLog.query.get_or_404(content_id)
        
        if request.method == 'POST':
            # Handle image selection or upload
            image_type = request.form.get('image_type', 'search')
            
            if image_type == 'search':
                # Handle image from search
                image_data = json.loads(request.form.get('image_data', '{}'))
                
                if not image_data:
                    flash("No image selected", "warning")
                    return redirect(request.url)
                
                # Update the content log
                content.set_featured_image(image_data)
                db.session.commit()
                
                flash("Featured image updated successfully", "success")
                return redirect(url_for('images.preview_article_image', content_id=content.id))
                
            elif image_type == 'upload':
                # Handle image upload
                if 'image_file' not in request.files:
                    flash("No file part", "warning")
                    return redirect(request.url)
                
                file = request.files['image_file']
                
                if file.filename == '':
                    flash("No selected file", "warning")
                    return redirect(request.url)
                
                if file and allowed_file(file.filename):
                    # Save the file
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(UPLOAD_FOLDER, filename)
                    file.save(filepath)
                    
                    # Create image data
                    image_data = {
                        'url': f"/{filepath}",
                        'source': 'upload',
                        'attribution_text': 'Uploaded by user',
                        'width': None,
                        'height': None
                    }
                    
                    # Update the content log
                    content.set_featured_image(image_data)
                    db.session.commit()
                    
                    flash("Featured image uploaded successfully", "success")
                    return redirect(url_for('images.preview_article_image', content_id=content.id))
                    
                else:
                    flash(f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}", "danger")
                    return redirect(request.url)
            
            elif image_type == 'library':
                # Handle image from library
                image_id = request.form.get('image_id')
                
                if not image_id:
                    flash("No image selected", "warning")
                    return redirect(request.url)
                
                # Get the image from the library
                image = ImageLibrary.query.get_or_404(image_id)
                
                # Create image data
                image_data = {
                    'url': image.url,
                    'source': image.source,
                    'attribution_text': image.attribution,
                    'attribution_url': image.attribution_url,
                    'width': image.width,
                    'height': image.height
                }
                
                # Update the content log
                content.set_featured_image(image_data)
                db.session.commit()
                
                flash("Featured image updated successfully", "success")
                return redirect(url_for('images.preview_article_image', content_id=content.id))
                
        # GET request - show the change image form
        # Get images from the library for this blog
        library_images = ImageLibrary.query.filter_by(blog_id=content.blog_id).order_by(desc(ImageLibrary.created_at)).limit(20).all()
        
        return render_template(
            'images/change.html', 
            content=content, 
            library_images=library_images
        )
        
    except Exception as e:
        flash(f"Error changing image: {str(e)}", "danger")
        return redirect(url_for('content.dashboard'))


@images_bp.route('/images/library', methods=['GET'])
def image_library():
    """Show the image library"""
    # Get the blog ID filter if provided
    blog_id = request.args.get('blog_id', None)
    
    try:
        # Get all blogs for the filter dropdown
        blogs = Blog.query.filter_by(active=True).all()
        
        # Query images
        query = ImageLibrary.query
        
        if blog_id:
            query = query.filter_by(blog_id=blog_id)
            
        # Get the images
        images = query.order_by(desc(ImageLibrary.created_at)).all()
        
        return render_template('images/library.html', images=images, blogs=blogs, selected_blog_id=blog_id)
        
    except Exception as e:
        flash(f"Error loading image library: {str(e)}", "danger")
        return redirect(url_for('dashboard.index'))


@images_bp.route('/images/library/add', methods=['GET', 'POST'])
def add_to_library():
    """Add an image to the library"""
    if request.method == 'POST':
        # Get form data
        blog_id = request.form.get('blog_id')
        
        if not blog_id:
            flash("Blog ID is required", "danger")
            return redirect(request.url)
        
        # Check if blog exists
        blog = Blog.query.get_or_404(blog_id)
        
        # Handle the image source
        source_type = request.form.get('source_type', 'search')
        
        if source_type == 'search':
            # Handle image from search
            image_data = json.loads(request.form.get('image_data', '{}'))
            
            if not image_data:
                flash("No image selected", "warning")
                return redirect(request.url)
            
            # Create a new library image
            image = ImageLibrary(
                blog_id=blog_id,
                title=request.form.get('title'),
                url=image_data.get('url'),
                thumbnail_url=image_data.get('thumb_url'),
                width=image_data.get('width'),
                height=image_data.get('height'),
                source=image_data.get('source'),
                source_id=image_data.get('id'),
                attribution=image_data.get('attribution_text'),
                attribution_url=image_data.get('attribution_url')
            )
            
            # Set tags if provided
            tags = request.form.get('tags', '')
            if tags:
                image.set_tags([tag.strip() for tag in tags.split(',')])
            
            db.session.add(image)
            db.session.commit()
            
            flash("Image added to library successfully", "success")
            return redirect(url_for('images.image_library'))
            
        elif source_type == 'upload':
            # Handle image upload
            if 'image_file' not in request.files:
                flash("No file part", "warning")
                return redirect(request.url)
            
            file = request.files['image_file']
            
            if file.filename == '':
                flash("No selected file", "warning")
                return redirect(request.url)
            
            if file and allowed_file(file.filename):
                # Save the file
                filename = secure_filename(file.filename)
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)
                
                # Create a new library image
                image = ImageLibrary(
                    blog_id=blog_id,
                    title=request.form.get('title'),
                    url=f"/{filepath}",
                    thumbnail_url=f"/{filepath}",
                    source='upload',
                    attribution='Uploaded by user'
                )
                
                # Set tags if provided
                tags = request.form.get('tags', '')
                if tags:
                    image.set_tags([tag.strip() for tag in tags.split(',')])
                
                db.session.add(image)
                db.session.commit()
                
                flash("Image uploaded to library successfully", "success")
                return redirect(url_for('images.image_library'))
                
            else:
                flash(f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}", "danger")
                return redirect(request.url)
    
    # GET request - show the add form
    # Get all blogs for the dropdown
    blogs = Blog.query.filter_by(active=True).all()
    
    return render_template('images/add_to_library.html', blogs=blogs)


@images_bp.route('/images/library/delete/<image_id>', methods=['POST'])
def delete_from_library(image_id):
    """Delete an image from the library"""
    try:
        # Get the image
        image = ImageLibrary.query.get_or_404(image_id)
        
        # Delete the image
        db.session.delete(image)
        db.session.commit()
        
        flash("Image deleted from library successfully", "success")
        
    except Exception as e:
        flash(f"Error deleting image: {str(e)}", "danger")
    
    return redirect(url_for('images.image_library'))


def register_routes(app):
    """Register the image routes with the Flask app"""
    app.register_blueprint(images_bp)