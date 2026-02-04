# 📚 MASTER AGENT AI - Hiperszczegółowa Dokumentacja Techniczna

**Data utworzenia:** 21 listopada 2025  
**Wersja systemu:** 2.1  
**Status automatyzacji:** WYŁĄCZONY (tylko manualne generowanie)

---

# SPIS TREŚCI

1. [Architektura systemu](#1-architektura-systemu)
2. [Stos technologiczny](#2-stos-technologiczny)
3. [Struktura plików projektu](#3-struktura-plików-projektu)
4. [Moduł generowania artykułów](#4-moduł-generowania-artykułów)
5. [Moduł wyszukiwania obrazów](#5-moduł-wyszukiwania-obrazów)
6. [Moduł publikacji WordPress](#6-moduł-publikacji-wordpress)
7. [Moduł SEO i tagów](#7-moduł-seo-i-tagów)
8. [Moduł automatyzacji i harmonogramowania](#8-moduł-automatyzacji-i-harmonogramowania)
9. [Workflow Engine - silnik przepływu pracy](#9-workflow-engine---silnik-przepływu-pracy)
10. [Baza danych - struktura i relacje](#10-baza-danych---struktura-i-relacje)
11. [API i integracje zewnętrzne](#11-api-i-integracje-zewnętrzne)
12. [Panel administracyjny - frontend](#12-panel-administracyjny---frontend)
13. [Obsługa błędów i mechanizmy naprawcze](#13-obsługa-błędów-i-mechanizmy-naprawcze)
14. [Konfiguracja blogów](#14-konfiguracja-blogów)
15. [Pełny przepływ generowania artykułu](#15-pełny-przepływ-generowania-artykułu)
16. [Ostatnie poprawki i zmiany](#16-ostatnie-poprawki-i-zmiany)

---

# 1. ARCHITEKTURA SYSTEMU

## 1.1 Ogólny schemat architektury

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MASTER AGENT AI                                    │
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │   FRONTEND   │    │   BACKEND    │    │   BAZA       │                   │
│  │   (Flask)    │◄──►│   (Python)   │◄──►│   DANYCH     │                   │
│  │   Jinja2     │    │              │    │ (PostgreSQL) │                   │
│  │   Bootstrap  │    │              │    │              │                   │
│  └──────────────┘    └──────────────┘    └──────────────┘                   │
│         │                   │                                                │
│         │                   ▼                                                │
│         │      ┌────────────────────────┐                                   │
│         │      │   INTEGRACJE ZEWNĘTRZNE │                                  │
│         │      │                          │                                  │
│         │      │  ┌─────────────────────┐ │                                 │
│         │      │  │ OpenRouter API      │ │  ◄── Generowanie AI             │
│         │      │  │ (Claude Haiku 4.5)  │ │                                 │
│         │      │  └─────────────────────┘ │                                 │
│         │      │                          │                                  │
│         │      │  ┌─────────────────────┐ │                                 │
│         │      │  │ Unsplash API        │ │  ◄── Obrazy                     │
│         │      │  └─────────────────────┘ │                                 │
│         │      │                          │                                  │
│         │      │  ┌─────────────────────┐ │                                 │
│         │      │  │ WordPress REST API  │ │  ◄── Publikacja                 │
│         │      │  └─────────────────────┘ │                                 │
│         │      │                          │                                  │
│         │      │  ┌─────────────────────┐ │                                 │
│         │      │  │ Google Trends       │ │  ◄── SEO/Trendy                 │
│         │      │  └─────────────────────┘ │                                 │
│         │      └────────────────────────┘                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 1.2 Przepływ danych

```
UŻYTKOWNIK                    SYSTEM                         ZEWNĘTRZNE API
    │                            │                                │
    │  1. Żądanie generowania    │                                │
    │ ─────────────────────────► │                                │
    │                            │  2. Generuj treść              │
    │                            │ ─────────────────────────────► │ OpenRouter
    │                            │                                │
    │                            │ ◄───────────────────────────── │
    │                            │  3. Treść artykułu             │
    │                            │                                │
    │                            │  4. Szukaj obrazów             │
    │                            │ ─────────────────────────────► │ Unsplash
    │                            │                                │
    │                            │ ◄───────────────────────────── │
    │                            │  5. Lista obrazów              │
    │                            │                                │
    │                            │  6. Publikuj artykuł           │
    │                            │ ─────────────────────────────► │ WordPress
    │                            │                                │
    │                            │ ◄───────────────────────────── │
    │                            │  7. Post ID                    │
    │                            │                                │
    │ ◄───────────────────────── │  8. Sukces                     │
    │                            │                                │
```

---

# 2. STOS TECHNOLOGICZNY

## 2.1 Backend

| Komponent | Technologia | Wersja | Opis |
|-----------|-------------|--------|------|
| Framework webowy | Flask | 2.3.x | Główny framework aplikacji |
| ORM | SQLAlchemy | 2.0.x | Mapowanie obiektowo-relacyjne |
| Baza danych | PostgreSQL | 15.x | Produkcyjna baza danych (Neon) |
| Scheduler | APScheduler | 3.10.x | Harmonogramowanie zadań |
| HTTP Client | Requests | 2.31.x | Komunikacja z API |
| Walidacja | WTForms | 3.1.x | Walidacja formularzy |
| Autentykacja | Flask-Login | 0.6.x | Zarządzanie sesjami użytkowników |

## 2.2 Frontend

| Komponent | Technologia | Wersja | Opis |
|-----------|-------------|--------|------|
| Szablony | Jinja2 | 3.1.x | System szablonów HTML |
| CSS Framework | Bootstrap | 5.3.2 | Responsywny UI |
| Ikony | Font Awesome | 6.4.0 | Biblioteka ikon |
| JavaScript | Vanilla JS | ES6+ | Interakcje użytkownika |
| Kolorystyka | Consist UI | - | Spójny schemat kolorów |

## 2.3 Integracje zewnętrzne

| Serwis | Typ | Użycie |
|--------|-----|--------|
| OpenRouter API | AI/LLM | Generowanie treści artykułów |
| Anthropic Claude Haiku 4.5 | Model AI | Główny model do pisania |
| Unsplash API | Obrazy | Darmowe profesjonalne zdjęcia |
| Google Custom Search | Obrazy | Alternatywne źródło obrazów |
| Pexels API | Obrazy | Trzecie źródło obrazów |
| WordPress REST API | CMS | Publikacja artykułów |
| Google Trends | SEO | Analiza trendów wyszukiwania |

---

# 3. STRUKTURA PLIKÓW PROJEKTU

## 3.1 Główna struktura katalogów

```
projekt/
│
├── main.py                          # Punkt wejścia aplikacji
├── app.py                           # Konfiguracja Flask i SQLAlchemy
├── models.py                        # Definicje modeli bazy danych
├── routes.py                        # Wszystkie endpointy HTTP
│
├── utils/                           # Moduły pomocnicze
│   ├── __init__.py
│   │
│   ├── ai_content_strategy/         # Strategia generowania treści AI
│   │   ├── __init__.py
│   │   ├── article_generator.py     # GŁÓWNY GENERATOR ARTYKUŁÓW
│   │   ├── topic_generator.py       # Generator tematów
│   │   └── seo_optimizer.py         # Optymalizacja SEO
│   │
│   ├── content/                     # Adaptery AI
│   │   ├── __init__.py
│   │   ├── ai_adapter.py            # Adapter OpenRouter API
│   │   └── mock_adapter.py          # Adapter testowy (mock)
│   │
│   ├── images/                      # Obsługa obrazów
│   │   ├── __init__.py
│   │   ├── auto_image_finder.py     # WYSZUKIWANIE OBRAZÓW
│   │   ├── unsplash_service.py      # Integracja Unsplash
│   │   ├── google_images.py         # Integracja Google Images
│   │   └── pexels_service.py        # Integracja Pexels
│   │
│   ├── automation/                  # Automatyzacja
│   │   ├── __init__.py
│   │   ├── scheduler.py             # HARMONOGRAM (WYŁĄCZONY)
│   │   └── workflow_engine.py       # SILNIK PRZEPŁYWU PRACY
│   │
│   ├── wordpress/                   # Integracja WordPress
│   │   ├── __init__.py
│   │   ├── api_client.py            # Klient REST API WordPress
│   │   └── publisher.py             # PUBLIKACJA ARTYKUŁÓW
│   │
│   └── seo/                         # Narzędzia SEO
│       ├── __init__.py
│       ├── trends.py                # Google Trends
│       ├── keywords.py              # Analiza słów kluczowych
│       └── monkey_patch.py          # Poprawki kompatybilności
│
├── templates/                       # Szablony HTML (Jinja2)
│   ├── base.html                    # Szablon bazowy
│   ├── dashboard.html               # Pulpit główny
│   ├── blogs.html                   # Zarządzanie blogami
│   ├── topics.html                  # Tematy artykułów
│   ├── content_creator.html         # Kreator treści
│   ├── schedule.html                # Kalendarz publikacji
│   ├── pending_articles.html        # Artykuły oczekujące
│   ├── logs.html                    # Historia działań
│   └── ...                          # Pozostałe szablony
│
├── static/                          # Pliki statyczne
│   ├── css/                         # Style CSS
│   ├── js/                          # Skrypty JavaScript
│   └── images/                      # Obrazy statyczne
│
├── INSTRUKCJA_OBSLUGI_SYSTEMU.md    # Instrukcja obsługi
├── DOKUMENTACJA_TECHNICZNA_HIPERSZCZEGOLOWA.md  # Ten dokument
└── replit.md                        # Konfiguracja projektu
```

## 3.2 Kluczowe pliki i ich funkcje

### main.py
```python
# Punkt wejścia - importuje aplikację Flask
from app import app

# WYŁĄCZONE: Automatyczny scheduler
# from utils.automation.scheduler import start_automation_scheduler
# with app.app_context():
#     start_automation_scheduler()
```

### app.py
```python
# Konfiguracja Flask
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")

# Konfiguracja bazy danych PostgreSQL
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")

# Inicjalizacja SQLAlchemy
db = SQLAlchemy(model_class=Base)
db.init_app(app)
```

---

# 4. MODUŁ GENEROWANIA ARTYKUŁÓW

## 4.1 Lokalizacja pliku
**Plik:** `utils/ai_content_strategy/article_generator.py`

## 4.2 Główna klasa: ArticleGenerator

```python
class ArticleGenerator:
    """
    Generator artykułów wykorzystujący AI do tworzenia treści.
    
    Atrybuty:
        ai_adapter: Adapter do komunikacji z API AI (OpenRouter)
        blog_config: Konfiguracja bloga (długość, styl, kategorie)
        timeout: Maksymalny czas generowania (domyślnie 600 sekund = 10 minut)
    """
```

## 4.3 Proces generowania artykułu - krok po kroku

### KROK 1: Inicjalizacja generatora
```python
generator = ArticleGenerator(
    ai_adapter=OpenRouterAdapter(),
    blog_config={
        'name': 'MamaTestuje',
        'min_words': 2000,
        'max_words': 2500,
        'language': 'pl',
        'style': 'informacyjny, przyjazny'
    }
)
```

### KROK 2: Przygotowanie promptu dla AI
```python
def _prepare_article_prompt(self, topic, category):
    """
    Tworzy szczegółowy prompt dla modelu AI.
    
    Prompt zawiera:
    - Temat artykułu
    - Kategorię
    - Wymaganą długość (min. 1200 słów)
    - Styl pisania
    - Strukturę (wstęp, 5 sekcji, podsumowanie)
    - Wymagania SEO
    """
    return f"""
    Napisz profesjonalny artykuł blogowy na temat: "{topic}"
    Kategoria: {category}
    
    WYMAGANIA:
    1. Język: Polski
    2. Długość: minimum 1200 słów (4 strony A4)
    3. Struktura:
       - Wstęp (150-200 słów)
       - 5 głównych sekcji z nagłówkami H2 (każda 200-250 słów)
       - Podsumowanie (150-200 słów)
    4. Styl: profesjonalny, ale przystępny
    5. Formatowanie: HTML z nagłówkami H2, H3, listami
    6. Każde zdanie musi być kompletne
    7. Używaj naturalnego języka polskiego
    ...
    """
```

### KROK 3: Generowanie wielosekcyjne (7 wywołań AI)
```python
def generate_article(self, topic, category):
    """
    Generuje artykuł w 7 etapach:
    
    1. WSTĘP - wprowadzenie do tematu
    2. SEKCJA 1 - pierwsza główna część
    3. SEKCJA 2 - druga główna część
    4. SEKCJA 3 - trzecia główna część
    5. SEKCJA 4 - czwarta główna część
    6. SEKCJA 5 - piąta główna część
    7. PODSUMOWANIE - wnioski końcowe
    
    Każde wywołanie AI:
    - Timeout: 120 sekund
    - Model: anthropic/claude-haiku-4.5
    - Max tokens: 4000
    - Temperature: 0.7
    """
    
    sections = []
    
    # Generuj wstęp
    intro = self._generate_section("wstęp", topic, category)
    sections.append(intro)
    
    # Generuj 5 sekcji głównych
    for i in range(1, 6):
        section = self._generate_section(f"sekcja_{i}", topic, category)
        sections.append(section)
    
    # Generuj podsumowanie
    conclusion = self._generate_section("podsumowanie", topic, category)
    sections.append(conclusion)
    
    # Złóż wszystkie sekcje
    full_article = self._combine_sections(sections)
    
    return full_article
```

### KROK 4: Mechanizm retry z exponential backoff
```python
def _generate_with_retry(self, prompt, max_attempts=3):
    """
    Mechanizm ponawiania przy błędach API.
    
    Opóźnienia między próbami:
    - Próba 1: natychmiast
    - Próba 2: po 2 sekundach
    - Próba 3: po 5 sekundach
    - Próba 4: po 12 sekundach (jeśli włączone)
    
    Obsługiwane błędy:
    - Rate limiting (429)
    - Timeout
    - Connection errors
    - API errors
    """
    delays = [0, 2, 5, 12]
    
    for attempt in range(max_attempts):
        try:
            if attempt > 0:
                time.sleep(delays[attempt])
                logging.info(f"Retry attempt {attempt + 1}/{max_attempts}")
            
            response = self.ai_adapter.generate(prompt)
            return response
            
        except RateLimitError:
            logging.warning(f"Rate limit hit, waiting {delays[attempt + 1]}s")
            continue
            
        except Exception as e:
            logging.error(f"Generation error: {e}")
            if attempt == max_attempts - 1:
                raise  # Re-raise na ostatniej próbie
            continue
    
    raise GenerationError("All retry attempts failed")
```

### KROK 5: Walidacja i czyszczenie treści
```python
def _validate_and_clean(self, content):
    """
    Walidacja wygenerowanej treści.
    
    Sprawdza:
    1. Czy treść ma minimum 1200 słów
    2. Czy zawiera wymagane nagłówki H2
    3. Czy wszystkie zdania są kompletne (kończą się na . ! ?)
    4. Czy tagi HTML są poprawnie zamknięte
    5. Czy nie ma placeholderów [...] lub TODO
    
    Czyści:
    1. Usuwa nadmiarowe białe znaki
    2. Naprawia niezamknięte tagi HTML
    3. Uzupełnia zdania bez kropek
    """
    
    # Sprawdź liczbę słów
    word_count = len(content.split())
    if word_count < 1200:
        raise ValidationError(f"Article too short: {word_count} words")
    
    # Sprawdź kompletność zdań
    if not self._check_sentence_completion(content):
        content = self._fix_incomplete_sentences(content)
    
    # Sprawdź tagi HTML
    content = self._fix_html_tags(content)
    
    return content
```

## 4.4 Konfiguracja modelu AI

```python
# Konfiguracja OpenRouter API
AI_CONFIG = {
    'model': 'anthropic/claude-haiku-4.5',
    'max_tokens': 4000,
    'temperature': 0.7,
    'top_p': 0.9,
    'frequency_penalty': 0.3,
    'presence_penalty': 0.3
}

# Koszty modelu
# Input: $0.25 / 1M tokens
# Output: $1.25 / 1M tokens
# Średni koszt artykułu: ~$0.01-0.10
```

## 4.5 Obsługa błędów

```python
# KRYTYCZNA POPRAWKA (Nov 20, 2025):
# System NIE używa już fallback content!
# Każdy błąd jest logowany z pełnym traceback i re-raised

try:
    article = generator.generate_article(topic, category)
except Exception as e:
    # Loguj pełny traceback
    logging.error(f"Article generation failed: {e}")
    logging.error(traceback.format_exc())
    
    # NIE generuj placeholder content!
    # raise zamiast return fallback
    raise ArticleGenerationError(f"Failed to generate article: {e}")
```

---

# 5. MODUŁ WYSZUKIWANIA OBRAZÓW

## 5.1 Lokalizacja pliku
**Plik:** `utils/images/auto_image_finder.py`

## 5.2 Główna klasa: AutoImageFinder

```python
class AutoImageFinder:
    """
    Automatycznie wyszukuje i pobiera obrazy do artykułów.
    
    Źródła obrazów (w kolejności priorytetów):
    1. Unsplash (darmowe, wysokiej jakości)
    2. Pexels (darmowe, alternatywa)
    3. Google Images (gdy poprzednie nie znajdą)
    
    Atrybuty:
        unsplash_client: Klient Unsplash API
        pexels_client: Klient Pexels API
        google_client: Klient Google Custom Search
    """
```

## 5.3 Proces wyszukiwania obrazów

### KROK 1: Ekstrakcja słów kluczowych z tytułu
```python
def _extract_keywords(self, title):
    """
    Wyciąga słowa kluczowe z tytułu artykułu.
    
    Przykład:
    Input: "Jak wybrać idealny wózek dla dziecka - poradnik dla rodziców"
    Output: ["wózek", "dziecko", "rodzice", "poradnik"]
    
    Proces:
    1. Usuń stop words (jak, dla, i, w, na, do, ...)
    2. Lemmatyzacja (wózka → wózek)
    3. Wybierz 3-5 najważniejszych słów
    """
    
    stop_words = ['jak', 'dla', 'w', 'na', 'do', 'i', 'lub', 'czy', 'to', 'ten', 'ta']
    
    words = title.lower().split()
    keywords = [w for w in words if w not in stop_words and len(w) > 3]
    
    return keywords[:5]
```

### KROK 2: Tłumaczenie na angielski (dla API)
```python
def _translate_to_english(self, keywords):
    """
    Tłumaczy polskie słowa kluczowe na angielski.
    
    Słownik tłumaczeń:
    - wózek → stroller, baby carriage
    - dziecko → child, baby
    - kosmetyki → cosmetics, beauty
    - mama → mother, mom
    - zabawka → toy
    ...
    
    Dlaczego: Unsplash i Pexels lepiej rozumieją angielskie zapytania.
    """
    
    translations = {
        'wózek': 'baby stroller',
        'dziecko': 'baby child',
        'kosmetyki': 'cosmetics beauty',
        'mama': 'mother parenting',
        # ... więcej tłumaczeń
    }
    
    english_keywords = []
    for kw in keywords:
        if kw in translations:
            english_keywords.append(translations[kw])
        else:
            english_keywords.append(kw)
    
    return ' '.join(english_keywords)
```

### KROK 3: Wyszukiwanie na Unsplash
```python
def _search_unsplash(self, query, count=5):
    """
    Wyszukuje obrazy na Unsplash.
    
    Parametry API:
    - query: Zapytanie wyszukiwania
    - per_page: Liczba wyników (max 30)
    - orientation: landscape/portrait/squarish
    - content_filter: high (tylko bezpieczne treści)
    
    Zwraca:
    - Lista URL obrazów
    - Dane autora (attribution)
    - Wymiary obrazu
    """
    
    url = "https://api.unsplash.com/search/photos"
    params = {
        'query': query,
        'per_page': count,
        'orientation': 'landscape',
        'content_filter': 'high'
    }
    headers = {
        'Authorization': f'Client-ID {UNSPLASH_API_KEY}'
    }
    
    response = requests.get(url, params=params, headers=headers)
    data = response.json()
    
    images = []
    for photo in data['results']:
        images.append({
            'url': photo['urls']['regular'],
            'thumb': photo['urls']['thumb'],
            'author': photo['user']['name'],
            'author_url': photo['user']['links']['html'],
            'width': photo['width'],
            'height': photo['height'],
            'description': photo['description'] or photo['alt_description']
        })
    
    return images
```

### KROK 4: Wybór najlepszego obrazu na featured image
```python
def _select_featured_image(self, images):
    """
    Wybiera najlepszy obraz jako featured image.
    
    Kryteria oceny:
    1. Orientacja pozioma (landscape) - preferowana
    2. Rozdzielczość > 1920x1080
    3. Pasuje tematycznie do artykułu
    4. Dobra jakość wizualna
    
    Algorytm:
    1. Filtruj obrazy poziome
    2. Sortuj po rozdzielczości malejąco
    3. Wybierz pierwszy (najlepszy)
    """
    
    # Filtruj poziome obrazy
    landscape = [img for img in images if img['width'] > img['height']]
    
    if not landscape:
        landscape = images  # Użyj wszystkich jeśli brak poziomych
    
    # Sortuj po rozdzielczości
    sorted_images = sorted(landscape, key=lambda x: x['width'] * x['height'], reverse=True)
    
    return sorted_images[0] if sorted_images else None
```

### KROK 5: Obcinanie zbyt długich tytułów (POPRAWKA)
```python
def _truncate_image_title(self, title, max_length=250):
    """
    POPRAWKA z Nov 20, 2025:
    
    Problem: Unsplash czasem zwraca bardzo długie opisy (>255 znaków),
    co powodowało błąd bazy danych (kolumna VARCHAR(255)).
    
    Rozwiązanie: Obcinamy tytuł do 250 znaków + "..."
    """
    
    if title and len(title) > max_length:
        return title[:max_length] + "..."
    return title
```

## 5.4 Integracja z Pexels (alternatywa)

```python
def _search_pexels(self, query, count=5):
    """
    Wyszukuje obrazy na Pexels gdy Unsplash nie znajdzie.
    
    API Pexels:
    - Darmowe z limitem 200 req/hour
    - Wysokiej jakości zdjęcia
    - Dobra alternatywa dla Unsplash
    """
    
    url = "https://api.pexels.com/v1/search"
    params = {
        'query': query,
        'per_page': count,
        'orientation': 'landscape'
    }
    headers = {
        'Authorization': PEXELS_API_KEY
    }
    
    response = requests.get(url, params=params, headers=headers)
    return self._parse_pexels_response(response.json())
```

---

# 6. MODUŁ PUBLIKACJI WORDPRESS

## 6.1 Lokalizacja pliku
**Plik:** `utils/wordpress/publisher.py`

## 6.2 Główna klasa: WordPressPublisher

```python
class WordPressPublisher:
    """
    Publikuje artykuły na WordPress przez REST API.
    
    Funkcje:
    - Tworzenie postów
    - Upload mediów (obrazów)
    - Zarządzanie kategoriami i tagami
    - Rotacja autorów
    - Ustawianie featured image
    
    Atrybuty:
        api_url: URL WordPress REST API (np. https://blog.pl/wp-json/wp/v2)
        username: Nazwa użytkownika WordPress
        app_password: Application Password z WordPress
    """
```

## 6.3 Proces publikacji artykułu

### KROK 1: Autentykacja
```python
def _authenticate(self):
    """
    Autoryzacja do WordPress REST API.
    
    Metoda: HTTP Basic Auth
    Credentials: username:application_password (base64)
    
    Application Password:
    - Tworzony w WordPress: Users → Profile → Application Passwords
    - Format: xxxx xxxx xxxx xxxx xxxx xxxx
    - Nigdy nie wygasa, ale można cofnąć
    """
    
    credentials = base64.b64encode(
        f"{self.username}:{self.app_password}".encode()
    ).decode()
    
    return {
        'Authorization': f'Basic {credentials}',
        'Content-Type': 'application/json'
    }
```

### KROK 2: Upload featured image do Media Library
```python
def upload_featured_image(self, image_url, title):
    """
    Uploaduje obraz jako featured image do WordPress.
    
    Proces:
    1. Pobierz obraz z URL (Unsplash)
    2. Prześlij do WordPress Media Library
    3. Otrzymaj Media ID
    4. Zwróć ID do użycia w poście
    
    Endpoint: POST /wp-json/wp/v2/media
    """
    
    # Pobierz obraz
    image_response = requests.get(image_url)
    image_data = image_response.content
    
    # Określ typ MIME
    content_type = image_response.headers.get('Content-Type', 'image/jpeg')
    
    # Nazwa pliku
    filename = self._generate_filename(title)
    
    # Upload do WordPress
    upload_url = f"{self.api_url}/media"
    headers = self._authenticate()
    headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    headers['Content-Type'] = content_type
    
    response = requests.post(
        upload_url,
        headers=headers,
        data=image_data
    )
    
    if response.status_code == 201:
        media_data = response.json()
        return media_data['id']  # Media ID
    else:
        raise UploadError(f"Failed to upload image: {response.text}")
```

### KROK 3: Pobieranie autorów (rotacja)
```python
def get_authors(self):
    """
    Pobiera listę autorów z WordPress.
    
    Endpoint: GET /wp-json/wp/v2/users
    
    Filtrowanie:
    - Tylko autorzy z uprawnieniami do publikacji
    - Pomija administratorów (opcjonalnie)
    
    Rotacja:
    - System pamięta ostatnio użytego autora
    - Następny artykuł = następny autor w liście
    - Po ostatnim autorze wraca do pierwszego
    """
    
    url = f"{self.api_url}/users"
    params = {
        'roles': 'author,editor,administrator',
        'per_page': 100
    }
    
    response = requests.get(url, headers=self._authenticate(), params=params)
    authors = response.json()
    
    return [{'id': a['id'], 'name': a['name']} for a in authors]
```

### KROK 4: Tworzenie lub pobieranie tagów
```python
def get_or_create_tags(self, tag_names):
    """
    Pobiera ID tagów lub tworzy nowe.
    
    Proces dla każdego tagu:
    1. Szukaj istniejącego tagu
    2. Jeśli istnieje → użyj jego ID
    3. Jeśli nie istnieje → utwórz nowy
    
    Limit: System generuje DOKŁADNIE 12 tagów na artykuł
    """
    
    tag_ids = []
    
    for tag_name in tag_names:
        # Szukaj istniejącego
        search_url = f"{self.api_url}/tags"
        response = requests.get(
            search_url,
            headers=self._authenticate(),
            params={'search': tag_name}
        )
        
        existing_tags = response.json()
        
        if existing_tags:
            # Użyj istniejącego
            tag_ids.append(existing_tags[0]['id'])
        else:
            # Utwórz nowy
            create_response = requests.post(
                search_url,
                headers=self._authenticate(),
                json={'name': tag_name}
            )
            new_tag = create_response.json()
            tag_ids.append(new_tag['id'])
    
    return tag_ids
```

### KROK 5: Publikacja posta
```python
def publish_article(self, article_data):
    """
    Publikuje artykuł na WordPress.
    
    Dane wejściowe:
    - title: Tytuł artykułu
    - content: Treść HTML
    - category_id: ID kategorii WordPress
    - tag_ids: Lista ID tagów (12 tagów)
    - author_id: ID autora (rotacja)
    - featured_media: ID featured image
    - status: 'publish' lub 'draft'
    
    Endpoint: POST /wp-json/wp/v2/posts
    """
    
    post_data = {
        'title': article_data['title'],
        'content': article_data['content'],
        'status': 'publish',
        'categories': [article_data['category_id']],
        'tags': article_data['tag_ids'],
        'author': article_data['author_id'],
        'featured_media': article_data['featured_media']
    }
    
    url = f"{self.api_url}/posts"
    
    response = requests.post(
        url,
        headers=self._authenticate(),
        json=post_data
    )
    
    if response.status_code == 201:
        post = response.json()
        return {
            'post_id': post['id'],
            'url': post['link'],
            'status': 'published'
        }
    else:
        raise PublishError(f"Failed to publish: {response.text}")
```

## 6.4 Rotacja autorów

```python
class AuthorRotator:
    """
    Zarządza rotacją autorów dla batch generation.
    
    Cel: Równomierne rozłożenie artykułów między autorów
    
    Algorytm:
    1. Pobierz listę wszystkich autorów
    2. Zapamiętaj indeks ostatnio użytego
    3. Dla każdego artykułu: następny autor w kolejce
    4. Po ostatnim autorze: wróć do pierwszego
    """
    
    def __init__(self, authors):
        self.authors = authors
        self.current_index = 0
    
    def get_next_author(self):
        author = self.authors[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.authors)
        return author
```

---

# 7. MODUŁ SEO I TAGÓW

## 7.1 Lokalizacja pliku
**Plik:** `utils/ai_content_strategy/seo_optimizer.py`

## 7.2 Generator tagów SEO

```python
class SEOOptimizer:
    """
    Optymalizuje artykuły pod kątem SEO.
    
    Funkcje:
    - Generowanie tagów (DOKŁADNIE 12 na artykuł)
    - Tworzenie meta description
    - Analiza słów kluczowych
    - Sugestie optymalizacji
    """
```

### Generowanie 12 tagów SEO
```python
def generate_tags(self, title, content, category):
    """
    Generuje DOKŁADNIE 12 tagów SEO dla artykułu.
    
    Proces:
    1. Analizuj tytuł - wyciągnij główne słowa kluczowe
    2. Analizuj treść - znajdź najczęstsze frazy
    3. Uwzględnij kategorię - dodaj tagi kategorii
    4. Użyj AI do wygenerowania dodatkowych tagów
    5. Deduplikacja i selekcja 12 najlepszych
    
    Przykład output:
    ["wózek dziecięcy", "akcesoria niemowlęce", "bezpieczeństwo",
     "spacer z dzieckiem", "poradnik dla rodziców", "wybór wózka",
     "wielofunkcyjny wózek", "niemowlę", "rodzicielstwo", 
     "pierwsza wyprawa", "komfort dziecka", "jakość wózka"]
    """
    
    # Prompt dla AI
    prompt = f"""
    Wygeneruj DOKŁADNIE 12 tagów SEO po polsku dla artykułu:
    
    Tytuł: {title}
    Kategoria: {category}
    
    Wymagania:
    1. Tagi muszą być po polsku
    2. Każdy tag 1-4 słowa
    3. Tagi muszą być relevantne do treści
    4. Mix: ogólne i szczegółowe tagi
    5. Nie powtarzaj słów między tagami
    
    Zwróć jako listę oddzieloną przecinkami.
    """
    
    response = self.ai_adapter.generate(prompt)
    tags = self._parse_tags(response)
    
    # Upewnij się że jest dokładnie 12
    if len(tags) < 12:
        tags.extend(self._generate_additional_tags(title, 12 - len(tags)))
    elif len(tags) > 12:
        tags = tags[:12]
    
    return tags
```

### Meta description
```python
def generate_meta_description(self, title, content):
    """
    Generuje meta description dla SEO.
    
    Wymagania:
    - Długość: 150-160 znaków
    - Zawiera główne słowo kluczowe
    - Zachęca do kliknięcia
    - Naturalny język
    
    Przykład:
    "Dowiedz się jak wybrać idealny wózek dla dziecka. 
     Kompletny poradnik z porównaniem modeli i poradami ekspertów."
    """
    
    prompt = f"""
    Napisz meta description (150-160 znaków) dla artykułu:
    Tytuł: {title}
    
    Meta description musi:
    1. Zawierać główne słowo kluczowe
    2. Zachęcać do kliknięcia
    3. Być naturalnym zdaniem po polsku
    """
    
    return self.ai_adapter.generate(prompt)
```

---

# 8. MODUŁ AUTOMATYZACJI I HARMONOGRAMOWANIA

## 8.1 Lokalizacja pliku
**Plik:** `utils/automation/scheduler.py`

## 8.2 Status: WYŁĄCZONY

```python
# WAŻNE: Scheduler jest WYŁĄCZONY od 21 listopada 2025
# Powód: Na żądanie użytkownika
# Artykuły można generować tylko ręcznie przez panel administracyjny

# Aby ponownie włączyć scheduler:
# 1. Edytuj plik main.py
# 2. Odkomentuj linie 39-43:
#    from utils.automation.scheduler import start_automation_scheduler
#    with app.app_context():
#        start_automation_scheduler()
# 3. Zrestartuj aplikację
```

## 8.3 Jak scheduler działał (przed wyłączeniem)

```python
class AutomationScheduler:
    """
    Harmonogramował automatyczne generowanie artykułów.
    
    Harmonogram (przed wyłączeniem):
    - 05:00 UTC (07:00 PL): MamaTestuje - 3 artykuły
    - 06:00 UTC (08:00 PL): ZnaneKosmetyki - 3 artykuły
    - 07:00 UTC (09:00 PL): HomosOnly - 3 artykuły
    
    Łącznie: 9 artykułów dziennie
    """
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.timezone = pytz.UTC
    
    def start(self):
        # MamaTestuje - 05:00 UTC
        self.scheduler.add_job(
            func=self._generate_batch,
            trigger='cron',
            hour=5,
            minute=0,
            args=['MamaTestuje', 3],
            id='mamatestuje_batch'
        )
        
        # ZnaneKosmetyki - 06:00 UTC
        self.scheduler.add_job(
            func=self._generate_batch,
            trigger='cron',
            hour=6,
            minute=0,
            args=['ZnaneKosmetyki', 3],
            id='znanekosmetyki_batch'
        )
        
        # HomosOnly - 07:00 UTC
        self.scheduler.add_job(
            func=self._generate_batch,
            trigger='cron',
            hour=7,
            minute=0,
            args=['HomosOnly', 3],
            id='homosonly_batch'
        )
        
        self.scheduler.start()
```

---

# 9. WORKFLOW ENGINE - SILNIK PRZEPŁYWU PRACY

## 9.1 Lokalizacja pliku
**Plik:** `utils/automation/workflow_engine.py`

## 9.2 Główna klasa: WorkflowEngine

```python
class WorkflowEngine:
    """
    Orkiestruje cały proces tworzenia i publikacji artykułu.
    
    Workflow składa się z kroków:
    1. Wybór/generowanie tematu
    2. Generowanie artykułu
    3. Wyszukiwanie obrazów
    4. Upload featured image
    5. Generowanie tagów SEO
    6. Publikacja na WordPress
    7. (Opcjonalnie) Udostępnienie w social media
    8. Zapisanie logu do bazy
    
    Timeout: 10 minut (600 sekund) na cały workflow
    """
```

## 9.3 Pełny przepływ workflow

```python
def execute_workflow(self, blog_id, category_id, topic=None):
    """
    Wykonuje pełny workflow generowania i publikacji.
    
    Parametry:
    - blog_id: ID bloga w bazie danych
    - category_id: ID kategorii WordPress
    - topic: Opcjonalny temat (jeśli None - generuj nowy)
    
    Zwraca:
    - post_id: ID opublikowanego posta
    - url: Link do artykułu
    - status: 'success' lub 'failed'
    """
    
    start_time = time.time()
    timeout = 600  # 10 minut
    
    try:
        # KROK 1: Pobierz konfigurację bloga
        blog = Blog.query.get(blog_id)
        if not blog or not blog.active:
            raise WorkflowError("Blog not found or inactive")
        
        # KROK 2: Wybierz lub wygeneruj temat
        if topic is None:
            topic = self._get_or_generate_topic(blog_id, category_id)
        
        logging.info(f"Starting workflow for topic: {topic}")
        
        # KROK 3: Wygeneruj artykuł
        article_generator = ArticleGenerator(blog_config=blog.config)
        article_content = article_generator.generate_article(
            topic=topic,
            category=category_id
        )
        
        self._check_timeout(start_time, timeout, "Article generation")
        
        # KROK 4: Znajdź obrazy
        image_finder = AutoImageFinder()
        images = image_finder.find_images(topic, count=3)
        
        if not images:
            logging.warning("No images found, continuing without featured image")
            featured_image_id = None
        else:
            # KROK 5: Upload featured image do WordPress
            publisher = WordPressPublisher(blog)
            featured_image_id = publisher.upload_featured_image(
                image_url=images[0]['url'],
                title=self._truncate_title(images[0].get('description', topic))
            )
        
        self._check_timeout(start_time, timeout, "Image processing")
        
        # KROK 6: Wygeneruj tagi SEO (dokładnie 12)
        seo_optimizer = SEOOptimizer()
        tags = seo_optimizer.generate_tags(
            title=topic,
            content=article_content,
            category=category_id
        )
        
        # KROK 7: Pobierz następnego autora (rotacja)
        authors = publisher.get_authors()
        author = self.author_rotator.get_next_author(authors)
        
        # KROK 8: Pobierz/utwórz tagi w WordPress
        tag_ids = publisher.get_or_create_tags(tags)
        
        self._check_timeout(start_time, timeout, "Tag creation")
        
        # KROK 9: Publikuj na WordPress
        result = publisher.publish_article({
            'title': topic,
            'content': article_content,
            'category_id': category_id,
            'tag_ids': tag_ids,
            'author_id': author['id'],
            'featured_media': featured_image_id
        })
        
        # KROK 10: Zapisz log do bazy
        self._save_content_log(
            blog_id=blog_id,
            title=topic,
            content=article_content,
            status='published',
            post_id=result['post_id'],
            category_id=category_id,
            tags=tags,
            featured_image=images[0] if images else None
        )
        
        logging.info(f"Workflow completed: Post ID {result['post_id']}")
        
        return {
            'status': 'success',
            'post_id': result['post_id'],
            'url': result['url'],
            'word_count': len(article_content.split()),
            'tags_count': len(tags),
            'execution_time': time.time() - start_time
        }
        
    except Exception as e:
        # Loguj błąd z pełnym traceback
        logging.error(f"Workflow failed: {e}")
        logging.error(traceback.format_exc())
        
        # Zapisz failed log
        self._save_content_log(
            blog_id=blog_id,
            title=topic or "Unknown",
            content="",
            status='failed',
            error=str(e)
        )
        
        # Re-raise exception (NIE używaj fallback!)
        raise
```

## 9.4 Rotacja kategorii w batch generation

```python
def execute_batch(self, blog_id, count):
    """
    Generuje wiele artykułów dla jednego bloga.
    
    Rotacja kategorii:
    - Każdy kolejny artykuł używa innej kategorii
    - Cyklicznie przechodzi przez wszystkie kategorie
    - Zapewnia różnorodność treści
    
    Przykład dla 3 artykułów:
    1. Kategoria A
    2. Kategoria B
    3. Kategoria C
    """
    
    # Pobierz wszystkie kategorie bloga
    categories = Category.query.filter_by(blog_id=blog_id).all()
    category_rotator = CategoryRotator(categories)
    
    results = []
    for i in range(count):
        category = category_rotator.get_next_category()
        
        try:
            result = self.execute_workflow(blog_id, category.wordpress_id)
            results.append(result)
            
        except Exception as e:
            logging.error(f"Batch item {i+1} failed: {e}")
            # Kontynuuj z następnymi artykułami
            continue
    
    return results
```

---

# 10. BAZA DANYCH - STRUKTURA I RELACJE

## 10.1 Lokalizacja pliku
**Plik:** `models.py`

## 10.2 Diagram relacji

```
┌─────────────┐     ┌─────────────────┐     ┌──────────────┐
│    Blog     │────<│   ContentLog    │     │   Category   │
│             │     │                 │>────│              │
│ id          │     │ id              │     │ id           │
│ name        │     │ blog_id (FK)    │     │ blog_id (FK) │
│ url         │     │ title           │     │ name         │
│ api_url     │     │ content         │     │ wordpress_id │
│ username    │     │ status          │     └──────────────┘
│ api_token   │     │ post_id         │
│ active      │     │ category_id     │     ┌──────────────┐
│ config      │     │ tags            │     │     Tag      │
└─────────────┘     │ featured_image  │     │              │
      │             │ created_at      │     │ id           │
      │             │ published_at    │     │ blog_id (FK) │
      │             └─────────────────┘     │ name         │
      │                                      │ wordpress_id │
      │                                      └──────────────┘
      │
      │             ┌─────────────────┐     ┌──────────────────┐
      └────────────<│  ArticleTopic   │     │  AutomationRule  │
                    │                 │     │                  │
                    │ id              │     │ id               │
                    │ blog_id (FK)    │     │ blog_id (FK)     │
                    │ category        │     │ name             │
                    │ topic           │     │ category         │
                    │ status          │     │ articles_per_day │
                    │ created_at      │     │ schedule_time    │
                    └─────────────────┘     │ auto_publish     │
                                            │ is_active        │
                                            └──────────────────┘
```

## 10.3 Definicje modeli

### Model Blog
```python
class Blog(db.Model):
    """
    Reprezentuje blog WordPress w systemie.
    
    Pola:
    - id: Klucz główny (Integer)
    - name: Nazwa bloga (String 100)
    - url: URL bloga (String 255)
    - api_url: URL REST API WordPress (String 255)
    - username: Nazwa użytkownika WordPress (String 100)
    - api_token: Application Password (String 255, zaszyfrowany)
    - active: Czy blog jest aktywny (Boolean)
    - config: Konfiguracja JSON (długość artykułów, styl, itp.)
    - created_at: Data utworzenia (DateTime)
    """
    
    __tablename__ = 'blog'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    api_url = db.Column(db.String(255))
    username = db.Column(db.String(100))
    api_token = db.Column(db.String(255))
    active = db.Column(db.Boolean, default=True)
    config = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacje
    content_logs = db.relationship('ContentLog', backref='blog', lazy=True)
    categories = db.relationship('Category', backref='blog', lazy=True)
    topics = db.relationship('ArticleTopic', backref='blog', lazy=True)
```

### Model ContentLog
```python
class ContentLog(db.Model):
    """
    Log każdego wygenerowanego/opublikowanego artykułu.
    
    Pola:
    - id: Klucz główny
    - blog_id: FK do Blog
    - title: Tytuł artykułu (String 500)
    - content: Pełna treść HTML (Text)
    - status: draft/published/failed (String 50)
    - post_id: ID posta w WordPress (Integer, nullable)
    - category_id: ID kategorii WordPress (Integer)
    - tags: Lista tagów JSON (12 tagów)
    - featured_image_data: Dane obrazu JSON
    - error_message: Komunikat błędu jeśli failed (Text)
    - word_count: Liczba słów (Integer)
    - created_at: Data utworzenia
    - published_at: Data publikacji
    """
    
    __tablename__ = 'content_log'
    
    id = db.Column(db.Integer, primary_key=True)
    blog_id = db.Column(db.Integer, db.ForeignKey('blog.id'), nullable=False)
    title = db.Column(db.String(500), nullable=False)
    content = db.Column(db.Text)
    status = db.Column(db.String(50), default='draft')
    post_id = db.Column(db.Integer)
    category_id = db.Column(db.Integer)
    tags = db.Column(db.JSON)
    featured_image_data = db.Column(db.JSON)
    error_message = db.Column(db.Text)
    word_count = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    published_at = db.Column(db.DateTime)
```

### Model ArticleTopic
```python
class ArticleTopic(db.Model):
    """
    Tematy artykułów do napisania.
    
    Pola:
    - id: Klucz główny
    - blog_id: FK do Blog
    - category: Nazwa kategorii (String 200)
    - topic: Temat artykułu (String 500)
    - status: pending/used/archived (String 50)
    - keywords: Słowa kluczowe JSON
    - created_at: Data utworzenia
    - used_at: Data użycia
    """
    
    __tablename__ = 'article_topic'
    
    id = db.Column(db.Integer, primary_key=True)
    blog_id = db.Column(db.Integer, db.ForeignKey('blog.id'), nullable=False)
    category = db.Column(db.String(200))
    topic = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(50), default='pending')
    keywords = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    used_at = db.Column(db.DateTime)
```

### Model Category
```python
class Category(db.Model):
    """
    Kategorie zsynchronizowane z WordPress.
    
    Pola:
    - id: Klucz główny (lokalny)
    - blog_id: FK do Blog
    - name: Nazwa kategorii (String 200)
    - wordpress_id: ID kategorii w WordPress (Integer)
    - parent_id: ID kategorii nadrzędnej (Integer, nullable)
    - count: Liczba postów w kategorii (Integer)
    """
    
    __tablename__ = 'category'
    
    id = db.Column(db.Integer, primary_key=True)
    blog_id = db.Column(db.Integer, db.ForeignKey('blog.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    wordpress_id = db.Column(db.Integer, nullable=False)
    parent_id = db.Column(db.Integer)
    count = db.Column(db.Integer, default=0)
```

### Model ImageLibrary
```python
class ImageLibrary(db.Model):
    """
    Biblioteka użytych obrazów.
    
    Pola:
    - id: Klucz główny
    - blog_id: FK do Blog
    - url: URL obrazu (String 500)
    - title: Tytuł/opis (String 255) - OGRANICZENIE po poprawce
    - source: Źródło: unsplash/pexels/google (String 50)
    - author: Autor zdjęcia (String 200)
    - author_url: Link do profilu autora (String 500)
    - tags: Tagi obrazu JSON
    - used_in_post_id: ID posta gdzie użyty (Integer)
    - created_at: Data dodania
    """
    
    __tablename__ = 'image_library'
    
    id = db.Column(db.Integer, primary_key=True)
    blog_id = db.Column(db.Integer, db.ForeignKey('blog.id'))
    url = db.Column(db.String(500), nullable=False)
    title = db.Column(db.String(255))  # MAX 255 znaków!
    source = db.Column(db.String(50))
    author = db.Column(db.String(200))
    author_url = db.Column(db.String(500))
    tags = db.Column(db.JSON)
    used_in_post_id = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

---

# 11. API I INTEGRACJE ZEWNĘTRZNE

## 11.1 OpenRouter API (AI)

### Konfiguracja
```python
OPENROUTER_CONFIG = {
    'base_url': 'https://openrouter.ai/api/v1',
    'model': 'anthropic/claude-haiku-4.5',
    'api_key': os.environ.get('OPENROUTER_API_KEY'),
    
    # Parametry generowania
    'max_tokens': 4000,
    'temperature': 0.7,
    'top_p': 0.9,
    'frequency_penalty': 0.3,
    'presence_penalty': 0.3,
    
    # Limity
    'timeout': 120,  # sekundy na request
    'max_retries': 3,
    'retry_delays': [2, 5, 12]  # sekundy
}
```

### Struktura requestu
```python
def call_openrouter(prompt, system_message=None):
    """
    Wywołuje OpenRouter API.
    
    Endpoint: POST /api/v1/chat/completions
    """
    
    headers = {
        'Authorization': f'Bearer {OPENROUTER_API_KEY}',
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://masteragent.ai',
        'X-Title': 'Master Agent AI'
    }
    
    messages = []
    if system_message:
        messages.append({
            'role': 'system',
            'content': system_message
        })
    messages.append({
        'role': 'user',
        'content': prompt
    })
    
    payload = {
        'model': 'anthropic/claude-haiku-4.5',
        'messages': messages,
        'max_tokens': 4000,
        'temperature': 0.7
    }
    
    response = requests.post(
        'https://openrouter.ai/api/v1/chat/completions',
        headers=headers,
        json=payload,
        timeout=120
    )
    
    return response.json()['choices'][0]['message']['content']
```

### Koszty
```
Model: anthropic/claude-haiku-4.5

Input tokens:  $0.25 / 1M tokens
Output tokens: $1.25 / 1M tokens

Średni artykuł (1200 słów):
- Input: ~2000 tokens
- Output: ~4000 tokens
- Koszt: ~$0.01-0.05

Miesięczny koszt (270 artykułów):
- Szacowany: $10-30
```

## 11.2 Unsplash API

### Konfiguracja
```python
UNSPLASH_CONFIG = {
    'base_url': 'https://api.unsplash.com',
    'access_key': os.environ.get('UNSPLASH_API_KEY'),
    
    # Limity
    'requests_per_hour': 50,
    'images_per_request': 10
}
```

### Endpointy używane
```
GET /search/photos      - Wyszukiwanie obrazów
GET /photos/:id         - Szczegóły obrazu
GET /photos/:id/download - Pobieranie (do statystyk Unsplash)
```

### Struktura odpowiedzi
```json
{
    "total": 500,
    "total_pages": 50,
    "results": [
        {
            "id": "abc123",
            "width": 4000,
            "height": 3000,
            "description": "Baby stroller in park",
            "urls": {
                "raw": "https://images.unsplash.com/...",
                "full": "https://images.unsplash.com/...",
                "regular": "https://images.unsplash.com/...?w=1080",
                "small": "https://images.unsplash.com/...?w=400",
                "thumb": "https://images.unsplash.com/...?w=200"
            },
            "user": {
                "name": "John Doe",
                "username": "johndoe",
                "links": {
                    "html": "https://unsplash.com/@johndoe"
                }
            }
        }
    ]
}
```

## 11.3 WordPress REST API

### Autentykacja
```
Metoda: HTTP Basic Authentication
Format: base64(username:application_password)
Header: Authorization: Basic {credentials}
```

### Endpointy używane
```
GET  /wp-json/wp/v2/posts          - Lista postów
POST /wp-json/wp/v2/posts          - Tworzenie posta
GET  /wp-json/wp/v2/categories     - Lista kategorii
GET  /wp-json/wp/v2/tags           - Lista tagów
POST /wp-json/wp/v2/tags           - Tworzenie tagu
POST /wp-json/wp/v2/media          - Upload obrazu
GET  /wp-json/wp/v2/users          - Lista użytkowników (autorów)
```

### Struktura posta
```json
{
    "title": "Tytuł artykułu",
    "content": "<p>Treść HTML...</p>",
    "status": "publish",
    "categories": [45],
    "tags": [12, 34, 56, 78, 90, 23, 45, 67, 89, 10, 11, 13],
    "author": 5,
    "featured_media": 2987
}
```

---

# 12. PANEL ADMINISTRACYJNY - FRONTEND

## 12.1 Struktura szablonów

```
templates/
├── base.html              # Szablon bazowy z nawigacją
├── dashboard.html         # Pulpit główny ze statystykami
├── blogs.html             # Lista i zarządzanie blogami
├── blog_form.html         # Formularz dodawania/edycji bloga
├── topics.html            # Generowanie i lista tematów
├── content_creator.html   # Kreator artykułów
├── pending_articles.html  # Artykuły oczekujące na publikację
├── schedule.html          # Kalendarz publikacji
├── logs.html              # Historia działań systemu
├── images.html            # Biblioteka obrazów
├── social_accounts.html   # Konta social media
├── seo_tools.html         # Narzędzia SEO
└── settings.html          # Ustawienia systemu
```

## 12.2 Dashboard - główne metryki

```html
<!-- Dashboard pokazuje: -->

1. STATYSTYKI OGÓLNE
   - Liczba aktywnych blogów: 3
   - Artykułów dzisiaj: 0 (scheduler wyłączony)
   - Artykułów w tym miesiącu: 270
   - Tematów w kolejce: 45

2. SZYBKIE AKCJE
   - [Generuj artykuł] - ręczne generowanie
   - [Dodaj blog] - nowy blog WordPress
   - [Generuj tematy] - nowe pomysły na artykuły

3. OSTATNIE ARTYKUŁY
   - Lista 10 ostatnio opublikowanych
   - Status, blog, tytuł, data

4. HARMONOGRAM (WYŁĄCZONY)
   - Informacja że scheduler jest wyłączony
   - Wszystkie akcje tylko ręcznie
```

## 12.3 Kreator artykułów

```html
<!-- Formularz generowania artykułu: -->

<form action="/generate-article" method="POST">
    <!-- Wybór bloga -->
    <select name="blog_id">
        <option value="2">MamaTestuje</option>
        <option value="3">ZnaneKosmetyki</option>
        <option value="4">HomosOnly</option>
    </select>
    
    <!-- Wybór kategorii -->
    <select name="category_id">
        <!-- Dynamicznie ładowane z WordPress -->
    </select>
    
    <!-- Temat (opcjonalny) -->
    <input type="text" name="topic" 
           placeholder="Zostaw puste aby system wygenerował temat">
    
    <!-- Opcje -->
    <label>
        <input type="checkbox" name="auto_publish" checked>
        Publikuj automatycznie
    </label>
    
    <button type="submit">Generuj artykuł</button>
</form>
```

---

# 13. OBSŁUGA BŁĘDÓW I MECHANIZMY NAPRAWCZE

## 13.1 Hierarchia błędów

```python
class MasterAgentError(Exception):
    """Bazowa klasa błędów systemu."""
    pass

class ArticleGenerationError(MasterAgentError):
    """Błąd podczas generowania artykułu."""
    pass

class ImageSearchError(MasterAgentError):
    """Błąd podczas wyszukiwania obrazów."""
    pass

class WordPressPublishError(MasterAgentError):
    """Błąd podczas publikacji na WordPress."""
    pass

class APIError(MasterAgentError):
    """Błąd komunikacji z zewnętrznym API."""
    pass

class ValidationError(MasterAgentError):
    """Błąd walidacji danych."""
    pass
```

## 13.2 Mechanizm retry z exponential backoff

```python
# POPRAWKA z Nov 20, 2025

RETRY_CONFIG = {
    'max_attempts': 3,
    'delays': [2, 5, 12],  # sekundy
    'retryable_errors': [
        'RateLimitError',
        'TimeoutError',
        'ConnectionError',
        '429',  # Too Many Requests
        '503',  # Service Unavailable
        '504'   # Gateway Timeout
    ]
}

def retry_with_backoff(func, *args, **kwargs):
    """
    Wykonuje funkcję z automatycznym ponawianiem przy błędach.
    
    Algorytm:
    1. Próba 1: natychmiast
    2. Jeśli błąd retryable: czekaj delays[0] sekund
    3. Próba 2
    4. Jeśli błąd: czekaj delays[1] sekund
    5. Próba 3
    6. Jeśli nadal błąd: re-raise exception
    """
    
    for attempt in range(RETRY_CONFIG['max_attempts']):
        try:
            return func(*args, **kwargs)
            
        except Exception as e:
            error_type = type(e).__name__
            
            # Sprawdź czy błąd jest retryable
            if not is_retryable(e):
                raise
            
            # Ostatnia próba - re-raise
            if attempt == RETRY_CONFIG['max_attempts'] - 1:
                logging.error(f"All {attempt + 1} attempts failed: {e}")
                raise
            
            # Czekaj przed następną próbą
            delay = RETRY_CONFIG['delays'][attempt]
            logging.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s: {e}")
            time.sleep(delay)
```

## 13.3 Logowanie błędów

```python
# POPRAWKA z Nov 20, 2025: Pełny traceback

import logging
import traceback

# Konfiguracja logowania
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/master_agent.log')
    ]
)

def log_error_with_traceback(error, context=None):
    """
    Loguje błąd z pełnym traceback.
    
    Zawiera:
    - Typ błędu
    - Komunikat błędu
    - Pełny stack trace
    - Kontekst (np. blog_id, topic)
    """
    
    logging.error(f"Error occurred: {error}")
    logging.error(f"Context: {context}")
    logging.error(f"Full traceback:\n{traceback.format_exc()}")
```

## 13.4 KRYTYCZNE: Brak fallback content

```python
# STARY KOD (NIEPOPRAWNY):
# try:
#     article = generate_article(topic)
# except:
#     article = "Przepraszamy, artykuł jest niedostępny..."  # FALLBACK
#     return article  # Publikował 276 słów zamiast 4000!

# NOWY KOD (POPRAWNY):
try:
    article = generate_article(topic)
except Exception as e:
    logging.error(f"Generation failed: {e}")
    logging.error(traceback.format_exc())
    raise  # NIE używaj fallback, przekaż błąd dalej!
```

---

# 14. KONFIGURACJA BLOGÓW

## 14.1 Aktualnie skonfigurowane blogi

| ID | Nazwa | URL | Typ treści | Długość artykułu |
|----|-------|-----|------------|------------------|
| 2 | MamaTestuje | mamatestuje.com | Parenting, dzieci | 2000-2500 słów |
| 3 | ZnaneKosmetyki | znanekosmetyki.pl | Kosmetyki, uroda | 2500-3500 słów |
| 4 | HomosOnly | homosonly.pl | LGBT+ lifestyle | 1800-2200 słów |

## 14.2 Konfiguracja każdego bloga

### MamaTestuje (ID: 2)
```python
{
    'name': 'MamaTestuje',
    'url': 'https://mamatestuje.com',
    'api_url': 'https://mamatestuje.com/wp-json/wp/v2',
    'config': {
        'min_words': 2000,
        'max_words': 2500,
        'language': 'pl',
        'style': 'przyjazny, pomocny, ekspercki',
        'target_audience': 'rodzice małych dzieci',
        'topics': [
            'akcesoria dziecięce',
            'zabawki edukacyjne',
            'zdrowie dzieci',
            'rozwój dziecka',
            'porady dla rodziców'
        ],
        'articles_per_day': 3  # TYLKO RĘCZNIE
    }
}
```

### ZnaneKosmetyki (ID: 3)
```python
{
    'name': 'ZnaneKosmetyki',
    'url': 'https://znanekosmetyki.pl',
    'api_url': 'https://znanekosmetyki.pl/wp-json/wp/v2',
    'config': {
        'min_words': 2500,
        'max_words': 3500,
        'language': 'pl',
        'style': 'profesjonalny, ekspercki, szczegółowy',
        'target_audience': 'kobiety zainteresowane urodą',
        'topics': [
            'pielęgnacja skóry',
            'makijaż',
            'perfumy',
            'kosmetyki naturalne',
            'recenzje produktów'
        ],
        'articles_per_day': 3  # TYLKO RĘCZNIE
    }
}
```

### HomosOnly (ID: 4)
```python
{
    'name': 'HomosOnly',
    'url': 'https://homosonly.pl',
    'api_url': 'https://homosonly.pl/wp-json/wp/v2',
    'config': {
        'min_words': 1800,
        'max_words': 2200,
        'language': 'pl',
        'style': 'nowoczesny, inkluzywny, wspierający',
        'target_audience': 'społeczność LGBT+',
        'topics': [
            'lifestyle',
            'kultura',
            'prawa LGBT+',
            'zdrowie',
            'relacje'
        ],
        'articles_per_day': 3  # TYLKO RĘCZNIE
    }
}
```

---

# 15. PEŁNY PRZEPŁYW GENEROWANIA ARTYKUŁU

## 15.1 Diagram sekwencyjny

```
┌──────────┐ ┌──────────────┐ ┌───────────────┐ ┌──────────┐ ┌───────────┐ ┌───────────┐
│ Użytkownik│ │ Panel Admin  │ │WorkflowEngine │ │AI Adapter│ │ImageFinder│ │ WordPress │
└────┬─────┘ └──────┬───────┘ └───────┬───────┘ └────┬─────┘ └─────┬─────┘ └─────┬─────┘
     │              │                 │              │             │             │
     │ 1. Kliknij   │                 │              │             │             │
     │    Generuj   │                 │              │             │             │
     │─────────────>│                 │              │             │             │
     │              │                 │              │             │             │
     │              │ 2. Start        │              │             │             │
     │              │    workflow     │              │             │             │
     │              │────────────────>│              │             │             │
     │              │                 │              │             │             │
     │              │                 │ 3. Generuj   │             │             │
     │              │                 │    wstęp     │             │             │
     │              │                 │─────────────>│             │             │
     │              │                 │              │             │             │
     │              │                 │<─────────────│             │             │
     │              │                 │   Wstęp OK   │             │             │
     │              │                 │              │             │             │
     │              │                 │ 4. Generuj   │             │             │
     │              │                 │    sekcja 1  │             │             │
     │              │                 │─────────────>│             │             │
     │              │                 │<─────────────│             │             │
     │              │                 │              │             │             │
     │              │                 │ ... (powtórz dla sekcji 2-5 i podsumowania) │
     │              │                 │              │             │             │
     │              │                 │ 5. Znajdź    │             │             │
     │              │                 │    obrazy    │             │             │
     │              │                 │────────────────────────────>│             │
     │              │                 │              │             │             │
     │              │                 │<────────────────────────────│             │
     │              │                 │   3 obrazy   │             │             │
     │              │                 │              │             │             │
     │              │                 │ 6. Upload    │             │             │
     │              │                 │    featured  │             │             │
     │              │                 │─────────────────────────────────────────>│
     │              │                 │              │             │             │
     │              │                 │<─────────────────────────────────────────│
     │              │                 │   Media ID   │             │             │
     │              │                 │              │             │             │
     │              │                 │ 7. Generuj   │             │             │
     │              │                 │    12 tagów  │             │             │
     │              │                 │─────────────>│             │             │
     │              │                 │<─────────────│             │             │
     │              │                 │              │             │             │
     │              │                 │ 8. Publikuj  │             │             │
     │              │                 │    post      │             │             │
     │              │                 │─────────────────────────────────────────>│
     │              │                 │              │             │             │
     │              │                 │<─────────────────────────────────────────│
     │              │                 │   Post ID    │             │             │
     │              │                 │              │             │             │
     │              │ 9. Sukces       │              │             │             │
     │              │<────────────────│              │             │             │
     │              │                 │              │             │             │
     │ 10. Wyświetl │                 │              │             │             │
     │     sukces   │                 │              │             │             │
     │<─────────────│                 │              │             │             │
     │              │                 │              │             │             │
```

## 15.2 Szczegółowy opis każdego kroku

### KROK 1: Inicjalizacja żądania
```
Użytkownik klika "Generuj artykuł" w panelu.
Formularz wysyła POST do /generate-article z:
- blog_id: 2 (MamaTestuje)
- category_id: 45 (Akcesoria dziecięce)
- topic: "" (pusty = wygeneruj nowy)
- auto_publish: true
```

### KROK 2: WorkflowEngine otrzymuje żądanie
```python
workflow = WorkflowEngine()
result = workflow.execute_workflow(
    blog_id=2,
    category_id=45,
    topic=None  # System wygeneruje
)
```

### KROK 3: Generowanie tematu (jeśli pusty)
```python
# Jeśli topic nie podany, generuj nowy
if topic is None:
    topic_generator = TopicGenerator(ai_adapter)
    topic = topic_generator.generate(
        blog_name="MamaTestuje",
        category="Akcesoria dziecięce"
    )
    # Wynik: "Jak wybrać idealny wózek dla dziecka - kompletny poradnik"
```

### KROK 4-9: Generowanie artykułu sekcja po sekcji
```python
# 7 wywołań AI (wstęp + 5 sekcji + podsumowanie)
# Każde wywołanie: ~20-30 sekund
# Łączny czas: 2-4 minuty

article_generator = ArticleGenerator(blog_config)
sections = []

# Wstęp (200 słów)
sections.append(article_generator.generate_section("intro", topic))

# 5 sekcji głównych (po 200-250 słów)
for i in range(5):
    sections.append(article_generator.generate_section(f"section_{i+1}", topic))

# Podsumowanie (200 słów)
sections.append(article_generator.generate_section("conclusion", topic))

# Złóż całość
full_article = article_generator.combine_sections(sections)
# Wynik: ~1400 słów HTML
```

### KROK 10: Wyszukiwanie obrazów
```python
image_finder = AutoImageFinder()
images = image_finder.find_images(
    title=topic,
    count=3
)

# Wynik:
# [
#     {'url': 'https://unsplash.com/photo/abc', 'description': 'Baby stroller'},
#     {'url': 'https://unsplash.com/photo/def', 'description': 'Parent walking'},
#     {'url': 'https://unsplash.com/photo/ghi', 'description': 'Child in park'}
# ]
```

### KROK 11: Upload featured image
```python
publisher = WordPressPublisher(blog)
featured_image_id = publisher.upload_featured_image(
    image_url=images[0]['url'],
    title=images[0]['description'][:250]  # Obcięte do 250 znaków!
)
# Wynik: 2987 (Media ID w WordPress)
```

### KROK 12: Generowanie tagów SEO
```python
seo_optimizer = SEOOptimizer(ai_adapter)
tags = seo_optimizer.generate_tags(
    title=topic,
    content=full_article,
    category="Akcesoria dziecięce"
)
# Wynik: 12 tagów
# ["wózek dziecięcy", "poradnik dla rodziców", "bezpieczeństwo", ...]
```

### KROK 13: Pobieranie/tworzenie tagów w WordPress
```python
tag_ids = publisher.get_or_create_tags(tags)
# Wynik: [12, 34, 56, 78, 90, 23, 45, 67, 89, 10, 11, 13]
```

### KROK 14: Rotacja autora
```python
authors = publisher.get_authors()
# [{'id': 1, 'name': 'Anna'}, {'id': 2, 'name': 'Kasia'}, ...]

author = author_rotator.get_next_author()
# Wynik: {'id': 2, 'name': 'Kasia'}
```

### KROK 15: Publikacja na WordPress
```python
result = publisher.publish_article({
    'title': topic,
    'content': full_article,
    'category_id': 45,
    'tag_ids': tag_ids,
    'author_id': 2,
    'featured_media': 2987
})

# Wynik:
# {
#     'post_id': 3138,
#     'url': 'https://mamatestuje.com/jak-wybrac-idealny-wozek',
#     'status': 'published'
# }
```

### KROK 16: Zapisanie logu
```python
content_log = ContentLog(
    blog_id=2,
    title=topic,
    content=full_article,
    status='published',
    post_id=3138,
    category_id=45,
    tags=tags,
    featured_image_data=images[0],
    word_count=len(full_article.split()),
    published_at=datetime.utcnow()
)
db.session.add(content_log)
db.session.commit()
```

### KROK 17: Zwrócenie wyniku
```python
return {
    'status': 'success',
    'post_id': 3138,
    'url': 'https://mamatestuje.com/jak-wybrac-idealny-wozek',
    'word_count': 1423,
    'tags_count': 12,
    'execution_time': 245.6  # sekundy
}
```

---

# 16. OSTATNIE POPRAWKI I ZMIANY

## 16.1 Poprawka: Fallback content (20 listopada 2025)

**Problem:**
System publikował 276-słowne placeholder artykuły zamiast pełnych 4000+ słów.

**Przyczyna:**
Błąd w obsłudze wyjątków - zamiast propagować błąd, system używał fallback content.

**Rozwiązanie:**
```python
# PRZED (niepoprawne):
except Exception as e:
    return "Przepraszamy, treść niedostępna..."  # FALLBACK

# PO (poprawne):
except Exception as e:
    logging.error(f"Error: {e}")
    logging.error(traceback.format_exc())
    raise  # Propaguj błąd, nie używaj fallback!
```

## 16.2 Poprawka: Retry mechanism (20 listopada 2025)

**Problem:**
Pojedyncze błędy API (rate limiting, timeout) powodowały całkowitą awarię generowania.

**Rozwiązanie:**
Dodano mechanizm retry z exponential backoff:
- 3 próby
- Opóźnienia: 2s, 5s, 12s
- Obsługa: 429, 503, 504, timeout, connection errors

## 16.3 Poprawka: Image title truncation (20 listopada 2025)

**Problem:**
Unsplash czasem zwraca opisy zdjęć dłuższe niż 255 znaków, co powodowało błąd bazy danych (VARCHAR(255)).

**Rozwiązanie:**
```python
def _truncate_title(self, title, max_length=250):
    if title and len(title) > max_length:
        return title[:max_length] + "..."
    return title
```

## 16.4 Wyłączenie schedulera (21 listopada 2025)

**Zmiana:**
Na żądanie użytkownika wyłączono automatyczny scheduler.

**Lokalizacja:**
`main.py` - skomentowane linie 39-43

**Efekt:**
- Brak automatycznego generowania o 05:00, 06:00, 07:00 UTC
- Wszystkie artykuły tylko przez ręczne generowanie w panelu
- Możliwość ponownego włączenia przez odkomentowanie kodu

---

# PODSUMOWANIE

## Kluczowe komponenty systemu:

1. **ArticleGenerator** - generuje artykuły 1200+ słów używając AI
2. **AutoImageFinder** - wyszukuje obrazy z Unsplash/Pexels
3. **WordPressPublisher** - publikuje na WordPress przez REST API
4. **SEOOptimizer** - generuje 12 tagów SEO
5. **WorkflowEngine** - orkiestruje cały proces
6. **Scheduler** - WYŁĄCZONY (tylko manualne generowanie)

## Aktualny status:

- ✅ Generowanie artykułów: DZIAŁA (tylko ręcznie)
- ✅ Wyszukiwanie obrazów: DZIAŁA
- ✅ Publikacja WordPress: DZIAŁA
- ✅ Generowanie tagów SEO: DZIAŁA
- ❌ Automatyczny scheduler: WYŁĄCZONY
- ✅ Retry mechanism: DZIAŁA
- ✅ Obsługa błędów z pełnym traceback: DZIAŁA

## Koszty:

- Model AI: anthropic/claude-haiku-4.5
- Koszt na artykuł: ~$0.01-0.10
- Koszt miesięczny (270 artykułów): ~$10-30

---

**Dokument utworzony:** 21 listopada 2025  
**Autor:** MASTER AGENT AI System  
**Wersja dokumentu:** 1.0
