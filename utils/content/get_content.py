"""
Minimalistyczny moduł do pobierania treści.
Zgodnie z zasadą: "Minimalizm to nie brak. To perfekcyjna ilość."
"""
import json
import logging
from models import ContentLog

# Utwórz logger
logger = logging.getLogger(__name__)

def get_simple_content(content_id):
    """
    Pobiera prostą treść na podstawie ID.
    Minimalna logika, jednoznaczny przepływ danych.
    
    Args:
        content_id (int): ID treści do pobrania
        
    Returns:
        tuple: (success, title, content, status, message)
    """
    try:
        # Pobierz wpis z bazy danych - bezpośrednie zapytanie
        content_log = ContentLog.query.get(content_id)
        
        if not content_log:
            return False, None, None, None, f"Content with ID {content_id} not found"
        
        # Prosta ekstrakcja danych z pola error_message
        content_data = {}
        if content_log.error_message:
            try:
                content_data = json.loads(content_log.error_message)
            except json.JSONDecodeError:
                # Brak złożonych obsług błędów - minimalizm w akcji
                content_data = {}
        
        # Zwracamy rozpakowane dane wprost
        return (
            True, 
            content_log.title,
            content_data.get('content', ''),
            content_log.status,
            "Content retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting content: {str(e)}")
        return False, None, None, None, f"Error getting content: {str(e)}"