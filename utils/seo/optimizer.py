"""
SEO Optimizer

This module provides functions for optimizing content for SEO.
"""
import logging
import re

# Setup logging
logger = logging.getLogger(__name__)

def seo_optimizer(content, keywords=None, meta_description=None):
    """
    Optimize content for SEO.
    
    Args:
        content: The content to optimize
        keywords: List of target keywords
        meta_description: Meta description to optimize
        
    Returns:
        Dictionary containing optimized content and metadata
    """
    logger.info("Optimizing content for SEO")
    
    optimized = {
        'content': content,
        'meta_description': meta_description,
        'recommendations': []
    }
    
    # Optimize content
    if content:
        optimized['content'] = optimize_content(content, keywords)
    
    # Optimize meta description
    if meta_description:
        optimized['meta_description'] = optimize_meta_description(meta_description, keywords)
    
    return optimized

def optimize_content(content, keywords=None):
    """
    Optimize content for SEO.
    
    Args:
        content: The content to optimize
        keywords: List of target keywords
        
    Returns:
        Optimized content
    """
    optimized_content = content
    
    # Replace generic words with keywords if possible
    if keywords:
        generic_words = [
            'thing', 'stuff', 'item', 'product', 'solution',
            'idea', 'concept', 'option', 'alternative', 'possibility'
        ]
        
        for word in generic_words:
            for keyword in keywords:
                # Find instances of generic words
                pattern = rf'\\b{word}\\b'
                if re.search(pattern, optimized_content, re.IGNORECASE):
                    # Replace some instances with keywords (not all to avoid keyword stuffing)
                    optimized_content = re.sub(
                        pattern, 
                        keyword, 
                        optimized_content, 
                        count=1, 
                        flags=re.IGNORECASE
                    )
    
    return optimized_content

def optimize_meta_description(meta_description, keywords=None):
    """
    Optimize meta description for SEO.
    
    Args:
        meta_description: The meta description to optimize
        keywords: List of target keywords
        
    Returns:
        Optimized meta description
    """
    if not meta_description:
        return ""
    
    optimized_meta = meta_description
    
    # Ensure meta description is the right length (150-160 characters)
    if len(optimized_meta) > 160:
        # Truncate to 157 characters and add ellipsis
        optimized_meta = optimized_meta[:157] + "..."
    
    # Ensure meta description contains at least one keyword if provided
    if keywords and not any(keyword.lower() in optimized_meta.lower() for keyword in keywords):
        # Try to add a keyword to the meta description
        keyword = keywords[0]
        if len(optimized_meta) + len(keyword) + 12 <= 160:
            optimized_meta = f"{optimized_meta} Learn about {keyword}."
    
    return optimized_meta

def generate_title_variations(title, keywords=None, limit=5):
    """
    Generate SEO-optimized title variations.
    
    Args:
        title: The original title
        keywords: List of target keywords
        limit: Maximum number of variations to generate
        
    Returns:
        List of title variations
    """
    variations = []
    
    # Add the original title as the first variation
    variations.append(title)
    
    # Generate variations based on common patterns
    patterns = [
        "Top 10 {title} Tips You Need to Know",
        "How to Master {title} in 5 Simple Steps",
        "The Ultimate Guide to {title}",
        "{title}: A Complete Beginner's Guide",
        "Why {title} Matters for Your Business",
        "{title} Explained: Everything You Need to Know",
        "5 Ways {title} Can Improve Your Life",
        "Understanding {title}: Key Concepts and Benefits"
    ]
    
    for pattern in patterns:
        variation = pattern.replace("{title}", title)
        
        # Ensure title is not too long (60-70 characters is optimal)
        if len(variation) <= 70:
            variations.append(variation)
            
            # Check if we have enough variations
            if len(variations) >= limit:
                break
    
    # Add keyword-focused variations if provided
    if keywords and len(variations) < limit:
        for keyword in keywords:
            if keyword.lower() not in title.lower():
                variation = f"{title} - {keyword.capitalize()}"
                
                if len(variation) <= 70:
                    variations.append(variation)
                    
                    # Check if we have enough variations
                    if len(variations) >= limit:
                        break
    
    return variations[:limit]