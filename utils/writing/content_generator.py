"""
Content Generator Utility Module
"""
import json
import random
import logging
import re
from datetime import datetime
import os

import anthropic
from anthropic import Anthropic
from app import db

logger = logging.getLogger(__name__)

# Content style templates to guide the AI
CONTENT_STYLES = {
    'informative': "Write in an informative, educational style with a neutral tone. Focus on providing clear explanations and factual information. Use a professional third-person perspective.",
    
    'conversational': "Write in a friendly, conversational style as if talking directly to the reader. Use 'you' and 'we' pronouns, ask rhetorical questions, and maintain an approachable, helpful tone.",
    
    'professional': "Write in a formal, authoritative style appropriate for a business or technical audience. Use industry terminology where appropriate and maintain a serious, professional tone.",
    
    'storytelling': "Write using narrative techniques and storytelling elements. Include anecdotes, scenarios, or case studies to illustrate points. Create an engaging flow that draws the reader through the content.",
    
    'persuasive': "Write in a persuasive style that aims to convince the reader of a particular viewpoint. Use compelling arguments, evidence, and calls-to-action.",
}

# Content length settings in approximate word counts
CONTENT_LENGTHS = {
    'short': {
        'word_count': 800,
        'description': "A concise article of around 800 words with essential information only."
    },
    'medium': {
        'word_count': 1200,
        'description': "A standard article of around 1200 words with comprehensive coverage of the topic."
    },
    'long': {
        'word_count': 1600,
        'description': "An in-depth article of around 1600 words with detailed explanations and examples."
    }
}


def generate_article(topic, keywords=None, style='informative', length='medium'):
    """
    Generate a complete article using AI models
    
    Args:
        topic (str): The main topic/title of the article
        keywords (list): List of keywords to include in the article
        style (str): Writing style to use (e.g., 'informative', 'conversational')
        length (str): Desired article length ('short', 'medium', 'long')
    
    Returns:
        dict: Generated article content and metadata
    """
    logger.info(f"Generating article: '{topic}' with style '{style}' and length '{length}'")
    
    # Default to sensible values if invalid options provided
    if style not in CONTENT_STYLES:
        style = 'informative'
    
    if length not in CONTENT_LENGTHS:
        length = 'medium'
    
    # Ensure keywords is a list
    if keywords is None:
        keywords = []
    elif isinstance(keywords, str):
        keywords = [k.strip() for k in keywords.split(',')]
    
    # Try to use Anthropic API
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    if api_key:
        try:
            logger.info("Using Anthropic API for content generation")
            return generate_with_anthropic(topic, keywords, style, length)
        except Exception as e:
            logger.error(f"Error with Anthropic API: {str(e)}")
            # Fall back to template-based generation
    
    # If we don't have an API key or the API call failed, use template-based generation
    return generate_with_templates(topic, keywords, style, length)


