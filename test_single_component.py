#!/usr/bin/env python3
"""
Test pojedynczego komponentu generatora artykułów - planu artykułu.
Mniejszy test, który nie wymaga tyle czasu co pełne testy.
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
    
    topic = "Efektywne zarządzanie czasem w pracy zdalnej"
    keywords = ["praca zdalna", "produktywność", "work-life balance", "zarządzanie zadaniami"]
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
        
        # Zapisanie wygenerowanego planu do pliku JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_plan_{timestamp}.json"
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(plan, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Plan zapisany do pliku: {filename}")
        return True
    else:
        logger.error("❌ Błąd generowania planu artykułu")
        if plan:
            logger.error(f"Zwrócony plan: {plan}")
        return False


if __name__ == "__main__":
    test_article_plan()