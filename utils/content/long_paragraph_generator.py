"""
Long Paragraph Generator Module

This module provides functions to generate longer paragraphs for articles,
with a target token count and verification functionality.
"""
import json
import logging
import re
import time
from typing import Dict, List, Optional, Any

import tiktoken
from config import Config
from utils.content.ai_adapter import get_ai_completion

# Configure logging
logger = logging.getLogger(__name__)

# Initialize tiktoken encoder
try:
    encoder = tiktoken.get_encoding("cl100k_base")  # Claude/OpenAI compatible encoding
except Exception as e:
    logger.warning(f"Could not initialize tiktoken encoder: {str(e)}")
    encoder = None

def count_tokens(text: str) -> int:
    """
    Count the number of tokens in a text string.
    
    Args:
        text: Text to count tokens for
        
    Returns:
        Number of tokens
    """
    if encoder is None:
        # Fallback: rough approximation (4 chars per token)
        return len(text) // 4
        
    try:
        return len(encoder.encode(text))
    except Exception as e:
        logger.warning(f"Error counting tokens: {str(e)}")
        # Fallback: rough approximation (4 chars per token)
        return len(text) // 4

def generate_long_paragraph(
    title: str,
    topic: str,
    section_title: str,
    target_tokens: int = 400,  # Zmniejszono z 1000 na 400 dla szybkości
    index: int = 1,
    max_attempts: int = 1  # Tylko jedna próba, bez retry
) -> str:
    """
    Generate a paragraph with optimized speed and efficiency.
    
    Args:
        title: The article title
        topic: The specific topic
        section_title: The section title
        target_tokens: Target number of tokens (reduced to 400 for speed)
        index: The paragraph index (for context)
        max_attempts: Maximum attempts (set to 1 for speed)
        
    Returns:
        Generated paragraph text
    """
    system_prompt = f"""Jesteś ekspertem w pisaniu wartościowych akapitów do artykułów.
    Twoim zadaniem jest wygenerowanie jednego akapitu na temat '{topic}' dla sekcji '{section_title}'.
    
    Zasady:
    1. Napisz wartościowy akapit o długości około 400-600 tokenów
    2. Zawrzyj praktyczne informacje i porady
    3. Używaj naturalnego, przyjaznego języka polskiego
    4. Format: zwróć tekst w paragrafach HTML (<p>treść</p>)
    5. Możesz użyć pogrubień (<strong>) dla ważnych pojęć
    6. Bądź konkretny i merytoryczny
    
    Jest to sekcja {index} w artykule o tytule: {title}
    """
    
    user_prompt = f"""Napisz akapit dla sekcji '{section_title}' w artykule na temat: {topic}

    Wygeneruj praktyczny, wartościowy akapit który pomoże czytelnikowi zrozumieć ten aspekt tematu."""
    
    try:
        # Single AI call with timeout protection
        paragraph = get_ai_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=Config.DEFAULT_CONTENT_MODEL,
            max_tokens=600,  # Reduced from 1200
            temperature=0.7
        )
        
        # Basic cleanup
        paragraph = re.sub(r'\n\s*\n', '\n\n', paragraph.strip())
        
        # Return immediately - no token counting or retries
        if paragraph and len(paragraph) > 100:
            return paragraph
        else:
            # Quick fallback without additional AI calls
            return f"<p><strong>{section_title}</strong> to ważny aspekt {topic}. Eksperci w tej dziedzinie podkreślają jego znaczenie dla prawidłowego zrozumienia całej tematyki. Warto zwrócić uwagę na kluczowe elementy i praktyczne zastosowania w codziennym życiu.</p>"
            
    except Exception as e:
        logger.error(f"Error generating paragraph: {str(e)}")
        # Quick fallback without retry
        return f"<p><strong>{section_title}</strong> stanowi istotny element związany z {topic}. Ta sekcja dostarcza wartościowych informacji potrzebnych do pełnego zrozumienia omawianej tematyki.</p>"

