"""
Automatic Image Finder for Articles

This module provides functionality for automatically finding and associating
images with articles based on their title or content.
"""

import logging
import os
from typing import List, Dict, Any, Optional, Tuple
import re
from models import Article, ImageLibrary, db
from utils.images.finder import search_images, clean_image_metadata
from sqlalchemy.exc import SQLAlchemyError
import uuid
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

def prepare_image_metadata(
    url: str, 
    thumbnail_url: str = None, 
    source: str = "unknown", 
    title: str = "", 
    attribution: str = ""
) -> Dict[str, Any]:
    """
    Prepare standardized image metadata for use in the application.
    
    Args:
        url: The main image URL
        thumbnail_url: URL for the thumbnail version, if available
        source: Source of the image (e.g., 'Google Images', 'Unsplash')
        title: Title or description of the image
        attribution: Attribution text (photographer, website, etc.)
        
    Returns:
        Dictionary with standardized image metadata
    """
    # Generate a unique ID for the image
    image_id = str(uuid.uuid4())
    
    # Use the main URL as thumbnail if none provided
    if not thumbnail_url:
        thumbnail_url = url
        
    # Standardize the metadata format
    return {
        "id": image_id,
        "url": url,
        "thumbnail_url": thumbnail_url,
        "source": source,
        "title": title or f"Image from {source}",
        "attribution": attribution,
        "date_added": datetime.now().isoformat()
    }

def extract_keywords_from_title(title: str) -> List[str]:
    """
    Extract main keywords from article title for better image search.
    
    Args:
        title: The article title
        
    Returns:
        A list of extracted keywords
    """
    # Remove common stop words (Polish and English)
    stop_words = {
        'a', 'aby', 'ach', 'acz', 'aczkolwiek', 'aj', 'albo', 'ale', 'ależ', 'ani', 'aż', 'bardziej', 'bardzo', 'bo',
        'bowiem', 'by', 'byli', 'bym', 'był', 'była', 'było', 'były', 'być', 'będzie', 'będą', 'chce', 'choć', 'ci',
        'cię', 'co', 'coraz', 'coś', 'czy', 'czyli', 'często', 'dla', 'do', 'gdy', 'gdyż', 'gdzie', 'go', 'i', 'ich',
        'im', 'inne', 'iż', 'ja', 'jak', 'jakie', 'jako', 'je', 'jednak', 'jego', 'jej', 'jest', 'jeszcze', 'jeśli',
        'jeżeli', 'już', 'ją', 'kiedy', 'kilka', 'komu', 'kto', 'która', 'które', 'którego', 'której', 'który',
        'których', 'którym', 'którzy', 'lat', 'lecz', 'lub', 'ma', 'mają', 'mi', 'mnie', 'mogą', 'może', 'możliwe',
        'można', 'mu', 'na', 'nad', 'nam', 'nas', 'nasz', 'nasza', 'nasze', 'naszego', 'naszych', 'natomiast',
        'nawet', 'nic', 'nich', 'nie', 'nigdy', 'nim', 'niż', 'no', 'o', 'od', 'około', 'on', 'ona', 'one', 'oni',
        'ono', 'oraz', 'pan', 'po', 'pod', 'podczas', 'pomimo', 'ponad', 'ponieważ', 'powinien', 'powinna', 'powinni',
        'powinno', 'poza', 'prawie', 'przecież', 'przed', 'przede', 'przez', 'przy', 'raz', 'razie', 'roku', 'również',
        'się', 'sobie', 'sposób', 'swoje', 'są', 'ta', 'tak', 'taka', 'taki', 'takich', 'takie', 'także', 'tam',
        'te', 'tego', 'tej', 'ten', 'teraz', 'też', 'to', 'tobie', 'toteż', 'trzeba', 'tu', 'twoim', 'twoja',
        'twoje', 'twym', 'ty', 'tych', 'tylko', 'tym', 'u', 'w', 'we', 'według', 'wiele', 'wielu', 'więc',
        'więcej', 'wszyscy', 'wszystkich', 'wszystkie', 'wszystkim', 'wszystko', 'właśnie', 'z', 'za', 'zaś',
        'ze', 'że', 'żeby',
        # English stop words
        'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', 'as', 'at',
        'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by', 'can', 'did', 'do',
        'does', 'doing', 'down', 'during', 'each', 'few', 'for', 'from', 'further', 'had', 'has', 'have', 'having',
        'he', 'her', 'here', 'hers', 'herself', 'him', 'himself', 'his', 'how', 'i', 'if', 'in', 'into', 'is',
        'it', 'its', 'itself', 'just', 'me', 'more', 'most', 'my', 'myself', 'no', 'nor', 'not', 'now', 'of',
        'off', 'on', 'once', 'only', 'or', 'other', 'our', 'ours', 'ourselves', 'out', 'over', 'own', 's', 'same',
        'she', 'should', 'so', 'some', 'such', 't', 'than', 'that', 'the', 'their', 'theirs', 'them', 'themselves',
        'then', 'there', 'these', 'they', 'this', 'those', 'through', 'to', 'too', 'under', 'until', 'up', 'very',
        'was', 'we', 'were', 'what', 'when', 'where', 'which', 'while', 'who', 'whom', 'why', 'will', 'with',
        'would', 'you', 'your', 'yours', 'yourself', 'yourselves'
    }
    
    # Normalize the title (lowercase, remove punctuation)
    title = title.lower()
    title = re.sub(r'[^\w\s]', ' ', title)
    
    # Split into words and filter out stop words
    words = [w for w in title.split() if w not in stop_words and len(w) > 2]
    
    # Return unique keywords, longer words first (they're often more significant)
    return sorted(list(set(words)), key=len, reverse=True)

