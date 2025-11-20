"""
AI Article Generator

This module provides functions to generate article content for a given category and topic
using AI models (Claude 3.5 Sonnet via OpenRouter API), with paragraph-based approach.
"""
import logging
import os
import json
import re
from typing import Dict, List, Optional, Any

from config import Config
from utils.content.ai_adapter import get_ai_completion, MockAdapter
from utils.content.long_paragraph_generator import generate_long_paragraph

# Configure logging
logger = logging.getLogger(__name__)

# Blog-specific configuration mapping
BLOG_CONFIGS = {
    2: {  # MAMATESTUJE.COM
        'name': 'MAMATESTUJE.COM',
        'type': 'parenting',
        'min_words': 2000,
        'target_words': 2200,
        'min_chars_with_spaces': 13000,
        'min_chars_no_spaces': 10500
    },
    3: {  # ZNANEKOSMETYKI.PL
        'name': 'ZNANEKOSMETYKI.PL',
        'type': 'cosmetics',
        'min_words': 2500,
        'target_words': 3000,
        'min_chars_with_spaces': 17000,
        'min_chars_no_spaces': 14000
    },
    4: {  # HOMOSONLY.PL
        'name': 'HOMOSONLY.PL',
        'type': 'lifestyle',
        'min_words': 1800,
        'target_words': 2000,
        'min_chars_with_spaces': 12000,
        'min_chars_no_spaces': 9500
    }
}

def get_blog_config_by_name(blog_name: Optional[str]) -> Dict:
    """Get blog configuration by name with fallback to default."""
    if not blog_name:
        return {
            'type': 'default',
            'min_words': 1800,
            'target_words': 2000,
            'min_chars_with_spaces': 12000,
            'min_chars_no_spaces': 9500
        }
    
    # Match by name substring
    blog_upper = blog_name.upper()
    for blog_id, config in BLOG_CONFIGS.items():
        if config['name'] in blog_upper or any(word in blog_upper for word in config['name'].split('.')):
            return config
    
    # Default fallback
    return {
        'type': 'default',
        'min_words': 1800,
        'target_words': 2000,
        'min_chars_with_spaces': 12000,
        'min_chars_no_spaces': 9500
    }


def validate_article_length(content: str, blog_config: Dict) -> Dict[str, Any]:
    """
    Validate article length against blog-specific requirements.
    
    Args:
        content: The article HTML content
        blog_config: Blog configuration with min/target word counts
        
    Returns:
        Dictionary with validation results:
        {
            'valid': bool,
            'word_count': int,
            'chars_with_spaces': int,
            'chars_no_spaces': int,
            'min_words_required': int,
            'target_words': int,
            'meets_word_count': bool,
            'meets_char_count': bool,
            'percentage_of_target': float,
            'issues': List[str]
        }
    """
    # Strip HTML tags to get plain text for word counting
    plain_text = re.sub(r'<[^>]+>', ' ', content)
    plain_text = re.sub(r'\s+', ' ', plain_text).strip()
    
    # Calculate metrics
    word_count = len(plain_text.split())
    chars_with_spaces = len(plain_text)
    chars_no_spaces = len(plain_text.replace(' ', ''))
    
    # Check requirements
    min_words = blog_config.get('min_words', 1800)
    target_words = blog_config.get('target_words', 2000)
    min_chars_with_spaces = blog_config.get('min_chars_with_spaces', 12000)
    min_chars_no_spaces = blog_config.get('min_chars_no_spaces', 9500)
    
    meets_word_count = word_count >= min_words
    meets_char_count = (chars_with_spaces >= min_chars_with_spaces and 
                        chars_no_spaces >= min_chars_no_spaces)
    
    percentage = (word_count / target_words * 100) if target_words > 0 else 0
    
    issues = []
    if not meets_word_count:
        shortage = min_words - word_count
        issues.append(f"Za mało słów: {word_count}/{min_words} (brakuje {shortage} słów)")
    
    if not meets_char_count:
        if chars_with_spaces < min_chars_with_spaces:
            shortage = min_chars_with_spaces - chars_with_spaces
            issues.append(f"Za mało znaków ze spacjami: {chars_with_spaces}/{min_chars_with_spaces} (brakuje {shortage})")
        if chars_no_spaces < min_chars_no_spaces:
            shortage = min_chars_no_spaces - chars_no_spaces
            issues.append(f"Za mało znaków bez spacji: {chars_no_spaces}/{min_chars_no_spaces} (brakuje {shortage})")
    
    valid = meets_word_count and meets_char_count
    
    return {
        'valid': valid,
        'word_count': word_count,
        'chars_with_spaces': chars_with_spaces,
        'chars_no_spaces': chars_no_spaces,
        'min_words_required': min_words,
        'target_words': target_words,
        'meets_word_count': meets_word_count,
        'meets_char_count': meets_char_count,
        'percentage_of_target': round(percentage, 1),
        'issues': issues
    }


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

