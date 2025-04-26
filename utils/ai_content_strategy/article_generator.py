"""
AI-Driven Content Strategy - Article Generator

This module provides functionality for generating articles based on AI-generated topics
using Claude 3.5 via OpenRouter.
"""

import os
import logging
import json
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

# Import the OpenRouter integration
from .topic_generator import openrouter_call, get_openrouter_api_key

# Setup logging
logger = logging.getLogger(__name__)

def generate_article(topic: str, category: str, min_paragraph_tokens: int = 1000, num_paragraphs: int = 4) -> Dict[str, str]:
    """
    Generate a complete article for a given topic and category using Claude 3.5
    
    Args:
        topic: The article topic
        category: The article category
        min_paragraph_tokens: Minimum tokens per paragraph (default: 1000)
        num_paragraphs: Number of paragraphs in the article (default: 4)
        
    Returns:
        Dictionary containing article parts (title, introduction, paragraphs, conclusion, meta)
    """
    try:
        # Generate article structure with detailed paragraphs
        prompt = f"""
        Napisz ekspercki, rozbudowany artykuł na temat: "{topic}" dla bloga z kategorii: "{category}".
        
        Artykuł powinien zawierać następujące części:
        1. Tytuł (kreatywny i przyciągający uwagę)
        2. Wstęp (min. 500 słów)
        3. {num_paragraphs} bardzo rozbudowane akapity (minimum {min_paragraph_tokens} tokenów każdy)
        4. Podsumowanie (min. 500 słów)
        
        Wymogi dotyczące akapitów:
        - Każdy akapit musi zawierać konkretną, głęboką analizę tematu.
        - Akapity muszą logicznie wynikać jeden z drugiego.
        - Każdy akapit powinien dotyczyć innego aspektu tematu.
        - Zadbaj o przykłady, dane i szczegóły w każdym akapicie.
        
        Sformatuj artykuł używając znaczników HTML dla struktury:
        - <h1>Tytuł</h1>
        - <h2>Podtytuły sekcji</h2>
        - <p>Paragrafy</p>
        
        Dodatkowo, na samym końcu dodaj sekcję META_DATA w formacie:
        
        --- META_DATA ---
        Tytuł SEO: [krótki tytuł z słowami kluczowymi]
        Opis: [meta description 150-160 znaków]
        Słowa kluczowe: [5-7 słów kluczowych oddzielonych przecinkami]
        --- END META_DATA ---
        """
        
        # Get response from Claude 3.5 via OpenRouter
        response = openrouter_call(prompt, model="anthropic/claude-3-5-sonnet-20241022", max_tokens=8000)
        
        # Parse the article and extract its components
        article_parts = parse_article(response)
        
        # Add metadata
        article_parts['generated_at'] = datetime.now().isoformat()
        article_parts['topic'] = topic
        article_parts['category'] = category
        
        return article_parts
        
    except Exception as e:
        logger.error(f"Error generating article for topic '{topic}': {str(e)}")
        # Return a basic structure with error information
        return {
            'title': f"Article about {topic}",
            'content': f"<p>Error generating content: {str(e)}</p>",
            'meta_title': topic,
            'meta_description': f"Article about {topic} in the {category} category",
            'keywords': [category, topic],
            'error': str(e)
        }