def extract_content_summary(content: str, max_chars: int = 500) -> str:
    """
    Extract a content summary to use for image search.
    
    Args:
        content: The article content
        max_chars: Maximum characters for the summary
        
    Returns:
        A summarized version of the content
    """
    # Remove HTML tags if present
    content = re.sub(r'<[^>]+>', ' ', content)
    
    # Remove excess whitespace
    content = re.sub(r'\s+', ' ', content).strip()
    
    # Take the first N characters
    if len(content) > max_chars:
        content = content[:max_chars]
        # Try to end at a complete sentence
        last_period = content.rfind('.')
        if last_period > max_chars * 0.7:  # If there's a period in the latter part
            content = content[:last_period + 1]
    
    return content

def find_images_for_article(
    article_title: str, 
    article_content: Optional[str] = None,
    num_images: int = 3,
    prefer_source: str = 'google'  # Using Google as primary source
) -> List[Dict[str, Any]]:
    """
    Find images that match an article's title and content.
    
    Args:
        article_title: The title of the article
        article_content: Optional article content
        num_images: Number of images to find
        prefer_source: Preferred image source
        
    Returns:
        A list of image metadata dictionaries
    """
    # Extract keywords from title
    keywords = extract_keywords_from_title(article_title)
    
    # If we have less than 2 keywords, but have content, add some from the content
    if len(keywords) < 2 and article_content:
        content_summary = extract_content_summary(article_content)
        content_keywords = extract_keywords_from_title(content_summary)
        # Add unique content keywords
        for kw in content_keywords:
            if kw not in keywords:
                keywords.append(kw)
    
    # Ensure we have at least one keyword
    if not keywords:
        keywords = [article_title]  # Use the full title if we couldn't extract keywords
    
    # Create search queries of increasing complexity
    queries = []
    
    # First, try the top 1-2 keywords for more specific results
    if len(keywords) >= 2:
        queries.append(" ".join(keywords[:2]))
    
    # Then try the full title for context
    queries.append(article_title)
    
    # If we have very few keywords, add the individual words
    if len(keywords) <= 3:
        for kw in keywords:
            queries.append(kw)
    
    logger.info(f"Generated image search queries for '{article_title}': {queries}")
    
    # Search for images using each query
    all_images = []
    for query in queries:
        try:
            images = search_images(
                query=query,
                source=prefer_source,
                per_page=num_images,
                orientation='landscape'  # Prefer landscape for articles
            )
            
            # Add to our results
            for img in images:
                # Skip if we already have this image (by URL)
                if any(existing['url'] == img['url'] for existing in all_images):
                    continue
                
                all_images.append(img)
            
            # If we have enough images, stop searching
            if len(all_images) >= num_images:
                break
                
        except Exception as e:
            logger.warning(f"Error searching for images with query '{query}': {str(e)}")
    
    # Return the top N images
    return all_images[:num_images]