def generate_article_from_topic(category: str, topic: str, blog_name: Optional[str] = None) -> Dict[str, str]:
    """
    Generate a complete article in a single AI call for maximum speed.
    
    Args:
        category: The category for which to generate content
        topic: The specific topic to create content for
        blog_name: Optional blog name for specialized prompts
        
    Returns:
        Dictionary with 'title' and 'content' keys
    """
    # Handle None or empty topic
    if not topic or topic == 'None':
        topic = f"Praktyczny przewodnik w kategorii {category}"
    
    logger.info(f"Fast generating article for topic '{topic}' in category '{category}' (blog: {blog_name})")
    
    try:
        # Get blog configuration
        blog_config = get_blog_config_by_name(blog_name)
        blog_type = blog_config['type']
        
        logger.info(f"Using blog type: {blog_type} (min words: {blog_config['min_words']}, target: {blog_config['target_words']})")
        
        # ==========================================
        # PROMPT 1: ZNANEKOSMETYKI.PL - Blog Kosmetyczny
        # ==========================================
        if blog_type == 'cosmetics':
            system_prompt = f"""Jesteś ekspertem kosmetologiem i dermatologiem piszącym dla profesjonalnego bloga kosmetycznego ZnaneKosmetyki.pl w kategorii '{category}'.

FUNDAMENTALNE ZASADY BLOGA KOSMETYCZNEGO:
- WYŁĄCZNIE język polski (zero słów angielskich, tłumacz nazwy składników)
- Głęboka analiza naukowa i dermatologiczna
- Szczegółowe omówienie składników aktywnych (INCI, stężenia, mechanizmy działania)
- Profesjonalny ton jak w czasopiśmie dermatologicznym, ale przystępny
- Konkretne produkty, marki, porównania składów
- Czysta treść HTML bez artefaktów markdown

Napisz BARDZO ZAAWANSOWANY, DOGŁĘBNY artykuł ekspercki na temat: '{topic}'

SZCZEGÓŁOWE WYMAGANIA (6-7 STRON A4):
1. DŁUGOŚĆ EKSTREMALNA (artykuł kosmetyczny musi być kompleksowy):
   - MINIMUM 2500 SŁÓW (docelowo 3000-3500 słów)
   - MINIMUM 17000 ZNAKÓW ZE SPACJAMI  
   - MINIMUM 14000 ZNAKÓW BEZ SPACJI
   - Równowartość 6-7 stron A4 tekstu naukowego

2. STRUKTURA ZAAWANSOWANA (kosmetologia):
   - Wstęp naukowy (350-400 słów): problematyka skórna, statystyki, badania
   - Sekcja biochemiczna (400+ słów): jak działa na poziomie komórkowym
   - Sekcja składników (500+ słów): szczegółowa analiza INCI, stężenia, synergie
   - Sekcja procedur (400+ słów): instrukcje aplikacji krok po kroku
   - Sekcja porównawcza (350+ słów): porównanie produktów, marek, technologii
   - Sekcja błędów (300+ słów): częste błędy w pielęgnacji
   - Sekcja rekomendacji (400+ słów): konkretne produkty z uzasadnieniem
   - Podsumowanie naukowe (300+ słów): wnioski, plan pielęgnacji

3. ELEMENTY ZAAWANSOWANE:
   - <h2> dla głównych sekcji
   - <h3> dla podsekcji (składniki, produkty)
   - <p> dla długich, rozbudowanych akapitów (8-12 zdań każdy)
   - <strong> dla nazw składników, produktów, stężeń
   - <em> dla uwag dermatologicznych
   - <ul>, <li> dla list składników, kroków aplikacji
   - Tabele porównawcze w HTML (opcjonalnie)

4. TREŚĆ KOSMETOLOGICZNA (KLUCZOWE):
   - Nazwy składników po polsku + INCI w nawiasach
   - Stężenia procentowe składników aktywnych
   - Mechanizmy działania na poziomie molekularnym
   - pH produktów, tekstury, wykończenia
   - Typy skóry (sucha, tłusta, mieszana, wrażliwa, dojrzała)
   - Konkretne marki i produkty (aptekarskie, dermokosmetyki, luksusowe)
   - Badania kliniczne, publikacje dermatologiczne
   - Porównania przed/po, rezultaty czasowe
   - Interakcje składników, synergie, przeciwwskazania
   - Pory roku, temperatura, warunki stosowania

5. TON PROFESJONALNY:
   - Naukowy ale przystępny
   - Konkretny i merytoryczny
   - Oparty na faktach i badaniach
   - Bez pustych frazesów marketingowych
   - Z przykładami produktów i składników

ODPOWIEDZ TYLKO CZYSTĄ TREŚCIĄ HTML - od pierwszego <p> do ostatniego </p>.
Żadnych znaczników markdown, JSON, cudzysłowów. Samo HTML."""
        
        # ==========================================
        # PROMPT 2: MAMATESTUJE.COM - Blog Parentingowy
        # ==========================================
        elif blog_type == 'parenting':
            system_prompt = f"""Jesteś ekspertem w rodzicielstwie, psychologii dziecięcej i rozwoju niemowląt piszącym dla bloga MamaTestuje.com w kategorii '{category}'.

FUNDAMENTALNE ZASADY BLOGA PARENTINGOWEGO:
- WYŁĄCZNIE język polski (zero słów angielskich)
- Ciepły, wspierający ton dla rodziców i przyszłych rodziców
- Praktyczne porady oparte na badaniach i doświadczeniu
- Empatia, zrozumienie wyzwań rodzicielskich
- Czysta treść HTML bez artefaktów markdown

Napisz KOMPLEKSOWY, PRAKTYCZNY artykuł ekspercki na temat: '{topic}'

SZCZEGÓŁOWE WYMAGANIA (5-6 STRON A4):
1. DŁUGOŚĆ ROZBUDOWANA (artykuł parentingowy musi być wyczerpujący):
   - MINIMUM 2000 SŁÓW (docelowo 2200-2500 słów)
   - MINIMUM 13000 ZNAKÓW ZE SPACJAMI
   - MINIMUM 10500 ZNAKÓW BEZ SPACJI
   - Równowartość 5-6 stron A4

2. STRUKTURA DLA RODZICÓW:
   - Wprowadzenie empatyczne (350+ słów): relacja z problemem, hook emocjonalny
   - Sekcja bazowa (350+ słów): podstawy, co warto wiedzieć, etapy rozwoju
   - Sekcja praktyczna (400+ słów): konkretne porady krok po kroku
   - Sekcja produktowa (350+ słów): rekomendacje produktów, wyposażenia
   - Sekcja problemowa (300+ słów): częste trudności i jak sobie radzić
   - Sekcja bezpieczeństwa (300+ słów): aspekty bezpieczeństwa, normy, certyfikaty
   - Sekcja FAQ (250+ słów): najczęstsze pytania rodziców
   - Podsumowanie wspierające (300+ słów): kluczowe wnioski, wsparcie

3. ELEMENTY PRAKTYCZNE:
   - <h2> dla głównych sekcji
   - <h3> dla pod-tematów (etapy wieku, produkty)
   - <p> dla ciepłych, wspierających akapitów (6-10 zdań)
   - <strong> dla kluczowych rad, produktów, norm bezpieczeństwa
   - <em> dla uwag psychologicznych, wskazówek ekspertów
   - <ul>, <li> dla list kontrolnych, kroków, wyposażenia
   - Tabele porównawcze produktów (opcjonalnie)

4. TREŚĆ PARENTINGOWA (KLUCZOWE):
   - Konkretne zakresy wiekowe (0-3 miesiące, 3-6 miesięcy, etc.)
   - Kamienie milowe rozwoju dziecka
   - Konkretne produkty i marki (Chicco, BabyOno, Lansinoh, etc.)
   - Normy bezpieczeństwa (CE, badania dermatologiczne)
   - Opinie pediatrów, psychologów dziecięcych
   - Prawdziwe historie rodziców, case studies
   - Porównania przed/po, rezultaty
   - Porady dla różnych sytuacji (karmienie piersią, butelką, etc.)
   - Budget-friendly vs premium opcje
   - Sezonowość (lato, zima) jeśli relevantne

5. TON WSPIERAJĄCY:
   - Ciepły i empatyczny
   - "Jesteśmy razem" zamiast "musisz"
   - Praktyczny, bez osądzania
   - Oparty na nauce ale przystępny
   - Z real-life przykładami
   - Bez perfekcjonizmu - normalizacja trudności

ODPOWIEDZ TYLKO CZYSTĄ TREŚCIĄ HTML - od pierwszego <p> do ostatniego </p>.
Żadnych znaczników markdown, JSON, cudzysłowów. Samo HTML."""
        
        # ==========================================
        # PROMPT 3: HOMOSONLY.PL - Blog Lifestyle/LGBTQ+
        # ==========================================
        elif blog_type == 'lifestyle':
            system_prompt = f"""Jesteś ekspertem w kulturze, lifestyle i tematyce LGBTQ+ piszącym dla bloga HomosOnly.pl w kategorii '{category}'.

FUNDAMENTALNE ZASADY BLOGA LIFESTYLE:
- WYŁĄCZNIE język polski (zero słów angielskich)
- Inkluzywny, otwarty ton bez uprzedzeń
- Kulturalne, społeczne i lifestyle'owe podejście
- Współczesność, trendy, życie w społeczności
- Czysta treść HTML bez artefaktów markdown

Napisz ANGAŻUJĄCY, KULTURALNY artykuł na temat: '{topic}'

SZCZEGÓŁOWE WYMAGANIA (4-5 STRON A4):
1. DŁUGOŚĆ ANGAŻUJĄCA:
   - MINIMUM 1800 SŁÓW (docelowo 2000-2200 słów)
   - MINIMUM 12000 ZNAKÓW ZE SPACJAMI
   - MINIMUM 9500 ZNAKÓW BEZ SPACJI
   - Równowartość 4-5 stron A4

2. STRUKTURA LIFESTYLE:
   - Wprowadzenie angażujące (300+ słów): context społeczny, trendy, hook
   - Sekcja historyczna/kontekstowa (300+ słów): tło, ewolucja, znaczenie
   - Sekcja praktyczna (350+ słów): jak to działa dzisiaj, porady
   - Sekcja kulturowa (300+ słów): reprezentacja w mediach, sztuce, popkulturze
   - Sekcja społeczna (300+ słów): aspekty prawne, społeczne, wyzwania
   - Sekcja zasobów (250+ słów): gdzie szukać wsparcia, informacji
   - Podsumowanie inspirujące (250+ słów): przyszłość, pozytywne wnioski

3. ELEMENTY ANGAŻUJĄCE:
   - <h2> dla głównych tematów
   - <h3> dla subtematów (trendy, osoby, miejsca)
   - <p> dla narratywnych akapitów (6-10 zdań)
   - <strong> dla kluczowych pojęć, nazwisk, tytułów
   - <em> dla cytatów, refleksji, uwag kulturowych
   - <ul>, <li> dla list zasobów, rekomendacji
   - Cytaty z wywiadów, ekspertów

4. TREŚĆ KULTURALNA (KLUCZOWE):
   - Kontekst społeczno-kulturowy
   - Reprezentacja w filmach, serialach, książkach
   - Konkretne tytuły, nazwiska, wydarzenia
   - Aspekty prawne (w Polsce i świecie)
   - Organizacje wspierające
   - Statystyki, badania społeczne
   - Historie osobiste, wywiady
   - Międzynarodowe porównania
   - Trendy i przemiany społeczne
   - Pozytywne przykłady zmian

5. TON INKLUZYWNY:
   - Otwarty i wspierający
   - Bez uprzedzeń i stereotypów
   - Edukacyjny ale przystępny
   - Z poczuciem humoru gdzie pasuje
   - Celebrujący różnorodność
   - Empowerment i pozytywne nastawienie

ODPOWIEDZ TYLKO CZYSTĄ TREŚCIĄ HTML - od pierwszego <p> do ostatniego </p>.
Żadnych znaczników markdown, JSON, cudzysłowów. Samo HTML."""
        
        # ==========================================
        # PROMPT DOMYŚLNY (fallback)
        # ==========================================
        else:
            system_prompt = f"""Jesteś ekspertem w pisaniu artykułów w kategorii '{category}'.

FUNDAMENTALNE ZASADY:
- WYŁĄCZNIE język polski
- Czysta treść HTML bez artefaktów
- Profesjonalna jakość

Napisz ekspercki artykuł na temat: '{topic}'

WYMAGANIA:
- Minimum 1800 słów, 12000 znaków ze spacjami
- Struktura z H2, długie akapity
- Szczegółowe, praktyczne porady

ODPOWIEDZ TYLKO HTML - od <p> do </p>."""
        
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
        
        # Dostosuj długość intro i sekcje w zależności od bloga
        if blog_type == 'cosmetics':
            intro_words = 400
            section_words = 500
            max_intro_tokens = 2000
            max_section_tokens = 2500
        elif blog_type == 'parenting':
            intro_words = 350
            section_words = 400
            max_intro_tokens = 1800
            max_section_tokens = 2000
        else:
            intro_words = 300
            section_words = 350
            max_intro_tokens = 1500
            max_section_tokens = 1800
        
        # Generate introduction
        intro_prompt = f"Napisz bardzo długie wprowadzenie (minimum {intro_words} słów) do artykułu o temacie: {topic}. Kategoria: {category}. Użyj storytelling, statystyk, hook'a dla czytelnika. Format: czysty HTML z tagami <p>. ZAKOŃCZ PEŁNYM ZDANIEM I ZAMKNIĘTYM TAGIEM </p>."
        intro_response = get_ai_completion(
            system_prompt="Jesteś ekspertem w pisaniu długich wprowadzeń do artykułów. ZAWSZE kończ pełnym zdaniem z kropką i zamkniętym tagiem </p>.",
            user_prompt=intro_prompt,
            model=Config.DEFAULT_CONTENT_MODEL,
            max_tokens=max_intro_tokens,
            temperature=0.7
        )
        content_parts.append(intro_response.strip())
        
        # Sekcje specyficzne dla każdego bloga
        if blog_type == 'cosmetics':
            sections = [
                f"Jak {topic} działa na poziomie skóry - biochemia i mechanizmy działania",
                f"Kluczowe składniki aktywne w {topic} - analiza INCI, stężenia, synergie",
                f"Procedury i instrukcje aplikacji {topic} - techniki, częstotliwość, porady dermatologiczne",
                f"Porównanie produktów i marek związanych z {topic} - dermokosmetyki, apteczne, luksusowe",
                f"Najczęstsze błędy w stosowaniu {topic} i jak ich unikać",
                f"Rekomendacje produktów dla różnych typów skóry w kontekście {topic}"
            ]
        elif blog_type == 'parenting':
            sections = [
                f"Podstawy i etapy rozwoju w kontekście {topic}",
                f"Praktyczne porady krok po kroku dotyczące {topic}",
                f"Rekomendacje produktów i wyposażenia dla {topic}",
                f"Częste trudności i jak sobie z nimi radzić w {topic}",
                f"Bezpieczeństwo i normy certyfikacji w {topic}",
                f"Najczęstsze pytania rodziców o {topic}"
            ]
        elif blog_type == 'lifestyle':
            sections = [
                f"Kontekst historyczny i społeczny {topic}",
                f"Jak {topic} wygląda współcześnie - praktyczne porady",
                f"Reprezentacja {topic} w kulturze i mediach",
                f"Aspekty prawne i społeczne {topic} w Polsce i świecie",
                f"Zasoby, wsparcie i społeczność związana z {topic}"
            ]
        else:
            sections = [
                f"Podstawowe informacje o {topic}",
                f"Szczegółowe porady i wskazówki dotyczące {topic}",
                f"Praktyczne przykłady i przypadki z życia związane z {topic}",
                f"Najczęstsze błędy i jak ich unikać w kontekście {topic}",
                f"Plan działania i następne kroki dla {topic}"
            ]
        
        for i, section_topic in enumerate(sections, 1):
            section_prompt = f"Napisz bardzo długą sekcję artykułu (minimum {section_words} słów) na temat: {section_topic}. Dodaj nagłówek H2, szczegółowe akapity z przykładami, statystykami, poradami. Format: HTML z <h2> i <p>. ZAKOŃCZ PEŁNYM ZDANIEM I ZAMKNIĘTYM TAGIEM </p>."
            section_response = get_ai_completion(
                system_prompt="Jesteś ekspertem w pisaniu długich, szczegółowych sekcji artykułów. ZAWSZE kończ pełnym zdaniem z kropką i zamkniętym tagiem </p>.",
                user_prompt=section_prompt,
                model=Config.DEFAULT_CONTENT_MODEL,
                max_tokens=max_section_tokens,
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
        
        # Validate article length before returning
        validation_result = validate_article_length(content, blog_config)
        
        # Log validation results
        logger.info(f"Article validation for blog type '{blog_type}':")
        logger.info(f"  - Word count: {validation_result['word_count']}/{validation_result['target_words']} ({validation_result['percentage_of_target']}% of target)")
        logger.info(f"  - Characters (with spaces): {validation_result['chars_with_spaces']}/{blog_config['min_chars_with_spaces']}")
        logger.info(f"  - Characters (no spaces): {validation_result['chars_no_spaces']}/{blog_config['min_chars_no_spaces']}")
        logger.info(f"  - Meets word count: {validation_result['meets_word_count']}")
        logger.info(f"  - Meets char count: {validation_result['meets_char_count']}")
        logger.info(f"  - Overall valid: {validation_result['valid']}")
        
        if validation_result['issues']:
            logger.warning(f"Article validation issues:")
            for issue in validation_result['issues']:
                logger.warning(f"  - {issue}")
        
        return {
            'title': title,
            'content': content,
            'excerpt': excerpt,
            'validation': validation_result  # Include validation result for workflow
        }
        
    except Exception as e:
        # CRITICAL: Log full exception details with traceback
        import traceback
        logger.error("=" * 80)
        logger.error("🚨 CRITICAL: Article generation FAILED - Exception caught!")
        logger.error(f"Topic: {topic}")
        logger.error(f"Category: {category}")
        logger.error(f"Blog: {blog_name}")
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Exception message: {str(e)}")
        logger.error("Full traceback:")
        logger.error(traceback.format_exc())
        logger.error("=" * 80)
        
        # RE-RAISE exception instead of returning fallback content
        # This forces workflow_engine to retry or fail instead of publishing placeholder
        raise Exception(f"Article generation failed for '{topic}': {str(e)}") from e


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