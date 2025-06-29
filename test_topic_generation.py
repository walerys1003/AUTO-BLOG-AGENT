#!/usr/bin/env python3
"""
Test skrypt do sprawdzenia generowania tematów AI
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from utils.content.ai_adapter import get_ai_completion
from config import Config
import json

def test_topic_generation():
    """Test bezpośredniego generowania tematów AI"""
    
    with app.app_context():
        system_prompt = """Jesteś ekspertem w tworzeniu pomysłów na artykuły blogowe dla matek i rodzin.
        Twoim zadaniem jest wygenerowanie listy interesujących tematów na artykuły dla podanej kategorii.
        
        Zasady:
        1. Tematy powinny być w języku polskim
        2. Każdy temat powinien być konkretny i szczegółowy
        3. Tematy powinny być zróżnicowane i obejmować różne aspekty kategorii
        4. Unikaj ogólnych i zbyt szerokich tematów
        5. Każdy temat powinien mieć potencjał na artykuł o długości 1200-1600 słów
        6. Zwróć odpowiedź jako tablicę JSON zawierającą listę tematów
        
        Wygeneruj dokładnie 3 tematy dla testów.
        """
        
        user_prompt = f"Wygeneruj 3 interesujące i szczegółowe tematy na artykuły blogowe dla kategorii: Planowanie ciąży"
        
        print("Testuję generowanie tematów AI...")
        print(f"Model: {Config.DEFAULT_TOPIC_MODEL}")
        print(f"System prompt: {system_prompt[:100]}...")
        print(f"User prompt: {user_prompt}")
        
        try:
            response = get_ai_completion(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=Config.DEFAULT_TOPIC_MODEL,
                max_tokens=1000,
                temperature=0.8,
                response_format={"type": "json_object"}
            )
            
            print(f"\nSurowa odpowiedź AI:\n{response}")
            
            # Spróbuj sparsować JSON
            try:
                parsed = json.loads(response)
                print(f"\nSparsowany JSON:\n{json.dumps(parsed, indent=2, ensure_ascii=False)}")
                
                # Sprawdź różne struktury
                if isinstance(parsed, list):
                    print(f"\nOdpowiedź jest listą z {len(parsed)} elementami")
                elif isinstance(parsed, dict):
                    print(f"\nOdpowiedź jest słownikiem z kluczami: {list(parsed.keys())}")
                    
                    for key in ['topics', 'results', 'ideas', 'tematy']:
                        if key in parsed:
                            print(f"Znaleziony klucz '{key}' z wartością: {parsed[key]}")
                
            except json.JSONDecodeError as e:
                print(f"\nBłąd parsowania JSON: {e}")
                
        except Exception as e:
            print(f"\nBłąd podczas wywołania AI: {e}")

if __name__ == "__main__":
    test_topic_generation()