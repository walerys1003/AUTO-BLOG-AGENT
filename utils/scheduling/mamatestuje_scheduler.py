"""
Zaktualizowany scheduler dla MamaTestuje.com używający prawdziwych kategorii WordPress
"""
import logging
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
from collections import defaultdict

logger = logging.getLogger(__name__)

class MamaTestujeScheduler:
    """Scheduler dopasowany do prawdziwych kategorii MamaTestuje.com"""
    
    def __init__(self):
        self.blog_name = "MamaTestuje.com"
        
        # Prawdziwe kategorie MamaTestuje.com z WordPress (produktowo-recenzyjne)
        self.main_categories = {
            "Planowanie ciąży": [
                "Testy ciążowe",
                "Testy płodności", 
                "Wsparcie płodności"
            ],
            "Zdrowie w ciąży": [
                "Witaminy ciążowe",
                "Układ moczowy",
                "Odporność w ciąży",
                "Mdłości i nudności",
                "Zaparcia i wzdęcia"
            ],
            "Kosmetyki dla mam": [
                "Nawilżające",
                "Okolice intymne",
                "Pielęgnacja biustu",
                "Pielęgnacja nóg",
                "Przeciw rozstępom",
                "Ujędrniające"
            ],
            "Bielizna poporodowa": [
                "Majtki i wkłady",
                "Pasy"
            ],
            "Laktacja i karmienie": [
                "Laktatory",
                "Podgrzewacze i sterylizatory",
                "Przechowywanie",
                "Wkładki laktacyjne i muszle"
            ],
            "Karmienie dziecka": [
                "Witaminy",
                "Mleka dla dzieci",
                "Zupki dla dzieci",
                "Obiadki dla dzieci",
                "Kaszki dla dzieci",
                "Deserki, Słodycze i przekąski",
                "Herbatki dla dzieci",
                "Żywienie medyczne dzieci"
            ],
            "Przewijanie dziecka": [
                "Pieluchy dla dzieci",
                "Chusteczki nawilżane",
                "Podkłady do przewijania"
            ],
            "Kosmetyki dla dzieci": [
                "Balsamy i emolienty",
                "Kąpiel dziecka",
                "Kremy dla dzieci",
                "Oliwki dla dzieci",
                "Pasty do zębów dla dzieci",
                "Preparaty na ciemieniuchę",
                "Pudry i zasypki",
                "Szampony dla dzieci"
            ],
            "Zdrowie dziecka": [
                "Odporność i witaminy",
                "Infekcje i przeziębienia",
                "Zdrowe trawienie i apetyt",
                "Higiena i pielęgnacja",
                "Problemy alergiczne i specjalistyczne",
                "Podróże i choroba lokomocyjna",
                "Urazy i pierwsza pomoc",
                "Rozwój i koncentracja"
            ],
            "Akcesoria dziecięce": [
                "Aspiratory i higiena nosa",
                "Karmienie niemowląt",
                "Gryzaki i zabawki",
                "Pielęgnacja włosów i paznokci",
                "Higiena codzienna",
                "Naczynia i sztućce dla dzieci",
                "Śliniaki i ochrona odzieży",
                "Pomiar temperatury"
            ]
        }
        
        # Godziny publikacji (3-4 artykuły dziennie)
        self.publication_hours = ["08:00", "12:00", "16:00", "20:00"]
        
        # Szablony tematów produktowo-recenzyjnych
        self.topic_templates = {
            "Testy ciążowe": [
                "Najlepsze testy ciążowe 2025 - ranking i recenzje",
                "Jakie testy ciążowe są najdokładniejsze - porównanie marek",
                "Test ciążowy cyfrowy vs tradycyjny - który wybrać",
                "Kiedy robić test ciążowy - poradnik krok po kroku",
                "Najpopularniejsze testy ciążowe - opinie i ceny"
            ],
            "Testy płodności": [
                "Najlepsze testy płodności dla kobiet - ranking 2025",
                "Domowe testy płodności - jak działają i czy warto",
                "Test owulacji vs test płodności - różnice i zastosowanie",
                "Testy płodności dla mężczyzn - przegląd dostępnych opcji",
                "Ile kosztują testy płodności - porównanie cen"
            ],
            "Witaminy ciążowe": [
                "Najlepsze witaminy ciążowe - ranking 2025",
                "Kwas foliowy w ciąży - które preparaty wybrać",
                "Witaminy prenatalne - porównanie składów i cen",
                "DHA w ciąży - najlepsze suplementy omega-3",
                "Żelazo w ciąży - przegląd najskuteczniejszych preparatów"
            ],
            "Laktatory": [
                "Najlepsze laktatory 2025 - ranking i test popularnych modeli",
                "Laktator ręczny vs elektryczny - który wybrać",
                "Philips Avent vs Medela - porównanie najlepszych laktatorów",
                "Akcesoria do laktatorów - co jest niezbędne",
                "Ile kosztuje dobry laktator - przegląd cen"
            ],
            "Pieluchy dla dzieci": [
                "Najlepsze pieluchy dla dzieci - test i ranking 2025",
                "Pampers vs Huggies - które pieluchy wybrać",
                "Pieluchy ekologiczne - przegląd najlepszych marek",
                "Pieluchy na noc - które najlepiej chłoną",
                "Rozmiary pieluch - jak dobrać odpowiedni size"
            ],
            "Mleka dla dzieci": [
                "Najlepsze mleka modyfikowane - ranking 2025",
                "Mleko HA vs zwykłe mleko modyfikowane - różnice",
                "Mleka bez laktozy dla dzieci - przegląd opcji",
                "Mleka organiczne dla dzieci - czy warto dopłacać",
                "Przejście z mleka 1 na 2 - kiedy i jak to zrobić"
            ],
            "Kremy dla dzieci": [
                "Najlepsze kremy dla dzieci - ranking 2025",
                "Kremy na odparzenia - które najszybciej pomagają",
                "Kremy nawilżające dla dzieci z atopowym zapaleniem skóry",
                "Naturalne kremy dla dzieci - bezpieczne składniki",
                "Kremy z filtrem UV dla dzieci - ochrona przed słońcem"
            ],
            "Odporność i witaminy": [
                "Najlepsze witaminy na odporność dla dzieci - ranking",
                "Witamina D dla dzieci - które preparaty wybrać",
                "Syropy na odporność - przegląd skutecznych produktów",
                "Probiotyki dla dzieci - które najlepiej wspierają odporność",
                "Naturalne sposoby wzmacniania odporności u dzieci"
            ]
        }
    
    def generate_30_day_schedule(self, start_date: datetime = None) -> List[Dict[str, Any]]:
        """Generuje 30-dniowy harmonogram publikacji dla MamaTestuje.com"""
        if start_date is None:
            start_date = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
        
        schedule = []
        all_subcategories = []
        
        # Przygotuj listę wszystkich podkategorii z wagami
        for main_cat, subcats in self.main_categories.items():
            for subcat in subcats:
                # Przypisz wagi na podstawie popularności kategorii
                weight = self._get_category_weight(main_cat, subcat)
                all_subcategories.extend([(main_cat, subcat)] * weight)
        
        # Przetasuj dla losowości
        random.shuffle(all_subcategories)
        
        # Generuj harmonogram na 30 dni (100 artykułów)
        current_date = start_date
        article_count = 0
        target_articles = 100
        
        for day in range(30):
            daily_categories = set()
            articles_per_day = 3 if day % 7 in [0, 6] else 4  # Mniej w weekendy
            
            for hour_idx in range(articles_per_day):
                if article_count >= target_articles:
                    break
                    
                # Wybierz kategorię zapewniając różnorodność
                main_cat, subcat = self._select_balanced_category(
                    daily_categories, all_subcategories, article_count
                )
                
                # Wygeneruj temat
                topic = self._generate_topic(main_cat, subcat)
                
                # Ustaw godzinę publikacji
                hour = self.publication_hours[hour_idx % len(self.publication_hours)]
                
                # Utworz wpis harmonogramu
                schedule_entry = {
                    "date": current_date.strftime("%Y-%m-%d"),
                    "time": hour,
                    "datetime": current_date.replace(
                        hour=int(hour.split(':')[0]),
                        minute=int(hour.split(':')[1])
                    ),
                    "main_category": main_cat,
                    "subcategory": subcat,
                    "title": topic["title"],
                    "description": topic["description"],
                    "keywords": topic["keywords"],
                    "priority": topic["priority"],
                    "estimated_length": topic["estimated_length"]
                }
                
                schedule.append(schedule_entry)
                daily_categories.add(main_cat)
                article_count += 1
            
            # Następny dzień
            current_date += timedelta(days=1)
        
        logger.info(f"Wygenerowano harmonogram: {len(schedule)} artykułów na 30 dni")
        return schedule
    
    def _get_category_weight(self, main_category: str, subcategory: str) -> int:
        """Zwraca wagę dla kategorii (częstość występowania w harmonogramie)"""
        # Kategorie o wysokim priorytecie
        high_priority = [
            "Testy ciążowe", "Witaminy ciążowe", "Pieluchy dla dzieci",
            "Mleka dla dzieci", "Laktatory", "Kremy dla dzieci"
        ]
        
        # Kategorie o średnim priorytecie
        medium_priority = [
            "Testy płodności", "Odporność i witaminy", "Kąpiel dziecka",
            "Nawilżające", "Gryzaki i zabawki"
        ]
        
        if subcategory in high_priority:
            return 4  # Będą występować częściej
        elif subcategory in medium_priority:
            return 3
        else:
            return 2  # Standardowa częstość
    
    def _select_balanced_category(self, daily_categories: set, all_subcategories: List, article_count: int):
        """Wybiera kategorię zapewniając równowagę i różnorodność"""
        # Najpierw spróbuj wybrać kategorię, której jeszcze nie było dzisiaj
        available_today = [
            (main, sub) for main, sub in all_subcategories 
            if main not in daily_categories
        ]
        
        if available_today:
            return random.choice(available_today)
        else:
            # Jeśli wszystkie kategorie główne już były, wybierz losowo
            return random.choice(all_subcategories)
    
    def _generate_topic(self, main_category: str, subcategory: str) -> Dict[str, Any]:
        """Generuje temat artykułu dla podkategorii"""
        # Użyj szablonu jeśli istnieje
        if subcategory in self.topic_templates:
            title = random.choice(self.topic_templates[subcategory])
        else:
            # Fallback dla kategorii bez szablonów
            templates = [
                f"Najlepsze {subcategory.lower()} - ranking i test 2025",
                f"Jak wybrać {subcategory.lower()} - poradnik dla rodziców",
                f"{subcategory} - porównanie marek i cen",
                f"Test {subcategory.lower()} - które produkty wybrać",
                f"{subcategory} - opinie ekspertów i użytkowników"
            ]
            title = random.choice(templates)
        
        # Generuj słowa kluczowe
        keywords = self._generate_keywords(main_category, subcategory, title)
        
        # Ustaw priorytet
        priority = self._calculate_priority(main_category, subcategory)
        
        return {
            "title": title,
            "description": f"Szczegółowy test i ranking produktów z kategorii {subcategory}. "
                          f"Porównanie najlepszych marek, cen i opinii użytkowników.",
            "keywords": keywords,
            "priority": priority,
            "estimated_length": random.randint(1500, 2500),  # Dłuższe artykuły produktowe
            "type": "product_review"
        }
    
    def _generate_keywords(self, main_category: str, subcategory: str, title: str) -> List[str]:
        """Generuje słowa kluczowe SEO"""
        keywords = []
        
        # Podstawowe słowa z kategorii
        keywords.extend([
            subcategory.lower(),
            main_category.lower().replace(" ", " "),
            "ranking",
            "test",
            "porównanie"
        ])
        
        # Słowa z tytułu
        title_words = title.lower().split()
        keywords.extend([word for word in title_words if len(word) > 3])
        
        # Usuń duplikaty i zachowaj pierwsze 8
        return list(dict.fromkeys(keywords))[:8]
    
    def _calculate_priority(self, main_category: str, subcategory: str) -> int:
        """Oblicza priorytet artykułu (1-10)"""
        # Wysokie priorytety dla popularnych kategorii
        high_priority_categories = [
            "Testy ciążowe", "Witaminy ciążowe", "Pieluchy dla dzieci", "Mleka dla dzieci"
        ]
        
        medium_priority_categories = [
            "Laktatory", "Kremy dla dzieci", "Odporność i witaminy"
        ]
        
        if subcategory in high_priority_categories:
            return random.randint(7, 9)
        elif subcategory in medium_priority_categories:
            return random.randint(5, 7)
        else:
            return random.randint(3, 6)


