"""
Minimalistyczny moduł do zapisywania treści.
Zgodnie z zasadą: "Minimalizm to nie brak. To perfekcyjna ilość."
"""
import json
import logging
from models import ContentLog, Blog, db

# Utwórz logger
logger = logging.getLogger(__name__)

def save_simple_content(title, content, status='draft', content_id=None, blog_id=None):
    """
    Zapisuje prostą treść jako wpis w bazie danych.
    Minimalna logika obsługi, jeden zasadniczy cel funkcji.
    
    Args:
        title (str): Tytuł treści
        content (str): Zawartość HTML
        status (str): Status zawartości (draft, ready_to_publish, published)
        content_id (int, optional): ID istniejącej treści do aktualizacji
        blog_id (int, optional): ID bloga dla nowej treści
        
    Returns:
        tuple: (success, content_id, message)
    """
    try:
        # Prosty mechanizm obsługi: nowy wpis lub aktualizacja
        if content_id:
            # Aktualizacja istniejącego wpisu
            content_log = ContentLog.query.get(content_id)
            if not content_log:
                return False, None, f"Content with ID {content_id} not found"
        else:
            # Tworzenie nowego wpisu
            # Pobieramy pierwszy aktywny blog jeśli nie podano blog_id
            if not blog_id:
                blog = Blog.query.filter_by(active=True).first()
                if not blog:
                    return False, None, "No active blog found"
                blog_id = blog.id
            
            content_log = ContentLog(blog_id=blog_id)
        
        # Prosty update danych
        content_log.title = title
        content_log.status = status
        
        # Zapisz treść w polu error_message (tymczasowo)
        content_data = {
            'content': content,
            'meta_description': '',
            'excerpt': content[:150] + '...' if len(content) > 150 else content,
            'tags': []
        }
        content_log.error_message = json.dumps(content_data)
        
        # Zapisz do bazy danych
        db.session.add(content_log)
        db.session.commit()
        
        return True, content_log.id, "Content saved successfully"
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving content: {str(e)}")
        return False, None, f"Error saving content: {str(e)}"