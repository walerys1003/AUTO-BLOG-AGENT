#!/usr/bin/env python3
"""
Test generowania wstępu do artykułu.
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

def test_introduction_generation():
    """Test generowania wstępu do artykułu"""
    logger.info("\n=== TEST GENEROWANIA WSTĘPU ===")
    
    # Używamy tematu i słów kluczowych z poprzednio wygenerowanego planu
    topic = "Efektywne zarządzanie czasem w pracy zdalnej"
    keywords = ["praca zdalna", "produktywność", "work-life balance", "zarządzanie zadaniami"]
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
        logger.info(f"Fragment wstępu (pierwsze 300 znaków):")
        logger.info(f"{intro[:300]}...")
        
        # Zapisz wstęp do pliku HTML
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_intro_{timestamp}.html"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"<h1>{topic}</h1>\n")
            f.write(intro)
        
        logger.info(f"Wstęp zapisany do pliku: {filename}")
        return True
    else:
        logger.error("❌ Błąd generowania wstępu")
        return False


if __name__ == "__main__":
    test_introduction_generation()