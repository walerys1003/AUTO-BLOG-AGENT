"""
AI-powered Image Query Planner
Generates intelligent search queries for finding relevant images for articles
"""
import json
import logging
from typing import Dict, List, Optional
from utils.content.ai_adapter import get_ai_completion

logger = logging.getLogger(__name__)

def generate_image_queries_with_ai(
    title: str,
    content: str = "",
    tags: List[str] = None,
    category: str = ""
) -> Dict:
    """
    Use AI to generate intelligent image search queries based on article context
    
    Args:
        title: Article title
        content: Article content (HTML or text)
        tags: List of SEO tags
        category: Article category
        
    Returns:
        Dict with:
        - primary_query: Main search query
        - alternates: List of alternative queries
        - negative: List of negative keywords to avoid
        - domain_terms: Important domain-specific terms
        - orientation: Preferred orientation (landscape/portrait/square)
        - style: Image style preference (photo/illustration/symbolic)
    """
    if tags is None:
        tags = []
    
    # Prepare context for AI
    context = {
        "title": title,
        "content_preview": content[:1000] if content else "",
        "tags": tags[:10],  # First 10 tags
        "category": category
    }
    
    system_prompt = """Jesteś ekspertem w doborze zdjęć do artykułów blogowych.
Twoje zadanie: na podstawie kontekstu artykułu wygenerować optymalne zapytania do wyszukiwarki obrazów.

ZASADY:
1. primary_query - główne zapytanie (2-5 słów), najlepiej opisujące temat
2. alternates - 2-3 alternatywne zapytania (różne podejścia do tematu)
3. negative - słowa-klucze których NIE chcemy w obrazach
4. domain_terms - kluczowe terminy domenowe do sprawdzenia w opisie zdjęcia
5. orientation - landscape/portrait/square (najczęściej landscape dla blogów)
6. style - photo/illustration/symbolic

WAŻNE:
- Zapytania w języku angielskim (lepsze wyniki w wyszukiwarkach)
- Konkretne, nie ogólne terminy
- Uwzględnij specyfikę kategorii (kosmetyki, dzieci, lifestyle)
- Unikaj dwuznaczności

ODPOWIEDŹ: tylko JSON bez dodatkowych komentarzy."""

    user_prompt = f"""Kontekst artykułu:
{json.dumps(context, ensure_ascii=False, indent=2)}

Wygeneruj zapytania do wyszukiwania obrazów dla tego artykułu."""

    try:
        logger.info(f"Generating AI image queries for: {title[:60]}...")
        
        # Call AI with JSON response format
        response = get_ai_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model="anthropic/claude-3.5-sonnet",
            max_tokens=500,
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        # Parse JSON response
        result = json.loads(response)
        
        # Validate and set defaults
        if "primary_query" not in result:
            # Fallback: use title words
            result["primary_query"] = " ".join(title.split()[:4])
        
        if "alternates" not in result:
            result["alternates"] = []
        
        if "negative" not in result:
            result["negative"] = []
            
        if "domain_terms" not in result:
            result["domain_terms"] = tags[:5] if tags else []
            
        if "orientation" not in result:
            result["orientation"] = "landscape"
            
        if "style" not in result:
            result["style"] = "photo"
        
        logger.info(f"Generated primary query: '{result['primary_query']}'")
        logger.info(f"Alternates: {result['alternates']}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error generating AI image queries: {e}")
        
        # Fallback to simple query
        return {
            "primary_query": " ".join(title.split()[:4]),
            "alternates": [" ".join(tags[:3])] if tags else [],
            "negative": [],
            "domain_terms": tags[:5] if tags else [],
            "orientation": "landscape",
            "style": "photo"
        }

def extract_content_summary(content: str, max_length: int = 500) -> str:
    """
    Extract a clean text summary from HTML content for query generation
    
    Args:
        content: HTML content
        max_length: Maximum length of summary
        
    Returns:
        Clean text summary
    """
    try:
        from bs4 import BeautifulSoup
        
        # Parse HTML
        soup = BeautifulSoup(content, 'html.parser')
        
        # Get text content
        text = soup.get_text(separator=' ', strip=True)
        
        # Clean up whitespace
        text = ' '.join(text.split())
        
        # Truncate
        if len(text) > max_length:
            text = text[:max_length] + "..."
        
        return text
        
    except Exception as e:
        logger.warning(f"Error extracting content summary: {e}")
        return content[:max_length] if content else ""
