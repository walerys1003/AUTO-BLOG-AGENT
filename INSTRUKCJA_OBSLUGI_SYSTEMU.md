# 📘 MASTER AGENT AI - Pełna Instrukcja Obsługi Systemu

## 🎯 CO TO JEST?

**MASTER AGENT AI** to inteligentny system do automatycznego tworzenia i publikowania artykułów na blogach WordPress. System działa 24/7 i samodzielnie:
- Wymyśla tematy artykułów
- Pisze długie artykuły (2400+ słów)
- Znajduje obrazy
- Dodaje tagi SEO
- Publikuje na WordPress
- Udostępnia w mediach społecznościowych

---

## 🖥️ FRONTEND (To co widzisz na ekranie)

### 1. **Dashboard (Pulpit główny)**
Pierwszy ekran po zalogowaniu pokazuje:
- Liczbę blogów (ile blogów obsługujesz)
- Ile artykułów już opublikowano
- Ile tematów czeka w kolejce
- Harmonogram publikacji na dziś

### 2. **Blogs (Zarządzanie blogami)**
Tutaj dodajesz swoje blogi WordPress:
- Nazwa bloga (np. "MamaTestuje")
- Adres URL (np. "https://mamatestuje.pl")
- Dane logowania do WordPress (nazwa użytkownika + token API)
- Wybór kategorii

**Co możesz robić:**
- Dodać nowy blog
- Edytować istniejący blog
- Włączyć/wyłączyć blog
- Synchronizować kategorie z WordPress

### 3. **Topics (Tematy artykułów)**
Miejsce do generowania pomysłów na artykuły:
- Wybierasz blog
- Wybierasz kategorię (np. "Akcesoria dziecięce")
- Możesz dodać słowa kluczowe
- System wygeneruje 5-20 tematów PO POLSKU

**Wszystkie tematy są po polsku!** System wie, że piszesz dla polskich czytelników.

### 4. **Content Creator (Tworzenie artykułów)**

**Prosty edytor:**
- Wpisujesz tytuł
- Wybierasz blog i kategorię
- Klikasz "Generuj artykuł"
- System tworzy gotowy artykuł z obrazami

**Zaawansowany kreator:**
- Więcej opcji kontroli
- Wybór długości artykułu
- Możliwość edycji przed publikacją

### 5. **Schedule Calendar (Kalendarz publikacji)**
Zobacz kiedy artykuły będą publikowane:
- Jutro rano: MamaTestuje - 4 artykuły (07:00)
- Jutro rano: ZnaneKosmetyki - 3 artykuły (08:00)
- Jutro rano: HomosOnly - 2 artykuły (09:00)

### 6. **Pending Articles (Artykuły oczekujące)**
Lista artykułów gotowych do publikacji:
- Możesz je przejrzeć
- Edytować
- Zatwierdzić do publikacji
- Usunąć jeśli nie pasują

### 7. **Logs (Historia działań)**
Pełna historia co system robił:
- Kiedy wygenerował artykuł
- Kiedy opublikował
- Czy były błędy
- Jakie obrazy dodał

### 8. **Social Media**
Zarządzanie kontami społecznościowymi:
- Facebook
- Twitter/X
- LinkedIn
- Instagram
- TikTok

Możesz podłączyć konta i system automatycznie udostępni artykuły.

### 9. **SEO Tools (Narzędzia SEO)**
Analiza i optymalizacja:
- Trendy Google (co ludzie szukają)
- Analiza słów kluczowych
- Podpowiedzi jak poprawić artykuły

### 10. **Images (Biblioteka obrazów)**
Wszystkie obrazy użyte w artykułach:
- Skąd pochodzą (Unsplash, Google)
- Do jakich artykułów zostały dodane
- Możliwość ponownego użycia

### 11. **Publishing Dashboard (Panel publikacji)**
Kontroluj proces publikacji:
- Status każdego artykułu
- Czy został opublikowany
- Link do opublikowanego artykułu na WordPress

---

## ⚙️ BACKEND (Co dzieje się w tle)

### 1. **Automatyzacja treści**