def create_mamatestuje_schedule(export_csv: bool = True) -> Dict[str, Any]:
    """Funkcja pomocnicza do tworzenia harmonogramu"""
    try:
        scheduler = MamaTestujeScheduler()
        schedule = scheduler.generate_30_day_schedule()
        
        # Oblicz statystyki
        stats = _calculate_schedule_stats(schedule, scheduler.main_categories)
        
        result = {
            "success": True,
            "schedule": schedule,
            "total_articles": len(schedule),
            "stats": stats
        }
        
        if export_csv:
            csv_filename = _export_to_csv(schedule)
            result["csv_file"] = csv_filename
        
        return result
        
    except Exception as e:
        logger.error(f"Błąd tworzenia harmonogramu: {str(e)}")
        return {"success": False, "error": str(e)}


def _calculate_schedule_stats(schedule: List[Dict[str, Any]], categories: Dict[str, List[str]]) -> Dict[str, Any]:
    """Oblicza statystyki harmonogramu"""
    stats = {
        "articles_per_day": round(len(schedule) / 30, 1),
        "category_distribution": defaultdict(int),
        "subcategory_distribution": defaultdict(int),
        "avg_daily_category_diversity": 0,
        "total_subcategories": sum(len(subcats) for subcats in categories.values()),
        "covered_subcategories": 0,
        "coverage_percentage": 0
    }
    
    # Policz rozkład kategorii
    daily_categories = defaultdict(set)
    covered_subcats = set()
    
    for article in schedule:
        stats["category_distribution"][article["main_category"]] += 1
        stats["subcategory_distribution"][article["subcategory"]] += 1
        daily_categories[article["date"]].add(article["main_category"])
        covered_subcats.add(article["subcategory"])
    
    # Oblicz średnią różnorodność dzienną
    diversity_sum = sum(len(cats) for cats in daily_categories.values())
    stats["avg_daily_category_diversity"] = round(diversity_sum / len(daily_categories), 1)
    
    # Oblicz pokrycie podkategorii
    stats["covered_subcategories"] = len(covered_subcats)
    stats["coverage_percentage"] = round(
        (len(covered_subcats) / stats["total_subcategories"]) * 100, 1
    )
    
    # Dodaj szczegóły pokrycia
    stats["subcategory_coverage"] = {
        "total_subcategories": stats["total_subcategories"],
        "covered_subcategories": stats["covered_subcategories"],
        "coverage_percentage": stats["coverage_percentage"]
    }
    
    return stats


def _export_to_csv(schedule: List[Dict[str, Any]]) -> str:
    """Eksportuje harmonogram do CSV"""
    import csv
    import os
    
    filename = f"harmonogram_mamatestuje_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    filepath = os.path.join("data", filename)
    
    # Utwórz katalog jeśli nie istnieje
    os.makedirs("data", exist_ok=True)
    
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['date', 'time', 'main_category', 'subcategory', 'title', 'priority', 'keywords']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for article in schedule:
            writer.writerow({
                'date': article['date'],
                'time': article['time'],
                'main_category': article['main_category'],
                'subcategory': article['subcategory'],
                'title': article['title'],
                'priority': article['priority'],
                'keywords': ', '.join(article['keywords'])
            })
    
    logger.info(f"Harmonogram wyeksportowany do: {filepath}")
    return filename