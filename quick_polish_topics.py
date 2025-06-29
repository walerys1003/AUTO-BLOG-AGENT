#!/usr/bin/env python3
"""
Szybki skrypt do generowania polskich tematów dla MamaTestuje
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import ArticleTopic, Blog
from utils.ai_content_strategy.topic_generator import generate_ai_topics_for_category
from datetime import datetime
import random

def generate_polish_topics():
    """Generuje polskie tematy dla najważniejszych kategorii"""
    
    with app.app_context():
        # Kategorie główne
        categories = [
            "Planowanie ciąży", "Zdrowie w ciąży", "Kosmetyki dla mam", 
            "Laktacja i karmienie", "Karmienie dziecka", "Zdrowie dziecka"
        ]
        
        print(f"Generuję polskie tematy dla {len(categories)} kategorii...")
        
        for category in categories:
            print(f"\nKategoria: {category}")
            
            try:
                # Generuj 5 tematów na kategorię
                topics = generate_ai_topics_for_category(category, 5)
                
                for topic in topics:
                    # Utwórz nowy temat
                    new_topic = ArticleTopic()
                    new_topic.blog_id = 2
                    new_topic.title = topic
                    new_topic.category = category
                    new_topic.score = random.uniform(0.7, 0.9)
                    new_topic.priority = random.randint(1, 5)
                    new_topic.status = 'approved'
                    new_topic.created_at = datetime.utcnow()
                    new_topic.updated_at = datetime.utcnow()
                    new_topic.approved_at = datetime.utcnow()
                    new_topic.approved_by = 1  # System user ID
                    
                    db.session.add(new_topic)
                    print(f"  ✓ {topic}")
                
                db.session.commit()
                
            except Exception as e:
                print(f"  ✗ Błąd: {str(e)}")
                db.session.rollback()
                
        print(f"\n🎉 Gotowe! Sprawdzam wygenerowane tematy...")
        
        # Pokaż statystyki
        total = ArticleTopic.query.filter_by(blog_id=2, status='approved').count()
        print(f"✅ Łącznie: {total} zatwierdzonych polskich tematów")

if __name__ == "__main__":
    generate_polish_topics()