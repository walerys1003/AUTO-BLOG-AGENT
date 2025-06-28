"""
Advanced Publication Scheduler for Blog Automation
Creates intelligent 30-day publishing schedules with balanced category distribution
"""
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict, Counter
import random

logger = logging.getLogger(__name__)

class PublicationScheduler:
    """Advanced scheduler for blog content publication"""
    
    def __init__(self, blog_name: str = "MamaTestuje.com"):
        self.blog_name = blog_name
        
        # Kategorie główne dla MamaTestuje.com
        self.main_categories = {
            "Planowanie ciąży": [
                "Przygotowanie do ciąży",
                "Zdrowie przed ciążą", 
                "Żywienie w okresie przedkoncepcyjnym",
                "Suplementacja",
                "Badania przedkoncepcyjne"
            ],
            "Ciąża": [
                "I trymestr",
                "II trymestr", 
                "III trymestr",
                "Żywienie w ciąży",
                "Ćwiczenia w ciąży",
                "Badania prenatalne",
                "Komplikacje ciąży",
                "Psychologia ciąży"
            ],
            "Poród": [
                "Przygotowanie do porodu",
                "Rodzaje porodów",
                "Ból porodowy",
                "Wyprawka do szpitala",
                "Pierwsze dni po porodzie"
            ],
            "Noworodek": [
                "Pielęgnacja noworodka",
                "Karmienie piersią",
                "Karmienie butelką",
                "Sen noworodka",
                "Rozwój noworodka",
                "Zdrowie noworodka"
            ],
            "Niemowlę": [
                "Rozwój niemowlęcia 0-6 miesięcy",
                "Rozwój niemowlęcia 6-12 miesięcy",
                "Żywienie niemowląt",
                "Zabawki dla niemowląt",
                "Pielęgnacja niemowlęcia",
                "Sen niemowlęcia"
            ],
            "Dziecko": [
                "Rozwój dziecka 1-3 lata",
                "Żywienie małych dzieci",
                "Wychowanie i dyscyplina",
                "Zabawki i rozwój",
                "Przedszkole",
                "Zdrowie dziecka"
            ],
            "Rodzicielstwo": [
                "Psychologia rodzicielstwa",
                "Relacje w rodzinie",
                "Organizacja czasu",
                "Finansy rodzinne",
                "Urlopy i wyjazdy z dziećmi",
                "Powrót do pracy"
            ],
            "Zdrowie i uroda": [
                "Zdrowie kobiety",
                "Uroda w ciąży",
                "Dieta i odżywianie",
                "Sport i aktywność",
                "Suplementy",
                "Medycyna naturalna"
            ]
        }
        
        # Godziny publikacji (3-4 artykuły dziennie)
        self.publication_hours = ["08:00", "12:00", "16:00", "20:00"]
    
    def generate_30_day_schedule(self, start_date: datetime = None) -> List[Dict[str, Any]]:
        """
        Generuje harmonogram publikacji na 30 dni z równomiernym rozkładem kategorii
        """
        if start_date is None:
            start_date = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
        
        logger.info(f"Generating 30-day publication schedule starting {start_date}")
        
        schedule = []
        category_usage = defaultdict(int)
        subcategory_usage = defaultdict(int)
        daily_category_tracker = defaultdict(set)
        
        # Przygotuj pule tematów dla każdej podkategorii
        topic_pools = self._prepare_topic_pools()
        
        for day in range(30):
            current_date = start_date + timedelta(days=day)
            daily_articles = []
            daily_categories = set()
            
            # Określ liczbę artykułów na dzień (3-4)
            articles_per_day = 4 if day % 3 == 0 else 3  # Co trzeci dzień 4 artykuły
            
            for article_idx in range(articles_per_day):
                # Wybierz kategorię główną zapewniającą różnorodność
                main_category = self._select_balanced_main_category(
                    daily_categories, category_usage, day
                )
                daily_categories.add(main_category)
                
                # Wybierz podkategorię
                subcategory = self._select_balanced_subcategory(
                    main_category, subcategory_usage
                )
                
                # Wygeneruj temat artykułu
                article_topic = self._generate_unique_topic(
                    main_category, subcategory, topic_pools
                )
                
                # Utwórz wpis harmonogramu
                article_entry = {
                    "date": current_date.strftime("%Y-%m-%d"),
                    "time": self.publication_hours[article_idx],
                    "datetime": current_date.replace(
                        hour=int(self.publication_hours[article_idx].split(":")[0]),
                        minute=int(self.publication_hours[article_idx].split(":")[1])
                    ),
                    "main_category": main_category,
                    "subcategory": subcategory,
                    "title": article_topic["title"],
                    "description": article_topic["description"],
                    "keywords": article_topic["keywords"],
                    "priority": self._calculate_priority(main_category, subcategory, day)
                }
                
                daily_articles.append(article_entry)
                schedule.append(article_entry)
                
                # Aktualizuj liczniki
                category_usage[main_category] += 1
                subcategory_usage[f"{main_category}_{subcategory}"] += 1
                daily_category_tracker[day].add(main_category)
        
        # Walidacja harmonogramu
        self._validate_schedule(schedule)
        
        logger.info(f"Generated schedule with {len(schedule)} articles over 30 days")
        return schedule
    
    def _prepare_topic_pools(self) -> Dict[str, List[Dict[str, Any]]]:
        """Przygotowuje pule tematów dla każdej podkategorii"""
        topic_pools = {}
        
        for main_category, subcategories in self.main_categories.items():
            for subcategory in subcategories:
                # Generuj tematy specyficzne dla podkategorii
                topics = self._generate_subcategory_topics(main_category, subcategory)
                topic_pools[f"{main_category}_{subcategory}"] = topics
        
        return topic_pools
    
    def _generate_subcategory_topics(self, main_category: str, subcategory: str) -> List[Dict[str, Any]]:
        """Generuje specyficzne tematy dla podkategorii"""
        
        # Szablony tematów dla różnych podkategorii
        topic_templates = {
            "Przygotowanie do ciąży": [
                "Jak przygotować się do ciąży - kompletny przewodnik krok po kroku",
                "10 najważniejszych kroków przed zajściem w ciążę - lista kontrolna",
                "Plan przygotowań do ciąży dla par planujących potomstwo",
                "Przygotowanie psychiczne i fizyczne do ciąży - porady specjalistów",
                "Optymalizacja płodności - naturalne sposoby zwiększenia szans na ciążę"
            ],
            "Zdrowie przed ciążą": [
                "Badania przed ciążą - kompletna lista niezbędnych badań",
                "Profilaktyka zdrowotna przed zajściem w ciążę - co warto wiedzieć",
                "Jak poprawić płodność naturalnie - sprawdzone metody",
                "Choroby przewlekłe a planowanie ciąży - porady lekarza",
                "Szczepienia przed ciążą - które są obowiązkowe"
            ],
            "I trymestr": [
                "Pierwszy trymestr ciąży - rozwój dziecka tydzień po tygodniu",
                "Objawy pierwszego trymestru i skuteczne sposoby radzenia sobie",
                "Badania w pierwszym trymestrze ciąży - terminy i znaczenie",
                "Żywienie w pierwszych miesiącach ciąży - co jeść, czego unikać",
                "Nudności ciążowe - naturalne sposoby łagodzenia dolegliwości"
            ],
            "Karmienie piersią": [
                "Jak rozpocząć karmienie piersią - przewodnik dla początkujących mam",
                "Problemy z karmieniem piersią i ich skuteczne rozwiązania",
                "Dieta matki karmiącej - pełnowartościowe menu na każdy dzień",
                "Karmienie piersią a powrót do pracy - praktyczne porady",
                "Odciąganie pokarmu - techniki i najlepsze odciągacze"
            ],
            "Rozwój niemowlęcia 0-6 miesięcy": [
                "Kamienie milowe w rozwoju niemowlęcia - pierwsze 6 miesięcy życia",
                "Jak stymulować rozwój niemowlęcia - zabawy i ćwiczenia",
                "Rozwój motoryczny niemowlęcia miesiąc po miesiącu",
                "Pierwsze uśmiechy, gaworzenie - rozwój społeczny maluszka",
                "Wzorce snu niemowlęcia - jak ustalić zdrowe nawyki"
            ],
            "Żywienie niemowląt": [
                "Wprowadzanie pokarmów stałych - metoda BLW krok po kroku",
                "Pierwsze posiłki niemowlęcia - przepisy na zdrowe przeciery",
                "Alergie pokarmowe u niemowląt - objawy i profilaktyka",
                "Rozszerzanie diety niemowlęcia - harmonogram wprowadzania pokarmów",
                "Karmienie mieszane - jak łączyć pierś z butelką"
            ],
            "Rozwój dziecka 1-3 lata": [
                "Rozwój dziecka w drugim roku życia - co potrafi roczek",
                "Pierwsze słowa i nauka mowy - jak wspierać rozwój językowy",
                "Samodzielność dwulatka - jak wspierać niezależność dziecka",
                "Kryzys dwulatka - zrozumienie i radzenie sobie z trudnymi momentami",
                "Przygotowanie do przedszkola - co powinno umieć 3-latek"
            ],
            "Psychologia rodzicielstwa": [
                "Budowanie więzi z dzieckiem - znaczenie przywiązania",
                "Radzenie sobie ze stresem rodzicielskim - praktyczne strategie",
                "Komunikacja z dzieckiem - jak słuchać i być słuchanym",
                "Ustalanie granic w wychowaniu - pozytywna dyscyplina",
                "Równowaga między życiem zawodowym a rodzicielskim"
            ],
            "Zdrowie kobiety": [
                "Zdrowie kobiety po porodzie - regeneracja organizmu",
                "Depresja poporodowa - rozpoznanie i sposoby leczenia",
                "Powrót do formy po ciąży - bezpieczny trening dla mam",
                "Badania ginekologiczne - jak często i dlaczego są ważne",
                "Hormonalna antykoncepcja a karmienie piersią"
            ]
        }
        
        # Użyj szablonów lub wygeneruj nowe tematy
        if subcategory in topic_templates:
            base_topics = topic_templates[subcategory]
        else:
            base_topics = [
                f"Wszystko o {subcategory.lower()} - kompletny przewodnik dla rodziców",
                f"Najważniejsze aspekty {subcategory.lower()} - porady ekspertów",
                f"Praktyczne porady dotyczące {subcategory.lower()} - sprawdzone metody",
                f"Często zadawane pytania o {subcategory.lower()} - odpowiedzi specjalistów",
                f"{subcategory} krok po kroku - poradnik dla początkujących rodziców"
            ]
        
        # Rozszerz każdy temat o dodatkowe informacje
        topics = []
        for i, title in enumerate(base_topics):
            topic = {
                "title": title,
                "description": f"Szczegółowy artykuł poświęcony {subcategory.lower()} w ramach kategorii {main_category}. Zawiera praktyczne porady, najnowsze badania i opinię ekspertów.",
                "keywords": self._generate_keywords(main_category, subcategory, title),
                "difficulty": "medium",
                "estimated_length": random.randint(1200, 1800),
                "target_audience": self._determine_target_audience(main_category, subcategory)
            }
            topics.append(topic)
        
        return topics
    
    def _select_balanced_main_category(self, daily_categories: set, category_usage: dict, day: int) -> str:
        """Wybiera kategorię główną zapewniającą równowagę"""
        available_categories = list(self.main_categories.keys())
        
        # Jeśli pierwszy artykuł dnia, wybierz najmniej używaną kategorię
        if len(daily_categories) == 0:
            return min(available_categories, key=lambda x: category_usage[x])
        
        # Dla kolejnych artykułów, wybierz kategorię różną od już użytych
        remaining_categories = [cat for cat in available_categories if cat not in daily_categories]
        
        if remaining_categories:
            return min(remaining_categories, key=lambda x: category_usage[x])
        else:
            # Jeśli wszystkie kategorie już użyte, wybierz najmniej używaną
            return min(available_categories, key=lambda x: category_usage[x])
    
    def _select_balanced_subcategory(self, main_category: str, subcategory_usage: dict) -> str:
        """Wybiera podkategorię zapewniającą równowagę"""
        subcategories = self.main_categories[main_category]
        
        # Wybierz najmniej używaną podkategorię
        return min(subcategories, key=lambda x: subcategory_usage[f"{main_category}_{x}"])
    
    def _generate_unique_topic(self, main_category: str, subcategory: str, topic_pools: dict) -> Dict[str, Any]:
        """Generuje unikalny temat artykułu"""
        pool_key = f"{main_category}_{subcategory}"
        
        if pool_key in topic_pools and topic_pools[pool_key]:
            # Użyj tematu z puli i usuń go (zapewnia unikalność)
            return topic_pools[pool_key].pop(0)
        else:
            # Wygeneruj nowy temat jeśli pula wyczerpana
            return {
                "title": f"Przewodnik po {subcategory.lower()} - eksperckie porady i praktyczne wskazówki",
                "description": f"Kompleksowy artykuł o {subcategory.lower()} zawierający najnowsze informacje i sprawdzone metody",
                "keywords": self._generate_keywords(main_category, subcategory, "przewodnik"),
                "difficulty": "medium",
                "estimated_length": 1500,
                "target_audience": self._determine_target_audience(main_category, subcategory)
            }
    
    def _generate_keywords(self, main_category: str, subcategory: str, title: str) -> List[str]:
        """Generuje słowa kluczowe dla artykułu"""
        base_keywords = [main_category.lower(), subcategory.lower()]
        
        # Dodaj słowa z tytułu
        title_words = [word.lower() for word in title.split() if len(word) > 3 and word.lower() not in ['dla', 'jak', 'czy', 'oraz', 'przy', 'przez']]
        base_keywords.extend(title_words[:3])
        
        # Dodaj związane słowa kluczowe
        related_keywords = {
            "ciąża": ["brzuszek", "mama", "dziecko", "rozwój", "trymester"],
            "noworodek": ["pielęgnacja", "karmienie", "sen", "zdrowie", "maluszek"],
            "karmienie": ["pierś", "mleko", "butelka", "odżywianie", "pokarm"],
            "rozwój": ["miesięcznik", "roczek", "umiejętności", "zabawa", "motoryka"],
            "rodzicielstwo": ["wychowanie", "rodzina", "więź", "komunikacja", "granice"],
            "zdrowie": ["badania", "profilaktyka", "leczenie", "objawy", "diagnoza"]
        }
        
        for keyword, related in related_keywords.items():
            if keyword in " ".join(base_keywords).lower():
                base_keywords.extend(related[:2])
        
        return list(set(base_keywords))[:10]  # Maksymalnie 10 unikalnych słów kluczowych
    
    def _determine_target_audience(self, main_category: str, subcategory: str) -> str:
        """Określa docelową grupę odbiorców"""
        audience_map = {
            "Planowanie ciąży": "Kobiety planujące ciążę, pary chcące mieć dziecko",
            "Ciąża": "Kobiety w ciąży, przyszłe mamy",
            "Poród": "Kobiety w zaawansowanej ciąży, przygotowujące się do porodu",
            "Noworodek": "Świeżo upieczone mamy, rodzice noworodków",
            "Niemowlę": "Rodzice niemowląt (0-12 miesięcy)",
            "Dziecko": "Rodzice małych dzieci (1-3 lata)",
            "Rodzicielstwo": "Wszystkie grupy rodziców, osoby zainteresowane wychowaniem",
            "Zdrowie i uroda": "Kobiety w ciąży i po porodzie, mamy dbające o zdrowie"
        }
        
        return audience_map.get(main_category, "Rodzice i osoby planujące rodzicielstwo")
    
    def _calculate_priority(self, main_category: str, subcategory: str, day: int) -> int:
        """Oblicza priorytet artykułu"""
        # Wyższy priorytet dla niektórych kategorii
        high_priority_categories = ["Ciąża", "Noworodek", "Planowanie ciąży"]
        
        base_priority = 5
        if main_category in high_priority_categories:
            base_priority += 2
        
        # Wyższy priorytet w weekendy (więcej czasu na czytanie)
        if day % 7 in [5, 6]:  # Sobota, Niedziela
            base_priority += 1
        
        return min(base_priority, 10)
    
    def _validate_schedule(self, schedule: List[Dict[str, Any]]) -> None:
        """Waliduje poprawność harmonogramu"""
        # Sprawdź czy każdego dnia są minimum 2 różne kategorie główne
        daily_categories = defaultdict(set)
        for article in schedule:
            day = article["date"]
            daily_categories[day].add(article["main_category"])
        
        violations = []
        for day, categories in daily_categories.items():
            if len(categories) < 2:
                violations.append(f"Dzień {day}: tylko {len(categories)} kategoria główna")
        
        if violations:
            logger.warning(f"Naruszenia zasad różnorodności: {violations}")
        
        # Sprawdź czy każda podkategoria ma przynajmniej 1 artykuł
        subcategory_count = defaultdict(int)
        for article in schedule:
            key = f"{article['main_category']}_{article['subcategory']}"
            subcategory_count[key] += 1
        
        all_subcategories = []
        for main_cat, subcats in self.main_categories.items():
            for subcat in subcats:
                all_subcategories.append(f"{main_cat}_{subcat}")
        
        missing_subcategories = [sub for sub in all_subcategories if subcategory_count[sub] == 0]
        if missing_subcategories:
            logger.warning(f"Brakujące podkategorie w harmonogramie: {missing_subcategories}")
    
    def export_schedule_to_csv(self, schedule: List[Dict[str, Any]], filename: str = None) -> str:
        """Eksportuje harmonogram do pliku CSV"""
        if filename is None:
            filename = f"harmonogram_{self.blog_name}_{datetime.now().strftime('%Y%m%d')}.csv"
        
        import csv
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['data', 'godzina', 'kategoria_glowna', 'podkategoria', 'tytul', 'opis', 'slowa_kluczowe', 'priorytet', 'grupa_docelowa']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for article in schedule:
                writer.writerow({
                    'data': article['date'],
                    'godzina': article['time'],
                    'kategoria_glowna': article['main_category'],
                    'podkategoria': article['subcategory'],
                    'tytul': article['title'],
                    'opis': article['description'],
                    'slowa_kluczowe': ', '.join(article['keywords']),
                    'priorytet': article['priority'],
                    'grupa_docelowa': article.get('target_audience', '')
                })
        
        return filename


