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
    Generate a full article for a given category and topic using AI.
    
    Args:
        category: The category for which to generate content
        topic: The specific topic to create content for
        
    Returns:
        Dictionary with 'title' and 'content' keys
    """
    logger.info(f"Generating article for topic '{topic}' in category '{category}'")
    
    # First, generate an article title and plan
    title, plan = generate_article_title_and_plan(category, topic)
    
    # Then generate paragraphs based on the plan
    paragraphs = []
    try:
        # Generate an introduction
        intro = generate_article_intro(title, topic, category, plan)
        paragraphs.append(intro)
        
        # Generate main content paragraphs
        if plan and len(plan) > 0:
            for i, section in enumerate(plan[:3]):  # Limit to 3 sections for now
                paragraph = generate_long_paragraph(
                    title=title,
                    topic=topic,
                    section_title=section,
                    target_tokens=1000,
                    index=i+1
                )
                paragraphs.append(f"<h2>{section}</h2>\n\n{paragraph}")
        else:
            # Fallback: generate general paragraphs if no plan is available
            for i in range(3):
                paragraph = generate_long_paragraph(
                    title=title,
                    topic=topic,
                    section_title=f"Część {i+1}",
                    target_tokens=1000,
                    index=i+1
                )
                paragraphs.append(paragraph)
        
        # Generate a conclusion
        conclusion = generate_article_conclusion(title, topic, category, plan, paragraphs)
        paragraphs.append("<h2>Podsumowanie</h2>\n\n" + conclusion)
        
    except Exception as e:
        logger.error(f"Error generating article paragraphs: {str(e)}")
        # Add fallback paragraphs if needed
        if len(paragraphs) < 4:
            missing = 4 - len(paragraphs)
            for i in range(missing):
                paragraphs.append(f"<p>To jest przykładowy akapit {i+1} dla artykułu na temat {topic}.</p>")
    
    # Combine everything into the full article
    content = "\n\n".join(paragraphs)
    
    return {
        'title': title,
        'content': content,
        'sections': plan
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