def generate_with_anthropic(topic, keywords, style, length):
    """Generate article using Anthropic Claude API"""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    client = Anthropic(api_key=api_key)
    
    # Prepare keywords string
    keywords_str = ", ".join(keywords) if keywords else "No specific keywords required"
    
    # Get content style and length descriptions
    style_description = CONTENT_STYLES.get(style, CONTENT_STYLES['informative'])
    length_info = CONTENT_LENGTHS.get(length, CONTENT_LENGTHS['medium'])
    word_count = length_info['word_count']
    
    # Create the system prompt
    system_prompt = f"""You are an expert content writer specializing in creating SEO-optimized blog articles.
Your task is to create a high-quality article on the provided topic that is informative, engaging, and optimized for search engines."""

    # Create the user prompt
    user_prompt = f"""Please write a complete blog article with the following specifications:

TITLE: {topic}

KEYWORDS TO INCLUDE: {keywords_str}

STYLE GUIDELINES: {style_description}

LENGTH: Approximately {word_count} words

STRUCTURE REQUIREMENTS:
1. Include an engaging introduction
2. Use properly formatted H2 and H3 headings throughout the article
3. Include bullet points or numbered lists where appropriate
4. Write short, readable paragraphs (2-4 sentences each)
5. Include a conclusion section

SEO CONSIDERATIONS:
1. Naturally incorporate the keywords throughout the text
2. Create SEO-friendly headings
3. Optimize readability with short sentences and paragraphs
4. Include transitional phrases between sections

OUTPUT FORMAT:
1. Provide the article in HTML format with appropriate tags (<h2>, <h3>, <p>, <ul>, <li>, etc.)
2. After the article, provide:
   - A meta description (150-160 characters)
   - An excerpt/snippet (50-60 words)
   - A list of 5-8 relevant tags for the article

The article should be comprehensive, factually accurate, and provide genuine value to readers interested in this topic."""

    # Send the request to Anthropic
    try:
        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=4000,
            temperature=0.7,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        
        # Extract the content
        content = response.content[0].text
        
        # Parse the response to extract different components
        article_html, meta_description, excerpt, tags = parse_anthropic_response(content)
        
        # Return the structured content
        return {
            'content': article_html,
            'meta_description': meta_description,
            'excerpt': excerpt,
            'tags': tags,
            'featured_image_url': '' # We're not generating images in this example
        }
        
    except Exception as e:
        logger.error(f"Error generating content with Anthropic: {str(e)}")
        # Fall back to template-based generation
        return generate_with_templates(topic, keywords, style, length)


def parse_anthropic_response(content):
    """Parse the response from Anthropic to extract article, meta description, excerpt, and tags"""
    # Default values
    article_html = ""
    meta_description = ""
    excerpt = ""
    tags = []
    
    # Extract article HTML (everything before Meta Description)
    meta_desc_match = re.search(r'(?i)META\s+DESCRIPTION', content)
    if meta_desc_match:
        article_html = content[:meta_desc_match.start()].strip()
    else:
        # If meta description not found, take the whole content as article
        article_html = content
        return article_html, meta_description, excerpt, tags
    
    # Extract meta description
    excerpt_match = re.search(r'(?i)EXCERPT', content[meta_desc_match.end():])
    if excerpt_match:
        meta_desc_text = content[meta_desc_match.end():meta_desc_match.end() + excerpt_match.start()].strip()
        
        # Extract the actual text, removing labels and special characters
        meta_desc_clean = re.sub(r'(?i)^.*?:', '', meta_desc_text).strip()
        meta_description = meta_desc_clean
    
    # Extract excerpt
    tags_match = re.search(r'(?i)TAGS', content[meta_desc_match.end() + excerpt_match.end():])
    if tags_match:
        excerpt_text = content[meta_desc_match.end() + excerpt_match.end():meta_desc_match.end() + excerpt_match.end() + tags_match.start()].strip()
        
        # Extract the actual text, removing labels and special characters
        excerpt_clean = re.sub(r'(?i)^.*?:', '', excerpt_text).strip()
        excerpt = excerpt_clean
    
    # Extract tags
    if tags_match:
        tags_text = content[meta_desc_match.end() + excerpt_match.end() + tags_match.end():].strip()
        
        # Remove any labels and get individual tags
        tags_clean = re.sub(r'(?i)^.*?:', '', tags_text).strip()
        
        # Extract individual tags
        # Try to handle various formats (comma-separated, bullet points, etc.)
        if ',' in tags_clean:
            tags = [tag.strip() for tag in tags_clean.split(',')]
        else:
            # Look for bullet points or numbered lists
            tag_lines = [line.strip() for line in tags_clean.split('\n') if line.strip()]
            tag_items = []
            for line in tag_lines:
                # Remove bullets, numbers, dashes, etc.
                cleaned = re.sub(r'^[\*\-•#\d\.\s]+', '', line).strip()
                if cleaned:
                    tag_items.append(cleaned)
            
            if tag_items:
                tags = tag_items
            else:
                # Just use the whole thing as one tag if we couldn't parse it
                tags = [tags_clean]
    
    return article_html, meta_description, excerpt, tags


