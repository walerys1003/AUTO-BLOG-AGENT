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
    ContentMetrics, ImageLibrary, Notification, ContentLog
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
    
    def _select_author_for_article(self, category: str, article_id: int) -> Dict[str, Any]:
        """
        Wybiera autora na podstawie kategorii i systemu rotacji MamaTestuje.com
        """
        # Autorzy MamaTestuje.com z równymi wagami (25% każdy)
        authors = {
            2: {
                "name": "Tomasz Kotliński",
                "wordpress_id": 2,
                "specialties": ["Planowanie ciąży", "Zdrowie w ciąży", "Kosmetyki dla mam", "Laktacja i karmienie"],
                "weight": 25
            },
            5: {
                "name": "Gabriela Bielec", 
                "wordpress_id": 5,
                "specialties": ["Karmienie dziecka", "Kosmetyki dla dzieci", "Akcesoria dziecięce"],
                "weight": 25
            },
            4: {
                "name": "Helena Rybikowska",
                "wordpress_id": 4, 
                "specialties": ["Zdrowie dziecka", "Przewijanie dziecka"],
                "weight": 25
            },
            3: {
                "name": "Zofia Chryplewicz",
                "wordpress_id": 3,
                "specialties": ["Kosmetyki dla mam", "Bielizna poporodowa"],
                "weight": 25
            }
        }
        
        # Znajdź specjalistów dla kategorii
        specialists = []
        all_authors = []
        
        for author_id, author_data in authors.items():
            if category in author_data["specialties"]:
                specialists.append(author_data)
            all_authors.append(author_data)
        
        # Preferuj specjalistów (80% szans)
        import random
        if specialists and random.random() < 0.8:
            available_authors = specialists
        else:
            available_authors = all_authors
        
        # Rotacja na podstawie ID artykułu i wag
        author_pool = []
        for author in available_authors:
            repetitions = max(1, int(author["weight"] / 10))
            author_pool.extend([author] * repetitions)
        
        # Wybierz autora
        if author_pool:
            selected_author = author_pool[article_id % len(author_pool)]
        else:
            selected_author = authors[2]  # Fallback na Tomasz Kotliński
            
        logger.info(f"Selected author for article {article_id}: {selected_author['name']}")
        return selected_author
    
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
                                new_topic = ArticleTopic()
                                new_topic.blog_id = automation_rule.blog_id
                                new_topic.topic = topic_text
                                new_topic.category = category_name
                                new_topic.status = 'approved' if automation_rule.auto_approve_topics else 'pending'
                                new_topic.priority = 5
                                new_topic.created_at = datetime.utcnow()
                                if automation_rule.auto_approve_topics:
                                    new_topic.approved_at = datetime.utcnow()
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
            
            logger.info(f"Selected topic: {selected_topic.title}")
            return selected_topic
            
        except Exception as e:
            logger.error(f"Topic selection failed: {str(e)}")
            return None
    
    def _execute_content_generation(self, automation_rule: AutomationRule, topic: ArticleTopic, max_retries: int = 2) -> Dict[str, Any]:
        """
        Generuje artykuł na podstawie wybranego tematu z retry mechanism.
        """
        logger.info(f"Generating content for topic: {topic.title}")
        
        for attempt in range(max_retries + 1):
            try:
                logger.info(f"Content generation attempt {attempt + 1}/{max_retries + 1}")
                
                blog = Blog.query.get(automation_rule.blog_id)
                
                # Timeout protection - max 3 minutes per article
                import signal
                import threading
                
                def timeout_handler():
                    raise TimeoutError("Article generation timeout after 3 minutes")
                
                timer = threading.Timer(180.0, timeout_handler)  # 3 minutes
                timer.start()
                
                try:
                    # Generuj artykuł z timeout protection
                    article_result = generate_article_from_topic(
                        category=topic.category,
                        topic=topic.title
                    )
                finally:
                    timer.cancel()
                
                if not article_result or not article_result.get("title"):
                    if attempt < max_retries:
                        logger.warning(f"Content generation returned empty result, retrying ({attempt + 1}/{max_retries})")
                        continue
                    return {"success": False, "error": "Failed to generate article content after retries"}
                
                # Enhanced content validation using the new validator
                from utils.content.content_validator import validate_before_publication
                
                title = article_result.get("title", "")
                excerpt = article_result.get("excerpt", "")
                content = article_result.get("content", "")
                
                # Basic length check first
                if len(content) < 200:
                    if attempt < max_retries:
                        logger.warning(f"Generated content too short, retrying ({attempt + 1}/{max_retries})")
                        continue
                    logger.warning("Generated content is very short but using it anyway")
                
                # Comprehensive validation
                is_valid, validation_errors = validate_before_publication(title, excerpt, content, topic.category)
                
                if not is_valid and len(validation_errors) > 3:  # Allow minor issues
                    if attempt < max_retries:
                        logger.warning(f"Content validation failed with {len(validation_errors)} errors, retrying ({attempt + 1}/{max_retries})")
                        for error in validation_errors[:3]:  # Log first 3 errors
                            logger.warning(f"   - {error}")
                        continue
                    else:
                        logger.warning(f"Content validation failed but using anyway after {max_retries} attempts")
                elif validation_errors:
                    logger.info(f"Minor content issues detected: {len(validation_errors)} warnings")
                else:
                    logger.info("Content validation passed successfully")
                
                # Generate 12 SEO tags
                from utils.seo.tag_generator import generate_seo_tags
                seo_tags = generate_seo_tags(title, content, topic.category)
                logger.info(f"Generated {len(seo_tags)} SEO tags")
                
                # Zapisz artykuł w bazie z lepszą obsługą błędów i 12 tagami
                try:
                    article = ContentLog()
                    article.blog_id = automation_rule.blog_id
                    article.title = article_result["title"]
                    article.content = article_result["content"]
                    article.excerpt = article_result.get("excerpt", "")[:200] if article_result.get("excerpt") else ""
                    article.status = "ready" if automation_rule.auto_publish else "draft"
                    article.category_id = None  # Zostanie ustawione podczas publikacji
                    article.created_at = datetime.utcnow()
                    
                    # Set exactly 12 SEO tags
                    article.set_tags(seo_tags)
                    
                    db.session.add(article)
                    db.session.commit()
                    
                    logger.info(f"Article created successfully with ID: {article.id}")
                    
                    return {
                        "success": True,
                        "article_id": article.id,
                        "article": article,
                        "content_metrics": article_result.get("metrics", {}),
                        "attempts": attempt + 1
                    }
                    
                except Exception as db_error:
                    db.session.rollback()
                    logger.error(f"Database error saving article: {str(db_error)}")
                    if attempt < max_retries:
                        logger.info(f"Database error, retrying ({attempt + 1}/{max_retries})")
                        continue
                    return {"success": False, "error": f"Database error: {str(db_error)}"}
                
            except TimeoutError as e:
                logger.error(f"Content generation timeout on attempt {attempt + 1}: {str(e)}")
                if attempt < max_retries:
                    logger.info(f"Timeout occurred, retrying ({attempt + 1}/{max_retries})")
                    continue
                return {"success": False, "error": "Content generation timeout after multiple attempts"}
                
            except Exception as e:
                logger.error(f"Content generation error on attempt {attempt + 1}: {str(e)}")
                if attempt < max_retries:
                    logger.info(f"Error occurred, retrying ({attempt + 1}/{max_retries})")
                    continue
                return {"success": False, "error": f"Content generation failed after {max_retries + 1} attempts: {str(e)}"}
        
        return {"success": False, "error": "Maximum retries exceeded"}
    
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
                        blog_id=article.id,
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
        Publikuje artykuł na WordPress z automatyczną rotacją autorów.
        """
        logger.info(f"Publishing article to WordPress: {article.title}")
        
        try:
            blog = Blog.query.get(automation_rule.blog_id)
            if not blog:
                return {"success": False, "error": "Blog not found"}
            
            # Wybierz autora na podstawie kategorii i rotacji (fallback jeśli brak kategorii)
            category = getattr(article, 'category', 'Planowanie ciąży')
            selected_author = self._select_author_for_article(category, article.id)
            
            # Znajdź ID kategorii WordPress
            category_id = self._get_wordpress_category_id(blog, category)
            
            # Utwórz tagi w WordPress i pobierz ich ID
            tag_names = self._generate_tags_for_category(category)
            tag_ids = self._create_tags_in_wordpress(blog, tag_names)
            
            # Przygotuj dane do publikacji
            post_data = {
                "title": article.title,
                "content": article.content,
                "excerpt": article.excerpt,
                "status": "publish" if automation_rule.auto_publish else "draft",
                "author": selected_author["wordpress_id"],  # Przypisz autora
                "categories": [category_id] if category_id else [],
                "tags": tag_ids
            }
            
            # Dodaj featured image jeśli dostępny
            featured_image_id = self._get_featured_image_for_article(blog, article)
            if featured_image_id:
                post_data["featured_media"] = featured_image_id
            
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
                logger.info(f"Published with category ID: {category_id}, tags: {self._generate_tags_for_category(category)}")
                
                return {
                    "success": True, 
                    "post_id": post_result["id"],
                    "category_assigned": category_id,
                    "tags_assigned": len(self._generate_tags_for_category(category)),
                    "featured_image": featured_image_id
                }
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
    
    def _get_wordpress_category_id(self, blog: Blog, category_name: str) -> Optional[int]:
        """
        Pobiera ID kategorii WordPress na podstawie nazwy.
        """
        try:
            from utils.wordpress.client import build_wp_api_url
            
            api_url = build_wp_api_url(blog.api_url, "categories")
            auth = (blog.username, blog.api_token)
            
            # Szukaj kategorii po nazwie
            response = requests.get(f"{api_url}?search={category_name}", auth=auth)
            response.raise_for_status()
            
            categories = response.json()
            for cat in categories:
                if cat['name'].lower() == category_name.lower():
                    return cat['id']
            
            # Jeśli nie znaleziono, zwróć standardową kategorię "Planowanie ciąży"
            response = requests.get(f"{api_url}?search=Planowanie", auth=auth)
            response.raise_for_status()
            categories = response.json()
            for cat in categories:
                if 'planowanie' in cat['name'].lower():
                    return cat['id']
                    
            return None
        except Exception as e:
            logger.error(f"Failed to get WordPress category ID: {e}")
            return None
    
    def _generate_tags_for_category(self, category: str) -> List[str]:
        """
        Generuje tagi na podstawie kategorii.
        """
        tag_mapping = {
            "Planowanie ciąży": ["planowanie ciąży", "płodność", "zdrowie", "rodzina", "przygotowanie"],
            "Zdrowie w ciąży": ["ciąża", "zdrowie", "mama", "dziecko", "opieka"],
            "Wychowanie": ["wychowanie", "dzieci", "rozwój", "edukacja", "rodzina"],
            "Kosmetyki": ["kosmetyki", "uroda", "pielęgnacja", "mama", "produkty"],
            "Żywienie": ["żywienie", "dzieci", "zdrowie", "dieta", "rozwój"]
        }
        
        return tag_mapping.get(category, ["mama", "dzieci", "rodzina"])
    
    def _create_tags_in_wordpress(self, blog: Blog, tag_names: List[str]) -> List[int]:
        """
        Tworzy tagi w WordPress API i zwraca listę ich ID.
        """
        from utils.wordpress.client import build_wp_api_url
        
        tag_ids = []
        auth = (blog.username, blog.api_token)
        
        for tag_name in tag_names:
            try:
                # Sprawdź czy tag już istnieje
                search_url = build_wp_api_url(blog.api_url, "tags")
                search_response = requests.get(f"{search_url}?search={tag_name}", auth=auth)
                
                if search_response.status_code == 200:
                    existing_tags = search_response.json()
                    if existing_tags:
                        tag_ids.append(existing_tags[0]['id'])
                        logger.info(f"Found existing tag: {tag_name} (ID: {existing_tags[0]['id']})")
                        continue
                
                # Utwórz nowy tag
                create_url = build_wp_api_url(blog.api_url, "tags")
                create_response = requests.post(create_url, auth=auth, json={"name": tag_name})
                
                if create_response.status_code == 201:
                    new_tag = create_response.json()
                    tag_ids.append(new_tag['id'])
                    logger.info(f"Created new tag: {tag_name} (ID: {new_tag['id']})")
                
            except Exception as e:
                logger.warning(f"Failed to create tag '{tag_name}': {e}")
                
        return tag_ids
    
    def _get_featured_image_for_article(self, blog: Blog, article: Article) -> Optional[int]:
        """
        Pobiera ID featured image dla artykułu z biblioteki obrazów.
        """
        try:
            # Znajdź pierwszy obraz z biblioteki dla tego artykułu
            image = ImageLibrary.query.filter_by(blog_id=blog.id).order_by(
                ImageLibrary.created_at.desc()
            ).first()
            
            if image and image.url:
                # Upload obrazu do WordPress Media Library
                media_id = self._upload_image_to_wordpress(blog, image.url, image.title or "Featured Image")
                return media_id
            
            return None
        except Exception as e:
            logger.error(f"Failed to get featured image: {e}")
            return None
    
    def _upload_image_to_wordpress(self, blog: Blog, image_url: str, title: str) -> Optional[int]:
        """
        Uploaduje obraz do WordPress Media Library.
        """
        try:
            from utils.wordpress.client import build_wp_api_url
            
            # Pobierz obraz
            image_response = requests.get(image_url)
            image_response.raise_for_status()
            
            # Przygotuj dane do uploadu
            api_url = build_wp_api_url(blog.api_url, "media")
            auth = (blog.username, blog.api_token)
            
            # Określ typ pliku
            content_type = image_response.headers.get('content-type', 'image/jpeg')
            filename = f"{title.replace(' ', '_')}.jpg"
            
            # Upload do WordPress
            files = {
                'file': (filename, image_response.content, content_type)
            }
            
            data = {
                'title': title,
                'alt_text': title
            }
            
            response = requests.post(api_url, auth=auth, files=files, data=data)
            response.raise_for_status()
            
            media_result = response.json()
            return media_result.get('id')
            
        except Exception as e:
            logger.error(f"Failed to upload image to WordPress: {e}")
            return None

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