**Workflow Engine (Silnik pracy):**
System działa według schematu:
```
KROK 1: Wymyśl temat
    ↓
KROK 2: Wygeneruj artykuł (2400+ słów)
    ↓
KROK 3: Znajdź obrazy (3 obrazy)
    ↓
KROK 4: Dodaj featured image (obraz główny)
    ↓
KROK 5: Wygeneruj tagi SEO (6 tagów)
    ↓
KROK 6: Opublikuj na WordPress
    ↓
KROK 7: Udostępnij w social media
```

**Harmonogram (Scheduler):**
- Codziennie o 07:00 (czas polski) → MamaTestuje generuje 4 artykuły
- Codziennie o 08:00 (czas polski) → ZnaneKosmetyki generuje 3 artykuły
- Codziennie o 09:00 (czas polski) → HomosOnly generuje 2 artykuły

**Recovery System (System naprawczy):**
Jeśli coś pójdzie nie tak (brak internetu, błąd API):
- System spróbuje ponownie za 5 minut
- Zapisze błąd do logów
- Powiadomi administratora

### 2. **Generator artykułów (Article Generator)**

**Sztuczna inteligencja:**
Używa modeli AI (Claude 3.5 Sonnet) przez OpenRouter API.

**Proces tworzenia artykułu:**
1. Otrzymuje temat (np. "Jak wybrać wózek dla dziecka")
2. Generuje strukturę artykułu (nagłówki)
3. Pisze każdy akapit osobno (długie, szczegółowe akapity)
4. Dba o naturalny język polski
5. Dodaje wnioski i podsumowanie
6. Wynik: 2400-3000 słów (4 strony A4)

**Jakość:**
- Naturalne zdania (nie robotyczne)
- Poprawna polska gramatyka
- Przydatne informacje
- SEO-friendly (przyjazne dla Google)

### 3. **Wyszukiwanie obrazów (Image Finder)**

**Źródła obrazów:**
- **Unsplash** (darmowe profesjonalne zdjęcia)
- **Google Images** (wyszukiwarka obrazów)
- **Pexels** (darmowe zdjęcia)

**Jak to działa:**
1. System analizuje tytuł artykułu
2. Wyciąga kluczowe słowa (np. "wózek", "dziecko")
3. Szuka obrazów pasujących do tematu
4. Wybiera 3 najlepsze obrazy
5. Pierwszy obraz = featured image (obraz główny w WordPress)

### 4. **Publikacja WordPress (WordPress Publisher)**

**Co robi:**
- Łączy się z Twoim blogiem WordPress przez API
- Tworzy nowy post
- Dodaje tytuł, treść, kategorię
- Uploaduje featured image
- Dodaje tagi SEO (6 tagów)
- Publikuje automatycznie LUB zapisuje jako draft

**Rotacja autorów:**
System automatycznie przypisuje artykuły do różnych autorów w WordPress:
- Autor 1 → artykuł o wózkach
- Autor 2 → artykuł o zabawkach
- Autor 3 → artykuł o ubrankach
(rotacja cykliczna)

### 5. **SEO Optimization (Optymalizacja SEO)**

**Generator tagów:**
- Analizuje treść artykułu
- Znajduje najważniejsze słowa kluczowe
- Generuje DOKŁADNIE 6 tagów (WordPress limit)
- Przykład: ["wózek dziecięcy", "akcesoria niemowlęce", "bezpieczeństwo", "spacer", "mama", "poradnik"]

**Meta description:**
- Krótki opis artykułu (150-160 znaków)
- Zachęcający do kliknięcia
- Zawiera słowa kluczowe

**Google Trends:**
- Sprawdza co jest popularne w Polsce
- Sugeruje tematy artykułów na podstawie trendów
- Pomaga trafić w zainteresowania czytelników

### 6. **Social Media Automation**

