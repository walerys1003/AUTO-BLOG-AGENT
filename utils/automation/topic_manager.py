"""
Topic Approval System

System zarządzający tematami - generowanie, zatwierdzanie, tracking statusu i automatyczne odświeżanie puli.
"""
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

from app import db
from models import ArticleTopic, Blog, AutomationRule, Category
from utils.ai_content_strategy.topic_generator import generate_ai_topics_for_category
from utils.content.ai_adapter import get_default_ai_service

# Configure logging
logger = logging.getLogger(__name__)

class TopicStatus(Enum):
    """Statusy tematów"""
    PENDING = "pending"       # Oczekuje na zatwierdzenie
    APPROVED = "approved"     # Zatwierdzony do użycia
    REJECTED = "rejected"     # Odrzucony
    USED = "used"            # Już użyty do artykułu
    ARCHIVED = "archived"     # Zarchiwizowany

class TopicPriority(Enum):
    """Priorytety tematów"""
    LOW = 1
    MEDIUM = 3
    HIGH = 5
    URGENT = 7

class TopicManager:
    """
    Główna klasa zarządzająca tematami w systemie
    """
    
    def __init__(self):
        self.ai_service = get_default_ai_service()
        
    def bulk_approve_topics(self, topic_ids: List[int], user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Masowe zatwierdzanie tematów.
        
        Args:
            topic_ids: Lista ID tematów do zatwierdzenia
            user_id: ID użytkownika zatwierdzającego (opcjonalne)
            
        Returns:
            Wynik operacji z liczbą zatwierdzonych tematów
        """
        logger.info(f"Bulk approving {len(topic_ids)} topics")
        
        try:
            approved_count = 0
            failed_topics = []
            
            for topic_id in topic_ids:
                topic = ArticleTopic.query.get(topic_id)
                if topic and topic.status == TopicStatus.PENDING.value:
                    topic.status = TopicStatus.APPROVED.value
                    topic.approved_at = datetime.utcnow()
                    topic.approved_by = user_id
                    approved_count += 1
                else:
                    failed_topics.append(topic_id)
                    
            db.session.commit()
            
            logger.info(f"Successfully approved {approved_count} topics")
            
            return {
                "success": True,
                "approved_count": approved_count,
                "failed_topics": failed_topics,
                "message": f"Zatwierdzono {approved_count} tematów"
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Bulk topic approval failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def bulk_reject_topics(self, topic_ids: List[int], reason: str = "", user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Masowe odrzucanie tematów.
        
        Args:
            topic_ids: Lista ID tematów do odrzucenia
            reason: Powód odrzucenia
            user_id: ID użytkownika odrzucającego
            
        Returns:
            Wynik operacji
        """
        logger.info(f"Bulk rejecting {len(topic_ids)} topics")
        
        try:
            rejected_count = 0
            
            for topic_id in topic_ids:
                topic = ArticleTopic.query.get(topic_id)
                if topic and topic.status == TopicStatus.PENDING.value:
                    topic.status = TopicStatus.REJECTED.value
                    topic.rejected_at = datetime.utcnow()
                    topic.rejected_by = user_id
                    topic.rejection_reason = reason
                    rejected_count += 1
                    
            db.session.commit()
            
            logger.info(f"Successfully rejected {rejected_count} topics")
            
            return {
                "success": True,
                "rejected_count": rejected_count,
                "message": f"Odrzucono {rejected_count} tematów"
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Bulk topic rejection failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def set_topic_priority(self, topic_id: int, priority: int) -> Dict[str, Any]:
        """
        Ustala priorytet tematu.
        
        Args:
            topic_id: ID tematu
            priority: Priorytet (1-7)
            
        Returns:
            Wynik operacji
        """
        try:
            topic = ArticleTopic.query.get(topic_id)
            if not topic:
                return {"success": False, "error": "Topic not found"}
                
            topic.priority = priority
            topic.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Set priority {priority} for topic {topic_id}")
            
            return {
                "success": True,
                "message": f"Priorytet tematu został ustawiony na {priority}"
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to set topic priority: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_topics_for_approval(self, blog_id: int, category: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """
        Pobiera tematy oczekujące na zatwierdzenie.
        
        Args:
            blog_id: ID bloga
            category: Opcjonalnie filtruj po kategorii
            limit: Maksymalna liczba tematów
            
        Returns:
            Lista tematów do zatwierdzenia
        """
        try:
            query = ArticleTopic.query.filter_by(
                blog_id=blog_id,
                status=TopicStatus.PENDING.value
            ).order_by(ArticleTopic.created_at.desc())
            
            if category:
                query = query.filter_by(category=category)
                
            topics = query.limit(limit).all()
            
            result = []
            for topic in topics:
                result.append({
                    "id": topic.id,
                    "topic": topic.topic,
                    "category": topic.category,
                    "priority": topic.priority,
                    "created_at": topic.created_at.isoformat(),
                    "description": getattr(topic, 'description', ''),
                    "estimated_words": getattr(topic, 'estimated_words', 0)
                })
                
            return result
            
        except Exception as e:
            logger.error(f"Failed to get topics for approval: {str(e)}")
            return []
    
    def get_topic_statistics(self, blog_id: int) -> Dict[str, Any]:
        """
        Pobiera statystyki tematów dla bloga.
        
        Args:
            blog_id: ID bloga
            
        Returns:
            Statystyki tematów
        """
        try:
            stats = {
                "total": 0,
                "pending": 0,
                "approved": 0,
                "rejected": 0,
                "used": 0,
                "by_category": {},
                "by_priority": {},
                "recent_activity": {}
            }
            
            # Ogólne statystyki
            for status in TopicStatus:
                count = ArticleTopic.query.filter_by(
                    blog_id=blog_id,
                    status=status.value
                ).count()
                stats[status.value] = count
                stats["total"] += count
                
            # Statystyki po kategoriach
            categories = db.session.query(
                ArticleTopic.category,
                db.func.count(ArticleTopic.id).label('count')
            ).filter_by(blog_id=blog_id).group_by(ArticleTopic.category).all()
            
            for category, count in categories:
                stats["by_category"][category] = count
                
            # Statystyki po priorytetach
            priorities = db.session.query(
                ArticleTopic.priority,
                db.func.count(ArticleTopic.id).label('count')
            ).filter_by(blog_id=blog_id).group_by(ArticleTopic.priority).all()
            
            for priority, count in priorities:
                stats["by_priority"][priority] = count
                
            # Aktywność w ostatnich 7 dniach
            week_ago = datetime.utcnow() - timedelta(days=7)
            recent_topics = ArticleTopic.query.filter(
                ArticleTopic.blog_id == blog_id,
                ArticleTopic.created_at >= week_ago
            ).count()
            
            stats["recent_activity"]["topics_created_last_week"] = recent_topics
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get topic statistics: {str(e)}")
            return {}
    
    def auto_refresh_topic_pool(self, blog_id: int, min_approved_topics: int = 10) -> Dict[str, Any]:
        """
        Automatycznie odświeża pulę tematów jeśli jest za mało zatwierdzonych.
        
        Args:
            blog_id: ID bloga
            min_approved_topics: Minimalna liczba zatwierdzonych tematów
            
        Returns:
            Wynik operacji odświeżania
        """
        logger.info(f"Auto-refreshing topic pool for blog {blog_id}")
        
        try:
            blog = Blog.query.get(blog_id)
            if not blog:
                return {"success": False, "error": "Blog not found"}
                
            # Sprawdź ile mamy zatwierdzonych tematów
            approved_count = ArticleTopic.query.filter_by(
                blog_id=blog_id,
                status=TopicStatus.APPROVED.value,
                used=False
            ).count()
            
            if approved_count >= min_approved_topics:
                return {
                    "success": True,
                    "message": f"Topic pool is sufficient ({approved_count} approved topics)",
                    "topics_generated": 0
                }
                
            # Pobierz kategorie z bloga lub z aktywnych reguł automatyzacji
            categories = self._get_blog_categories(blog_id)
            
            if not categories:
                return {"success": False, "error": "No categories found for topic generation"}
                
            topics_generated = 0
            
            for category in categories[:5]:  # Maksymalnie 5 kategorii na raz
                try:
                    # Sprawdź ile tematów ma już ta kategoria
                    category_topics = ArticleTopic.query.filter_by(
                        blog_id=blog_id,
                        category=category,
                        status=TopicStatus.APPROVED.value,
                        used=False
                    ).count()
                    
                    # Generuj nowe tematy jeśli potrzeba
                    if category_topics < 3:  # Minimum 3 tematy per kategoria
                        new_topics = generate_ai_topics_for_category(category, 10)
                        
                        for topic_text in new_topics:
                            # Sprawdź czy temat już istnieje
                            existing = ArticleTopic.query.filter_by(
                                blog_id=blog_id,
                                topic=topic_text
                            ).first()
                            
                            if not existing:
                                topic = ArticleTopic(
                                    blog_id=blog_id,
                                    topic=topic_text,
                                    category=category,
                                    status=TopicStatus.PENDING.value,
                                    priority=TopicPriority.MEDIUM.value,
                                    created_at=datetime.utcnow()
                                )
                                db.session.add(topic)
                                topics_generated += 1
                                
                except Exception as e:
                    logger.error(f"Failed to generate topics for category {category}: {str(e)}")
                    continue
                    
            db.session.commit()
            
            logger.info(f"Generated {topics_generated} new topics for blog {blog_id}")
            
            return {
                "success": True,
                "topics_generated": topics_generated,
                "message": f"Wygenerowano {topics_generated} nowych tematów"
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Auto-refresh topic pool failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def mark_topic_as_used(self, topic_id: int, article_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Oznacza temat jako użyty.
        
        Args:
            topic_id: ID tematu
            article_id: ID artykułu (opcjonalne)
            
        Returns:
            Wynik operacji
        """
        try:
            topic = ArticleTopic.query.get(topic_id)
            if not topic:
                return {"success": False, "error": "Topic not found"}
                
            topic.used = True
            topic.used_at = datetime.utcnow()
            topic.status = TopicStatus.USED.value
            
            if article_id:
                topic.article_id = article_id
                
            db.session.commit()
            
            logger.info(f"Marked topic {topic_id} as used")
            
            return {"success": True, "message": "Temat został oznaczony jako użyty"}
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to mark topic as used: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def cleanup_old_topics(self, blog_id: int, days_old: int = 30) -> Dict[str, Any]:
        """
        Czyści stare, nieużywane tematy.
        
        Args:
            blog_id: ID bloga
            days_old: Wiek tematów w dniach do usunięcia
            
        Returns:
            Wynik operacji
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            old_topics = ArticleTopic.query.filter(
                ArticleTopic.blog_id == blog_id,
                ArticleTopic.created_at < cutoff_date,
                ArticleTopic.status.in_([TopicStatus.REJECTED.value, TopicStatus.PENDING.value]),
                ArticleTopic.used == False
            ).all()
            
            deleted_count = len(old_topics)
            
            for topic in old_topics:
                db.session.delete(topic)
                
            db.session.commit()
            
            logger.info(f"Cleaned up {deleted_count} old topics for blog {blog_id}")
            
            return {
                "success": True,
                "deleted_count": deleted_count,
                "message": f"Usunięto {deleted_count} starych tematów"
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Topic cleanup failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _get_blog_categories(self, blog_id: int) -> List[str]:
        """
        Pobiera kategorie dla bloga z aktywnych reguł automatyzacji.
        """
        try:
            # Pobierz kategorie z aktywnych reguł automatyzacji
            active_rules = AutomationRule.query.filter_by(
                blog_id=blog_id,
                active=True
            ).all()
            
            categories = set()
            for rule in active_rules:
                rule_categories = rule.get_categories()
                categories.update(rule_categories)
                
            if categories:
                return list(categories)
                
            # Fallback: pobierz z modelu Category jeśli istnieją
            blog_categories = Category.query.filter_by(blog_id=blog_id).all()
            if blog_categories:
                return [cat.name for cat in blog_categories]
                
            # Ostatni fallback: pobierz z JSON w modelu Blog
            blog = Blog.query.get(blog_id)
            if blog and blog.categories:
                blog_cats = blog.get_categories()
                if blog_cats:
                    return [cat.get('name', '') for cat in blog_cats if cat.get('name')]
                    
            return []
            
        except Exception as e:
            logger.error(f"Failed to get blog categories: {str(e)}")
            return []

def get_topic_manager() -> TopicManager:
    """
    Factory function do pobierania instancji TopicManager.
    """
    return TopicManager()