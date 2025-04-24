import logging
import json
import random
from typing import List, Dict, Any, Optional
from config import Config
import traceback
from utils.helpers import get_ai_response, clean_html

# Setup logging
logger = logging.getLogger(__name__)

def generate_article_content(
    title: str, 
    keywords: List[str], 
    category: str, 
    blog_name: str,
    min_length: int = None,
    max_length: int = None
) -> Dict[str, Any]:
    """
    Generate a complete blog article with SEO optimization
    
    Args:
        title: Article title
        keywords: List of target keywords
        category: Article category
        blog_name: Name of the blog
        min_length: Minimum article length in words
        max_length: Maximum article length in words
        
    Returns:
        Dictionary with article content, meta description, excerpt, and tags
    """
    try:
        # Use config defaults if not specified
        min_length = min_length or Config.ARTICLE_MIN_LENGTH
        max_length = max_length or Config.ARTICLE_MAX_LENGTH
        
        # Create system prompt for content generation
        system_prompt = f"""You are an expert content writer for {blog_name}, specializing in creating high-quality, SEO-optimized blog articles.
Your content is informative, well-structured, and designed to rank well in search engines while providing genuine value to readers.
"""

        # Format keywords for prompt
        keywords_text = ", ".join(keywords)
        
        # Construct the main user prompt
        user_prompt = f"""Write a comprehensive, SEO-optimized blog article with the title: "{title}"

Target keywords: {keywords_text}
Category: {category}
Blog: {blog_name}
Length: Between {min_length} and {max_length} words

The article should:
1. Start with an engaging introduction that hooks the reader and clearly states what the article will cover
2. Include at least 3 main sections with descriptive H2 headings
3. Use H3 subheadings where appropriate
4. Include a bulleted or numbered list in at least one section
5. Incorporate all target keywords naturally throughout the text
6. End with a strong conclusion that summarizes key points
7. Include a call-to-action at the end

Additional SEO requirements:
- Include the primary keyword in the first paragraph
- Use at least one of the keywords in a heading
- Write in a conversational but authoritative tone
- Use short paragraphs (3-4 sentences maximum)
- Include transition phrases between sections

Format your response as a valid JSON object with these fields:
- content: The full HTML content of the article, properly formatted with semantic HTML tags
- meta_description: A compelling meta description under 160 characters that includes the primary keyword
- excerpt: A 2-3 sentence excerpt for social sharing and RSS feeds
- tags: A list of 12-15 relevant tags for the article, including the provided keywords

Ensure the article is completely original, informative, and provides genuine value to readers.
"""

        # Set up JSON response format
        response_format = {"type": "json_object"}
        
        # Get response from AI
        response = get_ai_response(
            prompt=user_prompt,
            model=Config.DEFAULT_CONTENT_MODEL,
            temperature=0.7,
            response_format=response_format,
            system_prompt=system_prompt
        )
        
        # Process response
        if not response:
            logger.error("No response from AI for content generation")
            return generate_fallback_article(title, keywords, category)
        
        # Ensure response is a dictionary
        if isinstance(response, str):
            try:
                response = json.loads(response)
            except:
                logger.error(f"Failed to parse response as JSON: {response}")
                return generate_fallback_article(title, keywords, category)
        
        # Clean HTML content if it exists
        if 'content' in response and response['content']:
            response['content'] = clean_html(response['content'])
        
        # Ensure all required fields are present
        required_fields = ['content', 'meta_description', 'excerpt', 'tags']
        for field in required_fields:
            if field not in response or not response[field]:
                logger.warning(f"Missing required field in article: {field}")
                if field == 'content':
                    # Can't proceed without content
                    return generate_fallback_article(title, keywords, category)
                elif field == 'tags':
                    # Set default tags from keywords
                    response['tags'] = keywords
                elif field == 'meta_description':
                    # Generate a basic meta description
                    response['meta_description'] = f"Learn about {title} in this comprehensive guide from {blog_name}."
                elif field == 'excerpt':
                    # Generate a basic excerpt from title
                    response['excerpt'] = f"A complete guide to {title}. Read more to learn everything you need to know."
        
        # If tags came as a string, convert to list
        if isinstance(response.get('tags'), str):
            try:
                # Try to parse as JSON
                response['tags'] = json.loads(response['tags'])
            except:
                # If it fails, split by commas
                response['tags'] = [tag.strip() for tag in response['tags'].split(',')]
        
        # Ensure tags include at least some keywords
        if isinstance(response.get('tags'), list):
            # Include keywords that aren't already in tags
            for keyword in keywords:
                if keyword.lower() not in [tag.lower() for tag in response['tags']]:
                    response['tags'].append(keyword)
        
        # Add title to response
        response['title'] = title
        
        # Add category to response
        response['category'] = category
        
        return response
        
    except Exception as e:
        logger.error(f"Error generating article content: {str(e)}")
        logger.error(traceback.format_exc())
        return generate_fallback_article(title, keywords, category)

