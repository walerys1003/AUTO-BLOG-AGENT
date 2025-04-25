#!/usr/bin/env python3
"""
Testy jednostkowe dla poszczególnych komponentów generatora artykułów.
Test sprawdza kolejno wszystkie etapy generowania treści:
1. Generowanie planu artykułu
2. Generowanie wstępu
3. Generowanie akapitów głównych
4. Generowanie zakończenia
5. Generowanie metadanych
"""

import os
import sys
import logging
import json
from datetime import datetime

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Ustawienie aktualnego katalogu jako root aplikacji
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import funkcji generatora
from utils.writing import content_generator
from utils.openrouter.client import OpenRouterClient

def test_article_plan():
    """Test generowania planu artykułu"""
    logger.info("=== TEST GENEROWANIA PLANU ARTYKUŁU ===")
    
    topic = "Nowoczesne technologie w marketingu cyfrowym"
    keywords = ["AI", "personalizacja", "automatyzacja", "analityka"]
    paragraph_count = 3
    style = "informative"
    
    logger.info(f"Temat: {topic}")
    logger.info(f"Słowa kluczowe: {keywords}")
    logger.info(f"Liczba akapitów: {paragraph_count}")
    
    plan = content_generator._generate_article_plan(topic, keywords, paragraph_count, style)
    
    if plan and 'paragraph_topics' in plan:
        logger.info("✅ Plan artykułu wygenerowany pomyślnie")
        logger.info(f"Proponowany tytuł: {plan.get('article_title', '')}")
        logger.info(f"Tematy akapitów:")
        for i, p_topic in enumerate(plan.get('paragraph_topics', [])):
            logger.info(f"  {i+1}. {p_topic}")
        return True
    else:
        logger.error("❌ Błąd generowania planu artykułu")
        return False

def test_introduction_generation():
    """Test generowania wstępu do artykułu"""
    logger.info("\n=== TEST GENEROWANIA WSTĘPU ===")
    
    topic = "Nowoczesne technologie w marketingu cyfrowym"
    keywords = ["AI", "personalizacja", "automatyzacja", "analityka"]
    style = "informative"
    
    logger.info(f"Temat: {topic}")
    logger.info(f"Słowa kluczowe: {keywords}")
    
    intro = content_generator._generate_paragraph(
        topic=topic,
        paragraph_topic="Introduction",
        previous_content="",
        keywords=keywords,
        style=style,
        is_introduction=True
    )
    
    if intro and "<p>" in intro:
        logger.info("✅ Wstęp wygenerowany pomyślnie")
        logger.info(f"Długość wstępu: {len(intro)} znaków")
        logger.info(f"Pierwsze 150 znaków: {intro[:150]}...")
        return True
    else:
        logger.error("❌ Błąd generowania wstępu")
        return False

def test_body_paragraph_generation():
    """Test generowania akapitu głównego"""
    logger.info("\n=== TEST GENEROWANIA AKAPITU GŁÓWNEGO ===")
    
    topic = "Nowoczesne technologie w marketingu cyfrowym"
    paragraph_topic = "Sztuczna inteligencja w personalizacji komunikacji marketingowej"
    keywords = ["AI", "personalizacja", "automatyzacja", "analityka"]
    style = "informative"
    
    logger.info(f"Temat główny: {topic}")
    logger.info(f"Temat akapitu: {paragraph_topic}")
    logger.info(f"Słowa kluczowe: {keywords}")
    
    paragraph = content_generator._generate_paragraph(
        topic=topic,
        paragraph_topic=paragraph_topic,
        previous_content="<p>Wstęp do artykułu o marketingu cyfrowym...</p>",
        keywords=keywords,
        style=style
    )
    
    if paragraph and "<p>" in paragraph:
        logger.info("✅ Akapit główny wygenerowany pomyślnie")
        logger.info(f"Długość akapitu: {len(paragraph)} znaków")
        logger.info(f"Pierwsze 150 znaków: {paragraph[:150]}...")
        return True
    else:
        logger.error("❌ Błąd generowania akapitu głównego")
        return False

def test_conclusion_generation():
    """Test generowania zakończenia"""
    logger.info("\n=== TEST GENEROWANIA ZAKOŃCZENIA ===")
    
    topic = "Nowoczesne technologie w marketingu cyfrowym"
    previous_content = """
    <p>Wstęp do artykułu o marketingu cyfrowym...</p>
    <p>Treść o sztucznej inteligencji w marketingu...</p>
    <p>Treść o analityce danych w marketingu...</p>
    """
    keywords = ["AI", "personalizacja", "automatyzacja", "analityka"]
    style = "informative"
    
    logger.info(f"Temat: {topic}")
    logger.info(f"Słowa kluczowe: {keywords}")
    
    conclusion = content_generator._generate_paragraph(
        topic=topic,
        paragraph_topic="Conclusion",
        previous_content=previous_content,
        keywords=keywords,
        style=style,
        is_conclusion=True
    )
    
    if conclusion and "<p>" in conclusion:
        logger.info("✅ Zakończenie wygenerowane pomyślnie")
        logger.info(f"Długość zakończenia: {len(conclusion)} znaków")
        logger.info(f"Pierwsze 150 znaków: {conclusion[:150]}...")
        return True
    else:
        logger.error("❌ Błąd generowania zakończenia")
        return False