def parse_article(content: str) -> Dict[str, Any]:
    """
    Parse the generated article and extract its components
    
    Args:
        content: The raw content from Claude
        
    Returns:
        Dictionary with article components
    """
    result = {
        'title': "",
        'content': content,  # Store the full content by default
        'meta_title': "",
        'meta_description': "",
        'keywords': []
    }
    
    # Extract META_DATA section if present
    if "--- META_DATA ---" in content and "--- END META_DATA ---" in content:
        meta_start = content.find("--- META_DATA ---")
        meta_end = content.find("--- END META_DATA ---") + len("--- END META_DATA ---")
        
        meta_section = content[meta_start:meta_end]
        content_without_meta = content[:meta_start].strip()
        
        # Update the content without metadata
        result['content'] = content_without_meta
        
        # Extract meta title
        if "Tytuł SEO:" in meta_section:
            title_start = meta_section.find("Tytuł SEO:") + len("Tytuł SEO:")
            title_end = meta_section.find("\n", title_start)
            result['meta_title'] = meta_section[title_start:title_end].strip()
        
        # Extract meta description
        if "Opis:" in meta_section:
            desc_start = meta_section.find("Opis:") + len("Opis:")
            desc_end = meta_section.find("\n", desc_start)
            result['meta_description'] = meta_section[desc_start:desc_end].strip()
        
        # Extract keywords
        if "Słowa kluczowe:" in meta_section:
            kw_start = meta_section.find("Słowa kluczowe:") + len("Słowa kluczowe:")
            kw_end = meta_section.find("\n", kw_start)
            if kw_end == -1:  # If it's the last line
                kw_end = len(meta_section)
            keywords_str = meta_section[kw_start:kw_end].strip()
            result['keywords'] = [k.strip() for k in keywords_str.split(',')]
    
    # Try to extract title from H1 tag
    import re
    h1_match = re.search(r'<h1>(.*?)</h1>', content, re.IGNORECASE | re.DOTALL)
    if h1_match:
        result['title'] = h1_match.group(1).strip()
    else:
        # Fallback to first line if no H1 tag
        first_line = content.strip().split('\n')[0]
        if first_line.startswith('#'):
            result['title'] = first_line.lstrip('#').strip()
        else:
            # Just use the first line as is
            result['title'] = first_line.strip()
    
    # If no meta title was found, use the article title
    if not result['meta_title']:
        result['meta_title'] = result['title']
    
    return result

def save_article(article_data: Dict[str, Any], filepath: Optional[str] = None) -> str:
    """
    Save the generated article to a JSON file
    
    Args:
        article_data: The article data
        filepath: Path to save the article (if None, one will be generated)
        
    Returns:
        Path to the saved article file
    """
    if filepath is None:
        # Generate a filename based on title and date
        title_slug = article_data['title'].lower().replace(' ', '-')[:30]
        date_str = datetime.now().strftime('%Y%m%d')
        filepath = f"data/articles/{date_str}-{title_slug}.json"
    
    try:
        # Create directory if needed
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Save article data as JSON
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(article_data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Article saved to {filepath}")
        return filepath
        
    except Exception as e:
        logger.error(f"Error saving article: {str(e)}")
        return ""

def get_random_topic_for_category(category: str, topics_filepath: str = "data/ai_topics.json") -> Optional[str]:
    """
    Get a random unused topic for a category
    
    Args:
        category: The category to get a topic for
        topics_filepath: Path to the topics JSON file
        
    Returns:
        A random topic string or None if no topics are available
    """
    try:
        # Load all topics
        topics_data = {}
        if os.path.exists(topics_filepath):
            with open(topics_filepath, 'r', encoding='utf-8') as f:
                topics_data = json.load(f)
        
        # Check if category exists in topics data
        if category not in topics_data or not topics_data[category]:
            logger.warning(f"No topics found for category '{category}'")
            return None
        
        # Load list of already used topics
        used_topics = []
        used_topics_path = "data/used_topics.json"
        if os.path.exists(used_topics_path):
            with open(used_topics_path, 'r', encoding='utf-8') as f:
                used_topics = json.load(f)
        
        # Filter out used topics
        available_topics = [t for t in topics_data[category] if t not in used_topics]
        
        if not available_topics:
            logger.warning(f"All topics for category '{category}' have been used")
            return None
        
        # Select a random topic
        import random
        topic = random.choice(available_topics)
        
        # Mark topic as used
        used_topics.append(topic)
        os.makedirs(os.path.dirname(used_topics_path), exist_ok=True)
        with open(used_topics_path, 'w', encoding='utf-8') as f:
            json.dump(used_topics, f, ensure_ascii=False, indent=2)
        
        return topic
        
    except Exception as e:
        logger.error(f"Error getting random topic for category '{category}': {str(e)}")
        return None