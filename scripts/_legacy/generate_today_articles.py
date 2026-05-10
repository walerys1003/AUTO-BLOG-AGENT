#!/usr/bin/env python3
"""
Skrypt do generowania dzisiejszych artykułów dla wszystkich blogów
"""
import sys
import logging
from app import app
from utils.automation.scheduler import AutomationScheduler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Generuj artykuły dla wszystkich trzech blogów"""
    
    # Mapowanie blog_id -> nazwa
    blogs = {
        2: "MAMATESTUJE.COM",
        3: "ZNANEKOSMETYKI.PL", 
        4: "HOMOSONLY.PL"
    }
    
    scheduler = AutomationScheduler()
    
    logger.info("=" * 80)
    logger.info("🚀 ROZPOCZYNAM GENEROWANIE DZISIEJSZYCH ARTYKUŁÓW")
    logger.info("=" * 80)
    
    for blog_id, blog_name in blogs.items():
        logger.info("")
        logger.info(f"📝 Generuję 3 artykuły dla {blog_name} (Blog ID: {blog_id})")
        logger.info("-" * 80)
        
        try:
            scheduler.batch_generate_articles(blog_id=blog_id)
            logger.info(f"✅ Ukończono generowanie dla {blog_name}")
            
        except Exception as e:
            logger.error(f"❌ Błąd podczas generowania dla {blog_name}: {str(e)}")
            import traceback
            traceback.print_exc()
            continue
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("🎉 ZAKOŃCZONO GENEROWANIE WSZYSTKICH ARTYKUŁÓW")
    logger.info("=" * 80)

if __name__ == "__main__":
    main()
