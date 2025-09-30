"""
Automation Scheduler

System harmonogramowania i automatycznego wykonywania reguł automatyzacji treści.
Integruje się z workflow engine i zarządza cyklicznym wykonywaniem zadań.
"""
import logging
import time
import schedule
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor

from app import app, db
from models import AutomationRule, Blog
from utils.automation.workflow_engine import execute_automation_rule

# Configure logging
logger = logging.getLogger(__name__)

class AutomationScheduler:
    """
    Główny scheduler do automatycznego wykonywania reguł automatyzacji
    """
    
    def __init__(self, max_workers: int = 3):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.is_running = False
        self.scheduler_thread = None
        
    def start(self):
        """Rozpoczyna scheduler w osobnym wątku"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
            
        self.is_running = True
        
        # NOWA FUNKCJA: Odzyskaj przegapione zadania z dzisiaj
        self.recover_missed_tasks()
        
        self.setup_schedules()
        
        # Uruchom scheduler w osobnym wątku
        self.scheduler_thread = threading.Thread(target=self._run_scheduler)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
        
        logger.info("Automation scheduler started")
    
    def recover_missed_tasks(self):
        """
        Automatyczne odzyskiwanie przegapionych zadań z dzisiaj.
        Sprawdza przy starcie aplikacji czy są zadania batch generation,
        które były zaplanowane na dzisiaj ale zostały pominięte.
        """
        logger.info("🔍 Checking for missed batch generation tasks from today...")
        
        try:
            with app.app_context():
                # Znajdź początek dzisiejszego dnia
                today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                current_time = datetime.utcnow()
                
                # Znajdź wszystkie aktywne reguły z przegapionymi wykonaniami
                missed_rules = AutomationRule.query.filter(
                    AutomationRule.is_active == True,
                    AutomationRule.next_execution_at >= today_start,
                    AutomationRule.next_execution_at < current_time
                ).all()
                
                if not missed_rules:
                    logger.info("✅ No missed tasks found - all caught up!")
                    return
                
                logger.info(f"⚠️  Found {len(missed_rules)} missed tasks from today - recovering now...")
                
                # Wykonaj każde przegapione zadanie
                for rule in missed_rules:
                    try:
                        blog = Blog.query.get(rule.blog_id)
                        if not blog:
                            continue
                        
                        missed_time = rule.next_execution_at.strftime('%H:%M')
                        logger.info(f"🔄 Recovering missed task for {blog.name} (was scheduled at {missed_time})")
                        
                        # Wykonaj batch generation
                        self.batch_generate_articles(blog_id=rule.blog_id)
                        
                        logger.info(f"✅ Successfully recovered missed task for {blog.name}")
                        
                    except Exception as e:
                        logger.error(f"❌ Failed to recover task for rule {rule.id}: {str(e)}")
                        continue
                
                logger.info(f"🎉 Recovery complete - processed {len(missed_rules)} missed tasks")
                
        except Exception as e:
            logger.error(f"Error during task recovery: {str(e)}")
    
    def stop(self):
        """Zatrzymuje scheduler"""
        self.is_running = False
        schedule.clear()
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
            
        self.executor.shutdown(wait=True)
        logger.info("Automation scheduler stopped")
    
    def setup_schedules(self):
        """Konfiguruje harmonogram wykonania zadań - BATCH GENERATION"""
        
        # NOWA LOGIKA: Batch generation dla każdego bloga o ustalonych godzinach
        schedule.every().day.at("07:00").do(self.batch_generate_articles, blog_id=2)  # MamaTestuje - 4 artykuły
        schedule.every().day.at("08:00").do(self.batch_generate_articles, blog_id=3)  # ZnaneKosmetyki - 3 artykuły  
        schedule.every().day.at("09:00").do(self.batch_generate_articles, blog_id=4)  # HomosOnly - 2 artykuły
        
        # STARA LOGIKA: Sprawdzanie reguł co 15 minut (backup)
        schedule.every(15).minutes.do(self.check_and_execute_rules)
        
        # Czyszczenie nieudanych zadań co godzinę
        schedule.every().hour.do(self.cleanup_failed_rules)
        
        # Raport dzienny o 10:00 (po wszystkich batch generation)
        schedule.every().day.at("10:00").do(self.generate_daily_report)
        
        logger.info("Scheduler configured with BATCH GENERATION at 07:00, 08:00, 09:00")
    
    def _run_scheduler(self):
        """Główna pętla schedulera"""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Sprawdzaj co minutę
            except Exception as e:
                logger.error(f"Scheduler error: {str(e)}")
                time.sleep(60)
    
    def batch_generate_articles(self, blog_id: int):
        """
        NOWA FUNKCJA: Generuje wszystkie artykuły dla danego bloga jedną sesją rano
        
        Args:
            blog_id: ID bloga dla którego generować artykuły
        """
        logger.info(f"🚀 BATCH GENERATION START for blog_id={blog_id}")
        
        try:
            with app.app_context():
                # Znajdź aktywną regułę automatyzacji dla tego bloga
                rule = AutomationRule.query.filter(
                    AutomationRule.blog_id == blog_id,
                    AutomationRule.is_active == True
                ).first()
                
                if not rule:
                    logger.error(f"No active automation rule found for blog_id={blog_id}")
                    return
                
                # Pobierz informacje o blogu
                from models import Blog
                blog = Blog.query.get(blog_id)
                if not blog or not blog.active:
                    logger.error(f"Blog {blog_id} not found or inactive")
                    return
                
                logger.info(f"Batch generating {rule.posts_per_day} articles for {blog.name}")
                
                # Oznacz rozpoczęcie batch generation
                rule.last_execution_at = datetime.utcnow()
                db.session.commit()
                
                # BATCH GENERATION: Wygeneruj wszystkie artykuły na raz
                successful_articles = 0
                failed_articles = 0
                
                for article_num in range(rule.posts_per_day):
                    logger.info(f"Generating article {article_num + 1}/{rule.posts_per_day} for {blog.name}")
                    
                    try:
                        # Wykonaj workflow dla pojedynczego artykułu
                        result = execute_automation_rule(rule.id)
                        
                        if result.get("success"):
                            successful_articles += 1
                            logger.info(f"✅ Article {article_num + 1} generated successfully")
                        else:
                            failed_articles += 1
                            logger.error(f"❌ Article {article_num + 1} failed: {result.get('error', 'Unknown error')}")
                            
                    except Exception as e:
                        failed_articles += 1
                        logger.error(f"❌ Exception generating article {article_num + 1}: {str(e)}")
                
                # Podsumowanie batch generation
                logger.info(f"🏁 BATCH GENERATION COMPLETE for {blog.name}: {successful_articles} success, {failed_articles} failed")
                
                # Ustaw następny czas wykonania (jutro o tej samej godzinie)
                self._schedule_next_batch_execution(rule)
                
                # Aktualizuj countery
                if successful_articles > 0:
                    rule.failure_count = 0  # Reset przy sukcesie
                else:
                    rule.failure_count += 1
                    if rule.failure_count >= rule.max_failures:
                        rule.is_active = False
                        logger.error(f"Rule {rule.name} disabled due to batch failures")
                        
                db.session.commit()
                
        except Exception as e:
            logger.error(f"Critical error in batch_generate_articles for blog_id={blog_id}: {str(e)}")
    
    def check_and_execute_rules(self):
        """Sprawdza i wykonuje gotowe do uruchomienia reguły automatyzacji"""
        logger.info("Checking automation rules for execution")
        
        try:
            with app.app_context():
                current_time = datetime.utcnow()
                
                # Znajdź aktywne reguły gotowe do wykonania
                ready_rules = AutomationRule.query.filter(
                    AutomationRule.is_active == True,
                    (AutomationRule.next_execution_at <= current_time) | 
                    (AutomationRule.next_execution_at.is_(None)),
                    AutomationRule.failure_count < AutomationRule.max_failures
                ).all()
                
                logger.info(f"Found {len(ready_rules)} rules ready for execution")
                
                for rule in ready_rules:
                    # Sprawdź czy czas wykonania jest odpowiedni
                    if self._should_execute_rule(rule, current_time):
                        # Wykonaj regułę asynchronicznie
                        self.executor.submit(self._execute_rule_async, rule.id)
                        
                        # Ustaw następny czas wykonania
                        self._schedule_next_execution(rule)
                        
        except Exception as e:
            logger.error(f"Error checking automation rules: {str(e)}")
    
    def _should_execute_rule(self, rule: AutomationRule, current_time: datetime) -> bool:
        """Sprawdza czy reguła powinna być wykonana w danym czasie"""
        
        # Sprawdź dzień tygodnia
        current_weekday = current_time.weekday()  # 0=Monday, 6=Sunday
        rule_days = rule.get_days_list()
        
        if rule_days and current_weekday not in rule_days:
            return False
            
        # Sprawdź godzinę
        current_time_str = current_time.strftime("%H:%M")
        
        # Sprawdź czy jest w oknie czasowym (±30 minut od ustalonej godziny)
        if rule.publishing_time:
            rule_time = datetime.strptime(rule.publishing_time, "%H:%M").time()
            rule_datetime = datetime.combine(current_time.date(), rule_time)
            
            time_diff = abs((current_time - rule_datetime).total_seconds())
            
            # Jeśli różnica jest większa niż 30 minut, nie wykonuj
            if time_diff > 1800:  # 30 minut
                return False
                
        # Sprawdź minimalny interwał między wykonaniami
        if rule.last_execution_at:
            min_interval = timedelta(hours=rule.min_interval_hours)
            if current_time - rule.last_execution_at < min_interval:
                return False
                
        return True
    
    def _execute_rule_async(self, rule_id: int):
        """Wykonuje regułę automatyzacji asynchronicznie"""
        try:
            with app.app_context():
                rule = AutomationRule.query.get(rule_id)
                if not rule:
                    logger.error(f"Rule {rule_id} not found")
                    return
                    
                logger.info(f"Executing automation rule: {rule.name}")
                
                # Oznacz rozpoczęcie wykonania
                rule.last_execution_at = datetime.utcnow()
                db.session.commit()
                
                # Wykonaj regułę przez workflow engine
                result = execute_automation_rule(rule_id)
                
                if result["success"]:
                    # Resetuj licznik błędów przy sukcesie
                    rule.failure_count = 0
                    logger.info(f"Successfully executed rule: {rule.name}")
                else:
                    # Zwiększ licznik błędów przy niepowodzeniu
                    rule.failure_count += 1
                    logger.error(f"Failed to execute rule: {rule.name} - {result.get('error', 'Unknown error')}")
                    
                    # Wyłącz regułę jeśli przekroczyła limit błędów
                    if rule.failure_count >= rule.max_failures:
                        rule.is_active = False
                        logger.error(f"Rule {rule.name} disabled due to too many failures")
                        
                db.session.commit()
                
        except Exception as e:
            logger.error(f"Error executing rule {rule_id}: {str(e)}")
            
            # Zwiększ licznik błędów
            with app.app_context():
                rule = AutomationRule.query.get(rule_id)
                if rule:
                    rule.failure_count += 1
                    if rule.failure_count >= rule.max_failures:
                        rule.is_active = False
                    db.session.commit()
    
    def _schedule_next_batch_execution(self, rule: AutomationRule):
        """
        NOWA FUNKCJA: Planuje następne batch generation - jutro o tej samej godzinie
        
        Args:
            rule: Reguła automatyzacji dla której planować następne batch generation
        """
        try:
            current_time = datetime.utcnow()
            
            # BATCH GENERATION LOGIC: Następny dzień o tej samej godzinie
            if rule.publishing_time:
                # Parsuj godzinę z publishing_time (format "HH:MM")
                time_parts = rule.publishing_time.split(':')
                target_hour = int(time_parts[0])
                target_minute = int(time_parts[1]) if len(time_parts) > 1 else 0
                
                # Następny dzień o tej samej godzinie
                tomorrow = current_time.date() + timedelta(days=1)
                next_execution = datetime.combine(tomorrow, datetime.min.time().replace(hour=target_hour, minute=target_minute))
            else:
                # Fallback: 24 godziny od teraz
                next_execution = current_time + timedelta(days=1)
                
            rule.next_execution_at = next_execution
            db.session.commit()
            
            logger.info(f"🗓️ Next BATCH GENERATION for {rule.name} scheduled at: {next_execution} ({rule.posts_per_day} articles)")
            
        except Exception as e:
            logger.error(f"Error scheduling next batch execution for rule {rule.id}: {str(e)}")
    
    def _schedule_next_execution(self, rule: AutomationRule):
        """STARA FUNKCJA: Planuje następne wykonanie reguły - po jednym artykule na sesję (BACKUP)"""
        try:
            current_time = datetime.utcnow()
            
            # Oblicz interwał między artykułami dla częstszych, krótszych sesji
            if rule.posts_per_day <= 1:
                # Jeden post dziennie - następny dzień o tej samej godzinie
                next_execution = current_time + timedelta(days=1)
            else:
                # Wiele postów dziennie - zoptymalizowany interwał 2.5 godziny
                # Częstsze sesje dla lepszej niezawodności i równomiernego rozkładu
                hours_between_posts = 2.5  # Stały interwał 2.5h zamiast obliczanego
                next_execution = current_time + timedelta(hours=hours_between_posts)
                
            rule.next_execution_at = next_execution
            db.session.commit()
            
            logger.info(f"Next execution for rule {rule.name} scheduled at: {next_execution}")
            
        except Exception as e:
            logger.error(f"Error scheduling next execution for rule {rule.id}: {str(e)}")
    
    def cleanup_failed_rules(self):
        """Czyści reguły z wieloma błędami i resetuje liczniki"""
        logger.info("Running cleanup of failed automation rules")
        
        try:
            with app.app_context():
                # Znajdź wyłączone reguły z błędami
                failed_rules = AutomationRule.query.filter(
                    AutomationRule.is_active == False,
                    AutomationRule.failure_count >= AutomationRule.max_failures
                ).all()
                
                for rule in failed_rules:
                    # Jeśli reguła była wyłączona przez ponad 24 godziny, zresetuj licznik
                    if (rule.last_execution_at and 
                        datetime.utcnow() - rule.last_execution_at > timedelta(days=1)):
                        
                        rule.failure_count = 0
                        logger.info(f"Reset failure count for rule: {rule.name}")
                        
                db.session.commit()
                
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
    
    def generate_daily_report(self):
        """Generuje dzienny raport z wykonanych automatyzacji"""
        logger.info("Generating daily automation report")
        
        try:
            with app.app_context():
                yesterday = datetime.utcnow() - timedelta(days=1)
                
                # Statystyki z ostatnich 24 godzin
                recent_executions = AutomationRule.query.filter(
                    AutomationRule.last_execution_at >= yesterday
                ).all()
                
                active_rules = AutomationRule.query.filter_by(is_active=True).count()
                failed_rules = AutomationRule.query.filter(
                    AutomationRule.failure_count > 0
                ).count()
                
                report = {
                    "date": datetime.utcnow().strftime("%Y-%m-%d"),
                    "executions_24h": len(recent_executions),
                    "active_rules": active_rules,
                    "failed_rules": failed_rules,
                    "executed_rules": [rule.name for rule in recent_executions]
                }
                
                logger.info(f"Daily report: {report}")
                
                # TODO: Wyślij raport przez email lub zapisz w systemie notyfikacji
                
        except Exception as e:
            logger.error(f"Error generating daily report: {str(e)}")
    
    def manual_execute_rule(self, rule_id: int) -> Dict[str, Any]:
        """Ręczne wykonanie reguły automatyzacji"""
        try:
            with app.app_context():
                rule = AutomationRule.query.get(rule_id)
                if not rule:
                    return {"success": False, "error": "Rule not found"}
                    
                if not rule.is_active:
                    return {"success": False, "error": "Rule is not active"}
                    
                logger.info(f"Manual execution of rule: {rule.name}")
                
                # Wykonaj przez executor
                future = self.executor.submit(self._execute_rule_async, rule_id)
                
                return {"success": True, "message": f"Rule {rule.name} execution started"}
                
        except Exception as e:
            logger.error(f"Error in manual rule execution: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """Zwraca status schedulera"""
        with app.app_context():
            active_rules = AutomationRule.query.filter_by(is_active=True).count()
            total_rules = AutomationRule.query.count()
            failed_rules = AutomationRule.query.filter(
                AutomationRule.failure_count > 0
            ).count()
            
            return {
                "is_running": self.is_running,
                "max_workers": self.max_workers,
                "active_rules": active_rules,
                "total_rules": total_rules,
                "failed_rules": failed_rules,
                "next_scheduled_jobs": len(schedule.jobs)
            }

# Global scheduler instance
automation_scheduler = AutomationScheduler()

def start_automation_scheduler():
    """Funkcja pomocnicza do uruchomienia schedulera"""
    automation_scheduler.start()

def stop_automation_scheduler():
    """Funkcja pomocnicza do zatrzymania schedulera"""
    automation_scheduler.stop()

def get_automation_scheduler() -> AutomationScheduler:
    """Zwraca instancję schedulera"""
    return automation_scheduler