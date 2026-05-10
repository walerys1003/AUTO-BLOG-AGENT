#!/usr/bin/env python3
"""
Skrypt do generowania polskich tematów artykułów dla kategorii MamaTestuje.com
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import ArticleTopic, Blog
from utils.ai_content_strategy.topic_generator import generate_ai_topics_for_category
from datetime import datetime
import random

def generate_polish_topics_for_blog():
    """Generuje polskie tematy dla bloga MamaTestuje"""
    
    with app.app_context():
        # Pobierz blog MamaTestuje
        blog = Blog.query.get(2)
        if not blog:
            print("Blog MamaTestuje nie znaleziony!")
            return
            
        # Kategorie z pełną listą z WordPress API
        categories = [
            "Planowanie ciąży", "Zdrowie w ciąży", "Kosmetyki dla mam", 
            "Laktacja i karmienie", "Karmienie dziecka", "Zdrowie dziecka",
            "Kosmetyki dla dzieci", "Pieluchy dla dzieci", "Higiena codzienna",
            "Kąpiel dziecka", "Pielęgnacja biustu", "Witaminy ciążowe",
            "Odporność i witaminy", "Kremy dla dzieci", "Balsamy i emolienty",
            "Chusteczki nawilżane", "Gryzaki i zabawki", "Mleka dla dzieci",
            "Kaszki dla dzieci", "Obiadki dla dzieci", "Zupki dla dzieci"
        ]
        
        print(f"Generuję polskie tematy dla {len(categories)} kategorii...")
        
        total_generated = 0
        
        for category in categories:
            print(f"\nGeneruję tematy dla kategorii: {category}")
            
            try:
                # Generuj 5 tematów na kategorię
                topics = generate_ai_topics_for_category(category, 5)
                
                if topics:
                    for topic in topics:
                        # Sprawdź czy temat już istnieje
                        existing = ArticleTopic.query.filter_by(
                            blog_id=blog.id,
                            title=topic,
                            category=category
                        ).first()
                        
                        if not existing:
                            # Utwórz nowy temat
                            new_topic = ArticleTopic(
                                blog_id=blog.id,
                                title=topic,
                                category=category,
                                score=random.uniform(0.7, 0.9),
                                priority=random.randint(1, 5),
                                status='pending',
                                created_at=datetime.utcnow(),
                                updated_at=datetime.utcnow()
                            )
                            
                            db.session.add(new_topic)
                            total_generated += 1
                            print(f"  ✓ {topic}")
                        else:
                            print(f"  - Temat już istnieje: {topic}")
                
                # Commituj po każdej kategorii
                db.session.commit()
                
            except Exception as e:
                print(f"  ✗ Błąd generowania tematów dla {category}: {str(e)}")
                db.session.rollback()
                
        print(f"\n🎉 Wygenerowano łącznie {total_generated} nowych polskich tematów!")
        
        # Zatwierdź wszystkie tematy automatycznie
        pending_topics = ArticleTopic.query.filter_by(
            blog_id=blog.id,
            status='pending'
        ).all()
        
        approved_count = 0
        for topic in pending_topics:
            topic.status = 'approved'
            topic.approved_at = datetime.utcnow()
            topic.approved_by = 'system'
            approved_count += 1
            
        db.session.commit()
        print(f"✅ Zatwierdzono {approved_count} tematów do użycia w workflow")

if __name__ == "__main__":
    generate_polish_topics_for_blog()