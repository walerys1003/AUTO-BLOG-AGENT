"""
SEO Optimizer Module

This module provides functions for optimizing content for SEO.
"""
import logging
import random
import re
from datetime import datetime

# Setup logging
logger = logging.getLogger(__name__)

def seo_optimizer(content, primary_keyword, secondary_keywords=None, optimize_headings=True, optimize_density=True):
    """
    Optimize content for SEO.
    
    Args:
        content: The content to optimize
        primary_keyword: The primary keyword to optimize for
        secondary_keywords: List of secondary keywords to include
        optimize_headings: Whether to optimize headings (default: True)
        optimize_density: Whether to optimize keyword density (default: True)
        
    Returns:
        Optimized content
    """
    logger.info(f"Optimizing content for primary keyword: {primary_keyword}")
    
    if not content:
        logger.warning("No content provided for optimization")
        return content
    
    secondary_keywords = secondary_keywords or []
    
    # Split content into paragraphs
    paragraphs = content.split('\n\n')
    paragraphs = [p for p in paragraphs if p.strip()]
    
    if not paragraphs:
        logger.warning("No paragraphs found in content")
        return content
    
    # Check if primary keyword is in first paragraph
    first_paragraph = paragraphs[0]
    if optimize_density and primary_keyword.lower() not in first_paragraph.lower():
        # Add primary keyword to first paragraph
        words = first_paragraph.split(' ')
        insert_position = min(len(words) // 2, 15)  # Insert keyword in first half of paragraph
        words.insert(insert_position, primary_keyword)
        paragraphs[0] = ' '.join(words)
    
    # Check if primary keyword is in last paragraph
    last_paragraph = paragraphs[-1]
    if optimize_density and primary_keyword.lower() not in last_paragraph.lower():
        # Add primary keyword to last paragraph
        words = last_paragraph.split(' ')
        insert_position = min(len(words) // 2, 10)  # Insert keyword in middle of paragraph
        words.insert(insert_position, primary_keyword)
        paragraphs[-1] = ' '.join(words)
    
    # Optimize headings
    if optimize_headings:
        # Check for h1 tag
        h1_pattern = re.compile(r'<h1[^>]*>(.*?)</h1>', re.IGNORECASE)
        h1_match = h1_pattern.search(content)
        
        if h1_match and primary_keyword.lower() not in h1_match.group(1).lower():
            # Update h1 tag to include primary keyword
            old_h1 = h1_match.group(0)
            h1_text = h1_match.group(1)
            words = h1_text.split(' ')
            insert_position = min(1, len(words) - 1)  # Insert keyword at beginning
            words.insert(insert_position, primary_keyword)
            new_h1_text = ' '.join(words)
            new_h1 = f"<h1>{new_h1_text}</h1>"
            content = content.replace(old_h1, new_h1)
        
        # Check for h2 tags
        h2_pattern = re.compile(r'<h2[^>]*>(.*?)</h2>', re.IGNORECASE)
        h2_matches = h2_pattern.findall(content)
        
        if h2_matches:
            # Check if any h2 contains primary keyword
            has_primary = any(primary_keyword.lower() in h2.lower() for h2 in h2_matches)
            
            if not has_primary and len(h2_matches) > 0:
                # Update one h2 tag to include primary keyword
                for i, h2 in enumerate(h2_matches):
                    if primary_keyword.lower() not in h2.lower():
                        old_h2 = f"<h2>{h2}</h2>"
                        words = h2.split(' ')
                        insert_position = min(1, len(words) - 1)  # Insert keyword at beginning
                        words.insert(insert_position, primary_keyword)
                        new_h2_text = ' '.join(words)
                        new_h2 = f"<h2>{new_h2_text}</h2>"
                        content = content.replace(old_h2, new_h2)
                        break
    
    # Rejoin paragraphs
    optimized_content = '\n\n'.join(paragraphs)
    
    return optimized_content

def generate_title_variations(title, keyword=None, count=3):
    """
    Generate variations of a title optimized for SEO.
    
    Args:
        title: The original title
        keyword: The primary keyword to include (default: None)
        count: Number of variations to generate (default: 3)
        
    Returns:
        List of title variations
    """
    logger.info(f"Generating title variations for: {title}")
    
    variations = []
    
    # Use the title as the keyword if none provided
    if not keyword:
        keyword = title
    
    # Basic variations
    variations.append(f"The Ultimate Guide to {title}")
    variations.append(f"How to {title}: A Complete Guide")
    variations.append(f"{count} Ways to {title} That Actually Work")
    variations.append(f"Everything You Need to Know About {title}")
    variations.append(f"{title}: The Complete Guide for {datetime.now().year}")
    variations.append(f"Why {title} Matters and How to Do It Right")
    variations.append(f"The Beginner's Guide to {title}")
    variations.append(f"Master {title} in {random.choice([5, 7, 10])} Simple Steps")
    variations.append(f"{title}: Tips, Tricks, and Best Practices")
    variations.append(f"The Science Behind {title} and Why It Works")
    
    # Question-based variations
    variations.append(f"What Is {title} and Why Does It Matter?")
    variations.append(f"How Can {title} Improve Your Life?")
    variations.append(f"Why Is {title} Important for Success?")
    
    # Number-based variations
    numbers = [5, 7, 10, 12, 15]
    variations.append(f"Top {random.choice(numbers)} {title} Strategies")
    variations.append(f"{random.choice(numbers)} Essential {title} Tips for Beginners")
    variations.append(f"{random.choice(numbers)} Expert-Approved {title} Techniques")
    
    # List-based variations
    variations.append(f"A Step-by-Step Guide to {title}")
    variations.append(f"The Do's and Don'ts of {title}")
    variations.append(f"The Pros and Cons of {title}")
    
    # Shuffle variations and return requested number
    random.shuffle(variations)
    return variations[:count]

def optimize_meta_description(content, keyword=None, max_length=155):
    """
    Generate an optimized meta description from content.
    
    Args:
        content: The content to extract meta description from
        keyword: The primary keyword to include (default: None)
        max_length: Maximum length of meta description (default: 155)
        
    Returns:
        Optimized meta description
    """
    logger.info("Generating optimized meta description")
    
    if not content:
        logger.warning("No content provided for meta description generation")
        return ""
    
    # Remove HTML tags
    clean_content = re.sub(r'<[^>]+>', '', content)
    
    # Get first paragraph
    paragraphs = clean_content.split('\n\n')
    paragraphs = [p for p in paragraphs if p.strip()]
    
    if not paragraphs:
        logger.warning("No paragraphs found in content")
        return ""
    
    first_paragraph = paragraphs[0]
    
    # If first paragraph is too long, truncate it
    if len(first_paragraph) > max_length:
        # Try to find a sentence break
        sentences = re.split(r'(?<=[.!?])\s+', first_paragraph)
        description = ""
        
        for sentence in sentences:
            if len(description + sentence) <= max_length - 3:  # Leave room for "..."
                description += sentence + " "
            else:
                break
        
        description = description.strip()
        
        # If still too long or no sentences found, truncate at word boundary
        if not description or len(description) > max_length - 3:
            words = first_paragraph.split(' ')
            description = ""
            
            for word in words:
                if len(description + word) <= max_length - 3:
                    description += word + " "
                else:
                    break
            
            description = description.strip()
        
        description += "..."
    else:
        description = first_paragraph
    
    # Ensure the keyword is included
    if keyword and keyword.lower() not in description.lower():
        # Try to insert keyword near the beginning
        words = description.split(' ')
        insert_position = min(3, len(words))  # Insert after first few words
        words.insert(insert_position, keyword)
        
        # Reconstruct and check length
        new_description = ' '.join(words)
        
        if len(new_description) <= max_length:
            description = new_description
        else:
            # If too long, try again with a shorter insertion point
            words = description.split(' ')
            truncated_words = words[:len(words) - 3]  # Remove last few words
            truncated_words.insert(insert_position, keyword)
            description = ' '.join(truncated_words) + "..."
    
    return description