"""
Content Generator Module

This module handles the generation of article content using AI.
It supports both word-count based generation and paragraph-based generation.
"""
import logging
import os
import json
import re
import sys
from typing import Dict, List, Any, Optional

# Import our OpenRouter client
from utils.openrouter import openrouter
from config import Config

logger = logging.getLogger(__name__)

# Determine if we have a valid API key
openrouter_key = os.environ.get('OPENROUTER_API_KEY')
has_openrouter = openrouter_key is not None and len(openrouter_key) > 0

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
        result = openrouter.generate_completion(
            prompt=user_prompt,
            model=model,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=500  # Reduced for more reliability
        )
        
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
            model = Config.DEFAULT_CONTENT_MODEL or "anthropic/claude-3.5-sonnet"
            
            # Send request to OpenRouter
            logger.info(f"Generating content using model: {model}")
            
            # Use our direct OpenRouter client
            content = openrouter.generate_completion(
                prompt=user_prompt,
                model=model,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=8000  # Drastically increased for much longer paragraphs
            )
            
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
    
    # Ensure paragraph count is within valid range
    if paragraph_count < 3:
        paragraph_count = 3
    elif paragraph_count > 6:
        paragraph_count = 6
    
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
            model = Config.DEFAULT_CONTENT_MODEL or "anthropic/claude-3.5-sonnet"
            
            # Send request to OpenRouter
            logger.info(f"Generating article plan using model: {model}")
            
            # Use our direct OpenRouter client
            result = openrouter.generate_completion(
                prompt=user_prompt,
                model=model,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=2000
            )
            
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

def _generate_paragraph(topic, paragraph_topic, previous_content="", keywords=None, style="informative", is_introduction=False, is_conclusion=False):
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
    
    # Create prompt for paragraph generation
    user_prompt = f"""Write a comprehensive section for a professional blog article on "{topic}".

This section should focus on: "{paragraph_topic}"
Section type: {paragraph_type}
Writing style: {style}
Keywords to include if relevant: {', '.join(keywords) if keywords else 'No specific keywords required'}

"""

    if is_introduction:
        user_prompt += """For this introduction section:
1. Start with an engaging hook to capture reader attention
2. Clearly introduce the main topic and establish its importance and relevance
3. Outline what the article will cover and why it matters to the reader
4. Set the tone for the article and create anticipation for the content
5. Make it compelling and inviting to continue reading
6. Write at least 1500-2000 words with multiple paragraphs for readability
7. Provide substantial background information to properly frame the topic
8. Consider including relevant statistics or expert opinions to establish credibility"""
    elif is_conclusion:
        user_prompt += """For this conclusion section:
1. Thoroughly summarize the key points and insights from the article
2. Reinforce the main message and central takeaway
3. Provide actionable next steps or recommendations for readers
4. End with a thought-provoking statement or powerful call to action
5. Leave the reader with a lasting impression
6. Write at least 1500-2000 words with multiple paragraphs for readability
7. Include reflection on broader implications or future developments
8. Address any potential counterarguments or limitations"""
    else:
        user_prompt += f"""For this main content section on "{paragraph_topic}":
1. Start with a strong topic sentence that clearly introduces this specific aspect
2. Thoroughly explore the topic with comprehensive explanations and in-depth analysis
3. Include multiple specific examples, relevant data points, expert opinions, and evidence
4. Address all potential questions readers might have about this aspect
5. Provide detailed practical applications and real-world implications
6. Add significant depth with nuanced perspectives and lesser-known information
7. Ensure the section is comprehensive - MUST be at least 1500-2000 words minimum
8. Format as multiple paragraphs for readability (at least 3-4 paragraphs in this section)
9. Include at least one relevant analogy or case study to illustrate key points
10. Anticipate and address common misconceptions or objections
11. Make it extremely informative while maintaining reader engagement
12. For complex aspects, include step-by-step explanations when appropriate"""

    if prev_content_summary:
        user_prompt += f"\n\nPrevious content for context:\n{prev_content_summary}"

    user_prompt += "\n\nPlease write the content in proper HTML format with <p> tags for paragraphs. Format as multiple paragraphs for readability. Do not include headings or any other HTML elements."

    # System prompt to guide AI behavior
    system_prompt = """You are an expert content writer specializing in creating extremely comprehensive, engaging, well-structured blog content with significant length and depth.
Your task is to write a detailed section on the specified topic that flows naturally with the rest of the article.
Use multiple <p> tags to create well-structured paragraphs for readability.
Provide ONLY the content in proper HTML format with <p> tags. Do not include any explanations or notes. Write very long, detailed paragraphs with at least 1500-2000 words total per section."""

    # Check if we have access to OpenRouter
    if has_openrouter:
        try:
            # Get default content model from config
            model = Config.DEFAULT_CONTENT_MODEL or "anthropic/claude-3.5-sonnet"
            
            # Send request to OpenRouter
            logger.info(f"Generating paragraph using model: {model}")
            
            # Use our direct OpenRouter client
            content = openrouter.generate_completion(
                prompt=user_prompt,
                model=model,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=8000  # Drastically increased for much longer paragraphs
            )
            
            if not content:
                logger.error("Failed to get paragraph from OpenRouter")
                return f"<p>This paragraph would discuss {paragraph_topic}.</p>"
            
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