def test_metadata_generation():
    """Test generowania metadanych"""
    logger.info("\n=== TEST GENEROWANIA METADANYCH ===")
    
    topic = "Nowoczesne technologie w marketingu cyfrowym"
    content = """
    <h1>Nowoczesne technologie w marketingu cyfrowym</h1>
    <p>Wstęp do artykułu o marketingu cyfrowym...</p>
    <h2>Sztuczna inteligencja w personalizacji komunikacji marketingowej</h2>
    <p>Treść o sztucznej inteligencji w marketingu...</p>
    <h2>Analityka danych jako fundament skutecznych kampanii</h2>
    <p>Treść o analityce danych w marketingu...</p>
    <h2>Automatyzacja procesów marketingowych</h2>
    <p>Treść o automatyzacji w marketingu...</p>
    <h2>Conclusion</h2>
    <p>Podsumowanie artykułu o technologiach w marketingu...</p>
    """
    keywords = ["AI", "personalizacja", "automatyzacja", "analityka"]
    
    logger.info(f"Temat: {topic}")
    logger.info(f"Słowa kluczowe: {keywords}")
    
    metadata = content_generator._generate_article_metadata(topic, content, keywords)
    
    if metadata and "meta_description" in metadata:
        logger.info("✅ Metadane wygenerowane pomyślnie")
        logger.info(f"Meta description: {metadata.get('meta_description', '')}")
        logger.info(f"Excerpt: {metadata.get('excerpt', '')[:100]}...")
        logger.info(f"Tagi: {metadata.get('tags', [])}")
        return True
    else:
        logger.error("❌ Błąd generowania metadanych")
        return False

def test_full_article_generation():
    """Test generowania pełnego artykułu metodą akapitową"""
    logger.info("\n=== TEST GENEROWANIA PEŁNEGO ARTYKUŁU ===")
    
    topic = "Nowoczesne technologie w marketingu cyfrowym"
    keywords = ["AI", "personalizacja", "automatyzacja", "analityka"]
    style = "informative"
    paragraph_count = 3
    
    logger.info(f"Temat: {topic}")
    logger.info(f"Słowa kluczowe: {keywords}")
    logger.info(f"Styl: {style}")
    logger.info(f"Liczba akapitów: {paragraph_count}")
    
    article_data = content_generator.generate_article_by_paragraphs(
        topic=topic,
        keywords=keywords,
        style=style,
        paragraph_count=paragraph_count
    )
    
    if article_data and "content" in article_data:
        logger.info("✅ Pełny artykuł wygenerowany pomyślnie")
        logger.info(f"Długość artykułu: {len(article_data.get('content', ''))} znaków")
        logger.info(f"Meta description: {article_data.get('meta_description', '')}")
        logger.info(f"Tagi: {article_data.get('tags', [])}")
        
        # Zapisanie wygenerowanego artykułu do pliku
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_article_{timestamp}.html"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(article_data.get('content', ''))
        
        logger.info(f"Artykuł zapisany do pliku: {filename}")
        return True
    else:
        logger.error("❌ Błąd generowania pełnego artykułu")
        return False

def run_all_tests():
    """Uruchomienie wszystkich testów"""
    start_time = datetime.now()
    logger.info(f"Rozpoczęcie testów: {start_time}")
    
    results = {}
    
    # Test 1: Plan artykułu
    results["plan"] = test_article_plan()
    
    # Test 2: Wstęp
    results["introduction"] = test_introduction_generation()
    
    # Test 3: Akapit główny
    results["body_paragraph"] = test_body_paragraph_generation()
    
    # Test 4: Zakończenie
    results["conclusion"] = test_conclusion_generation()
    
    # Test 5: Metadane
    results["metadata"] = test_metadata_generation()
    
    # Test 6: Pełny artykuł
    results["full_article"] = test_full_article_generation()
    
    # Podsumowanie wyników
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    logger.info("\n=== PODSUMOWANIE TESTÓW ===")
    logger.info(f"Czas trwania testów: {duration:.2f} sekund")
    
    success_count = sum(1 for result in results.values() if result)
    total_count = len(results)
    
    logger.info(f"Wyniki: {success_count}/{total_count} testów zakończonych sukcesem")
    
    for test_name, result in results.items():
        status = "✅ SUKCES" if result else "❌ BŁĄD"
        logger.info(f"{status}: {test_name}")
    
    return results

if __name__ == "__main__":
    run_all_tests()