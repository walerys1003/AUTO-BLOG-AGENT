"""
AI Article Generator

This module provides functions to generate article content for a given category and topic
using AI models (Claude 3.5 Sonnet via OpenRouter API), with paragraph-based approach.
"""
import logging
import os
import json
import re
from typing import Dict, List, Optional

from config import Config
from utils.content.ai_adapter import get_ai_completion, MockAdapter
from utils.content.long_paragraph_generator import generate_long_paragraph

# Configure logging
logger = logging.getLogger(__name__)


def clean_markdown_artifacts(content: str) -> str:
    """
    Remove markdown code block artifacts from AI-generated content.
    
    Args:
        content: The content to clean
        
    Returns:
        Content without markdown artifacts
    """
    if not content:
        return content
    
    # Remove markdown code blocks (```html ... ```)
    content = re.sub(r'^```html\s*\n?', '', content, flags=re.MULTILINE)
    content = re.sub(r'\n?```\s*$', '', content, flags=re.MULTILINE)
    content = re.sub(r'^```\s*\n?', '', content, flags=re.MULTILINE)
    
    return content.strip()

def ensure_complete_ending(content: str, topic: str) -> str:
    """
    Ensure article content ends with a complete sentence and proper HTML tag closure.
    
    Args:
        content: The article content to check
        topic: The topic of the article (for context if completion needed)
        
    Returns:
        Content with complete ending
    """
    if not content:
        return content
    
    # Check if content ends with complete </p> tag
    if not content.rstrip().endswith('</p>'):
        logger.warning("Content doesn't end with </p> tag - fixing")
        
        # Find last complete </p> tag
        last_p_close = content.rfind('</p>')
        if last_p_close > 0:
            # Truncate to last complete paragraph
            content = content[:last_p_close + 4]
            logger.info("Truncated to last complete </p> tag")
        else:
            # Add closing tag if missing
            content = content.rstrip() + '</p>'
    
    # Check if last sentence is complete (ends with punctuation)
    # Extract text from last paragraph
    last_p_match = re.search(r'<p>([^<]+)</p>\s*$', content)
    if last_p_match:
        last_text = last_p_match.group(1).strip()
        # Check if ends with proper punctuation
        if not re.search(r'[.!?]$', last_text):
            logger.warning(f"Last sentence incomplete: '{last_text[-50:]}'")
            
            # Try to complete the sentence using AI
            try:
                completion_prompt = f"Dokończ to zdanie naturalnie i poprawnie gramatycznie (odpowiedz TYLKO dokończeniem, bez żadnych dodatkowych słów): {last_text[-100:]}"
                completion = get_ai_completion(
                    system_prompt="Jesteś ekspertem w dokańczaniu zdań po polsku. Odpowiadasz TYLKO dokończeniem zdania.",
                    user_prompt=completion_prompt,
                    model=Config.DEFAULT_CONTENT_MODEL,
                    max_tokens=50,
                    temperature=0.3
                )
                
                # Remove the incomplete sentence and add completed version
                completed_text = last_text + ' ' + completion.strip()
                # Ensure it ends with punctuation
                if not re.search(r'[.!?]$', completed_text):
                    completed_text += '.'
                
                # Replace in content
                content = re.sub(r'<p>([^<]+)</p>\s*$', f'<p>{completed_text}</p>', content)
                logger.info("Completed incomplete sentence using AI")
                
            except Exception as e:
                logger.error(f"Failed to complete sentence: {e}")
                # Fallback: just add period
                content = re.sub(r'<p>([^<]+)</p>\s*$', lambda m: f'<p>{m.group(1).strip()}.</p>', content)
    
    return content