def create_30_day_schedule(blog_name: str = "MamaTestuje.com", export_csv: bool = True) -> Dict[str, Any]:
    """
    Główna funkcja tworząca 30-dniowy harmonogram publikacji
    """
    try:
        scheduler = PublicationScheduler(blog_name)
        schedule = scheduler.generate_30_day_schedule()
        
        result = {
            "success": True,
            "blog_name": blog_name,
            "total_articles": len(schedule),
            "schedule": schedule,
            "stats": _generate_schedule_stats(schedule, scheduler.main_categories)
        }
        
        if export_csv:
            csv_filename = scheduler.export_schedule_to_csv(schedule)
            result["csv_file"] = csv_filename
        
        return result
        
    except Exception as e:
        logger.error(f"Error creating publication schedule: {str(e)}")
        return {"success": False, "error": str(e)}


def _generate_schedule_stats(schedule: List[Dict[str, Any]], categories: Dict[str, List[str]]) -> Dict[str, Any]:
    """Generuje szczegółowe statystyki harmonogramu"""
    stats = {
        "total_articles": len(schedule),
        "articles_per_day": round(len(schedule) / 30, 1),
        "category_distribution": defaultdict(int),
        "subcategory_distribution": defaultdict(int),
        "daily_category_diversity": [],
        "weekly_distribution": defaultdict(int)
    }
    
    daily_categories = defaultdict(set)
    
    for article in schedule:
        stats["category_distribution"][article["main_category"]] += 1
        stats["subcategory_distribution"][article["subcategory"]] += 1
        daily_categories[article["date"]].add(article["main_category"])
        
        # Dodaj statystyki tygodniowe
        date_obj = datetime.strptime(article["date"], "%Y-%m-%d")
        week_number = date_obj.isocalendar()[1]
        stats["weekly_distribution"][f"Tydzień {week_number}"] += 1
    
    # Oblicz różnorodność kategorii na dzień
    for day, categories_set in daily_categories.items():
        stats["daily_category_diversity"].append(len(categories_set))
    
    stats["avg_daily_category_diversity"] = round(
        sum(stats["daily_category_diversity"]) / len(stats["daily_category_diversity"]), 1
    )
    
    # Sprawdź pokrycie wszystkich podkategorii
    all_subcategories = set()
    for main_cat, subcats in categories.items():
        for subcat in subcats:
            all_subcategories.add(subcat)
    
    covered_subcategories = set(stats["subcategory_distribution"].keys())
    stats["subcategory_coverage"] = {
        "total_subcategories": len(all_subcategories),
        "covered_subcategories": len(covered_subcategories),
        "coverage_percentage": round((len(covered_subcategories) / len(all_subcategories)) * 100, 1)
    }
    
    return dict(stats)