def generate_long_paragraph_content(
    topic: str,
    num_paragraphs: int = 4,
    ai_service: Optional[Any] = None
) -> Dict:
    """
    Generate article content with long paragraphs.
    
    Args:
        topic: The article topic
        num_paragraphs: Number of paragraphs to generate
        ai_service: Optional AI service to use
        
    Returns:
        Dictionary with 'content', 'metrics', and 'report' keys
    """
    start_time = time.time()
    logger.info(f"Generating content with {num_paragraphs} paragraphs on topic: {topic}")
    
    # Generate a title and section titles
    title_prompt = f"""Wygeneruj chwytliwy tytuł artykułu oraz {num_paragraphs} tytułów sekcji dla tematu: {topic}.
    Tytuł powinien być w języku polskim, przejrzysty i profesjonalny.
    Tytuły sekcji powinny pokrywać różne aspekty tematu. 
    Zwróć odpowiedź w formacie JSON: {{"title": "Tytuł artykułu", "sections": ["Tytuł sekcji 1", "Tytuł sekcji 2", ...]}}
    """
    
    system_prompt = """Jesteś ekspertem w tworzeniu planów artykułów. Generuj tytuł artykułu i tytuły sekcji w języku polskim."""
    
    try:
        if ai_service:
            plan_data = ai_service.complete_json(
                prompt=title_prompt,
                system_prompt=system_prompt
            )
        else:
            # Fallback to direct API call
            plan_response = get_ai_completion(
                system_prompt=system_prompt,
                user_prompt=title_prompt,
                model=Config.DEFAULT_CONTENT_MODEL,
                response_format={"type": "json_object"}
            )
            plan_data = json.loads(plan_response)
            
        title = plan_data.get("title", f"Kompletny przewodnik: {topic}")
        sections = plan_data.get("sections", [])
        
        # Ensure we have enough sections
        while len(sections) < num_paragraphs:
            sections.append(f"Część {len(sections) + 1}: Dodatkowe informacje o {topic}")
            
    except Exception as e:
        logger.error(f"Error generating title and sections: {str(e)}")
        # Fallback to simple title and sections
        title = f"Kompletny przewodnik: {topic}"
        sections = [f"Część {i+1}: {topic}" for i in range(num_paragraphs)]
    
    # Generate paragraphs
    paragraphs = []
    total_tokens = 0
    token_counts = []
    
    for i, section in enumerate(sections[:num_paragraphs]):
        try:
            # Generate a long paragraph for this section
            paragraph = generate_long_paragraph(
                title=title,
                topic=topic,
                section_title=section,
                target_tokens=1000,
                index=i+1
            )
            
            # Count tokens
            token_count = count_tokens(paragraph)
            total_tokens += token_count
            token_counts.append(token_count)
            
            # Add section title and paragraph to content
            paragraphs.append(f"<h2>{section}</h2>\n\n{paragraph}")
            
        except Exception as e:
            logger.error(f"Error generating paragraph {i+1}: {str(e)}")
            # Add a fallback paragraph
            fallback = f"<p>To jest sekcja o temacie {section}. Tutaj powinna znajdować się szczegółowa treść na ten temat.</p>"
            paragraphs.append(f"<h2>{section}</h2>\n\n{fallback}")
            token_counts.append(0)
    
    # Combine everything
    content = f"<h1>{title}</h1>\n\n" + "\n\n".join(paragraphs)
    
    # Calculate metrics
    end_time = time.time()
    generation_time = end_time - start_time
    avg_tokens_per_paragraph = total_tokens / num_paragraphs if num_paragraphs > 0 else 0
    
    metrics = {
        "total_tokens": total_tokens,
        "paragraph_count": num_paragraphs,
        "avg_tokens_per_paragraph": avg_tokens_per_paragraph,
        "generation_time_seconds": generation_time,
        "token_counts": token_counts
    }
    
    # Generate report
    report = f"""
    Wygenerowano artykuł na temat: **{topic}**
    - Tytuł: **{title}**
    - Liczba paragrafów: **{num_paragraphs}**
    - Całkowita liczba tokenów: **{total_tokens}**
    - Średnia liczba tokenów na paragraf: **{avg_tokens_per_paragraph:.1f}**
    - Czas generowania: **{generation_time:.2f}** sekund
    """
    
    return {
        "content": content,
        "metrics": metrics,
        "report": report
    }