#!/usr/bin/env python3
"""
Test nowych danych logowania WordPress
"""

import requests
import base64
import json

def test_wordpress_credentials(username, app_password):
    """Test nowych danych logowania WordPress"""
    
    print(f"🧪 TESTOWANIE DANYCH LOGOWANIA WORDPRESS")
    print("=" * 50)
    
    url = "https://mamatestuje.com"
    
    # Przygotuj autoryzację
    credentials = f'{username}:{app_password}'
    token = base64.b64encode(credentials.encode()).decode('utf-8')
    
    headers = {
        'Authorization': f'Basic {token}',
        'Content-Type': 'application/json'
    }
    
    print(f"👤 Username: {username}")
    print(f"🔑 Password: {app_password[:4]}...")
    
    # Test 1: Sprawdź informacje o użytkowniku
    print(f"\n⏳ TEST 1: Sprawdzenie uprawnień użytkownika...")
    try:
        response = requests.get(f"{url}/wp-json/wp/v2/users/me", headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"   ✅ Użytkownik: {user_data.get('name', 'Nieznany')}")
            print(f"   ✅ Role: {user_data.get('roles', [])}")
            print(f"   ✅ ID: {user_data.get('id', 'Nieznane')}")
            
            # Sprawdź uprawnienia
            capabilities = user_data.get('capabilities', {})
            can_publish = capabilities.get('publish_posts', False)
            can_edit = capabilities.get('edit_posts', False)
            
            print(f"   📝 Może publikować: {'✅ TAK' if can_publish else '❌ NIE'}")
            print(f"   📝 Może edytować: {'✅ TAK' if can_edit else '❌ NIE'}")
            
        else:
            print(f"   ❌ Błąd autoryzacji: {response.status_code}")
            try:
                error = response.json()
                print(f"   💬 Komunikat: {error.get('message', 'Nieznany błąd')}")
            except:
                pass
                
    except Exception as e:
        print(f"   ❌ Błąd połączenia: {str(e)}")
    
    # Test 2: Próba utworzenia testowego posta
    print(f"\n⏳ TEST 2: Próba utworzenia testowego posta...")
    
    test_post = {
        "title": "Test API - USUŃ",
        "content": "<p>To jest testowy post utworzony przez API. Można go usunąć.</p>",
        "status": "draft",
        "categories": [3]  # Planowanie ciąży
    }
    
    try:
        response = requests.post(f"{url}/wp-json/wp/v2/posts", json=test_post, headers=headers, timeout=15)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 201:
            post_data = response.json()
            print(f"   ✅ Post utworzony!")
            print(f"   📝 ID: {post_data.get('id')}")
            print(f"   🔗 URL: {post_data.get('link')}")
            print(f"   📊 Status: {post_data.get('status')}")
            print(f"   🗑️  MOŻNA USUNĄĆ ten testowy post z WordPress Admin")
            
        else:
            print(f"   ❌ Błąd tworzenia posta: {response.status_code}")
            try:
                error = response.json()
                print(f"   💬 Komunikat: {error.get('message', 'Nieznany błąd')}")
                print(f"   🔍 Kod: {error.get('code', 'Nieznany')}")
            except:
                print(f"   💬 Odpowiedź: {response.text[:200]}...")
                
    except Exception as e:
        print(f"   ❌ Błąd żądania: {str(e)}")
    
    print(f"\n📋 PODSUMOWANIE:")
    print(f"   Jeśli Test 1 ✅ i Test 2 ✅ → Uprawnienia naprawione!")
    print(f"   Jeśli Test 1 ❌ → Problem z hasłem aplikacji")
    print(f"   Jeśli Test 1 ✅ ale Test 2 ❌ → Problem z uprawnieniami")

if __name__ == "__main__":
    print("🔧 QUICK TEST - wklej nowe Application Password:")
    print("=" * 50)
    
    # Wprowadź tutaj nowe hasło z WordPress Admin
    NEW_PASSWORD = input("Wklej nowe Application Password: ").strip()
    
    if NEW_PASSWORD and len(NEW_PASSWORD) > 10:
        print(f"\n🧪 Testowanie nowego hasła...")
        test_wordpress_credentials("TomaszKotlinski", NEW_PASSWORD)
    else:
        print("❌ Nie wprowadzono hasła lub jest za krótkie")
        print("\nLub użyj bezpośrednio:")
        print("test_wordpress_credentials('TomaszKotlinski', 'NOWE_HASŁO')")