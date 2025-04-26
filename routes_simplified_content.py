"""
Routes for Simplified Content Generator

This module provides a simplified interface for generating content with long paragraphs.
"""

import logging
import traceback
from flask import Blueprint, jsonify, request, render_template, flash, redirect, url_for, session
from models import Article, Blog, db
from utils.content.ai_adapter import get_default_ai_service
from utils.content.long_paragraph_generator import generate_long_paragraph_content
from utils.images.google import search_google_images
from utils.images.unsplash import search_unsplash_images
from utils.images.auto_image_finder import prepare_image_metadata, find_and_associate_images

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
simplified_content_bp = Blueprint("simplified_content", __name__)

@simplified_content_bp.route("/simplified_content", methods=["GET"])
def simplified_content_page():
    """Render the simplified content generation page"""
    blogs = Blog.query.all()
    return render_template(
        "simplified_content.html", 
        blogs=blogs,
        page_title="Generator Treści z Długimi Akapitami"
    )

@simplified_content_bp.route("/api/generate_simplified_content", methods=["POST"])
def generate_simplified_content():
    """Generate content with long paragraphs"""
    try:
        # Get parameters from request
        data = request.json
        topic = data.get("topic")
        num_paragraphs = int(data.get("num_paragraphs", 4))
        
        if not topic:
            return jsonify({"success": False, "error": "Temat jest wymagany"}), 400
        
        # Get the AI service
        try:
            ai_service = get_default_ai_service()
        except Exception as e:
            logger.error(f"Error getting AI service: {str(e)}")
            return jsonify({
                "success": False, 
                "error": f"Błąd konfiguracji usługi AI: {str(e)}"
            }), 500
        
        # Generate content
        logger.info(f"Generating content with long paragraphs on topic: {topic}")
        result = generate_long_paragraph_content(
            topic=topic,
            num_paragraphs=num_paragraphs,
            ai_service=ai_service
        )
        
        # Return the result
        return jsonify({
            "success": True,
            "content": result["content"],
            "metrics": result["metrics"],
            "report": result["report"]
        })
        
    except Exception as e:
        logger.error(f"Error generating content: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": f"Błąd generowania treści: {str(e)}"
        }), 500

from utils.images.auto_image_finder import find_and_associate_images

@simplified_content_bp.route("/api/save_simplified_content", methods=["POST"])
def save_simplified_content():
    """Save generated content to the database"""
    try:
        # Get parameters from request
        data = request.json
        title = data.get("title")
        content = data.get("content")
        blog_id = data.get("blog_id")
        auto_find_images = data.get("auto_find_images", True)  # Default to true
        
        if not title or not content:
            return jsonify({
                "success": False, 
                "error": "Tytuł i treść są wymagane"
            }), 400
        
        if not blog_id:
            return jsonify({
                "success": False, 
                "error": "ID bloga jest wymagane"
            }), 400
        
        # Save the article
        article = Article(
            title=title,
            content=content,
            blog_id=blog_id,
            status="draft"
        )
        db.session.add(article)
        db.session.commit()
        
        # Find and associate images if requested
        images_found = []
        if auto_find_images:
            try:
                logger.info(f"Finding images for article: {article.title}")
                success, images_found = find_and_associate_images(
                    article=article,
                    num_images=3,  # Find 3 images, but only first will be set as featured
                    prefer_source='google',  # Changed to Google as primary source
                    save_to_library=True
                )
                
                if success:
                    logger.info(f"Successfully found and associated {len(images_found)} images with article {article.id}")
                else:
                    logger.warning(f"Failed to find images for article {article.id}")
            except Exception as img_err:
                logger.error(f"Error finding images for article {article.id}: {str(img_err)}")
                # This shouldn't fail the whole save operation
        
        # Return success
        return jsonify({
            "success": True,
            "article_id": article.id,
            "message": "Artykuł został zapisany jako szkic",
            "images": images_found
        })
        
    except Exception as e:
        logger.error(f"Error saving content: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": f"Błąd zapisywania treści: {str(e)}"
        }), 500
        
@simplified_content_bp.route("/api/find_images", methods=["POST"])
def find_images_api():
    """Find images for a given query using Google Images API"""
    try:
        # Get parameters from request
        data = request.json
        query = data.get("query")
        count = int(data.get("count", 4))
        
        if not query:
            return jsonify({"success": False, "error": "Zapytanie jest wymagane"}), 400
        
        # First try Google Images (preferred source)
        try:
            logger.info(f"Searching for images via Google for query: {query}")
            google_images = search_google_images(query, count)
            
            if google_images and len(google_images) > 0:
                # Process images to return standardized format
                processed_images = []
                for img in google_images:
                    processed = prepare_image_metadata(
                        url=img.get("link", ""),
                        thumbnail_url=img.get("image", {}).get("thumbnailLink", ""),
                        source="Google Images",
                        title=img.get("title", ""),
                        attribution=img.get("displayLink", "")
                    )
                    processed_images.append(processed)
                
                return jsonify({
                    "success": True,
                    "images": processed_images,
                    "source": "google"
                })
        except Exception as google_err:
            logger.error(f"Error searching Google Images: {str(google_err)}")
            # Continue to fallback source
            
        # If Google fails or returns no results, try Unsplash as fallback
        try:
            logger.info(f"Falling back to Unsplash for query: {query}")
            unsplash_images = search_unsplash_images(query, count)
            
            if unsplash_images and len(unsplash_images) > 0:
                # Process images to return standardized format
                processed_images = []
                for img in unsplash_images:
                    processed = prepare_image_metadata(
                        url=img.get("urls", {}).get("regular", ""),
                        thumbnail_url=img.get("urls", {}).get("small", ""),
                        source="Unsplash",
                        title=img.get("description", "Image from Unsplash"),
                        attribution=f"Photo by {img.get('user', {}).get('name', 'Unknown')} on Unsplash"
                    )
                    processed_images.append(processed)
                
                return jsonify({
                    "success": True,
                    "images": processed_images,
                    "source": "unsplash"
                })
        except Exception as unsplash_err:
            logger.error(f"Error searching Unsplash: {str(unsplash_err)}")
        
        # If both methods fail or return no results
        return jsonify({
            "success": False,
            "error": "Nie znaleziono pasujących obrazów",
            "images": []
        })
        
    except Exception as e:
        logger.error(f"Error finding images: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": f"Błąd wyszukiwania obrazów: {str(e)}",
            "images": []
        }), 500