"""
Workflow Automation Engine

Centralny silnik zarządzający całym cyklem automatycznego generowania i publikacji treści.
Integruje wszystkie komponenty systemu w jeden spójny workflow.
"""
import logging
import time
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

from app import db
from models import (
    AutomationRule, Blog, Article, ArticleTopic, Category, 
    ContentMetrics, ImageLibrary, Notification
)
from utils.ai_content_strategy.topic_generator import generate_ai_topics_for_category
from utils.ai_content_strategy.article_generator import generate_article_from_topic
from utils.images.auto_image_finder import find_article_images
from utils.wordpress.client import build_wp_api_url
from social.autopost import post_article_to_social_media
import requests
from utils.content.ai_adapter import get_default_ai_service

# Configure logging
logger = logging.getLogger(__name__)

class WorkflowStatus(Enum):
    """Status możliwych stanów workflow"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

class WorkflowStep(Enum):
    """Kroki w procesie workflow"""
    TOPIC_GENERATION = "topic_generation"
    TOPIC_SELECTION = "topic_selection"
    CONTENT_GENERATION = "content_generation"
    IMAGE_ACQUISITION = "image_acquisition"
    WORDPRESS_PUBLISHING = "wordpress_publishing"
    SOCIAL_MEDIA_POSTING = "social_media_posting"
    METRICS_UPDATE = "metrics_update"

class WorkflowEngine:
    """
    Centralny silnik workflow dla automatyzacji treści
    """
    
    def __init__(self):
        self.ai_service = get_default_ai_service()
        self.current_step = None
        self.workflow_id = None
        
    def execute_full_cycle(self, automation_rule: AutomationRule) -> Dict[str, Any]:
        """
        Wykonuje pełny cykl automatyzacji dla danej reguły.
        
        Args:
            automation_rule: Reguła automatyzacji do wykonania
            
        Returns:
            Dict z wynikami wykonania workflow
        """
        workflow_id = f"workflow_{automation_rule.id}_{int(time.time())}"
        self.workflow_id = workflow_id
        
        logger.info(f"Starting workflow {workflow_id} for automation rule: {automation_rule.name}")
        
        # Inicjalizacja wyników workflow
        workflow_result = {
            "workflow_id": workflow_id,
            "automation_rule_id": automation_rule.id,
            "status": WorkflowStatus.RUNNING.value,
            "started_at": datetime.utcnow(),
            "steps_completed": [],
            "steps_failed": [],
            "article_id": None,
            "wordpress_post_id": None,
            "social_media_posts": [],
            "errors": [],
            "metrics": {}
        }
        
        try:
            # Krok 1: Sprawdzenie i generowanie tematów
            topic_result = self._execute_topic_management(automation_rule)
            workflow_result["steps_completed"].append(WorkflowStep.TOPIC_GENERATION.value)
            
            if not topic_result["success"]:
                workflow_result["errors"].append(f"Topic management failed: {topic_result['error']}")
                workflow_result["status"] = WorkflowStatus.FAILED.value
                return workflow_result
                
            # Krok 2: Wybór tematu do artykułu
            selected_topic = self._select_topic_for_article(automation_rule)
            workflow_result["steps_completed"].append(WorkflowStep.TOPIC_SELECTION.value)
            
            if not selected_topic:
                workflow_result["errors"].append("No approved topics available for article generation")
                workflow_result["status"] = WorkflowStatus.FAILED.value
                return workflow_result
                
            # Krok 3: Generowanie artykułu
            article_result = self._execute_content_generation(automation_rule, selected_topic)
            workflow_result["steps_completed"].append(WorkflowStep.CONTENT_GENERATION.value)
            
            if not article_result["success"]:
                workflow_result["errors"].append(f"Content generation failed: {article_result['error']}")
                workflow_result["status"] = WorkflowStatus.FAILED.value
                return workflow_result
                
            workflow_result["article_id"] = article_result["article_id"]
            
            # Krok 4: Pobieranie obrazów
            image_result = self._execute_image_acquisition(article_result["article"])
            workflow_result["steps_completed"].append(WorkflowStep.IMAGE_ACQUISITION.value)
            
            if not image_result["success"]:
                logger.warning(f"Image acquisition failed: {image_result['error']}")
                # Obrazy nie są krytyczne - kontynuujemy bez nich
                
            # Krok 5: Publikacja na WordPress
            if automation_rule.auto_publish:
                publish_result = self._execute_wordpress_publishing(article_result["article"], automation_rule)
                workflow_result["steps_completed"].append(WorkflowStep.WORDPRESS_PUBLISHING.value)
                
                if publish_result["success"]:
                    workflow_result["wordpress_post_id"] = publish_result["post_id"]
                    
                    # Krok 6: Posty w social media (tylko jeśli publikacja się udała)
                    if automation_rule.auto_social_post:
                        social_result = self._execute_social_media_posting(article_result["article"], automation_rule)
                        workflow_result["steps_completed"].append(WorkflowStep.SOCIAL_MEDIA_POSTING.value)
                        workflow_result["social_media_posts"] = social_result.get("posts", [])
                else:
                    workflow_result["errors"].append(f"WordPress publishing failed: {publish_result['error']}")
                    
            # Krok 7: Aktualizacja metryki
            metrics_result = self._update_workflow_metrics(workflow_result, automation_rule)
            workflow_result["steps_completed"].append(WorkflowStep.METRICS_UPDATE.value)
            workflow_result["metrics"] = metrics_result
            
            # Oznacz jako zakończone
            workflow_result["status"] = WorkflowStatus.COMPLETED.value
            workflow_result["completed_at"] = datetime.utcnow()
            
            logger.info(f"Workflow {workflow_id} completed successfully")
            
            # Wysłanie powiadomienia o sukcesie
            self._create_notification(
                f"Workflow completed successfully",
                f"Article '{article_result['article'].title}' was generated and processed",
                "success"
            )
            
        except Exception as e:
            logger.error(f"Workflow {workflow_id} failed with exception: {str(e)}")
            logger.error(traceback.format_exc())
            
            workflow_result["status"] = WorkflowStatus.FAILED.value
            workflow_result["errors"].append(f"Unexpected error: {str(e)}")
            workflow_result["failed_at"] = datetime.utcnow()
            
            # Wysłanie powiadomienia o błędzie
            self._create_notification(
                f"Workflow failed",
                f"Automation rule '{automation_rule.name}' failed: {str(e)}",
                "error"
            )
            
        return workflow_result
    
    def _execute_topic_management(self, automation_rule: AutomationRule) -> Dict[str, Any]:
        """
        Zarządza tematami - sprawdza dostępność i generuje nowe jeśli potrzeba.
        """
        logger.info(f"Executing topic management for rule: {automation_rule.name}")
        
        try:
            blog = Blog.query.get(automation_rule.blog_id)
            if not blog:
                return {"success": False, "error": "Blog not found"}
                
            # Sprawdź dostępne zatwierdzone tematy
            approved_topics = ArticleTopic.query.filter_by(
                blog_id=automation_rule.blog_id,
                status='approved'
            ).filter(
                ArticleTopic.category.in_(automation_rule.get_categories())
            ).count()
            
            # Jeśli mało tematów, wygeneruj nowe
            if approved_topics < 5:  # Próg minimalny
                logger.info(f"Low topic count ({approved_topics}), generating new topics")
                
                for category_name in automation_rule.get_categories():
                    try:
                        # Generuj tematy dla kategorii
                        new_topics = generate_ai_topics_for_category(category_name, 10)
                        
                        # Zapisz tematy w bazie
                        for topic_text in new_topics:
                            existing = ArticleTopic.query.filter_by(
                                blog_id=automation_rule.blog_id,
                                topic=topic_text
                            ).first()
                            
                            if not existing:
                                new_topic = ArticleTopic(
                                    blog_id=automation_rule.blog_id,
                                    topic=topic_text,
                                    category=category_name,
                                    status='approved' if automation_rule.auto_approve_topics else 'pending',
                                    priority=5,  # Domyślny priorytet
                                    created_at=datetime.utcnow()
                                )
                                db.session.add(new_topic)
                                
                        db.session.commit()
                        logger.info(f"Generated {len(new_topics)} topics for category: {category_name}")
                        
                    except Exception as e:
                        logger.error(f"Error generating topics for category {category_name}: {str(e)}")
                        continue
                        
            return {"success": True, "topics_generated": True}
            
        except Exception as e:
            logger.error(f"Topic management failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _select_topic_for_article(self, automation_rule: AutomationRule) -> Optional[ArticleTopic]:
        """
        Wybiera najlepszy temat do wygenerowania artykułu.
        """
        logger.info("Selecting topic for article generation")
        
        try:
            # Znajdź zatwierdzone tematy dla tej reguły
            available_topics = ArticleTopic.query.filter_by(
                blog_id=automation_rule.blog_id,
                status='approved',
                used=False
            ).filter(
                ArticleTopic.category.in_(automation_rule.get_categories())
            ).order_by(ArticleTopic.priority.desc(), ArticleTopic.created_at.asc()).all()
            
            if not available_topics:
                logger.warning("No approved topics available")
                return None
                
            # Wybierz pierwszy (najwyższy priorytet, najstarszy)
            selected_topic = available_topics[0]
            
            # Oznacz jako używany
            selected_topic.used = True
            selected_topic.used_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Selected topic: {selected_topic.topic}")
            return selected_topic
            
        except Exception as e:
            logger.error(f"Topic selection failed: {str(e)}")
            return None
    
    def _execute_content_generation(self, automation_rule: AutomationRule, topic: ArticleTopic) -> Dict[str, Any]:
        """
        Generuje artykuł na podstawie wybranego tematu.
        """
        logger.info(f"Generating content for topic: {topic.topic}")
        
        try:
            blog = Blog.query.get(automation_rule.blog_id)
            
            # Generuj artykuł
            article_result = generate_article_from_topic(
                topic=topic.topic,
                category=topic.category,
                blog_name=blog.name,
                target_length=automation_rule.article_length or 1600,
                ai_service=self.ai_service
            )
            
            if not article_result["success"]:
                return {"success": False, "error": article_result["error"]}
                
            # Zapisz artykuł w bazie
            article = Article(
                blog_id=automation_rule.blog_id,
                title=article_result["title"],
                content=article_result["content"],
                excerpt=article_result.get("excerpt", ""),
                status="ready" if automation_rule.auto_publish else "draft",
                category_id=topic.category,
                token_count=article_result.get("token_count", 0),
                paragraph_count=article_result.get("paragraph_count", 0),
                metrics_data=article_result.get("metrics", {}),
                created_at=datetime.utcnow()
            )
            
            db.session.add(article)
            db.session.commit()
            
            logger.info(f"Article created with ID: {article.id}")
            
            return {
                "success": True,
                "article_id": article.id,
                "article": article,
                "content_metrics": article_result.get("metrics", {})
            }
            
        except Exception as e:
            logger.error(f"Content generation failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _execute_image_acquisition(self, article: Article) -> Dict[str, Any]:
        """
        Pobiera obrazy dla artykułu.
        """
        logger.info(f"Acquiring images for article: {article.title}")
        
        try:
            # Znajdź obrazy dla artykułu
            image_results = find_article_images(
                article_title=article.title,
                article_content=article.content,
                max_images=3
            )
            
            if image_results and len(image_results) > 0:
                # Ustaw pierwszy obraz jako featured image
                article.featured_image_url = image_results[0]["url"]
                
                # Zapisz obrazy w bibliotece
                for img in image_results:
                    image_entry = ImageLibrary(
                        blog_id=article.blog_id,
                        title=img.get("title", article.title),
                        url=img["url"],
                        source=img.get("source", "auto"),
                        tags=img.get("tags", ""),
                        created_at=datetime.utcnow()
                    )
                    db.session.add(image_entry)
                
                db.session.commit()
                logger.info(f"Found {len(image_results)} images for article")
                
                return {"success": True, "images_found": len(image_results)}
            else:
                logger.warning("No images found for article")
                return {"success": False, "error": "No images found"}
                
        except Exception as e:
            logger.error(f"Image acquisition failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _execute_wordpress_publishing(self, article: Article, automation_rule: AutomationRule) -> Dict[str, Any]:
        """
        Publikuje artykuł na WordPress.
        """
        logger.info(f"Publishing article to WordPress: {article.title}")
        
        try:
            blog = Blog.query.get(automation_rule.blog_id)
            if not blog:
                return {"success": False, "error": "Blog not found"}
            
            # Przygotuj dane do publikacji
            post_data = {
                "title": article.title,
                "content": article.content,
                "excerpt": article.excerpt,
                "status": "publish" if automation_rule.auto_publish else "draft",
                "featured_media": None  # TODO: Upload featured image first
            }
            
            # Dodaj kategorię jeśli istnieje
            if article.category_id:
                post_data["categories"] = [article.category_id]
            
            # Publikuj na WordPress przez API
            api_url = build_wp_api_url(blog.api_url, "posts")
            auth = (blog.username, blog.api_token)
            
            response = requests.post(api_url, auth=auth, json=post_data)
            response.raise_for_status()
            
            post_result = response.json()
            
            if post_result and "id" in post_result:
                # Aktualizuj artykuł z ID WordPress
                article.post_id = post_result["id"]
                article.status = "published"
                article.published_at = datetime.utcnow()
                db.session.commit()
                
                logger.info(f"Article published to WordPress with ID: {post_result['id']}")
                return {"success": True, "post_id": post_result["id"]}
            else:
                return {"success": False, "error": "WordPress API returned invalid response"}
                
        except Exception as e:
            logger.error(f"WordPress publishing failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _execute_social_media_posting(self, article: Article, automation_rule: AutomationRule) -> Dict[str, Any]:
        """
        Publikuje posty w social media dla artykułu.
        """
        logger.info(f"Posting to social media for article: {article.title}")
        
        try:
            blog = Blog.query.get(automation_rule.blog_id)
            social_accounts = blog.social_accounts if hasattr(blog, 'social_accounts') else []
            
            if not social_accounts:
                logger.warning("No social media accounts configured")
                return {"success": True, "posts": [], "message": "No social accounts configured"}
                
            posts_created = []
            
            for social_account in social_accounts:
                if social_account.active:
                    try:
                        # Tworzenie posta dla platformy
                        post_result = post_article_to_social_media(
                            article=article,
                            social_account=social_account,
                            blog_url=blog.url
                        )
                        
                        if post_result.get("success"):
                            posts_created.append({
                                "platform": social_account.platform,
                                "post_id": post_result.get("post_id"),
                                "url": post_result.get("url")
                            })
                            
                    except Exception as e:
                        logger.error(f"Failed to post to {social_account.platform}: {str(e)}")
                        continue
                        
            logger.info(f"Created {len(posts_created)} social media posts")
            return {"success": True, "posts": posts_created}
            
        except Exception as e:
            logger.error(f"Social media posting failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _update_workflow_metrics(self, workflow_result: Dict, automation_rule: AutomationRule) -> Dict[str, Any]:
        """
        Aktualizuje metryki workflow.
        """
        logger.info("Updating workflow metrics")
        
        try:
            # Oblicz czas wykonania
            started_at = workflow_result["started_at"]
            completed_at = workflow_result.get("completed_at", datetime.utcnow())
            execution_time = (completed_at - started_at).total_seconds()
            
            # Przygotuj metryki
            metrics = {
                "execution_time_seconds": execution_time,
                "steps_completed": len(workflow_result["steps_completed"]),
                "steps_failed": len(workflow_result["steps_failed"]),
                "success_rate": len(workflow_result["steps_completed"]) / 7 * 100,  # 7 kroków total
                "article_generated": workflow_result["article_id"] is not None,
                "wordpress_published": workflow_result["wordpress_post_id"] is not None,
                "social_posts_created": len(workflow_result["social_media_posts"]),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Zapisz metryki w bazie (jeśli artykuł został utworzony)
            if workflow_result["article_id"]:
                content_metrics = ContentMetrics(
                    blog_id=automation_rule.blog_id,
                    article_id=workflow_result["article_id"],
                    automation_rule_id=automation_rule.id,
                    workflow_id=workflow_result["workflow_id"],
                    execution_time=execution_time,
                    steps_completed=len(workflow_result["steps_completed"]),
                    success=workflow_result["status"] == WorkflowStatus.COMPLETED.value,
                    error_details="; ".join(workflow_result["errors"]) if workflow_result["errors"] else None,
                    created_at=datetime.utcnow()
                )
                db.session.add(content_metrics)
                db.session.commit()
                
            return metrics
            
        except Exception as e:
            logger.error(f"Metrics update failed: {str(e)}")
            return {"error": str(e)}
    
    def _create_notification(self, title: str, message: str, type: str = "info"):
        """
        Tworzy powiadomienie w systemie.
        """
        try:
            notification = Notification(
                title=title,
                message=message,
                type=type,
                read=False,
                created_at=datetime.utcnow()
            )
            db.session.add(notification)
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Failed to create notification: {str(e)}")

def execute_automation_rule(automation_rule_id: int) -> Dict[str, Any]:
    """
    Funkcja pomocnicza do wykonania reguły automatyzacji.
    
    Args:
        automation_rule_id: ID reguły automatyzacji
        
    Returns:
        Wynik wykonania workflow
    """
    try:
        automation_rule = AutomationRule.query.get(automation_rule_id)
        if not automation_rule:
            return {"success": False, "error": f"Automation rule {automation_rule_id} not found"}
            
        if not automation_rule.active:
            return {"success": False, "error": f"Automation rule {automation_rule_id} is not active"}
            
        # Utwórz silnik workflow i wykonaj
        engine = WorkflowEngine()
        result = engine.execute_full_cycle(automation_rule)
        
        return {"success": True, "workflow_result": result}
        
    except Exception as e:
        logger.error(f"Failed to execute automation rule {automation_rule_id}: {str(e)}")
        return {"success": False, "error": str(e)}