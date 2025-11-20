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

def compute_image_score(
    image: Dict[str, Any],
    context: Dict[str, Any],
    planner_result: Dict[str, Any] = None
) -> float:
    """
    Compute a relevance score for an image based on article context
    
    Args:
        image: Image metadata dictionary
        context: Article context with title, tags, category
        planner_result: AI query planner result with domain_terms, negative keywords
        
    Returns:
        Relevance score (higher is better)
    """
    score = 0.0
    
    # Combine searchable image text
    searchable_text = " ".join([
        str(image.get("description", "")),
        str(image.get("attribution_text", "")),
        str(image.get("url", "")),
        str(image.get("title", ""))
    ]).lower()
    
    # 1. Check for domain terms and tags (positive signals)
    if planner_result:
        domain_terms = planner_result.get("domain_terms", [])
        for term in domain_terms:
            if term.lower() in searchable_text:
                score += 2.0
    
    # Check article tags
    tags = context.get("tags", [])
    for tag in tags[:5]:  # Top 5 tags only
        if tag.lower() in searchable_text:
            score += 1.5
    
    # Check title keywords
    title = context.get("title", "")
    title_words = [w.lower() for w in title.split() if len(w) > 3]
    for word in title_words[:5]:
        if word in searchable_text:
            score += 1.0
    
    # 2. Check for negative keywords (penalties)
    if planner_result:
        negatives = planner_result.get("negative", [])
        for neg in negatives:
            if neg.lower() in searchable_text:
                score -= 3.0
    
    # 3. Orientation preference
    width = image.get("width", 0)
    height = image.get("height", 1)  # Avoid division by zero
    
    if planner_result:
        preferred_orientation = planner_result.get("orientation", "landscape")
    else:
        preferred_orientation = "landscape"
    
    if preferred_orientation == "landscape" and width > height:
        score += 1.5
    elif preferred_orientation == "portrait" and height > width:
        score += 1.5
    elif preferred_orientation == "square" and abs(width - height) < width * 0.1:
        score += 1.5
    
    # 4. Image size (prefer larger images, minimum 1200px width)
    if width >= 1200:
        score += 2.0
    elif width >= 800:
        score += 1.0
    elif width < 600:
        score -= 1.0
    
    # 5. Source quality (prefer licensed/curated sources)
    source = image.get("source", "").lower()
    if source in ("unsplash", "pexels"):
        score += 2.0  # Free, high-quality, licensed
    elif source == "bing":
        score += 0.5
    
    # 6. Attribution presence (good for licensing)
    if image.get("attribution_text") or image.get("attribution_url"):
        score += 0.5
    
    # 7. Penalty for adult content keywords (basic filter)
    adult_keywords = ["sexy", "nude", "porn", "xxx", "adult", "nsfw"]
    for keyword in adult_keywords:
        if keyword in searchable_text:
            score -= 10.0  # Strong penalty
    
    return score

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

