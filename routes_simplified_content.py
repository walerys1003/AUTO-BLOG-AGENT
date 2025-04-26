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

@simplified_content_bp.route("/api/save_simplified_content", methods=["POST"])
def save_simplified_content():
    """Save generated content to the database"""
    try:
        # Get parameters from request
        data = request.json
        title = data.get("title")
        content = data.get("content")
        blog_id = data.get("blog_id")
        
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
        
        # Return success
        return jsonify({
            "success": True,
            "article_id": article.id,
            "message": "Artykuł został zapisany jako szkic"
        })
        
    except Exception as e:
        logger.error(f"Error saving content: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": f"Błąd zapisywania treści: {str(e)}"
        }), 500