def generate_fallback_article(title: str, keywords: List[str], category: str) -> Dict[str, Any]:
    """
    Generate a basic fallback article when AI generation fails
    
    Args:
        title: Article title
        keywords: List of target keywords
        category: Article category
        
    Returns:
        Basic article with required fields
    """
    try:
        # Create a very basic article
        content = f"""
<h1>{title}</h1>

<p>This is an article about {title}.</p>

<h2>Introduction</h2>
<p>In this article, we will explore various aspects of {title} and why it matters.</p>

<h2>Key Points</h2>
<p>Here are some important things to know about {title}:</p>
<ul>
"""
        
        # Add keywords as bullet points
        for keyword in keywords[:5]:
            content += f"<li>{keyword}</li>\n"
        
        content += """
</ul>

<h2>Conclusion</h2>
<p>We hope this article has been informative and helpful in understanding more about this topic.</p>
"""
        
        return {
            "title": title,
            "content": content,
            "meta_description": f"Learn about {title} in this comprehensive guide. Covers {', '.join(keywords[:3])}.",
            "excerpt": f"A complete guide to {title}. Read more to learn everything you need to know.",
            "tags": keywords,
            "category": category
        }
    
    except Exception as e:
        logger.error(f"Error generating fallback article: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Return absolute minimum
        return {
            "title": title,
            "content": f"<h1>{title}</h1><p>Content coming soon.</p>",
            "meta_description": f"Learn about {title} in this guide.",
            "excerpt": f"Article about {title}.",
            "tags": keywords[:5],
            "category": category
        }

def generate_article_title_suggestions(category: str, keywords: List[str], count: int = 3) -> List[str]:
    """
    Generate engaging article title suggestions based on category and keywords
    
    Args:
        category: Article category
        keywords: Target keywords to include
        count: Number of titles to generate
        
    Returns:
        List of suggested titles
    """
    try:
        # Format keywords for prompt
        keywords_text = ", ".join(keywords)
        
        # Construct the prompt
        prompt = f"""Generate {count} engaging, SEO-friendly article titles for a blog post in the "{category}" category.

The titles should:
1. Include at least one of these keywords: {keywords_text}
2. Be between 50-70 characters long
3. Use strong, compelling language
4. Include numbers or specific details where appropriate (e.g., "7 Essential Tips...", "The Ultimate Guide to...")
5. Appeal to the reader's interests or solve a problem

Format your response as a JSON array of strings, with each string being a complete title.
"""

        # Set up JSON response format
        response_format = {"type": "json_object"}
        
        # Get response from AI
        response = get_ai_response(
            prompt=prompt,
            model=Config.DEFAULT_TOPIC_MODEL,
            temperature=0.8,  # Slightly higher for creativity
            response_format=response_format
        )
        
        # Process response
        if isinstance(response, dict) and 'titles' in response:
            # If response came as a wrapper object with a 'titles' key
            titles = response['titles']
        elif isinstance(response, list):
            # If response came directly as a list
            titles = response
        else:
            # Try to parse if we got a string but expected JSON
            if isinstance(response, str):
                try:
                    parsed = json.loads(response)
                    if isinstance(parsed, dict) and 'titles' in parsed:
                        titles = parsed['titles']
                    elif isinstance(parsed, list):
                        titles = parsed
                    else:
                        logger.error(f"Unexpected response format: {parsed}")
                        return generate_basic_titles(category, keywords, count)
                except:
                    logger.error(f"Failed to parse response as JSON: {response}")
                    return generate_basic_titles(category, keywords, count)
            else:
                logger.error(f"Unexpected response type: {type(response)}")
                return generate_basic_titles(category, keywords, count)
        
        # Validate titles
        valid_titles = []
        for title in titles:
            if isinstance(title, str) and title.strip():
                valid_titles.append(title.strip())
        
        # If we don't have enough titles, generate some basic ones
        if len(valid_titles) < count:
            additional_titles = generate_basic_titles(
                category, 
                keywords,
                count - len(valid_titles)
            )
            valid_titles.extend(additional_titles)
        
        # Return titles, limiting to requested count
        return valid_titles[:count]
        
    except Exception as e:
        logger.error(f"Error generating article titles: {str(e)}")
        logger.error(traceback.format_exc())
        return generate_basic_titles(category, keywords, count)

def generate_basic_titles(category: str, keywords: List[str], count: int) -> List[str]:
    """
    Generate basic article titles when AI generation fails
    
    Args:
        category: Article category
        keywords: Target keywords
        count: Number of titles to generate
        
    Returns:
        List of basic titles
    """
    titles = []
    
    # Templates for basic titles
    templates = [
        "The Ultimate Guide to {keyword}",
        "How to {keyword}: A Complete {category} Guide",
        "10 Essential Tips for {keyword}",
        "Understanding {keyword}: Everything You Need to Know",
        "Why {keyword} Matters in {category}",
        "The Beginner's Guide to {keyword}",
        "{keyword} 101: Getting Started with {category}",
        "How to Master {keyword} in 5 Simple Steps",
        "The Pros and Cons of {keyword} in {category}",
        "{keyword}: Best Practices for Success"
    ]
    
    # Generate titles
    for i in range(count):
        if not keywords:
            # No keywords provided, use category
            keyword = category
        else:
            # Pick a random keyword
            keyword = random.choice(keywords)
            
        # Pick a random template
        template = random.choice(templates)
        
        # Generate title
        title = template.format(keyword=keyword, category=category)
        
        titles.append(title)
        
        # Remove used template to avoid duplicates
        templates.remove(template)
        if not templates:
            # If we run out of templates, reset
            templates = [
                "The Complete {category} Guide to {keyword}",
                "Everything About {keyword} You Need to Know",
                "{keyword}: A Comprehensive Overview",
                "Exploring {keyword} in Detail",
                "The Importance of {keyword} in {category}"
            ]
    
    return titles