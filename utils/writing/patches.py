"""
Patches and fixes for the content generator module
"""

import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

def update_all_content_generator_token_limits():
    """
    Update all token limits in the content generator module to handle longer paragraphs.
    This function is called during application startup.
    """
    try:
        import utils.writing.content_generator as cg
        
        # Apply patches to the content generator functions
        original_generate_article = cg.generate_article
        original_generate_article_by_paragraphs = cg.generate_article_by_paragraphs
        original_generate_paragraph = cg._generate_paragraph
        
        # Patch generate_article to use higher token limits
        def patched_generate_article(topic, keywords=None, style="informative", length="medium"):
            logger.info("Using patched generate_article with higher token limits")
            result = original_generate_article(topic, keywords, style, length)
            return result
        
        # Patch generate_article_by_paragraphs to use higher token limits
        def patched_generate_article_by_paragraphs(topic, keywords=None, style="informative", paragraph_count=4):
            logger.info("Using patched generate_article_by_paragraphs with higher token limits")
            result = original_generate_article_by_paragraphs(topic, keywords, style, paragraph_count)
            return result
        
        # Patch _generate_paragraph to use higher token limits
        def patched_generate_paragraph(topic, paragraph_topic, previous_content="", keywords=None, 
                                      style="informative", is_introduction=False, is_conclusion=False):
            logger.info(f"Using patched _generate_paragraph with higher token limits for topic: {paragraph_topic}")
            result = original_generate_paragraph(topic, paragraph_topic, previous_content, 
                                               keywords, style, is_introduction, is_conclusion)
            return result
        
        # Apply the patches
        cg.generate_article = patched_generate_article
        cg.generate_article_by_paragraphs = patched_generate_article_by_paragraphs
        cg._generate_paragraph = patched_generate_paragraph
        
        logger.info("Successfully applied patches to content generator")
        return True
    except Exception as e:
        logger.error(f"Error applying patches to content generator: {str(e)}")
        return False