"""
AI Topic Generator

This module provides functions to generate relevant topics for a given category
using AI models (Claude 3.5 Sonnet via OpenRouter API).
"""
import json
import logging
import random
import time
from typing import List, Dict, Any, Optional

from config import Config
from utils.content.ai_adapter import get_ai_completion, get_default_ai_service

# Configure logging
logger = logging.getLogger(__name__)

def generate_ai_topics_for_category(category: str, count: int = 20) -> List[str]:
    """
    Generate topic ideas for a given category using AI.
    
    Args:
        category: The category for which to generate topics
        count: Number of topics to generate (default: 20)
        
    Returns:
        List of generated topic ideas as strings
    """
    logger.info(f"Generating {count} AI topics for category: {category}")
    
    system_prompt = """Jesteś ekspertem w tworzeniu pomysłów na artykuły blogowe dla matek i rodzin.
    Twoim zadaniem jest wygenerowanie listy interesujących tematów na artykuły dla podanej kategorii.
    
    Zasady:
    1. Tematy powinny być w języku polskim
    2. Każdy temat powinien być konkretny i szczegółowy
    3. Tematy powinny być zróżnicowane i obejmować różne aspekty kategorii
    4. Unikaj ogólnych i zbyt szerokich tematów
    5. Każdy temat powinien mieć potencjał na artykuł o długości 1200-1600 słów
    6. Zwróć odpowiedź w formacie JSON z kluczem "tematy" zawierającym listę tematów
    
    Wygeneruj dokładnie tyle tematów, ile zostało określone w zapytaniu.
    Odpowiedź: {"tematy": ["temat 1", "temat 2", ...]}
    """
    
    user_prompt = f"Wygeneruj {count} interesujących i szczegółowych tematów na artykuły blogowe dla kategorii: {category}"
    
    try:
        # Try to get topics using OpenRouter API
        response = get_ai_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=Config.DEFAULT_TOPIC_MODEL,
            max_tokens=2000,
            temperature=0.8,
            response_format={"type": "json_object"}
        )
        
        try:
            # Try to parse the response as JSON
            result = json.loads(response)
            
            # Extract topics from the response (handle different response formats)
            if isinstance(result, list):
                topics = result
            elif isinstance(result, dict) and "tematy" in result:
                topics = result["tematy"]
            elif isinstance(result, dict) and "topics" in result:
                topics = result["topics"]
            elif isinstance(result, dict) and "results" in result:
                topics = result["results"]
            elif isinstance(result, dict) and "ideas" in result:
                topics = result["ideas"]
            else:
                # If the structure is unknown, try to extract any list with at least 10 items
                for key, value in result.items():
                    if isinstance(value, list) and len(value) >= 10:
                        topics = value
                        break
                else:
                    # If no suitable list found, create dummy list
                    topics = [f"Temat {i+1} dla kategorii {category}" for i in range(count)]
            
            # Ensure we have exactly the requested number of topics
            if len(topics) < count:
                # If we have too few topics, add some simple ones to reach the count
                for i in range(len(topics), count):
                    topics.append(f"Dodatkowy temat {i+1} dla kategorii {category}")
            elif len(topics) > count:
                # If we have too many topics, truncate the list
                topics = topics[:count]
            
            return topics
            
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse AI response as JSON: {response[:100]}...")
            # Fallback to demo topics
            return _generate_demo_topics(category, count)
            
    except Exception as e:
        logger.error(f"Error generating AI topics: {str(e)}")
        # Fallback to demo topics
        return _generate_demo_topics(category, count)

def _generate_demo_topics(category: str, count: int) -> List[str]:
    """Generate demo topics for a category when AI generation fails"""
    logger.info(f"Generating {count} demo topics for category: {category}")
    
    # Create base templates for topics
    templates = [
        f"Najlepsze praktyki w {category}",
        f"Przewodnik po {category} dla początkujących",
        f"Jak rozwiązać najczęstsze problemy w {category}",
        f"Historia rozwoju {category} na przestrzeni lat",
        f"Przyszłość {category} - trendy i prognozy",
        f"5 mitów na temat {category}, w które wciąż wierzymy",
        f"Jak {category} zmienia się w 2025 roku",
        f"Profesjonalne wskazówki dotyczące {category}",
        f"Porównanie różnych podejść do {category}",
        f"Narzędzia i technologie usprawniające {category}",
        f"Wpływ sztucznej inteligencji na {category}",
        f"Jak zacząć przygodę z {category} - poradnik krok po kroku",
        f"Case study: Sukces w {category}",
        f"{category} dla zaawansowanych - techniki mistrzów",
        f"Analiza rynku {category} w Polsce",
        f"Najczęstsze błędy popełniane w {category}",
        f"Jak przekonać klienta do {category}",
        f"ROI z {category} - jak mierzyć efektywność",
        f"Najlepsze książki o {category}",
        f"Wywiady z ekspertami {category}",
        f"Psychologiczne aspekty {category}",
        f"Etyka w {category}",
        f"Prawne aspekty {category}",
        f"Jak {category} wpływa na naszą codzienność",
        f"Międzynarodowe standardy w {category}",
        f"Przegląd badań naukowych na temat {category}",
        f"Jak uczyć dzieci {category}",
        f"Kariera w {category} - ścieżki rozwoju",
        f"Jak {category} łączy się z innymi dziedzinami",
        f"Wyzwania w {category} na rok 2025"
    ]
    
    # Generate variations
    variations = []
    for template in templates:
        variations.append(template)
        variations.append(f"{template} - część 1")
        variations.append(f"Wszystko co musisz wiedzieć o {template.lower()}")
        variations.append(f"Jak skutecznie wykorzystać {template.lower()}")
        variations.append(f"Przewodnik eksperta: {template}")
    
    # Ensure we have enough variations
    while len(variations) < count * 2:
        variations.extend(templates)
    
    # Shuffle and select the requested number of topics
    random.shuffle(variations)
    return variations[:count]