def find_images_for_article_enhanced(
    article_title: str,
    article_content: Optional[str] = None,
    tags: List[str] = None,
    category: str = "",
    num_images: int = 3
) -> List[Dict[str, Any]]:
    """
    Enhanced image search using AI query planning and scoring
    
    Args:
        article_title: Article title
        article_content: Article content (HTML or text)
        tags: List of SEO tags
        category: Article category
        num_images: Number of images to return
        
    Returns:
        List of best-scored images
    """
    try:
        from utils.images.query_planner import generate_image_queries_with_ai, extract_content_summary
        
        # Prepare context
        content_summary = extract_content_summary(article_content) if article_content else ""
        context = {
            "title": article_title,
            "tags": tags or [],
            "category": category
        }
        
        # Generate intelligent queries using AI
        logger.info(f"Generating AI-powered image queries for: {article_title[:60]}...")
        planner_result = generate_image_queries_with_ai(
            title=article_title,
            content=content_summary,
            tags=tags,
            category=category
        )
        
        # Collect all queries
        all_queries = [planner_result["primary_query"]]
        all_queries.extend(planner_result.get("alternates", []))
        
        # Search multiple sources with each query
        sources = ["bing", "unsplash", "pexels"]  # Prioritize free, licensed sources
        all_candidates = []
        
        for query in all_queries[:3]:  # Use top 3 queries
            for source in sources:
                try:
                    logger.info(f"Searching {source} with query: '{query}'")
                    images = search_images(
                        query=query,
                        source=source,
                        per_page=10,  # Get multiple candidates
                        orientation=planner_result.get("orientation", "landscape")
                    )
                    
                    # Add to candidates if not duplicate
                    for img in images:
                        img_url = img.get("url", "")
                        if img_url and not any(c.get("url") == img_url for c in all_candidates):
                            all_candidates.append(img)
                    
                    # If we have enough candidates, can stop early
                    if len(all_candidates) >= 30:
                        break
                        
                except Exception as e:
                    logger.warning(f"Error searching {source}: {e}")
            
            if len(all_candidates) >= 30:
                break
        
        if not all_candidates:
            logger.warning(f"No images found for '{article_title}'")
            return []
        
        # Score all candidates
        logger.info(f"Scoring {len(all_candidates)} image candidates...")
        scored_images = []
        for img in all_candidates:
            score = compute_image_score(img, context, planner_result)
            scored_images.append((score, img))
        
        # Sort by score (descending)
        scored_images.sort(key=lambda x: x[0], reverse=True)
        
        # Log top scores
        for i, (score, img) in enumerate(scored_images[:5]):
            logger.info(f"  #{i+1}: score={score:.1f} - {img.get('description', 'No desc')[:60]}")
        
        # Return top N images
        best_images = [img for score, img in scored_images[:num_images]]
        return best_images
        
    except Exception as e:
        logger.error(f"Error in enhanced image search: {e}")
        # Fallback to original method
        return find_images_for_article(
            article_title=article_title,
            article_content=article_content,
            num_images=num_images
        )

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
        
        # Create new image record with truncated title to prevent DB errors
        image_title = cleaned_data.get('description', '')
        if len(image_title) > 250:
            image_title = image_title[:247] + '...'
            logger.debug(f"Truncated long image title to 250 characters")
        
        image = ImageLibrary(
            title=image_title,
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

def find_article_images(
    article_title: str,
    article_content: str = "",
    max_images: int = 3,
    tags: List[str] = None,
    category: str = ""
) -> List[Dict[str, Any]]:
    """
    Main function to find images for an article - compatibility wrapper for workflow engine.
    Uses enhanced AI-powered image search when tags/category available, falls back to basic search.
    
    Args:
        article_title: Title of the article
        article_content: Content of the article (optional)
        max_images: Maximum number of images to return
        tags: List of SEO tags (optional)
        category: Article category (optional)
        
    Returns:
        List of image dictionaries with url, title, source, tags
    """
    try:
        # Try enhanced search if we have tags or category
        if tags or category:
            logger.info(f"Using AI-enhanced image search for: {article_title[:60]}...")
            images = find_images_for_article_enhanced(
                article_title=article_title,
                article_content=article_content,
                tags=tags,
                category=category,
                num_images=max_images
            )
        else:
            # Fall back to original search
            logger.info(f"Using standard image search for: {article_title[:60]}...")
            images = find_images_for_article(
                article_title=article_title,
                article_content=article_content,
                num_images=max_images
            )
        
        # Convert to expected format for workflow engine
        result = []
        for img in images:
            result.append({
                'url': img.get('url', ''),
                'title': img.get('description', article_title),
                'source': img.get('source', 'auto'),
                'tags': '',
                'thumbnail_url': img.get('thumb_url', '')
            })
            
        return result
        
    except Exception as e:
        logger.error(f"Error finding article images: {str(e)}")
        # Ultimate fallback - try basic search
        try:
            images = find_images_for_article(
                article_title=article_title,
                article_content=article_content,
                num_images=max_images
            )
            result = []
            for img in images:
                result.append({
                    'url': img.get('url', ''),
                    'title': img.get('description', article_title),
                    'source': img.get('source', 'auto'),
                    'tags': '',
                    'thumbnail_url': img.get('thumb_url', '')
                })
            return result
        except:
            return []

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