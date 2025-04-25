"""
Simple Content Creator Routes Module - Uproszczona wersja generatora treści
Zgodnie z zasadą: "Minimalizm to nie brak. To perfekcyjna ilość."
"""
import logging
from flask import Blueprint, render_template, request, jsonify
from models import Blog
from utils.content.generate_content import generate_simple_article
from utils.content.save_content import save_simple_content
from utils.content.get_content import get_simple_content

# Utwórz logger - jedno źródło logowania
logger = logging.getLogger(__name__)

# Utwórz Blueprint - prosty, jednoznaczny punkt wejścia
simple_creator_bp = Blueprint('simple_creator', __name__)

@simple_creator_bp.route('/simple-editor', methods=['GET'])
def simple_editor():
    """Simple editor page - minimalistyczne API"""
    blogs = Blog.query.filter_by(active=True).all()
    return render_template('content/simple_editor.html', blogs=blogs)

@simple_creator_bp.route('/api/simple-generate', methods=['POST'])
def generate_simple_content():
    """Generate simple content API endpoint - jeden cel"""
    # Pobierz temat z formularza - prosty przepływ danych
    topic = request.form.get('topic', '')
    logger.info(f"Simple content generation requested for topic: {topic}")
    
    # Walidacja - minimalna, tylko to co niezbędne
    if not topic:
        return jsonify({
            'success': False,
            'message': 'No topic provided'
        })
    
    try:
        # Wywołaj modularną funkcję generowania treści
        content = generate_simple_article(topic)
        
        # Prosta obsługa błędu
        if not content:
            return jsonify({
                'success': False,
                'message': 'Failed to generate content, please try again'
            })
        
        # Jednoznaczny przepływ danych wyjściowych
        return jsonify({
            'success': True,
            'content': content
        })
    
    except Exception as e:
        logger.error(f"Error generating content: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error generating content: {str(e)}'
        })

@simple_creator_bp.route('/api/simple-save', methods=['POST'])
def save_simple_content():
    """Save simple content API endpoint - minimalistyczne API"""
    # Pobierz dane z formularza - prosty przepływ danych
    title = request.form.get('title', '')
    content = request.form.get('content', '')
    status = request.form.get('status', 'draft')
    content_id = request.form.get('content_id', '')
    
    # Walidacja - tylko to co niezbędne
    if not title:
        return jsonify({
            'success': False,
            'message': 'Title is required'
        })
    
    # Wywołaj modularną funkcję zapisu z modułu utils.content
    from utils.content.save_content import save_simple_content as save_content_util
    success, content_id, message = save_content_util(
        title=title,
        content=content,
        status=status,
        content_id=content_id if content_id else None
    )
    
    # Prosta odpowiedź API
    return jsonify({
        'success': success,
        'content_id': content_id,
        'message': message
    })

@simple_creator_bp.route('/api/simple-content/<int:content_id>', methods=['GET'])
def get_content(content_id):
    """Get content by ID API endpoint - minimalistyczne API"""
    # Wywołaj modularną funkcję pobierania treści
    success, title, content, status, message = get_simple_content(content_id)
    
    # Jednoznaczna odpowiedź API
    return jsonify({
        'success': success,
        'title': title,
        'content': content,
        'status': status,
        'message': message
    })