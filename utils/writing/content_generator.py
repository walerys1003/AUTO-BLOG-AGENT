"""
Content Generator Module

This module handles the generation of article content using AI.
It supports both word-count based generation and paragraph-based generation.
It also provides API for dynamic paragraph-by-paragraph generation.
"""
import logging
import os
import json
import re
import sys
from typing import Dict, List, Any, Optional

# Import our OpenRouter client
from utils.openrouter import openrouter
from config import Config as config

logger = logging.getLogger(__name__)

# Determine if we have a valid API key
openrouter_key = os.environ.get('OPENROUTER_API_KEY')
has_openrouter = openrouter_key is not None and len(openrouter_key) > 0

def generate_metadata(content):
    """
    Generate metadata from content using AI
    
    Args:
        content (str): The article content
        
    Returns:
        dict: Metadata including meta description, excerpt, and tags
    """
    logger.info("Generating metadata from content")
    
    # Default metadata if generation fails
    default_metadata = {
        'meta_description': '',
        'excerpt': '',
        'tags': []
    }
    
    # If content is empty, return default metadata
    if not content:
        return default_metadata
        
    # Strip HTML tags for processing
    content_text = re.sub(r'<[^>]+>', '', content)
    
    # Create prompt for metadata generation
    user_prompt = f"""Generate metadata for the following article content:

{content_text[:3000]}  # Limit to first 3000 chars to avoid token limits

Please provide:
1. A compelling meta description (150-160 characters)
2. A brief excerpt/snippet (200-250 characters)
3. 5-7 relevant tags/keywords (as a list)

Format your response as a JSON object with the following structure:
{{
  "meta_description": "The meta description text...",
  "excerpt": "The excerpt text...",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
}}"""

    # System prompt to guide AI behavior
    system_prompt = """You are an expert SEO specialist and content editor.
Your task is to create metadata that will improve search visibility and click-through rates.
Respond ONLY with a valid JSON object in the exact format requested."""
    
    # Check if we have access to OpenRouter
    if has_openrouter:
        try:
            # Get default content model from config
            model = config.DEFAULT_CONTENT_MODEL or "anthropic/claude-3.5-sonnet"
            
            # Send request to OpenRouter
            logger.info(f"Generating metadata using model: {model}")
            
            # Use our direct OpenRouter client
            result = openrouter.generate_completion(
                prompt=user_prompt,
                model=model,
                system=system_prompt,
                max_tokens=1000,
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            if result and result.get('choices') and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                try:
                    metadata = json.loads(content)
                    return {
                        'meta_description': metadata.get('meta_description', ''),
                        'excerpt': metadata.get('excerpt', ''),
                        'tags': metadata.get('tags', [])
                    }
                except json.JSONDecodeError:
                    logger.error("Failed to parse metadata JSON")
                    return default_metadata
            else:
                logger.error("No valid response from API for metadata generation")
                return default_metadata
                
        except Exception as e:
            logger.error(f"Error generating metadata: {str(e)}")
            return default_metadata
    else:
        logger.warning("OpenRouter key not available for metadata generation")
        return default_metadata


def _get_mock_content(topic, keywords, style, length):
    """
    Generate mock content when API is not available
    
    Args:
        topic (str): The article topic
        keywords (list): List of keywords
        style (str): Writing style
        length (str): Content length
        
    Returns:
        dict: Mock content data
    """
    logger.warning("Using mock content generator")
    
    title = f"The Complete Guide to {topic}"
    
    html_content = f"""
    <h1>{title}</h1>
    <p>This is a sample article about {topic}. In a real implementation, this would be generated using AI.</p>
    <h2>Key Points About {topic}</h2>
    <p>Here are some important aspects to consider when discussing {topic}:</p>
    <ul>
        <li>First key point about {topic}</li>
        <li>Second key point about {topic}</li>
        <li>Third key point about {topic}</li>
    </ul>
    <h2>Best Practices for {topic}</h2>
    <p>When implementing {topic}, consider these best practices:</p>
    <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam in dui mauris.</p>
    <h3>Advanced Strategies</h3>
    <p>For those looking to take their {topic} to the next level:</p>
    <p>Vestibulum pellentesque felis eu massa. Quisque ullamcorper placerat ipsum.</p>
    <h2>Conclusion</h2>
    <p>In conclusion, {topic} is an important subject that requires careful consideration.</p>
    """
    
    meta_description = f"Learn everything you need to know about {topic} in this comprehensive guide. We cover key concepts, best practices, and advanced strategies."
    
    excerpt = f"This comprehensive guide explores {topic} in detail, providing you with essential knowledge and practical tips."
    
    tags = [topic] + (keywords if keywords else [])
    
    return {
        "content": html_content,
        "meta_description": meta_description,
        "excerpt": excerpt,
        "tags": tags[:5],
        "featured_image_url": ""
    }

def _create_default_metadata(topic, keywords=None):
    """Create default metadata when AI generation fails"""
    tags = list(keywords) if keywords else []
    topic_words = topic.lower().split()
    for word in topic_words:
        if len(word) > 3 and word not in [t.lower() for t in tags]:
            tags.append(word.capitalize())
    
    return {
        "meta_description": f"Learn everything you need to know about {topic} in this comprehensive guide. We cover key concepts, best practices, and practical strategies.",
        "excerpt": f"This article explores {topic} in detail, providing you with essential knowledge and practical tips for success.",
        "tags": tags[:5]
    }

def _extract_html_content(content):
    """
    Extract HTML content from the AI response
    
    Args:
        content (str): The AI-generated content
        
    Returns:
        str: Clean HTML content
    """
    # Look for HTML content between opening and closing tags
    html_start = content.find("<h1")
    if html_start == -1:
        html_start = content.find("<H1")
    
    html_end = content.rfind("</p>")
    if html_end == -1:
        html_end = content.rfind("</P>")
    
    if html_start != -1 and html_end != -1:
        return content[html_start:html_end+4]
    
    # If no clear HTML, return the whole content
    return content


def _extract_meta_description(content):
    """
    Extract meta description from the AI response
    
    Args:
        content (str): The AI-generated content
        
    Returns:
        str: Meta description
    """
    meta_desc_patterns = [
        r"(?i)Meta\s*Description:\s*\"?([^\"]+)\"?",
        r"(?i)Meta\s*Description:\s*(.+?)(?:\n|$)",
        r"(?i)<meta\s+name=\"description\"\s+content=\"([^\"]+)\"",
    ]
    
    for pattern in meta_desc_patterns:
        match = re.search(pattern, content)
        if match:
            return match.group(1).strip()
    
    # If no meta description found, create one from the first paragraph
    paragraphs = re.findall(r"<p>(.*?)</p>", content, re.DOTALL)
    if paragraphs:
        # Clean the first paragraph of any HTML and limit to ~155 chars
        first_para = re.sub(r"<.*?>", "", paragraphs[0])
        if len(first_para) > 155:
            return first_para[:152] + "..."
        return first_para
        
    return ""


def _extract_excerpt(content):
    """
    Extract excerpt from the AI response
    
    Args:
        content (str): The AI-generated content
        
    Returns:
        str: Excerpt
    """
    excerpt_patterns = [
        r"(?i)Excerpt:\s*\"?([^\"]+)\"?",
        r"(?i)Excerpt:\s*(.+?)(?:\n|$)",
    ]
    
    for pattern in excerpt_patterns:
        match = re.search(pattern, content)
        if match:
            return match.group(1).strip()
    
    # If no excerpt found, use the meta description
    meta_desc = _extract_meta_description(content)
    if meta_desc:
        return meta_desc
        
    return ""


def _generate_tags_from_content(topic, keywords, content):
    """
    Generate tags from the content
    
    Args:
        topic (str): The article topic
        keywords (list): List of keywords
        content (str): The article content
        
    Returns:
        list: Generated tags
    """
    # Start with keywords if available
    tags = list(keywords) if keywords else []
    
    # Add the main topic as a tag if not already present
    topic_words = topic.lower().split()
    for word in topic_words:
        if len(word) > 3 and word not in [t.lower() for t in tags]:
            tags.append(word.capitalize())
    
    # Limit to 5 tags maximum
    return tags[:5]

def _generate_article_metadata(topic, content, keywords=None):
    """
    Generate metadata for the article (meta description, excerpt, tags)
    
    Args:
        topic (str): The article topic
        content (str): The full article content
        keywords (list): List of keywords
        
    Returns:
        dict: Metadata including meta description, excerpt, and tags
    """
    # For paragraph-based generation, start with sensible defaults first
    # This ensures we always have something valid to return
    default_metadata = _create_default_metadata(topic, keywords)
    
    # Only attempt AI generation if OpenRouter is available
    if not has_openrouter:
        logger.warning("No OpenRouter API key available, returning basic metadata")
        return default_metadata
        
    # Create a simpler prompt for more reliable metadata generation
    try:
        # Create prompt for metadata generation - simplified for reliability
        user_prompt = f"""Generate SEO metadata for a blog article titled: "{topic}"
        
        Please provide:
        1. A compelling meta description under 160 characters
        2. A brief excerpt for social sharing (2-3 sentences)
        3. 3-5 relevant SEO tags as a comma-separated list
        
        Keywords to include where relevant: {', '.join(keywords) if keywords else 'No specific keywords'}"""
        
        # System prompt to guide AI behavior - simpler format for reliability
        system_prompt = """You are an SEO expert. Create metadata that will help the article perform well in search results.
        Format your response as:
        
        Meta Description: [your meta description here]
        Excerpt: [your excerpt here]
        Tags: [tag1], [tag2], [tag3]"""
        
        # Use a simpler model for metadata generation
        model = "anthropic/claude-3.5-haiku"
        
        logger.info(f"Generating article metadata using simpler model: {model}")
        
        # Try with a shorter max_tokens to improve reliability
        response_obj = openrouter.generate_completion(
            prompt=user_prompt,
            model=model,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=500  # Reduced for more reliability
        )
        
        # Extract content from response object
        result = ""
        if response_obj and "choices" in response_obj and len(response_obj["choices"]) > 0:
            result = response_obj["choices"][0].get("message", {}).get("content", "")
        
        if not result:
            logger.warning("Empty result from OpenRouter, using default metadata")
            return default_metadata
        
        # Parse the structured format instead of JSON for better reliability
        metadata = {}
        
        # Extract meta description
        meta_desc_match = re.search(r"Meta Description:\s*(.+?)(?:\n|$)", result)
        if meta_desc_match:
            metadata["meta_description"] = meta_desc_match.group(1).strip()
        else:
            metadata["meta_description"] = default_metadata["meta_description"]
        
        # Extract excerpt
        excerpt_match = re.search(r"Excerpt:\s*(.+?)(?:\n|Tags:|$)", result, re.DOTALL)
        if excerpt_match:
            metadata["excerpt"] = excerpt_match.group(1).strip()
        else:
            metadata["excerpt"] = default_metadata["excerpt"]
        
        # Extract tags
        tags_match = re.search(r"Tags:\s*(.+?)(?:\n|$)", result)
        if tags_match:
            tags_str = tags_match.group(1).strip()
            metadata["tags"] = [tag.strip() for tag in tags_str.split(",")]
        else:
            metadata["tags"] = default_metadata["tags"]
        
        # If we got here with valid metadata, return it
        return metadata
        
    except Exception as e:
        # Catch-all exception handler
        logger.error(f"Error in metadata generation: {str(e)}")
        # Ensure we always return valid metadata
        return default_metadata

def generate_article(topic, keywords=None, style="informative", length="medium"):
    """
    Generate an article using AI
    
    Args:
        topic (str): The article topic or title
        keywords (list, optional): List of keywords to include
        style (str): Writing style (informative, conversational, professional, storytelling, persuasive)
        length (str): Content length (short, medium, long)
        
    Returns:
        dict: Generated content data including HTML, meta description, etc.
    """
    logger.info(f"Generating article content for topic: {topic}")
    
    # Convert length to exact word count
    word_count = {
        "short": 800,
        "medium": 1200,
        "long": 1600
    }.get(length, 1200)
    
    # Create the prompt for article generation with stronger emphasis on exact length
    user_prompt = f"""Write a comprehensive blog article about '{topic}' with EXACTLY {word_count} words.

Topic: {topic}
Style: {style}
Word count: EXACTLY {word_count} words (this is a non-negotiable requirement)
Keywords to include: {', '.join(keywords) if keywords else 'No specific keywords required'}

The article must be formatted with proper HTML structure including:
- An engaging headline (H1 tag)
- Introduction with a hook
- Well-organized sections with appropriate H2 and H3 subheadings
- Bullet points or numbered lists where appropriate
- A strong conclusion

CRITICAL REQUIREMENTS:
1. The article MUST contain EXACTLY {word_count} words - not more, not less. Count every word carefully.
2. After completion, verify the word count before providing the final result.
3. Do not include the word count in the article itself.
4. Be comprehensive and add valuable content - avoid fluff or filler text.
5. Include real examples, case studies, statistics, or research data as needed.
6. The article should be factually accurate, well-researched, and provide real value to readers.

After completing the article with EXACTLY {word_count} words, please also include:
- Meta description (under 160 characters)
- Brief excerpt for social sharing (2-3 sentences)
- 3-5 tags for the article (comma-separated)"""

    # System prompt to guide the AI's behavior
    system_prompt = """You are an expert content writer specializing in creating high-quality blog articles.
Your task is to write a well-structured, engaging, and informative article following the exact specifications provided.
Focus on accuracy, readability, and meeting the exact word count requirements."""

    # Check if we have access to OpenRouter
    if has_openrouter:
        try:
            # Get default content model from config
            model = config.DEFAULT_CONTENT_MODEL or "anthropic/claude-3.5-sonnet"
            
            # Send request to OpenRouter
            logger.info(f"Generating content using model: {model}")
            
            # Use our direct OpenRouter client
            response_obj = openrouter.generate_completion(
                prompt=user_prompt,
                model=model,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=4000  # Zwiększony limit dla zapewnienia pełnych odpowiedzi
            )
            
            # Extract content from response object
            content = ""
            if response_obj and "choices" in response_obj and len(response_obj["choices"]) > 0:
                content = response_obj["choices"][0].get("message", {}).get("content", "")
            
            if not content:
                logger.error("Failed to get content from OpenRouter")
                return _get_mock_content(topic, keywords, style, length)
            
            # Extract content sections
            html_content = _extract_html_content(content)
            meta_description = _extract_meta_description(content)
            excerpt = _extract_excerpt(content)
            
            # Generate tags
            tags = _generate_tags_from_content(topic, keywords, content)
            
            return {
                "content": html_content,
                "meta_description": meta_description,
                "excerpt": excerpt,
                "tags": tags,
                "featured_image_url": ""  # In a real implementation, this would be generated or fetched
            }
            
        except Exception as e:
            logger.error(f"Error generating content with AI: {str(e)}")
            return _get_mock_content(topic, keywords, style, length)
    else:
        # No API key, return mock content
        logger.warning("No OpenRouter API key available")
        return _get_mock_content(topic, keywords, style, length)

def generate_article_by_paragraphs(topic, keywords=None, style="informative", paragraph_count=4):
    """
    Generate an article using AI with a paragraph-by-paragraph approach
    
    Args:
        topic (str): The article topic or title
        keywords (list, optional): List of keywords to include
        style (str): Writing style (informative, conversational, professional, storytelling, persuasive)
        paragraph_count (int): Number of paragraphs to generate (3-6)
        
    Returns:
        dict: Generated content data including HTML, meta description, etc.
    """
    logger.info(f"Generating article content for topic: {topic} using paragraph-based approach")
    
    # Ensure paragraph count is within valid range - bardziej zachowawcze limity
    if paragraph_count < 3:
        paragraph_count = 3
    elif paragraph_count > 4:  # Zmniejszamy maksymalną liczbę akapitów dla większej stabilności
        paragraph_count = 4
    
    # First step: Generate a plan for the article with paragraph topics
    plan = _generate_article_plan(topic, keywords, paragraph_count, style)
    
    if not plan or 'paragraph_topics' not in plan:
        logger.error("Failed to generate article plan")
        return _get_mock_content(topic, keywords, style, "medium")
    
    # Get the paragraph topics
    paragraph_topics = plan.get('paragraph_topics', [])
    
    # Generate each paragraph in sequence
    full_html = f"<h1>{topic}</h1>\n"
    previous_paragraphs = ""
    full_content = ""
    
    # Generate introduction
    intro_paragraph = _generate_paragraph(
        topic=topic,
        paragraph_topic="Introduction",
        previous_content="",
        keywords=keywords,
        style=style,
        is_introduction=True
    )
    
    if intro_paragraph:
        full_html += intro_paragraph
        previous_paragraphs += intro_paragraph
        full_content += intro_paragraph
    
    # Generate each main paragraph
    for i, paragraph_topic in enumerate(paragraph_topics):
        logger.info(f"Generating paragraph {i+1} on topic: {paragraph_topic}")
        
        paragraph = _generate_paragraph(
            topic=topic,
            paragraph_topic=paragraph_topic,
            previous_content=previous_paragraphs,
            keywords=keywords,
            style=style
        )
        
        if paragraph:
            header_tag = f"<h2>{paragraph_topic}</h2>\n"
            full_html += header_tag + paragraph
            previous_paragraphs += paragraph
            full_content += header_tag + paragraph
    
    # Generate conclusion
    conclusion_paragraph = _generate_paragraph(
        topic=topic,
        paragraph_topic="Conclusion",
        previous_content=previous_paragraphs,
        keywords=keywords,
        style=style,
        is_conclusion=True
    )
    
    if conclusion_paragraph:
        full_html += "<h2>Conclusion</h2>\n" + conclusion_paragraph
        full_content += "<h2>Conclusion</h2>\n" + conclusion_paragraph
    
    # Generate metadata
    metadata = _generate_article_metadata(topic, full_content, keywords)
    
    return {
        "content": full_html,
        "meta_description": metadata.get("meta_description", ""),
        "excerpt": metadata.get("excerpt", ""),
        "tags": metadata.get("tags", []),
        "featured_image_url": ""
    }

def generate_article_plan(topic, paragraph_count, style):
    """
    Generate a plan for the article with paragraph topics (public API version)
    
    Args:
        topic (str): The article topic or title
        paragraph_count (int): Number of paragraphs to generate
        style (str): Writing style
        
    Returns:
        dict: Article plan data with paragraph topics
    """
    # Get plan using internal function
    keywords = []  # No keywords for public API
    plan = _generate_article_plan(topic, keywords, paragraph_count, style)
    
    if plan and 'paragraph_topics' in plan:
        return {'plan': plan['paragraph_topics']}
    
    # Fallback if plan generation fails
    return {'plan': [f"Aspect {i+1} of {topic}" for i in range(paragraph_count)]}

def generate_paragraph(topic, paragraph_topic, style, is_introduction=False, is_conclusion=False):
    """
    Generate a single paragraph for an article (public API version)
    
    Args:
        topic (str): The main article topic or title
        paragraph_topic (str): Topic for this specific paragraph
        style (str): Writing style
        is_introduction (bool): Whether this is the introduction paragraph
        is_conclusion (bool): Whether this is the conclusion paragraph
        
    Returns:
        dict: Dictionary with the generated paragraph content
    """
    # Generate the paragraph
    paragraph_html = _generate_paragraph(
        topic=topic,
        paragraph_topic=paragraph_topic,
        previous_content="",  # No previous content for API version
        keywords=[],  # No keywords for public API
        style=style,
        is_introduction=is_introduction,
        is_conclusion=is_conclusion
    )
    
    if paragraph_html:
        return {'content': paragraph_html}
    
    # Fallback if generation fails
    return {'content': f"<p>Content for {paragraph_topic} could not be generated. Please try again.</p>"}

def _generate_article_plan(topic, keywords, paragraph_count, style):
    """
    Generate a plan for the article with paragraph topics
    
    Args:
        topic (str): The main article topic
        keywords (list): List of keywords to include
        paragraph_count (int): Number of paragraphs to generate
        style (str): Writing style
        
    Returns:
        dict: Plan with paragraph topics
    """
    # Create prompt for article plan generation
    user_prompt = f"""Create a detailed plan for a blog article on the topic: "{topic}".

The article will have {paragraph_count} main paragraphs (not including introduction and conclusion).
For each paragraph, provide a specific sub-topic or aspect of the main topic to focus on.

Guidelines:
1. The sub-topics should progress logically and cover different aspects of the main topic
2. Each sub-topic should be substantive enough for a full paragraph (150-200 words)
3. The sub-topics should collectively provide comprehensive coverage of the main topic
4. Include keywords where relevant: {', '.join(keywords) if keywords else 'No specific keywords required'}

Please format your response as a JSON object with the following structure:
{{
  "article_title": "Suggested title",
  "paragraph_topics": [
    "Topic for paragraph 1",
    "Topic for paragraph 2",
    ...
  ]
}}"""

    # System prompt to guide AI behavior
    system_prompt = """You are an expert content strategist specializing in creating detailed content plans.
Your task is to create a logical, well-structured plan for an article with distinct paragraph topics.
Respond ONLY with a valid JSON object in the exact format requested."""

    # Check if we have access to OpenRouter
    if has_openrouter:
        try:
            # Get default content model from config
            model = config.DEFAULT_CONTENT_MODEL or "anthropic/claude-3.5-sonnet"
            
            # Send request to OpenRouter
            logger.info(f"Generating article plan using model: {model}")
            
            # Use our direct OpenRouter client
            response_obj = openrouter.generate_completion(
                prompt=user_prompt,
                model=model,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=2500
            )
            
            # Extract content from response object
            result = ""
            if response_obj and "choices" in response_obj and len(response_obj["choices"]) > 0:
                result = response_obj["choices"][0].get("message", {}).get("content", "")
            
            if not result:
                logger.error("Failed to get article plan from OpenRouter")
                return None
            
            # Extract JSON from the response
            try:
                # Find JSON object in the response
                json_start = result.find("{")
                json_end = result.rfind("}") + 1
                
                if json_start != -1 and json_end != -1:
                    json_str = result[json_start:json_end]
                    plan = json.loads(json_str)
                    return plan
                else:
                    logger.error("No valid JSON found in the article plan response")
                    return None
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing article plan JSON: {str(e)}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating article plan: {str(e)}")
            return None
    else:
        # No API key, return basic plan
        logger.warning("No OpenRouter API key available, returning basic article plan")
        return {
            "article_title": f"Guide to {topic}",
            "paragraph_topics": [
                f"Understanding {topic} Basics",
                f"Key Benefits of {topic}",
                f"Best Practices for {topic}",
                f"Future Trends in {topic}"
            ][:paragraph_count]
        }

# Ten fragment zostaje usunięty, ponieważ mamy duplikat funkcji generate_article_plan


def _generate_paragraph(topic, paragraph_topic, previous_content="", keywords=None, style="informative", is_introduction=False, is_conclusion=False, prev_content_summary=None):
    """
    Generate a single paragraph for the article
    
    Args:
        topic (str): The main article topic
        paragraph_topic (str): The specific topic for this paragraph
        previous_content (str): Content generated so far (for context)
        keywords (list): List of keywords to include
        style (str): Writing style
        is_introduction (bool): Whether this is the introduction paragraph
        is_conclusion (bool): Whether this is the conclusion paragraph
        
    Returns:
        str: Generated paragraph in HTML format
    """
    # Determine paragraph type for prompt
    paragraph_type = "introduction" if is_introduction else "conclusion" if is_conclusion else "body"
    
    # Create previous content summary (shortened to avoid token issues)
    prev_content_summary = ""
    if previous_content:
        # Remove HTML tags and get first 200 characters of each previous paragraph
        clean_previous = re.sub(r'<[^>]*>', ' ', previous_content)
        paragraphs = clean_previous.split('\n\n')
        summaries = []
        for p in paragraphs[:3]:  # Only include up to 3 previous paragraphs
            if p.strip():
                summaries.append(p[:200] + ("..." if len(p) > 200 else ""))
        prev_content_summary = "\n".join(summaries)
    
    # Create prompt for paragraph generation - optimized for lower token usage
    user_prompt = f"""Write a section for an article on "{topic}".

Focus: "{paragraph_topic}"
Type: {paragraph_type}
Style: {style}
Keywords: {', '.join(keywords) if keywords else 'N/A'}

"""

    if is_introduction:
        user_prompt += """For this introduction:
1. Start with an engaging hook
2. Introduce the topic and its importance
3. Outline article content and relevance
4. Set tone and create interest
5. Make it compelling
6. Write 600-800 words with multiple paragraphs
7. Provide background context
8. Include statistics/expert opinions where relevant"""
    elif is_conclusion:
        user_prompt += """For this conclusion:
1. Summarize key points
2. Reinforce main message
3. Provide actionable next steps
4. End with call to action
5. Create lasting impression
6. Write 600-800 words with multiple paragraphs
7. Include broader implications
8. Address limitations if relevant"""
    else:
        user_prompt += f"""For this main section on "{paragraph_topic}":
1. Start with clear topic sentence
2. Explore thoroughly with explanations and analysis
3. Include examples, data points, expert opinions
4. Address reader questions
5. Provide practical applications
6. Add depth with nuanced perspectives
7. Write 600-800 words total
8. Use multiple paragraphs (3-4 minimum)
9. Include a relevant analogy or case study
10. Address misconceptions
11. Balance information with engagement
12. Use step-by-step explanations where helpful"""

    if prev_content_summary:
        user_prompt += f"\n\nPrevious content for context:\n{prev_content_summary}"

    user_prompt += "\n\nPlease write the content in proper HTML format with <p> tags for paragraphs. Format as multiple paragraphs for readability. Do not include headings or any other HTML elements."

    # System prompt to guide AI behavior - optimized for lower token usage
    system_prompt = """You are an expert content writer.
Write a detailed section that flows naturally with the article.
Use <p> tags for paragraphs.
Provide ONLY the content in HTML format.
Write 600-800 words total per section."""

    # Check if we have access to OpenRouter
    if has_openrouter:
        try:
            # Get default content model from config
            model = config.DEFAULT_CONTENT_MODEL or "anthropic/claude-3.5-sonnet"
            
            # Send request to OpenRouter
            logger.info(f"Generating paragraph using model: {model}")
            
            # Use our direct OpenRouter client
            
            # Try to get content from OpenRouter
            response_obj = openrouter.generate_completion(
                prompt=user_prompt,
                model=model,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=3000  # Zwiększony limit dla pojedynczego akapitu
            )
            
            # Extract content from response object
            content = ""
            if response_obj and "choices" in response_obj and len(response_obj["choices"]) > 0:
                content = response_obj["choices"][0].get("message", {}).get("content", "")
            
            # If content generation fails, use fallback
            if not content:
                logger.warning(f"Failed to get content from OpenRouter, using fallback generation")
                
                # Create a fallback paragraph that's still useful
                fallback_content = ""
                
                # Add paragraph opening based on the topic
                if is_introduction:
                    fallback_content += f"<p>Understanding {topic} is crucial in today's rapidly evolving landscape. This article explores key aspects of {topic}, providing insights and practical strategies that can be applied in various contexts.</p>"
                    fallback_content += f"<p>As we delve into {topic}, we'll examine several important perspectives and approaches that can help readers gain a comprehensive understanding of this subject. The importance of {topic} cannot be overstated, as it impacts numerous aspects of both personal and professional development.</p>"
                elif is_conclusion:
                    fallback_content += f"<p>In conclusion, {topic} represents a significant area that deserves attention and thoughtful consideration. As we've explored throughout this article, there are multiple dimensions to consider when approaching this subject.</p>"
                    fallback_content += f"<p>By implementing the strategies discussed, readers can develop a more nuanced understanding of {topic} and apply these insights in practical ways. The journey of mastering {topic} is ongoing, but with these foundational principles, significant progress can be made.</p>"
                else:
                    # For middle sections, create something relevant to the paragraph topic
                    fallback_content += f"<p>When examining {paragraph_topic} in relation to {topic}, several key patterns emerge. This aspect of {topic} demonstrates important principles that apply across various scenarios and contexts.</p>"
                    fallback_content += f"<p>Research suggests that {paragraph_topic} significantly influences outcomes related to {topic}. By understanding this relationship, we can develop more effective approaches and strategies for implementation.</p>"
                    fallback_content += f"<p>Experts in the field recommend focusing on specific elements of {paragraph_topic} to maximize results when dealing with {topic}. These recommendations are based on extensive research and practical application in real-world situations.</p>"
                
                return fallback_content
            
            
            # Ensure content is wrapped in <p> tags if not already
            content = content.strip()
            if not content.startswith("<p>"):
                content = f"<p>{content}"
            if not content.endswith("</p>"):
                content = f"{content}</p>"
                
            return content
                
        except Exception as e:
            logger.error(f"Error generating paragraph: {str(e)}")
            return f"<p>This paragraph would discuss {paragraph_topic}.</p>"
    else:
        # No API key
        logger.warning("No OpenRouter API key available, returning placeholder paragraph")
        return f"<p>This paragraph would discuss {paragraph_topic} in an {style} style.</p>"