#!/usr/bin/env python3
"""
Test pełnego procesu automatyzacji - od tematu do publikacji
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import AutomationRule, ArticleTopic, ContentLog
from utils.automation.workflow_engine import WorkflowEngine

def test_full_automation():
    """Test kompletnego procesu automatyzacji"""
    
    with app.app_context():
        print("🚀 Rozpoczynam pełny test automatyzacji...")
        
        # Znajdź aktywną regułę automatyzacji
        rule = AutomationRule.query.filter_by(is_active=True).first()
        if not rule:
            print("❌ Brak aktywnych reguł automatyzacji")
            return
            
        print(f"📋 Używam reguły: {rule.name}")
        print(f"   Blog ID: {rule.blog_id}")
        print(f"   Auto-publikacja: {'TAK' if rule.auto_publish else 'NIE'}")
        
        # Sprawdź dostępne zatwierdzone tematy
        approved_topics = ArticleTopic.query.filter_by(
            blog_id=rule.blog_id,
            status='approved'
        ).count()
        
        print(f"📝 Dostępne zatwierdzone tematy: {approved_topics}")
        
        if approved_topics == 0:
            print("❌ Brak zatwierdzonych tematów do publikacji")
            return
        
        # Uruchom workflow engine
        engine = WorkflowEngine()
        
        print("\n🔄 Uruchamiam kompletny workflow automatyzacji...")
        
        # 1. Zarządzanie tematami
        print("1️⃣ Sprawdzanie i zarządzanie tematami...")
        topic_result = engine._execute_topic_management(rule)
        print(f"   Wynik: {'✅ Sukces' if topic_result.get('success') else '❌ Błąd'}")
        if not topic_result.get('success'):
            print(f"   Błąd: {topic_result.get('error', 'Nieznany błąd')}")
        
        # 2. Wybór tematu i generowanie treści
        print("\n2️⃣ Wybór tematu do artykułu...")
        selected_topic = engine._select_topic_for_article(rule)
        
        if not selected_topic:
            print("   ❌ Nie udało się wybrać tematu")
            return False
            
        print(f"   ✅ Wybrany temat: {selected_topic.title}")
        print(f"   📂 Kategoria: {selected_topic.category}")
        
        print("\n3️⃣ Generowanie treści artykułu...")
        content_result = engine._execute_content_generation(rule, selected_topic)
        print(f"   Wynik: {'✅ Sukces' if content_result.get('success') else '❌ Błąd'}")
        
        if content_result.get('success'):
            article = content_result.get('article')
            print(f"   📄 Tytuł: {article.title}")
            print(f"   📊 Długość: {len(article.content)} znaków")
            print(f"   🆔 ID artykułu: {article.id}")
            
            # 4. Pozyskiwanie obrazów
            print("\n4️⃣ Pozyskiwanie obrazów...")
            image_result = engine._execute_image_acquisition(article)
            print(f"   Wynik: {'✅ Sukces' if image_result.get('success') else '❌ Błąd'}")
            if image_result.get('success'):
                print(f"   🖼️ Znaleziono obrazów: {image_result.get('images_found', 0)}")
            
            # 5. Publikacja na WordPress
            print("\n5️⃣ Publikacja na WordPress...")
            publish_result = engine._execute_wordpress_publishing(article, rule)
            print(f"   Wynik: {'✅ Sukces' if publish_result.get('success') else '❌ Błąd'}")
            
            if publish_result.get('success'):
                post_id = publish_result.get('post_id')
                category_assigned = publish_result.get('category_assigned')
                tags_assigned = publish_result.get('tags_assigned', 0)
                featured_image = publish_result.get('featured_image')
                
                print(f"   🆔 WordPress Post ID: {post_id}")
                print(f"   🏷️ Kategoria ID: {category_assigned}")
                print(f"   🔖 Tagi: {tags_assigned} przypisanych")
                print(f"   🖼️ Featured image: {'✅ Tak' if featured_image else '❌ Nie'}")
                print(f"   🌐 URL: https://mamatestuje.com/?p={post_id}")
                
                # 6. Social media (opcjonalnie)
                print("\n6️⃣ Publikacja w social media...")
                print(f"   ⚠️ Social media: Funkcja w rozwoju")
                
                print(f"\n🎉 SUKCES! Artykuł '{article.title}' został w pełni zautomatyzowany!")
                print("🔍 Sprawdź WordPress aby zweryfikować metadane")
                
                return True
            else:
                print(f"   ❌ Błąd publikacji: {publish_result.get('error', 'Nieznany błąd')}")
        else:
            print(f"   ❌ Błąd generowania: {content_result.get('error', 'Nieznany błąd')}")
        
        return False

if __name__ == "__main__":
    success = test_full_automation()
    if success:
        print("\n✅ Pełny proces automatyzacji działa poprawnie!")
    else:
        print("\n❌ Proces automatyzacji wymaga naprawy")