**Automatyczne posty:**
Po opublikowaniu artykułu system:
1. Tworzy skrócony opis (200 znaków)
2. Dodaje link do artykułu
3. Dodaje hashtagi (#MamaTestuje #Poradnik)
4. Publikuje na podłączonych kontach społecznościowych

**Platformy:**
- Facebook → pełny opis + zdjęcie
- Twitter/X → krótki tweet + link
- LinkedIn → profesjonalny post
- Instagram → obraz + hashtagi

---

## 🗄️ BAZY DANYCH (Gdzie są zapisane dane)

System używa **PostgreSQL** (profesjonalna baza danych).

### Tabele w bazie:

#### 1. **Blog (Informacje o blogach)**
```
- id (numer bloga)
- name (nazwa: "MamaTestuje")
- url (adres: "https://mamatestuje.pl")
- api_url (adres API WordPress)
- username (login do WordPress)
- api_token (hasło/token API)
- active (czy blog jest aktywny: TAK/NIE)
- categories (lista kategorii)
```

#### 2. **ContentLog (Historia artykułów)**
```
- id (numer wpisu)
- blog_id (do którego bloga należy)
- title (tytuł artykułu)
- content (pełna treść artykułu)
- status (status: draft/published/failed)
- post_id (numer posta w WordPress)
- category_id (kategoria WordPress)
- tags (tagi SEO - 6 tagów)
- featured_image_data (dane obrazu głównego)
- created_at (kiedy utworzono)
- published_at (kiedy opublikowano)
```

#### 3. **ArticleTopic (Tematy do napisania)**
```
- id (numer tematu)
- blog_id (dla którego bloga)
- category (kategoria)
- topic (temat artykułu)
- status (pending/used/archived)
- created_at (kiedy dodano)
```

#### 4. **Category (Kategorie WordPress)**
```
- id (numer kategorii)
- blog_id (do którego bloga należy)
- name (nazwa: "Akcesoria dziecięce")
- wordpress_id (ID kategorii w WordPress)
```

#### 5. **Tag (Tagi WordPress)**
```
- id (numer taga)
- blog_id (do którego bloga należy)
- name (nazwa taga: "wózek")
- wordpress_id (ID taga w WordPress)
```

#### 6. **ImageLibrary (Biblioteka obrazów)**
```
- id (numer obrazu)
- blog_id (dla którego bloga)
- url (adres obrazu)
- title (tytuł obrazu)
- source (skąd: Unsplash/Google/Pexels)
- tags (słowa kluczowe)
```

#### 7. **SocialAccount (Konta społecznościowe)**
```
- id (numer konta)
- platform (platforma: Facebook/Twitter/LinkedIn)
- name (nazwa konta)
- api_token (token dostępu)
- blog_id (do którego bloga przypisane)
- active (czy aktywne: TAK/NIE)
```

#### 8. **AutomationRule (Reguły automatyzacji)**
```
- id (numer reguły)
- blog_id (dla którego bloga)
- name (nazwa reguły: "Generuj 4 artykuły MamaTestuje")
- category (kategoria artykułów)
- articles_per_day (ile artykułów dziennie: 4)
- schedule_time (godzina: "07:00")
- auto_publish (czy publikować automatycznie: TAK)
- is_active (czy reguła aktywna: TAK/NIE)
```

#### 9. **User (Użytkownicy systemu)**
```
- id (identyfikator użytkownika)
- email (adres email)
- first_name (imię)
- last_name (nazwisko)
```

---

## 🔌 INTEGRACJE (Połączenia z zewnętrznymi usługami)

### 1. **OpenRouter API** 
**Co to jest:** Dostęp do najlepszych modeli AI (Claude 3.5 Sonnet)

**Do czego używamy:**
- Generowanie artykułów
- Generowanie tematów
- Tworzenie tagów SEO
- Pisanie opisów dla social media

**Koszt:** ~$0.50 za artykuł (2400 słów)

### 2. **WordPress REST API**
**Co to jest:** Oficjalny interfejs do zarządzania WordPress

**Do czego używamy:**
- Publikacja artykułów
- Pobieranie kategorii
- Upload obrazów
- Zarządzanie tagami

**Wymagania:** Token API (application password) w WordPress

### 3. **Unsplash API**
**Co to jest:** Darmowa biblioteka profesjonalnych zdjęć

**Do czego używamy:**
- Wyszukiwanie obrazów do artykułów
- Pobieranie wysokiej jakości zdjęć
- Attribution (przypisanie autora)

**Limit:** 50 zapytań/godzinę (wystarczy na 50 artykułów)

### 4. **Google Custom Search API** (opcjonalnie)
**Co to jest:** Wyszukiwarka obrazów Google

**Do czego używamy:**
- Dodatkowe źródło obrazów
- Gdy Unsplash nie ma odpowiedniego zdjęcia

### 5. **Pexels API** (opcjonalnie)
**Co to jest:** Kolejna biblioteka darmowych zdjęć

**Do czego używamy:**
- Alternatywne źródło obrazów
- Większy wybór zdjęć

### 6. **Google Trends**
**Co to jest:** Narzędzie do sprawdzania popularnych wyszukiwań

**Do czego używamy:**
- Znajdowanie popularnych tematów w Polsce
- Sugerowanie artykułów na podstawie trendów
- Optymalizacja słów kluczowych

### 7. **Facebook Graph API** (opcjonalnie)
**Co to jest:** Interfejs do publikowania na Facebooku

**Do czego używamy:**
- Automatyczne posty na fanpage
- Udostępnianie artykułów

### 8. **Twitter/X API** (opcjonalnie)
**Co to jest:** Interfejs do publikowania tweetów

**Do czego używamy:**
- Automatyczne tweety z linkiem do artykułu

---

## 🔄 PEŁNY PROCES GENEROWANIA ARTYKUŁU (KROK PO KROKU)

### **FAZA 1: PRZYGOTOWANIE (Rano o 07:00)**

**Krok 1:** System budzi się
```
[07:00] Scheduler: "Czas na MamaTestuje!"
[07:00] System: "Generuję 4 artykuły dla kategorii: Akcesoria dziecięce"
```

**Krok 2:** Sprawdzenie czy są tematy
```
System sprawdza: Czy są gotowe tematy w bazie?
- TAK → Używa istniejących tematów
- NIE → Generuje nowe tematy
```

---

### **FAZA 2: GENEROWANIE TEMATÓW (jeśli potrzebne)**

**Krok 3:** Generator tematów AI
```
Prompt do AI:
"Wygeneruj 4 tematy artykułów o akcesoriach dziecięcych.
Tematy muszą być po polsku!
Każdy temat powinien nadawać się na artykuł 2400 słów."

AI odpowiada:
1. "Jak wybrać idealny wózek dla dziecka - poradnik dla rodziców"
2. "5 must-have akcesoriów do karmienia niemowląt w 2025"
3. "Bezpieczne noszenie dziecka - ergonomiczne nosidełka i chusty"
4. "Przewodnik po foteliku samochodowym - bezpieczeństwo przede wszystkim"
```

**Krok 4:** Zapisanie tematów
```
System zapisuje tematy do bazy danych:
- Status: "pending" (oczekują na użycie)
- Kategoria: "Akcesoria dziecięce"
- Blog: "MamaTestuje"
```

---

### **FAZA 3: GENEROWANIE PIERWSZEGO ARTYKUŁU**

**Krok 5:** Wybór tematu
```
System bierze pierwszy temat:
"Jak wybrać idealny wózek dla dziecka - poradnik dla rodziców"
```

**Krok 6:** Generowanie struktury artykułu
```
AI tworzy plan artykułu:

## Wstęp
## Co warto wiedzieć przed zakupem wózka?
## Rodzaje wózków - głęboki, spacerowy, wielofunkcyjny
## Na co zwrócić uwagę przy wyborze?
### Bezpieczeństwo
### Wygoda dla dziecka
### Wygoda dla rodzica
### Dostosowanie do stylu życia
## Najpopularniejsze modele 2025
## Budżet - ile kosztuje dobry wózek?
## Akcesoria do wózka
## Podsumowanie
```

**Krok 7:** Pisanie każdego akapitu
```
System pisze akapit po akapicie:

Akapit 1 (Wstęp):
"Wybór pierwszego wózka dla dziecka to jedno z najważniejszych 
decyzji młodych rodziców. Wózek będzie towarzyszył Wam przez 
pierwsze lata życia maluszka, dlatego warto poświęcić czas na 
dokładne przemyślenie zakupu. W tym poradniku przedstawimy 
wszystkie aspekty, które pomogą Wam wybrać idealny wózek..."
(250 słów)

Akapit 2 (Co warto wiedzieć...):
"Przed wyruszeniem do sklepu z wózkami warto zastanowić się 
nad kilkoma kluczowymi kwestiami. Po pierwsze, miejsce 
zamieszkania ma ogromne znaczenie..."
(300 słów)

[... i tak dalej dla każdego punktu]
```

**Krok 8:** Złożenie całości
```
System składa wszystkie akapity w jeden artykuł:
- Tytuł: "Jak wybrać idealny wózek dla dziecka - poradnik dla rodziców"
- Treść: 2450 słów (~ 4 strony A4)
- Nagłówki: H2, H3
- Format: HTML (gotowy do WordPress)
```

---

### **FAZA 4: ZNAJDOWANIE OBRAZÓW**

**Krok 9:** Analiza tematu
```
System wyciąga słowa kluczowe:
- "wózek"
- "dziecko"
- "rodzice"
- "spacer"
```

**Krok 10:** Wyszukiwanie na Unsplash
```
Zapytanie do Unsplash API:
"baby stroller parents"

Unsplash zwraca 10 zdjęć:
1. Zdjęcie wózka w parku (URL: https://unsplash.com/photo/abc123)
2. Mama z wózkiem (URL: https://unsplash.com/photo/def456)
3. Wózek wielofunkcyjny (URL: https://unsplash.com/photo/ghi789)
...
```

**Krok 11:** Wybór 3 najlepszych obrazów
```
System analizuje każde zdjęcie:
- Jakość: wysoka rozdzielczość?
- Tematyka: pasuje do artykułu?
- Orientacja: pozioma/pionowa?

Wybrane 3 obrazy:
1. Featured Image (główny) - zdjęcie wózka
2. Obraz 1 - mama z wózkiem
3. Obraz 2 - wózek w akcji
```

**Krok 12:** Upload featured image do WordPress
```
System:
1. Pobiera zdjęcie z Unsplash
2. Uploaduje do WordPress Media Library
3. Otrzymuje Media ID: 2987
4. Przypisuje jako featured image do artykułu
```

---

### **FAZA 5: GENEROWANIE TAGÓW SEO**

**Krok 13:** Analiza treści artykułu
```
AI czyta artykuł i znajduje najważniejsze słowa kluczowe:
- wózek dziecięcy (występuje 15 razy)
- bezpieczeństwo (występuje 8 razy)
- rodzice (występuje 12 razy)
- spacer (występuje 6 razy)
- wielofunkcyjny (występuje 5 razy)
- niemowlę (występuje 10 razy)
```

**Krok 14:** Generowanie 6 tagów
```
System tworzy DOKŁADNIE 6 tagów (WordPress limit):
1. "wózek dziecięcy"
2. "akcesoria niemowlęce"
3. "bezpieczeństwo dziecka"
4. "poradnik dla rodziców"
5. "wybór wózka"
6. "rodzicielstwo"
```

---

### **FAZA 6: PUBLIKACJA NA WORDPRESS**

**Krok 15:** Przygotowanie danych
```
Dane do wysłania:
{
  "title": "Jak wybrać idealny wózek dla dziecka - poradnik dla rodziców",
  "content": "<p>Wybór pierwszego wózka...</p>",
  "status": "publish",
  "categories": [45],  # ID kategorii "Akcesoria dziecięce"
  "tags": [12, 34, 56, 78, 90, 23],  # ID tagów w WordPress
  "featured_media": 2987  # ID featured image
}
```

**Krok 16:** Wysłanie do WordPress
```
POST https://mamatestuje.pl/wp-json/wp/v2/posts
Authorization: Basic [token]

WordPress odpowiada:
{
  "id": 1234,
  "link": "https://mamatestuje.pl/jak-wybrac-idealny-wozek",
  "status": "published"
}
```

**Krok 17:** Zapisanie w bazie danych
```
System zapisuje w ContentLog:
- post_id: 1234
- status: "published"
- published_at: "2025-10-01 07:15:23"
- featured_image_data: {...}
```

---

### **FAZA 7: SOCIAL MEDIA (opcjonalnie)**

**Krok 18:** Przygotowanie posta
```
System tworzy krótki opis:
"🚼 Wybierasz pierwszy wózek dla dziecka? Sprawdź nasz kompletny 
poradnik! Dowiedz się, na co zwrócić uwagę i jak wybrać najlepszy 
model dla Twojej rodziny. 👶

#MamaTestuje #WózekDziecięcy #Rodzicielstwo #PoradnikDlaRodziców

Link: https://mamatestuje.pl/jak-wybrac-idealny-wozek"
```

**Krok 19:** Publikacja na Facebook
```
POST https://graph.facebook.com/v12.0/{page-id}/feed
{
  "message": "🚼 Wybierasz pierwszy wózek...",
  "link": "https://mamatestuje.pl/jak-wybrac-idealny-wozek"
}
```

---

### **FAZA 8: POWTÓRZENIE DLA POZOSTAŁYCH 3 ARTYKUŁÓW**

```
[07:20] Artykuł 2: "5 must-have akcesoriów do karmienia..."
[07:35] Artykuł 3: "Bezpieczne noszenie dziecka..."
[07:50] Artykuł 4: "Przewodnik po foteliku samochodowym..."
[08:05] ✅ UKOŃCZONO: 4 artykuły opublikowane dla MamaTestuje
```

---

### **FAZA 9: NASTĘPNE BLOGI**

```
[08:00] System: "Czas na ZnaneKosmetyki!"
[08:00] Generowanie 3 artykułów dla kategorii: "Akcesoria kosmetyczne"

[09:00] System: "Czas na HomosOnly!"
[09:00] Generowanie 2 artykułów dla kategorii: "Aktualności"

[09:30] ✅ WSZYSTKO GOTOWE: 9 artykułów opublikowanych dzisiaj
```

---

## 📊 MONITORING I KONTROLA

### **Logi (Historia działań)**
```
[2025-10-01 07:00:15] INFO: Starting article generation for MamaTestuje
[2025-10-01 07:01:23] INFO: Topic generated: "Jak wybrać idealny wózek..."
[2025-10-01 07:05:45] INFO: Article content generated (2450 words)
[2025-10-01 07:08:12] INFO: Found 3 images from Unsplash
[2025-10-01 07:09:34] INFO: Featured image uploaded to WordPress (ID: 2987)
[2025-10-01 07:10:56] INFO: Generated 6 SEO tags
[2025-10-01 07:12:23] SUCCESS: Article published (Post ID: 1234)
[2025-10-01 07:13:45] INFO: Shared on Facebook
```

### **Statystyki**
```
Dzisiaj:
- Wygenerowano: 9 artykułów
- Opublikowano: 9 artykułów
- Błędów: 0
- Obrazów dodanych: 27
- Tagów SEO: 54

Ten miesiąc:
- Wygenerowano: 270 artykułów
- Słów napisanych: 648,000
- Kosztów AI: $135
```

---

## 🔧 KONFIGURACJA (Jak skonfigurować system)

### **KROK 1: Dodaj blog WordPress**

1. W menu wybierz **Blogs**
2. Kliknij **"Dodaj nowy blog"**
3. Wypełnij formularz:
   ```
   Nazwa: MamaTestuje
   URL: https://mamatestuje.pl
   API URL: https://mamatestuje.pl/wp-json/wp/v2
   Username: admin
   API Token: [wklej token z WordPress]
   ```
4. Kliknij **"Zapisz"**

### **KROK 2: Synchronizuj kategorie**

1. Przy blogu kliknij **"Synchronizuj kategorie"**
2. System pobierze wszystkie kategorie z WordPress
3. Wybierz kategorie, które chcesz używać

### **KROK 3: Dodaj regułę automatyzacji**

1. W menu wybierz **"Automation Rules"**
2. Kliknij **"Dodaj nową regułę"**
3. Wypełnij:
   ```
   Nazwa: Generuj artykuły MamaTestuje
   Blog: MamaTestuje
   Kategoria: Akcesoria dziecięce
   Ilość artykułów: 4
   Godzina: 07:00
   Auto-publikacja: TAK
   Aktywna: TAK
   ```
4. Kliknij **"Zapisz"**

### **KROK 4: Gotowe!**

System będzie teraz automatycznie:
- Generował 4 artykuły codziennie o 07:00
- Publikował je na MamaTestuje.pl
- Dodawał obrazy i tagi SEO

---

## 🆘 ROZWIĄZYWANIE PROBLEMÓW

### **Problem: Artykuły nie są publikowane**

**Sprawdź:**
1. Czy blog jest aktywny? (Blogs → Edit → Active: YES)
2. Czy reguła automatyzacji jest aktywna? (Automation Rules → Active: YES)
3. Czy token WordPress jest prawidłowy?
4. Sprawdź logi (Logs) czy są błędy

### **Problem: Obrazy nie są dodawane**

**Sprawdź:**
1. Czy API Unsplash działa? (Logs → "Unsplash API")
2. Czy WordPress przyjmuje upload obrazów?
3. Czy masz odpowiednie uprawnienia w WordPress?

### **Problem: Tematy po angielsku zamiast po polsku**

**Rozwiązanie:**
- To zostało naprawione w najnowszej wersji
- Jeśli nadal występuje: skontaktuj się z administratorem

### **Problem: Błąd "Failed to publish"**

**Przyczyny:**
1. Nieprawidłowy token WordPress
2. Kategoria nie istnieje w WordPress
3. Brak połączenia z internetem
4. WordPress wymaga zatwierdzenia administratora

**Rozwiązanie:**
1. Sprawdź token w WordPress (Users → Application Passwords)
2. Sprawdź czy kategoria istnieje
3. Sprawdź logi dla szczegółów błędu

---

## 💰 KOSZTY

### **Miesięczne koszty** (dla 9 artykułów dziennie):

1. **OpenRouter API (AI):**
   - 270 artykułów × $0.50 = **$135/miesiąc**

2. **Unsplash API:**
   - **Darmowe** (limit: 50 zapytań/godzinę)

3. **WordPress Hosting:**
   - To Twój koszt (niezależny od systemu)

4. **Replit Hosting:**
   - Darmowy plan: **$0**
   - Plan Hacker: **$7/miesiąc** (szybszy, 24/7)
   - Plan Pro: **$25/miesiąc** (najszybszy)

**Razem:** około **$135-160/miesiąc** dla 270 artykułów

**Koszt za artykuł:** ~$0.50

---

## 📈 MOŻLIWOŚCI ROZBUDOWY

### **Co można jeszcze dodać:**

1. **Więcej blogów**
   - Dodaj 5, 10, 20 blogów
   - Każdy blog może mieć własny harmonogram

2. **Newsletter**
   - Automatyczne wysyłanie najnowszych artykułów mailem
   - Integracja z Mailchimp/SendGrid

3. **Analytics**
   - Śledzenie ile osób czyta artykuły
   - Które artykuły są najpopularniejsze
   - Google Analytics 4 integration

4. **Video Content**
   - Generowanie krótkich video z artykułu
   - Publikacja na YouTube/TikTok

5. **Tłumaczenia**
   - Automatyczne tłumaczenie artykułów na inne języki
   - Publikacja na blogach w różnych językach

---

## 🎓 PODSUMOWANIE DLA LAIKA

**Czym jest MASTER AGENT AI?**
To robot, który pisze artykuły na Twoje blogi. Pracuje 24/7 bez przerw.

**Co robi?**
1. Wymyśla tematy artykułów
2. Pisze długie artykuły (2400 słów)
3. Znajduje obrazy
4. Publikuje na WordPress
5. Udostępnia w social media

**Jak to działa?**
- Rano (07:00, 08:00, 09:00) system budzi się
- Generuje artykuły dla każdego bloga
- Publikuje automatycznie
- Wszystko samo, bez Twojej interwencji

**Co musisz zrobić?**
1. Dodać swoje blogi WordPress
2. Wybrać kategorie
3. Ustawić harmonogram
4. Gotowe - system działa sam

**Ile to kosztuje?**
- ~$0.50 za jeden artykuł
- ~$135/miesiąc dla 270 artykułów (9 dziennie)

**Czy to bezpieczne?**
- TAK - system używa oficjalnych API
- Twoje hasła są szyfrowane
- Możesz wyłączyć auto-publikację i sprawdzać artykuły ręcznie

**Czy to działa na moim blogu WordPress?**
- TAK - działa z każdym blogiem WordPress
- Wymaga tylko tokenu API (5 minut setup)

---

## 📞 WSPARCIE

**Gdzie szukać pomocy:**
1. **Logs** - historia wszystkich działań
2. **Dashboard** - status systemu
3. **Dokumentacja** - ten plik

**Typowe pytania:**
- "Jak dodać nowy blog?" → Sekcja Konfiguracja
- "Dlaczego artykuł nie został opublikowany?" → Sekcja Rozwiązywanie Problemów
- "Jak zmienić harmonogram?" → Automation Rules → Edit

---

**Wersja dokumentacji:** 1.0  
**Data aktualizacji:** 01.10.2025  
**System:** MASTER AGENT AI v2.0

**Powodzenia z automatyzacją! 🚀**
