"""
Simple Content Creator Routes Module - Uproszczona wersja generatora treści
"""
import json
import logging
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash
from sqlalchemy import desc
from models import ContentLog, Blog, db
from utils.writing import content_generator
from utils.openrouter import openrouter
from config import Config as config

# Utwórz logger
logger = logging.getLogger(__name__)

# Utwórz Blueprint
simple_creator_bp = Blueprint('simple_creator', __name__)

@simple_creator_bp.route('/simple-editor', methods=['GET'])
def simple_editor():
    """Simple editor page"""
    blogs = Blog.query.filter_by(active=True).all()
    return render_template('content/simple_editor.html', blogs=blogs)

@simple_creator_bp.route('/api/simple-generate', methods=['POST'])
def generate_simple_content():
    """Generate simple content API endpoint"""
    # Logowanie informacji
    logger.info("Simple content generation API called")
    
    # Pobierz temat z formularza
    topic = request.form.get('topic', '')
    
    # Logowanie parametrów wejściowych
    logger.info(f"Generating content for topic: {topic}")
    
    # Walidacja danych wejściowych
    if not topic:
        logger.warning("No topic provided")
        return jsonify({
            'success': False,
            'message': 'No topic provided'
        })
    
    try:
        # Wywołaj funkcję generowania treści
        content = generate_simple_article(topic)
        
        if not content:
            logger.error("Failed to generate content")
            return jsonify({
                'success': False,
                'message': 'Failed to generate content, please try again'
            })
        
        # Zwróć wygenerowaną treść
        return jsonify({
            'success': True,
            'content': content
        })
    
    except Exception as e:
        # Logowanie błędu
        logger.error(f"Error generating content: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Zwróć informację o błędzie
        return jsonify({
            'success': False,
            'message': f'Error generating content: {str(e)}'
        })

@simple_creator_bp.route('/api/simple-save', methods=['POST'])
def save_simple_content():
    """Save simple content API endpoint"""
    try:
        # Pobierz dane z formularza
        title = request.form.get('title', '')
        content = request.form.get('content', '')
        status = request.form.get('status', 'draft')
        content_id = request.form.get('content_id', '')
        
        # Walidacja danych wejściowych
        if not title:
            return jsonify({
                'success': False,
                'message': 'Title is required'
            })
        
        # Pobierz bloga (używam pierwszego dostępnego)
        blog = Blog.query.filter_by(active=True).first()
        
        if not blog:
            return jsonify({
                'success': False,
                'message': 'No active blog found'
            })
        
        # Przygotuj dane
        content_data = {
            'content': content,
            'meta_description': '',
            'excerpt': '',
            'tags': []
        }
        
        # Aktualizuj istniejący wpis lub utwórz nowy
        if content_id:
            content_log = ContentLog.query.get(content_id)
            if not content_log:
                return jsonify({
                    'success': False,
                    'message': f'Content with ID {content_id} not found'
                })
        else:
            content_log = ContentLog(blog_id=blog.id)
        
        # Aktualizuj dane
        content_log.title = title
        content_log.status = status
        content_log.error_message = json.dumps(content_data)
        
        # Zapisz do bazy danych
        db.session.add(content_log)
        db.session.commit()
        
        # Zwróć ID zapisanej treści
        return jsonify({
            'success': True,
            'content_id': content_log.id,
            'message': 'Content saved successfully'
        })
    
    except Exception as e:
        # Logowanie błędu
        logger.error(f"Error saving content: {str(e)}")
        
        # Zwróć informację o błędzie
        return jsonify({
            'success': False,
            'message': f'Error saving content: {str(e)}'
        })

@simple_creator_bp.route('/api/simple-content/<int:content_id>', methods=['GET'])
def get_content(content_id):
    """Get content by ID API endpoint"""
    try:
        # Pobierz wpis z bazy danych
        content_log = ContentLog.query.get_or_404(content_id)
        
        # Przygotuj dane do zwrócenia
        content_data = {}
        if content_log.error_message:
            try:
                content_data = json.loads(content_log.error_message)
            except json.JSONDecodeError:
                content_data = {}
        
        return jsonify({
            'success': True,
            'title': content_log.title,
            'content': content_data.get('content', ''),
            'status': content_log.status
        })
    
    except Exception as e:
        # Logowanie błędu
        logger.error(f"Error getting content: {str(e)}")
        
        # Zwróć informację o błędzie
        return jsonify({
            'success': False,
            'message': f'Error getting content: {str(e)}'
        })

def generate_simple_article(topic):
    """
    Generuje prosty artykuł na podstawie tematu.
    
    Args:
        topic (str): Temat artykułu
        
    Returns:
        str: Wygenerowana treść artykułu w formacie HTML
    """
    logger.info(f"Generating simple article for topic: {topic}")
    
    # Sprawdź, czy mamy dostęp do OpenRouter
    model = config.DEFAULT_CONTENT_MODEL or "anthropic/claude-3.5-sonnet"
    logger.info(f"Using model: {model}")
    
    # Utwórz prosty prompt dla generowania treści
    system_prompt = """You are an expert content writer creating high-quality blog articles.
Your task is to write a complete, well-structured article on the given topic.
The article should include:
1. An engaging introduction
2. Several well-organized main sections with appropriate headers
3. A concise conclusion

Format the article in clean HTML with appropriate h2 tags for main sections.
Keep paragraphs concise and focused.
Write in a professional but accessible style.
The output should be ONLY the HTML content of the article, nothing else."""

    user_prompt = f"""Write a comprehensive blog article about the following topic:
    
Topic: {topic}

Create a complete article with proper HTML formatting using h2 tags for section headers and p tags for paragraphs.
Make sure the article is informative, well-structured, and engaging.
The length should be around 800-1200 words.
"""

    try:
        # Wywołaj OpenRouter API
        response_obj = openrouter.generate_completion(
            prompt=user_prompt,
            model=model,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=4000
        )
        
        # Wyciągnij treść z odpowiedzi
        content = ""
        if response_obj and "choices" in response_obj and len(response_obj["choices"]) > 0:
            content = response_obj["choices"][0].get("message", {}).get("content", "")
        
        if not content:
            logger.error("Failed to get content from OpenRouter")
            return None
        
        # Upewnij się, że treść jest poprawnym HTML
        if not content.strip().startswith("<"):
            content = f"<p>{content}</p>"
        
        return content
        
    except Exception as e:
        logger.error(f"Error generating simple article: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None