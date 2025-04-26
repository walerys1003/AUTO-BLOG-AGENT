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
    target_tokens: int = 1000,
    index: int = 1,
    max_attempts: int = 3
) -> str:
    """
    Generate a long paragraph with a target token count.
    
    Args:
        title: The article title
        topic: The specific topic
        section_title: The section title
        target_tokens: Target number of tokens (default: 1000)
        index: The paragraph index (for context)
        max_attempts: Maximum attempts to reach target length
        
    Returns:
        Generated paragraph text
    """
    system_prompt = f"""Jesteś ekspertem w pisaniu długich, szczegółowych akapitów do artykułów.
    Twoim zadaniem jest wygenerowanie jednego długiego akapitu na temat '{topic}' dla sekcji '{section_title}'.
    
    Zasady:
    1. Akapit powinien mieć około {target_tokens} tokenów (około {target_tokens*4} znaków)
    2. Akapit powinien zawierać szczegółowe, wartościowe informacje
    3. Unikaj powtarzania tych samych myśli i zwrotów
    4. Używaj różnorodnego, ale naturalnego języka
    5. Akapit powinien być spójny i logiczny
    6. Pisz w języku polskim, przyjaznym tonem eksperta
    7. Format: zwróć tekst w paragrafach HTML (<p>treść</p>)
    8. Możesz użyć pogrubień (<strong>) i kursywy (<em>) dla ważnych pojęć
    
    Jest to akapit numer {index} w artykule, więc zadbaj o spójność z resztą treści.
    """
    
    user_prompt = f"""Tytuł artykułu: {title}
    Temat: {topic}
    Tytuł sekcji: {section_title}
    
    Wygeneruj szczegółowy akapit dla tej sekcji artykułu.
    """
    
    attempts = 0
    while attempts < max_attempts:
        attempts += 1
        
        try:
            # Generate paragraph
            paragraph = get_ai_completion(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=Config.DEFAULT_CONTENT_MODEL,
                max_tokens=target_tokens + 200,  # Allow some extra tokens
                temperature=0.7
            )
            
            # Clean up paragraph (remove unnecessary line breaks, etc.)
            paragraph = re.sub(r'\n\s*\n', '\n\n', paragraph)
            
            # Check token count
            token_count = count_tokens(paragraph)
            
            if token_count >= target_tokens * 0.8:  # At least 80% of target
                # Successfully generated a paragraph of appropriate length
                return paragraph
                
            logger.warning(f"Generated paragraph too short: {token_count} tokens (target: {target_tokens})")
            
            if attempts < max_attempts:
                # Update prompt to request longer paragraph
                system_prompt = f"""Jesteś ekspertem w pisaniu bardzo długich, szczegółowych akapitów do artykułów.
                Poprzednia próba była zbyt krótka. Potrzebuję znacznie dłuższego i bardziej szczegółowego akapitu.
                
                Twoim zadaniem jest wygenerowanie jednego bardzo długiego akapitu na temat '{topic}' dla sekcji '{section_title}'.
                
                Zasady:
                1. Akapit MUSI mieć przynajmniej {target_tokens} tokenów (około {target_tokens*4} znaków)
                2. Akapit powinien zawierać wyczerpujące, wartościowe informacje
                3. Podaj wiele przykładów, szczegółów i wyjaśnień
                4. Unikaj powtarzania tych samych myśli i zwrotów
                5. Używaj różnorodnego, ale naturalnego języka
                6. Pisz w języku polskim, przyjaznym tonem eksperta
                7. Format: zwróć tekst w paragrafach HTML (<p>treść</p>)
                8. Możesz użyć pogrubień (<strong>) i kursywy (<em>) dla ważnych pojęć
                
                Jest to akapit numer {index} w artykule, więc zadbaj o spójność z resztą treści.
                """
                
                # Wait a bit before retrying
                time.sleep(1)
                continue
                
        except Exception as e:
            logger.error(f"Error generating long paragraph: {str(e)}")
            # Return simple fallback paragraph in case of failure
            return f"<p>W kontekście {topic}, {section_title} stanowi istotny element, który warto dokładnie przeanalizować. Eksperci w tej dziedzinie wielokrotnie podkreślają jego znaczenie dla całościowego zrozumienia omawianej tematyki.</p>"
    
    # If all attempts failed, return the last generated paragraph (even if too short)
    return paragraph

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