def generate_with_templates(topic, keywords, style, length):
    """Generate article using templates when API is not available"""
    # In a real implementation, this would use a more sophisticated template system
    # For now, we'll generate a very basic article structure
    
    word_count = CONTENT_LENGTHS.get(length, CONTENT_LENGTHS['medium'])['word_count']
    
    # Generate a simple article structure
    article_parts = []
    
    # Introduction
    article_parts.append(f"<h1>{topic}</h1>")
    article_parts.append("<p>This is an introductory paragraph about the topic. It provides an overview and sets the stage for the detailed discussion that follows.</p>")
    
    # Main content sections
    for i in range(3):
        section_title = f"Major Aspect {i+1} of {topic}"
        article_parts.append(f"<h2>{section_title}</h2>")
        article_parts.append("<p>This paragraph explains an important aspect of the main topic. It provides detailed information and examples to help the reader understand the concept better.</p>")
        
        for j in range(2):
            subsection = f"Sub-component {j+1}"
            article_parts.append(f"<h3>{subsection}</h3>")
            article_parts.append("<p>This paragraph explores a specific element of the section topic. It goes into greater depth on this particular aspect.</p>")
            
            # Add a list
            if j == 0:
                article_parts.append("<p>Here are some key points to consider:</p>")
                article_parts.append("<ul>")
                for k in range(3):
                    list_item = f"Important point {k+1}"
                    if keywords and k < len(keywords):
                        list_item += f" related to {keywords[k]}"
                    article_parts.append(f"<li>{list_item}</li>")
                article_parts.append("</ul>")
    
    # Conclusion
    article_parts.append("<h2>Conclusion</h2>")
    article_parts.append("<p>This final paragraph summarizes the key points discussed in the article and may suggest next steps or additional resources for the reader.</p>")
    
    # Combine parts into HTML
    article_html = "\n".join(article_parts)
    
    # Generate metadata
    meta_description = f"Learn all about {topic} in this comprehensive guide. Discover key insights and practical advice on {', '.join(keywords[:3]) if keywords else 'this topic'}."
    
    excerpt = f"This article provides a comprehensive overview of {topic}. Read on to learn the essential aspects of this important subject."
    
    # Generate tags
    tags = keywords[:8] if keywords else [f"Tag {i+1} for {topic}" for i in range(5)]
    
    # Return the generated content
    return {
        'content': article_html,
        'meta_description': meta_description,
        'excerpt': excerpt,
        'tags': tags,
        'featured_image_url': '' # We're not generating images in this example
    }


def generate_metadata(content):
    """Generate metadata (meta description, excerpt, tags) from existing content"""
    # Extract text from HTML content
    text_content = re.sub(r'<[^>]+>', ' ', content)
    text_content = re.sub(r'\s+', ' ', text_content).strip()
    
    # Create a meta description from the first ~155 characters
    meta_description = text_content[:155] + "..." if len(text_content) > 155 else text_content
    
    # Create an excerpt from the first ~50 words
    words = text_content.split()
    excerpt = " ".join(words[:50]) + "..." if len(words) > 50 else text_content
    
    # Extract potential tags from headings in the content
    headings = re.findall(r'<h[1-3][^>]*>(.*?)</h[1-3]>', content)
    potential_tags = []
    
    for heading in headings:
        # Clean the heading text
        clean_heading = re.sub(r'<[^>]+>', '', heading).strip()
        
        # Split into words and keep those longer than 3 characters
        words = clean_heading.split()
        for word in words:
            word = re.sub(r'[^\w\s]', '', word).strip()
            if len(word) > 3 and word.lower() not in ['this', 'that', 'with', 'from', 'have', 'what', 'been', 'were', 'when', 'where', 'will', 'your', 'their']:
                potential_tags.append(word)
    
    # Take unique tags, up to 8
    tags = list(set(potential_tags))[:8]
    
    return {
        'meta_description': meta_description,
        'excerpt': excerpt,
        'tags': tags
    }