def save_image_to_library(image_data: Dict[str, Any]) -> Optional[ImageLibrary]:
    """
    Save an image to the image library.
    
    Args:
        image_data: The image metadata from search_images
        
    Returns:
        The saved ImageLibrary instance or None if failed
    """
    try:
        # Clean the metadata for storage
        cleaned_data = clean_image_metadata(image_data)
        
        # Check if image already exists in database by URL
        existing_image = ImageLibrary.query.filter_by(url=cleaned_data['url']).first()
        if existing_image:
            logger.info(f"Image already exists in library: {cleaned_data['url']}")
            return existing_image
        
        # Create new image record
        image = ImageLibrary(
            title=cleaned_data.get('description', ''),
            url=cleaned_data['url'],
            thumbnail_url=cleaned_data.get('thumb_url', ''),
            source=cleaned_data.get('source', 'unknown'),
            source_id=cleaned_data.get('source_id', ''),
            width=cleaned_data.get('width'),
            height=cleaned_data.get('height'),
            attribution=cleaned_data.get('attribution_text', ''),
            attribution_url=cleaned_data.get('attribution_url', '')
        )
        
        # Save to database
        db.session.add(image)
        db.session.commit()
        
        logger.info(f"Saved image to library: {image.id} - {image.url}")
        return image
        
    except SQLAlchemyError as e:
        logger.error(f"Database error saving image: {str(e)}")
        db.session.rollback()
        return None
        
    except Exception as e:
        logger.error(f"Error saving image to library: {str(e)}")
        return None

def find_and_associate_images(
    article: Article, 
    num_images: int = 1, 
    prefer_source: str = 'google',  # Updated to use Google as default source
    save_to_library: bool = True
) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Find images for an article and associate the best one as featured image.
    
    Args:
        article: The Article instance
        num_images: Number of images to find
        prefer_source: Preferred image source
        save_to_library: Whether to save images to the library
        
    Returns:
        Tuple of (success, images_found)
    """
    if not article.title:
        logger.warning("Cannot find images for article without title")
        return False, []
    
    try:
        # Find images
        images = find_images_for_article(
            article_title=article.title,
            article_content=article.content,
            num_images=num_images,
            prefer_source=prefer_source
        )
        
        if not images:
            logger.warning(f"No images found for article: {article.title}")
            return False, []
        
        # Save images to library if requested
        saved_images = []
        if save_to_library:
            for img in images:
                saved_img = save_image_to_library(img)
                if saved_img:
                    saved_images.append({
                        'id': saved_img.id,
                        'url': saved_img.url,
                        'thumbnail_url': saved_img.thumbnail_url,
                        'attribution': saved_img.attribution
                    })
        
        # Set featured image (first image)
        if images:
            article.featured_image_url = images[0].get('url', '')
            db.session.commit()
            logger.info(f"Set featured image for article {article.id}: {article.featured_image_url}")
        
        return True, images if not save_to_library else saved_images
        
    except Exception as e:
        logger.error(f"Error associating images with article {article.id}: {str(e)}")
        return False, []