#!/usr/bin/env python3
"""
Testy różnych strategii generowania artykułów.
Porównanie strategii opartej na liczbie słów i liczbie akapitów.
"""

import os
import sys
import logging
import json
import time
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

def count_words(text):
    """Liczy słowa w tekście HTML"""
    # Usunięcie tagów HTML
    import re
    text_without_tags = re.sub(r'<[^>]*>', ' ', text)
    # Podział na słowa i liczenie
    words = text_without_tags.split()
    return len(words)

def measure_performance(func, *args, **kwargs):
    """Mierzy czas wykonania funkcji i zwraca wynik wraz z czasem"""
    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()
    duration = end_time - start_time
    return result, duration

def test_word_based_generation():
    """Test generowania artykułu opartego na liczbie słów"""
    logger.info("=== TEST GENEROWANIA ARTYKUŁU WEDŁUG LICZBY SŁÓW ===")
    
    topic = "Sztuczna inteligencja w codziennym życiu"
    keywords = ["machine learning", "asystenci głosowi", "automatyzacja", "przyszłość technologii"]
    style = "conversational"
    length = "medium"  # ok. 1200 słów
    
    logger.info(f"Temat: {topic}")
    logger.info(f"Słowa kluczowe: {keywords}")
    logger.info(f"Styl: {style}")
    logger.info(f"Długość: {length}")
    
    article_data, duration = measure_performance(
        content_generator.generate_article,
        topic=topic,
        keywords=keywords,
        style=style,
        length=length
    )
    
    logger.info(f"Czas generowania: {duration:.2f} sekund")
    
    if article_data and "content" in article_data:
        word_count = count_words(article_data.get('content', ''))
        logger.info("✅ Artykuł wygenerowany pomyślnie")
        logger.info(f"Liczba słów: {word_count}")
        logger.info(f"Długość artykułu: {len(article_data.get('content', ''))} znaków")
        logger.info(f"Meta description: {article_data.get('meta_description', '')}")
        
        # Zapisanie wygenerowanego artykułu do pliku
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_article_words_{timestamp}.html"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(article_data.get('content', ''))
        
        logger.info(f"Artykuł zapisany do pliku: {filename}")
        
        return {
            "success": True,
            "word_count": word_count,
            "duration": duration,
            "filename": filename
        }
    else:
        logger.error("❌ Błąd generowania artykułu opartego na liczbie słów")
        return {
            "success": False,
            "duration": duration
        }

def test_paragraph_based_generation():
    """Test generowania artykułu opartego na liczbie akapitów"""
    logger.info("\n=== TEST GENEROWANIA ARTYKUŁU WEDŁUG LICZBY AKAPITÓW ===")
    
    topic = "Sztuczna inteligencja w codziennym życiu"
    keywords = ["machine learning", "asystenci głosowi", "automatyzacja", "przyszłość technologii"]
    style = "conversational"
    paragraph_count = 3
    
    logger.info(f"Temat: {topic}")
    logger.info(f"Słowa kluczowe: {keywords}")
    logger.info(f"Styl: {style}")
    logger.info(f"Liczba akapitów: {paragraph_count}")
    
    article_data, duration = measure_performance(
        content_generator.generate_article_by_paragraphs,
        topic=topic,
        keywords=keywords,
        style=style,
        paragraph_count=paragraph_count
    )
    
    logger.info(f"Czas generowania: {duration:.2f} sekund")
    
    if article_data and "content" in article_data:
        word_count = count_words(article_data.get('content', ''))
        logger.info("✅ Artykuł wygenerowany pomyślnie")
        logger.info(f"Liczba słów: {word_count}")
        logger.info(f"Długość artykułu: {len(article_data.get('content', ''))} znaków")
        logger.info(f"Meta description: {article_data.get('meta_description', '')}")
        
        # Zapisanie wygenerowanego artykułu do pliku
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_article_paragraphs_{timestamp}.html"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(article_data.get('content', ''))
        
        logger.info(f"Artykuł zapisany do pliku: {filename}")
        
        return {
            "success": True,
            "word_count": word_count,
            "duration": duration,
            "filename": filename
        }
    else:
        logger.error("❌ Błąd generowania artykułu opartego na liczbie akapitów")
        return {
            "success": False,
            "duration": duration
        }

def compare_strategies():
    """Porównanie dwóch strategii generowania artykułów"""
    logger.info("=== PORÓWNANIE STRATEGII GENEROWANIA ARTYKUŁÓW ===")
    
    word_based_results = test_word_based_generation()
    paragraph_based_results = test_paragraph_based_generation()
    
    logger.info("\n=== PODSUMOWANIE PORÓWNANIA ===")
    
    if word_based_results["success"] and paragraph_based_results["success"]:
        logger.info("Obie strategie zakończone sukcesem, porównanie wyników:")
        
        logger.info(f"Strategia oparta na liczbie słów:")
        logger.info(f"  - Czas generowania: {word_based_results['duration']:.2f} sekund")
        logger.info(f"  - Liczba słów: {word_based_results['word_count']}")
        logger.info(f"  - Plik: {word_based_results['filename']}")
        
        logger.info(f"Strategia oparta na liczbie akapitów:")
        logger.info(f"  - Czas generowania: {paragraph_based_results['duration']:.2f} sekund")
        logger.info(f"  - Liczba słów: {paragraph_based_results['word_count']}")
        logger.info(f"  - Plik: {paragraph_based_results['filename']}")
        
        # Porównanie czasu generowania
        time_diff = word_based_results['duration'] - paragraph_based_results['duration']
        faster = "oparta na akapitach" if time_diff > 0 else "oparta na słowach"
        
        logger.info(f"Szybsza strategia: {faster} (różnica: {abs(time_diff):.2f} sekund)")
        
        # Porównanie liczby słów
        word_diff = word_based_results['word_count'] - paragraph_based_results['word_count']
        more_words = "oparta na słowach" if word_diff > 0 else "oparta na akapitach"
        
        logger.info(f"Strategia generująca więcej słów: {more_words} (różnica: {abs(word_diff)} słów)")
        
        return {
            "success": True,
            "word_based": word_based_results,
            "paragraph_based": paragraph_based_results
        }
    else:
        failed_strategies = []
        if not word_based_results["success"]:
            failed_strategies.append("oparta na liczbie słów")
        if not paragraph_based_results["success"]:
            failed_strategies.append("oparta na liczbie akapitów")
            
        logger.error(f"Nie można porównać strategii - następujące strategie zakończyły się błędem: {', '.join(failed_strategies)}")
        
        return {
            "success": False,
            "word_based_success": word_based_results["success"],
            "paragraph_based_success": paragraph_based_results["success"]
        }

if __name__ == "__main__":
    compare_strategies()