def generate_article_from_topic(category: str, topic: str) -> Dict[str, str]:
    """
    Generate a complete article in a single AI call for maximum speed.
    
    Args:
        category: The category for which to generate content
        topic: The specific topic to create content for
        
    Returns:
        Dictionary with 'title' and 'content' keys
    """
    # Handle None or empty topic
    if not topic or topic == 'None':
        topic = f"Praktyczny przewodnik w kategorii {category}"
    
    logger.info(f"Fast generating article for topic '{topic}' in category '{category}'")
    
    try:
        # Enhanced Polish-only article generation following exact specifications
        system_prompt = f"""Jesteś ekspertem w pisaniu artykułów dla polskiego bloga MamaTestuje.com w kategorii '{category}'.

FUNDAMENTALNE ZASADY:
- WYŁĄCZNIE język polski (zero słów angielskich)
- Czysta treść HTML bez artefaktów JSON
- Profesjonalna jakość jak w magazynie dla rodziców

Napisz ekspercki artykuł na temat: '{topic}'

SZCZEGÓŁOWE WYMAGANIA (4 STRONY A4):
1. DŁUGOŚĆ OBOWIĄZKOWA:
   - minimum 1200 słów (docelowo 1300-1400)
   - minimum 8000 znaków ze spacjami
   - minimum 6500 znaków bez spacji
   - Równowartość 4 stron A4 (Times New Roman 12pt, interlinia 1,5)
2. STRUKTURA OBOWIĄZKOWA:
   - Długi akapit wprowadzający (200+ słów)
   - 5-6 sekcji głównych z nagłówkami H2
   - Każda sekcja: 4-5 szczegółowych akapitów (min 200 słów na sekcję)
   - Rozbudowane podsumowanie z praktycznymi wskazówkami (200+ słów)
3. ELEMENTY HTML: <h2>, <p>, <strong>, <em>, <ul>, <li>
4. TREŚĆ MERYTORYCZNA:
   - Bardzo szczegółowe porady krok po kroku
   - Liczne przykłady z życia wzięte
   - Odwołania do badań i opinii ekspertów
   - Storytelling, pytania retoryczne, porównania
   - Konkretne liczby, statystyki, fakty
5. TON: ciepły ekspert, bardzo szczegółowy i wyczerpujący

ODPOWIEDZ TYLKO CZYSTĄ TREŚCIĄ HTML - od pierwszego <p> do ostatniego </p>.
Żadnych tytułów, JSON, cudzysłowów czy dodatkowych struktur."""
        
        user_prompt = f"""Temat artykułu: {topic}
Kategoria: {category}

Napisz profesjonalny, bardzo długi i dogłębny artykuł w języku polskim dla rodziców i przyszłych rodziców.

BEZWZGLĘDNE WYMAGANIA DŁUGOŚCI (4 STRONY A4):
- OBLIGATORYJNE MINIMUM: 1400 SŁÓW (nie można zakończyć poniżej tej liczby)
- OBLIGATORYJNE MINIMUM: 9000 ZNAKÓW ZE SPACJAMI
- OBLIGATORYJNE MINIMUM: 7500 ZNAKÓW BEZ SPACJI

STRATEGIA PISANIA:
- Każdy akapit musi mieć minimum 6-8 zdań (około 120-150 słów)
- Każda sekcja H2 musi mieć minimum 280 słów
- Wstęp minimum 300 słów, podsumowanie minimum 200 słów
- Dodawaj szczegółowe przykłady, cytaty, statystyki, porównania
- Używaj storytelling, przypadki z życia, pytania retoryczne
- NIE SKRACAJ - artykuł musi być naprawdę długi i szczegółowy
- MINIMUM 1300 słów (nie mniej!)
- MINIMUM 8500 znaków ze spacjami
- Każda sekcja H2 musi mieć co najmniej 4-5 długich akapitów
- Bardzo szczegółowy, wyczerpujący i praktyczny

STRUKTURA OBOWIĄZKOWA:
1. Długie wprowadzenie (250+ słów) - hook, problem, znaczenie tematu
2. Sekcja 1 z H2 (200+ słów) - podstawowe informacje
3. Sekcja 2 z H2 (200+ słów) - szczegółowe porady
4. Sekcja 3 z H2 (200+ słów) - praktyczne przykłady  
5. Sekcja 4 z H2 (200+ słów) - błędy do uniknięcia
6. Sekcja 5 z H2 (200+ słów) - plan działania
7. Długie podsumowanie (150+ słów) - kluczowe wnioski + CTA

Każdy akapit musi być rozbudowany (4-6 zdań). Dodaj liczne przykłady, statystyki, cytaty ekspertów, pytania retoryczne i storytelling.

To musi być bardzo długi, szczegółowy artykuł - nie oszczędzaj słów!"""
        
        # Multiple AI calls to guarantee length - paragraph by paragraph approach
        content_parts = []
        
        # Generate introduction (300+ words)
        intro_prompt = f"Napisz bardzo długie wprowadzenie (minimum 300 słów) do artykułu o temacie: {topic}. Kategoria: {category}. Użyj storytelling, statystyk, hook'a dla czytelnika. Format: czysty HTML z tagami <p>. ZAKOŃCZ PEŁNYM ZDANIEM I ZAMKNIĘTYM TAGIEM </p>."
        intro_response = get_ai_completion(
            system_prompt="Jesteś ekspertem w pisaniu długich wprowadzeń do artykułów. ZAWSZE kończ pełnym zdaniem z kropką i zamkniętym tagiem </p>.",
            user_prompt=intro_prompt,
            model=Config.DEFAULT_CONTENT_MODEL,
            max_tokens=1500,
            temperature=0.7
        )
        content_parts.append(intro_response.strip())
        
        # Generate 5 main sections (250+ words each)
        sections = [
            f"Podstawowe informacje o {topic}",
            f"Szczegółowe porady i wskazówki dotyczące {topic}",
            f"Praktyczne przykłady i przypadki z życia związane z {topic}",
            f"Najczęstsze błędy i jak ich unikać w kontekście {topic}",
            f"Plan działania i następne kroki dla {topic}"
        ]
        
        for i, section_topic in enumerate(sections, 1):
            section_prompt = f"Napisz bardzo długą sekcję artykułu (minimum 250 słów) na temat: {section_topic}. Dodaj nagłówek H2, szczegółowe akapity z przykładami, statystykami, poradami. Format: HTML z <h2> i <p>. ZAKOŃCZ PEŁNYM ZDANIEM I ZAMKNIĘTYM TAGIEM </p>."
            section_response = get_ai_completion(
                system_prompt="Jesteś ekspertem w pisaniu długich, szczegółowych sekcji artykułów. ZAWSZE kończ pełnym zdaniem z kropką i zamkniętym tagiem </p>.",
                user_prompt=section_prompt,
                model=Config.DEFAULT_CONTENT_MODEL,
                max_tokens=1200,
                temperature=0.7
            )
            content_parts.append(section_response.strip())
        
        # Generate conclusion (200+ words)
        conclusion_prompt = f"Napisz bardzo długie podsumowanie (minimum 200 słów) do artykułu o {topic}. Zawrzyj kluczowe wnioski, call-to-action, praktyczne wskazówki. Format: HTML z <p>. MUSISZ ZAKOŃCZYĆ PEŁNYM ZDANIEM Z KROPKĄ I ZAMKNIĘTYM TAGIEM </p> - to bardzo ważne!"
        conclusion_response = get_ai_completion(
            system_prompt="Jesteś ekspertem w pisaniu długich podsumowań artykułów. KRYTYCZNIE WAŻNE: ZAWSZE kończ tekst pełnym zdaniem z kropką i zamkniętym tagiem </p>. NIE PRZERYWAJ w połowie zdania!",
            user_prompt=conclusion_prompt,
            model=Config.DEFAULT_CONTENT_MODEL,
            max_tokens=1000,
            temperature=0.7
        )
        content_parts.append(conclusion_response.strip())
        
        # Combine all parts
        response = '\n\n'.join(content_parts)
        
        # Response is pure HTML content - no JSON parsing needed
        content = response.strip()
        
        # CRITICAL FIX: Remove markdown artifacts (```html ... ```)
        content = clean_markdown_artifacts(content)
        
        # FIX: Ensure content ends with complete sentence and closed tag
        content = ensure_complete_ending(content, topic)
        
        # Generate Polish title following exact specifications  
        title_prompt = f"""Wygeneruj chwytliwy, w pełni po polsku napisany tytuł blogowy na temat: {topic}

WYMAGANIA TYTUŁU:
- Maksymalnie 60 znaków
- 100% język polski (zero angielskich słów)
- Atrakcyjny dla czytelnika
- Zawiera słowa kluczowe
- Wzbudza ciekawość
- Unika clickbaitu
- Bez cudzysłowów, dwukropków, nawiasów

Kategoria: {category}

Odpowiedz WYŁĄCZNIE tytułem - bez dodatkowych słów, cudzysłowów czy znaków."""
        
        title_response = get_ai_completion(
            system_prompt="Jesteś ekspertem w tworzeniu tytułów artykułów dla polskich rodziców.",
            user_prompt=title_prompt,
            model=Config.DEFAULT_CONTENT_MODEL,
            max_tokens=100,
            temperature=0.5
        )
        
        title = title_response.strip().replace('"', '').replace('„', '').replace('"', '')
        
        # Ensure content has proper HTML structure
        if not '<p>' in content and not '<h2>' in content:
            # Convert plain text to HTML paragraphs
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
            content = '\n\n'.join([f'<p>{p}</p>' for p in paragraphs])
        
        # Generate professional excerpt following specifications
        excerpt_prompt = f"""Napisz krótki lead (excerpt) do artykułu o tytule: {title}

WYMAGANIA EXCERPT:
- 1-2 zdania po polsku
- Przyciąga uwagę i zachęca do lektury  
- Bez zbędnych znaków interpunkcyjnych
- Bez cudzysłowów czy struktur JSON
- Nie może być powieleniem pierwszego akapitu
- Maksymalnie 160 znaków

Temat artykułu: {topic}
Kategoria: {category}

Odpowiedz WYŁĄCZNIE tekstem excerpt - bez dodatkowych słów."""

        excerpt_response = get_ai_completion(
            system_prompt="Jesteś ekspertem w tworzeniu przyciągających zajawek dla polskich blogów parentingowych.",
            user_prompt=excerpt_prompt,
            model=Config.DEFAULT_CONTENT_MODEL,
            max_tokens=100,
            temperature=0.5
        )
        
        excerpt = excerpt_response.strip().replace('"', '').replace('„', '').replace('"', '')
        
        return {
            'title': title,
            'content': content,
            'excerpt': excerpt
        }
        
    except Exception as e:
        logger.error(f"Error in fast article generation: {str(e)}")
        
        # Enhanced fallback article with Polish content
        return {
            'title': f"Praktyczny przewodnik: {topic}",
            'content': f"""<p>Temat <strong>{topic.lower()}</strong> w kategorii {category} to zagadnienie, które wymaga dogłębnego zrozumienia i świadomego podejścia każdego rodzica. W dzisiejszych czasach dostęp do rzetelnej informacji ma kluczowe znaczenie dla podejmowania mądrych decyzji.</p>

<h2>Podstawy, które warto znać</h2>
<p>Każdy rodzic powinien mieć solidną wiedzę na temat {topic.lower()}. Eksperci jednogłośnie podkreślają, że kompleksowe podejście do tej tematyki może znacząco wpłynąć na jakość życia całej rodziny.</p>

<p>Badania naukowe pokazują, że świadome decyzje oparte na rzetelnej wiedzy przynoszą lepsze rezultaty niż działania oparte wyłącznie na intuicji czy przekazie społecznym.</p>

<h2>Praktyczne zastosowanie w codzienności</h2>
<p>Wiedza teoretyczna ma wartość tylko wtedy, gdy potrafimy ją zastosować w praktyce. W kontekście {topic.lower()}, oznacza to uwzględnienie indywidualnych potrzeb i możliwości każdej rodziny.</p>

<p>Specjaliści zalecają stopniowe wprowadzanie zmian i obserwowanie ich wpływu na codzienne funkcjonowanie. Nie ma uniwersalnych rozwiązań - to, co działa dla jednej rodziny, nie musi sprawdzić się u innych.</p>

<h2>Najczęstsze wyzwania i jak je pokonać</h2>
<p>W trakcie wprowadzania nowych rozwiązań związanych z {topic.lower()}, rodzice często spotykają się z różnymi trudnościami. Najważniejsze to cierpliwość i systematyczność w działaniu.</p>

<p>Pamiętajmy, że każda zmiana wymaga czasu i konsekwencji. Warto również skorzystać z doświadczeń innych rodziców i porady specjalistów, gdy napotykamy na przeszkody.</p>

<h2>Podsumowanie i kluczowe wnioski</h2>
<p>Zrozumienie {topic.lower()} stanowi fundament świadomego rodzicielstwa. Dzięki odpowiedniej wiedzy i praktycznemu podejściu można skutecznie wspierać rozwój dzieci i budować harmonijne relacje rodzinne.</p>

<p>Najważniejsze to pamiętać, że każda rodzina jest inna, a najlepsze rozwiązania to te, które są dostosowane do konkretnych potrzeb i możliwości. Inwestycja w wiedzę zawsze się opłaca.</p>""",
            'excerpt': f"Kompleksowy i praktyczny przewodnik dotyczący {topic.lower()} - wszystko, co powinni wiedzieć świadomi rodzice."
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