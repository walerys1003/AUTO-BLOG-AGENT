"""
Minimalistyczny moduł do generowania treści.
Zgodnie z zasadą: "Minimalizm to nie brak. To perfekcyjna ilość."
"""
import logging
from utils.openrouter import openrouter
from config import Config as config

# Utwórz logger
logger = logging.getLogger(__name__)

def generate_simple_article(topic):
    """
    Generuje prosty artykuł na podstawie tematu.
    Jeden parametr wejściowy, jedna funkcjonalność, brak złożoności.
    
    Args:
        topic (str): Temat artykułu
        
    Returns:
        str: Wygenerowana treść artykułu w formacie HTML
    """
    logger.info(f"Generating simple article for topic: {topic}")
    
    # Używamy bezpośrednio modelu z konfiguracji - proste i przejrzyste
    model = config.DEFAULT_CONTENT_MODEL or "anthropic/claude-3.5-sonnet"
    
    # Prosty systemowy prompt - jasne instrukcje bez zbędnych niuansów
    system_prompt = """You are an expert content writer creating high-quality blog articles.
Write a complete, well-structured article on the given topic.
Format the article in clean HTML with h2 tags for main sections.
Keep paragraphs concise and focused."""

    # Prosty użytkowniczy prompt - minimalna ilość instrukcji
    user_prompt = f"""Write a comprehensive blog article about: {topic}
Use proper HTML formatting with h2 tags for section headers and p tags for paragraphs.
Make it informative, well-structured, and engaging (800-1200 words)."""

    try:
        # Dodajmy logowanie maksymalnie prosty sposób - obserwacja wartości
        logger.info(f"Using model: {model}")
        logger.info(f"Generating content with topic: {topic}")
        
        # Wywołanie API - prosty przepływ danych
        response = openrouter.generate_completion(
            prompt=user_prompt,
            model=model,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=3000
        )
        
        # Logowanie odpowiedzi
        logger.info(f"Received response from OpenRouter: {response is not None}")
        
        # Wyciąganie treści - rozszerzona logika przetwarzania
        if response and "choices" in response and len(response["choices"]) > 0:
            content = response["choices"][0].get("message", {}).get("content", "")
            
            # Logowanie zawartości
            logger.info(f"Content extracted, length: {len(content) if content else 0}")
            
            # Minimalne formatowanie dla konsekwencji
            if not content or not content.strip().startswith("<"):
                content = f"<p>{content or 'Content generation failed. Please try again.'}</p>"
            
            return content
        
        # Dodatkowe informacje diagnostyczne
        if response:
            logger.error(f"OpenRouter response structure unexpected: {response}")
        else:
            logger.error("OpenRouter returned None response")
            
        # Zawsze zwracamy sensowną treść - minimalizm w obsłudze błędów
        return "<p>Content generation failed. Please try again with different topic.</p>"
        
    except Exception as e:
        # Rozszerzone logowanie błędów 
        import traceback
        logger.error(f"Error generating simple article: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Zawsze zwracamy sensowną treść - minimalizm w obsłudze błędów
        return "<p>Error during content generation. Please try again later.</p>"