"""
AI Article Generator

This module provides functions to generate article content for a given category and topic
using AI models (Claude 3.5 Sonnet via OpenRouter API), with paragraph-based approach.
"""
import logging
import os
import json
from typing import Dict, List, Optional

from config import Config
from utils.content.ai_adapter import get_ai_completion, MockAdapter
from utils.content.long_paragraph_generator import generate_long_paragraph

# Configure logging
logger = logging.getLogger(__name__)

def generate_article_from_topic(category: str, topic: str) -> Dict[str, str]:
    """
    Generate a complete article in a single AI call for maximum speed.
    
    Args:
        category: The category for which to generate content
        topic: The specific topic to create content for
        
    Returns:
        Dictionary with 'title' and 'content' keys
    """
    logger.info(f"Fast generating article for topic '{topic}' in category '{category}'")
    
    try:
        # Single AI call to generate complete article
        system_prompt = f"""Jesteś ekspertem w pisaniu artykułów dla bloga MamaTestuje.com w kategorii '{category}'.
        
        Twoim zadaniem jest napisanie kompletnego artykułu na temat: '{topic}'
        
        Zasady:
        1. Napisz artykuł o długości 1200-1600 słów w języku polskim
        2. Struktura: tytuł + wstęp + 3-4 główne sekcje + podsumowanie
        3. Każda sekcja powinna mieć nagłówek H2 i 2-3 akapity treści
        4. Używaj pogrubień <strong> dla ważnych pojęć
        5. Ton przyjazny, ekspercki, skierowany do rodziców i przyszłych rodziców
        6. Zawrzyj praktyczne porady i konkretne informacje
        7. Format HTML z użyciem <h2>, <p>, <strong>, <em>
        
        Zwróć wynik w formacie JSON:
        {{
            "title": "Tytuł artykułu",
            "content": "Pełna treść artykułu w HTML",
            "excerpt": "Krótkie podsumowanie (1-2 zdania)"
        }}
        """
        
        user_prompt = f"""Napisz kompletny artykuł na temat: '{topic}' 
        
        Kategoria: {category}
        
        Artykuł powinien być wartościowy dla czytelników MamaTestuje.com - rodziców i osób planujących potomstwo."""
        
        # Single AI completion with higher token limit
        response = get_ai_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=Config.DEFAULT_CONTENT_MODEL,
            max_tokens=2000,  # Enough for full article
            temperature=0.7
        )
        
        # Try to parse JSON response
        import json
        try:
            article_data = json.loads(response)
            if article_data.get('title') and article_data.get('content'):
                return {
                    'title': article_data['title'],
                    'content': article_data['content'],
                    'excerpt': article_data.get('excerpt', '')
                }
        except json.JSONDecodeError:
            logger.warning("AI response not in JSON format, parsing as text")
        
        # Fallback: if not JSON, try to extract title and content from text
        lines = response.strip().split('\n')
        title = ""
        content_lines = []
        
        for line in lines:
            if not title and (line.startswith('#') or len(line.strip()) < 100):
                title = line.strip().replace('#', '').strip()
            elif line.strip():
                content_lines.append(line.strip())
        
        if not title:
            title = f"Przewodnik: {topic}"
        
        content = '\n\n'.join(content_lines) if content_lines else response
        
        # Ensure content has proper HTML structure
        if not '<p>' in content and not '<h2>' in content:
            # Convert plain text to HTML paragraphs
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
            content = '\n\n'.join([f'<p>{p}</p>' for p in paragraphs])
        
        return {
            'title': title,
            'content': content,
            'excerpt': f"Praktyczny przewodnik na temat {topic.lower()}."
        }
        
    except Exception as e:
        logger.error(f"Error in fast article generation: {str(e)}")
        
        # Quick fallback article
        return {
            'title': f"Przewodnik: {topic}",
            'content': f"""<p><strong>{topic}</strong> to ważny temat w kategorii {category}, który zasługuje na szczególną uwagę każdego rodzica.</p>

<h2>Podstawowe informacje</h2>
<p>W kontekście {topic.lower()}, eksperci podkreślają znaczenie kompleksowego podejścia do tej tematyki. Warto zwrócić uwagę na kluczowe aspekty, które mogą wpłynąć na nasze codzienne decyzje.</p>

<h2>Praktyczne wskazówki</h2>
<p>Praktyczne zastosowanie wiedzy na temat {topic.lower()} może przynieść wymierne korzyści w życiu rodzinnym. Specjaliści zalecają uwzględnienie różnych perspektyw i indywidualnych potrzeb.</p>

<h2>Podsumowanie</h2>
<p>Zrozumienie {topic.lower()} stanowi fundament świadomych decyzji rodzicielskich. Dzięki odpowiedniej wiedzy można lepiej przygotować się na wyzwania związane z tym obszarem.</p>""",
            'excerpt': f"Kompleksowy przewodnik dotyczący {topic.lower()} dla świadomych rodziców."
        }


