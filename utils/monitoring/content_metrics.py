"""
Moduł monitorowania metryk związanych z generowaniem treści.

Zapewnia funkcje do śledzenia:
- Czasu generowania artykułów
- Długości generowanych artykułów
- Współczynników powodzenia 
- Liczby użytych tokenów

Pozwala na łatwe monitorowanie wydajności i szybkie wykrywanie problemów.
"""

import os
import json
import time
import logging
from datetime import datetime
from pathlib import Path
import re

# Konfiguracja logowania
logger = logging.getLogger(__name__)

# Domyślna lokalizacja dla przechowywania metryk
METRICS_DIR = os.path.join("logs", "content_metrics")

# Upewnij się, że katalog istnieje
os.makedirs(METRICS_DIR, exist_ok=True)

class ContentMetricsTracker:
    """Klasa do śledzenia metryk generowania treści"""
    
    def __init__(self, metrics_dir=METRICS_DIR):
        """Inicjalizacja trackera metryk"""
        self.metrics_dir = metrics_dir
        self.current_metrics = {
            "timestamp_start": "",
            "timestamp_end": "",
            "duration_seconds": 0,
            "topic": "",
            "generation_type": "",  # "word_based" lub "paragraph_based"
            "success": False,
            "content_length_chars": 0,
            "content_length_words": 0,
            "paragraphs_count": 0,
            "tokens_used": 0,
            "error": None
        }
        
        # Upewnij się, że katalog metryk istnieje
        os.makedirs(self.metrics_dir, exist_ok=True)
    
    def start_tracking(self, topic, generation_type):
        """Rozpocznij śledzenie generowania artykułu"""
        self.current_metrics = {
            "timestamp_start": datetime.now().isoformat(),
            "timestamp_end": "",
            "duration_seconds": 0,
            "topic": topic,
            "generation_type": generation_type,
            "success": False,
            "content_length_chars": 0,
            "content_length_words": 0,
            "paragraphs_count": 0,
            "tokens_used": 0,
            "error": None
        }
        logger.info(f"Rozpoczęto śledzenie generowania artykułu: {topic} (metoda: {generation_type})")
        return self
    
    def end_tracking(self, success=True, error=None):
        """Zakończ śledzenie i zapisz metryki"""
        end_time = datetime.now()
        start_time = datetime.fromisoformat(self.current_metrics["timestamp_start"])
        duration = (end_time - start_time).total_seconds()
        
        self.current_metrics["timestamp_end"] = end_time.isoformat()
        self.current_metrics["duration_seconds"] = duration
        self.current_metrics["success"] = success
        if error:
            self.current_metrics["error"] = str(error)
        
        self._save_metrics()
        
        logger.info(f"Zakończono śledzenie generowania artykułu: {self.current_metrics['topic']}")
        logger.info(f"Czas generowania: {duration:.2f} sekund")
        logger.info(f"Status: {'Sukces' if success else 'Błąd'}")
        if self.current_metrics["content_length_words"] > 0:
            logger.info(f"Długość artykułu: {self.current_metrics['content_length_words']} słów")
        return self.current_metrics
    
    def set_content_metrics(self, content):
        """Ustaw metryki związane z zawartością artykułu"""
        if not content:
            return self
        
        # Liczba znaków
        self.current_metrics["content_length_chars"] = len(content)
        
        # Liczba słów (przybliżona, po usunięciu tagów HTML)
        clean_content = re.sub(r'<[^>]*>', ' ', content)
        words = clean_content.split()
        self.current_metrics["content_length_words"] = len(words)
        
        # Liczba akapitów
        self.current_metrics["paragraphs_count"] = content.count("<p>")
        
        return self
    
    def set_tokens_used(self, tokens):
        """Ustaw liczbę tokenów użytych do generowania"""
        self.current_metrics["tokens_used"] = tokens
        return self
    
    def _save_metrics(self):
        """Zapisz metryki do pliku JSON"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        topic_slug = self.current_metrics["topic"].lower().replace(" ", "_")[:30]
        filename = f"metrics_{topic_slug}_{timestamp}.json"
        filepath = os.path.join(self.metrics_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.current_metrics, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Zapisano metryki do pliku: {filepath}")
        return filepath
    
    @staticmethod
    def count_words(text):
        """Liczy słowa w tekście HTML"""
        # Usunięcie tagów HTML
        clean_text = re.sub(r'<[^>]*>', ' ', text)
        # Podział na słowa i liczenie
        words = clean_text.split()
        return len(words)
    
    @staticmethod
    def get_recent_metrics(limit=10):
        """Pobiera ostatnie metryki generowania treści"""
        metrics_files = sorted(
            Path(METRICS_DIR).glob("metrics_*.json"),
            key=os.path.getmtime,
            reverse=True
        )[:limit]
        
        metrics = []
        for file in metrics_files:
            try:
                with open(file, "r", encoding="utf-8") as f:
                    metrics.append(json.load(f))
            except Exception as e:
                logger.error(f"Błąd podczas odczytu pliku metryk {file}: {str(e)}")
        
        return metrics
    
    @staticmethod
    def calculate_average_metrics(days=7):
        """Oblicza średnie metryki z ostatnich X dni"""
        # Oblicz datę graniczną
        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        metrics_files = Path(METRICS_DIR).glob("metrics_*.json")
        successful_generations = []
        failed_generations = []
        
        for file in metrics_files:
            # Sprawdź czy plik jest młodszy niż X dni
            if os.path.getmtime(file) >= cutoff_date:
                try:
                    with open(file, "r", encoding="utf-8") as f:
                        metrics = json.load(f)
                        if metrics["success"]:
                            successful_generations.append(metrics)
                        else:
                            failed_generations.append(metrics)
                except Exception as e:
                    logger.error(f"Błąd podczas odczytu pliku metryk {file}: {str(e)}")
        
        # Oblicz średnie dla udanych generacji
        avg_metrics = {
            "period_days": days,
            "total_generations": len(successful_generations) + len(failed_generations),
            "successful_generations": len(successful_generations),
            "failed_generations": len(failed_generations),
            "success_rate": 0,
            "avg_duration_seconds": 0,
            "avg_content_length_words": 0,
            "avg_paragraphs_count": 0,
            "avg_tokens_used": 0
        }
        
        if avg_metrics["total_generations"] > 0:
            avg_metrics["success_rate"] = len(successful_generations) / avg_metrics["total_generations"]
        
        if successful_generations:
            avg_metrics["avg_duration_seconds"] = sum(m["duration_seconds"] for m in successful_generations) / len(successful_generations)
            avg_metrics["avg_content_length_words"] = sum(m["content_length_words"] for m in successful_generations) / len(successful_generations)
            avg_metrics["avg_paragraphs_count"] = sum(m["paragraphs_count"] for m in successful_generations) / len(successful_generations)
            
            # Tokeny mogą nie być dostępne we wszystkich metrykach
            tokens_metrics = [m for m in successful_generations if m.get("tokens_used", 0) > 0]
            if tokens_metrics:
                avg_metrics["avg_tokens_used"] = sum(m["tokens_used"] for m in tokens_metrics) / len(tokens_metrics)
        
        return avg_metrics


# Funkcja pomocnicza do łatwego użycia
def track_content_generation(func):
    """Dekorator do śledzenia metryk generowania treści"""
    def wrapper(*args, **kwargs):
        # Ekstrakcja parametrów z argumentów funkcji
        topic = args[0] if args else kwargs.get("topic", "Unknown Topic")
        generation_type = "paragraph_based" if "paragraph_count" in kwargs else "word_based"
        
        # Inicjalizacja trackera
        tracker = ContentMetricsTracker().start_tracking(topic, generation_type)
        
        try:
            # Wywołanie oryginalnej funkcji
            result = func(*args, **kwargs)
            
            # Ustawienie metryk treści, jeśli generowanie się powiodło
            if result and "content" in result:
                tracker.set_content_metrics(result["content"])
            
            # Zapisanie metryk
            tracker.end_tracking(success=bool(result and "content" in result))
            return result
        except Exception as e:
            # W przypadku błędu, zapisz informacje o błędzie
            logger.error(f"Błąd podczas generowania treści: {str(e)}")
            tracker.end_tracking(success=False, error=str(e))
            raise
    
    return wrapper