def generate_article_title_and_plan(category: str, topic: str) -> tuple:
    """
    Generate an engaging article title and content plan based on the topic.
    
    Args:
        category: The category for which to generate the title
        topic: The specific topic to create a title for
        
    Returns:
        Tuple of (title, plan) where plan is a list of section titles
    """
    system_prompt = """Jesteś ekspertem w tworzeniu planów artykułów na blog. 
    Twoim zadaniem jest wygenerowanie chwytliwego tytułu i planu artykułu (3-5 sekcji).
    
    Zasady:
    1. Tytuł powinien być chwytliwy, ale nie clickbaitowy
    2. Tytuł powinien być w języku polskim i zawierać 50-80 znaków
    3. Plan powinien zawierać 3-5 sekcji
    4. Sekcje powinny być logicznie powiązane i prowadzić czytelnika przez temat
    5. Zwróć odpowiedź w formacie JSON: {"title": "Tytuł artykułu", "plan": ["Sekcja 1", "Sekcja 2", "Sekcja 3"]}
    
    Generujesz tytuł i plan dla artykułu w kategorii i temacie które podam.
    """
    
    user_prompt = f"Kategoria: {category}\nTemat: {topic}\n\nWygeneruj chwytliwy tytuł i plan artykułu na ten temat."
    
    try:
        response = get_ai_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=Config.DEFAULT_CONTENT_MODEL,
            max_tokens=1000,
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        try:
            result = json.loads(response)
            title = result.get("title", f"{topic} - kompletny przewodnik")
            plan = result.get("plan", [])
            
            if not plan or len(plan) < 3:
                # Generate a default plan if needed
                plan = [
                    f"Wprowadzenie do {topic}",
                    f"Najważniejsze aspekty {topic}",
                    f"Praktyczne zastosowania {topic}",
                    f"Podsumowanie i wnioski"
                ]
            
            return title, plan
            
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse AI response for title and plan: {response[:200]}...")
            return topic, []
            
    except Exception as e:
        logger.error(f"Error generating article title and plan: {str(e)}")
        return topic, []


def generate_article_intro(title: str, topic: str, category: str, plan: List[str]) -> str:
    """
    Generate an engaging introduction for the article.
    
    Args:
        title: The article title
        topic: The specific topic
        category: The category
        plan: The article content plan (list of section titles)
        
    Returns:
        Introduction text as a string
    """
    system_prompt = """Jesteś ekspertem w pisaniu wstępów do artykułów na blog.
    Twoim zadaniem jest napisanie wciągającego wstępu do artykułu o podanym tytule i temacie.
    
    Zasady:
    1. Wstęp powinien mieć 800-1000 znaków
    2. Wstęp powinien przyciągać uwagę czytelnika
    3. Wstęp powinien nakreślać zawartość artykułu
    4. Nie używaj zwrotów typu "w tym artykule", "w poniższym tekście" itp.
    5. Unikaj clickbaitu i przesadnych obietnic
    6. Pisz w języku polskim, przyjaznym tonem eksperta
    7. Wstęp nie powinien mieć śródtytułów
    8. Wstęp powinien kończyć się zapowiedzią zawartości artykułu
    
    Generujesz wstęp dla artykułu o podanym tytule, temacie i planie.
    """
    
    plan_text = "\n".join([f"- {section}" for section in plan]) if plan else ""
    user_prompt = f"Tytuł: {title}\nTemat: {topic}\nKategoria: {category}\n\nPlan artykułu:\n{plan_text}\n\nNapisz wciągający wstęp do tego artykułu."
    
    try:
        intro = get_ai_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=Config.DEFAULT_CONTENT_MODEL,
            max_tokens=1000,
            temperature=0.7
        )
        
        return intro
        
    except Exception as e:
        logger.error(f"Error generating article introduction: {str(e)}")
        # Return a fallback introduction
        return f"<p>Witaj w naszym przewodniku na temat {topic}. W tym artykule omówimy najważniejsze aspekty tego zagadnienia i podzielimy się praktycznymi wskazówkami.</p>"


def generate_article_conclusion(title: str, topic: str, category: str, plan: List[str], paragraphs: List[str]) -> str:
    """
    Generate a strong conclusion for the article.
    
    Args:
        title: The article title
        topic: The specific topic
        category: The category
        plan: The article content plan
        paragraphs: The article paragraphs
        
    Returns:
        Conclusion text as a string
    """
    system_prompt = """Jesteś ekspertem w pisaniu zakończeń artykułów na blog.
    Twoim zadaniem jest napisanie mocnego zakończenia artykułu, które podsumuje główne punkty i zachęci czytelnika do działania.
    
    Zasady:
    1. Zakończenie powinno mieć 700-900 znaków
    2. Zakończenie powinno podsumować najważniejsze punkty z artykułu
    3. Zakończenie powinno zawierać call-to-action - zachętę do podjęcia działania
    4. Unikaj rozpoczynania od zwrotów "podsumowując", "na koniec" itp.
    5. Pisz w języku polskim, przyjaznym tonem eksperta
    6. Zakończenie nie powinno wprowadzać nowych informacji
    7. Zakończenie powinno dawać czytelnikowi poczucie, że otrzymał kompletną i wartościową wiedzę
    
    Generujesz zakończenie dla artykułu o podanym tytule, temacie i planie.
    """
    
    plan_text = "\n".join([f"- {section}" for section in plan]) if plan else ""
    user_prompt = f"Tytuł: {title}\nTemat: {topic}\nKategoria: {category}\n\nPlan artykułu:\n{plan_text}\n\nNapisz mocne zakończenie do tego artykułu."
    
    try:
        conclusion = get_ai_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=Config.DEFAULT_CONTENT_MODEL,
            max_tokens=800,
            temperature=0.7
        )
        
        return conclusion
        
    except Exception as e:
        logger.error(f"Error generating article conclusion: {str(e)}")
        # Return a fallback conclusion
        return f"<p>To najważniejsze informacje na temat {topic}. Mamy nadzieję, że ten artykuł był pomocny i zachęcamy do wykorzystania zdobytej wiedzy w praktyce.</p>"