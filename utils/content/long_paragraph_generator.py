"""
Long Paragraph Generator

This module provides functionality for generating and validating longer paragraphs
in content generation. It ensures each paragraph meets the minimum token requirements
and automatically extends paragraphs that are too short.
"""

import logging
import tiktoken
from typing import List, Dict, Any, Tuple, Optional
import os
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

# Constants for paragraph generation
MIN_PARAGRAPH_TOKENS = 1000  # Minimum tokens per paragraph
MIN_INTRO_TOKENS = 500       # Minimum tokens for introduction
MIN_CONCLUSION_TOKENS = 500  # Minimum tokens for conclusion
TARGET_PARAGRAPHS = 4        # Default number of paragraphs

# Initialize tokenizer
def get_tokenizer(model_name="gpt-4"):
    """Get the appropriate tokenizer for the model."""
    try:
        return tiktoken.encoding_for_model(model_name)
    except KeyError:
        # Fallback to cl100k_base, which is used by GPT-4, GPT-3.5-Turbo, etc.
        return tiktoken.get_encoding("cl100k_base")

def count_tokens(text: str, model_name="gpt-4") -> int:
    """Count the number of tokens in a text string."""
    enc = get_tokenizer(model_name)
    return len(enc.encode(text))

def create_article_generation_prompt(topic: str, num_paragraphs: int = TARGET_PARAGRAPHS) -> str:
    """
    Create a prompt for generating an article with long paragraphs.
    
    Args:
        topic: The topic of the article
        num_paragraphs: Number of paragraphs to generate (default: 4)
        
    Returns:
        A formatted prompt string
    """
    return f"""
Napisz artykuł na temat: {topic}, który będzie zawierał dokładnie {num_paragraphs} bardzo rozbudowane akapity.

Każdy akapit ma mieć długość minimum {MIN_PARAGRAPH_TOKENS} tokenów (około 750 słów). 
- Akapity muszą być szczegółowe, analityczne, pełne danych, przykładów i przemyśleń.
- Każdy kolejny akapit rozwija poprzedni – zachowaj logiczny ciąg przyczynowo-skutkowy.
- Nie używaj krótkich zdań ani ogólników.
- Utrzymaj wysoki poziom merytoryczny i stylistyczny.

Struktura artykułu:
1. Wprowadzenie (min. {MIN_INTRO_TOKENS} tokenów) – kontekst, znaczenie tematu.
{chr(10).join([f"{i+2}. Akapit {i+1} – " + (
    "pierwszy aspekt tematu, szczegółowy opis." if i==0 else
    "logiczne rozwinięcie, analiza kolejnego aspektu." if i==1 else
    "kontynuacja, nowe dane, perspektywy." if i==2 else
    "rozszerzenie tematu, zamknięcie analizy."
) for i in range(num_paragraphs)])}
{num_paragraphs+2}. Podsumowanie (min. {MIN_CONCLUSION_TOKENS} tokenów) – wnioski, przemyślenia, konkluzje.

Jeśli którykolwiek akapit ma mniej niż {MIN_PARAGRAPH_TOKENS} tokenów, rozwiń go automatycznie, dodając nowe informacje, przykłady, dane, tak by spełniał wymóg długości.
"""

def create_paragraph_extension_prompt(paragraph: str, topic: str) -> str:
    """
    Create a prompt to extend a paragraph that is too short.
    
    Args:
        paragraph: The paragraph that needs extension
        topic: The topic of the article
        
    Returns:
        A formatted prompt string
    """
    current_tokens = count_tokens(paragraph)
    additional_tokens_needed = max(0, MIN_PARAGRAPH_TOKENS - current_tokens)
    
    return f"""
Poniższy akapit na temat "{topic}" jest za krótki (ma tylko {current_tokens} tokenów, a potrzebujemy minimum {MIN_PARAGRAPH_TOKENS}).

AKAPIT DO ROZSZERZENIA:
{paragraph}

Proszę rozszerzyć powyższy akapit, dodając co najmniej {additional_tokens_needed} tokenów nowej treści. Dodaj więcej:
- Szczegółowych informacji i danych
- Konkretnych przykładów
- Perspektyw i argumentów
- Wyjaśnień i kontekstu

Zachowaj styl, ton i logiczny ciąg myślowy. Tekst musi być spójny i płynnie przechodzić z istniejącej treści do nowej. Nie powtarzaj już przedstawionych informacji, tylko dodawaj nowe, wartościowe treści.
"""

def validate_paragraph_length(paragraph: str, 
                             min_tokens: int = MIN_PARAGRAPH_TOKENS, 
                             model_name: str = "gpt-4") -> Tuple[bool, int]:
    """
    Validate if a paragraph meets the minimum token length.
    
    Args:
        paragraph: The paragraph text to validate
        min_tokens: Minimum required tokens
        model_name: The model name for tokenization
        
    Returns:
        Tuple of (meets_requirement, actual_token_count)
    """
    token_count = count_tokens(paragraph, model_name)
    return (token_count >= min_tokens, token_count)

def split_article_into_sections(article_text: str) -> Dict[str, Any]:
    """
    Split an article into introduction, body paragraphs, and conclusion.
    
    This function uses heuristics to identify sections in the text.
    
    Args:
        article_text: The full article text
        
    Returns:
        Dictionary with 'intro', 'paragraphs' (list), and 'conclusion' keys
    """
    # Simple splitting based on double newlines
    chunks = [chunk.strip() for chunk in article_text.split("\n\n") if chunk.strip()]
    
    # Filter out section headers and short lines
    content_chunks = [chunk for chunk in chunks if len(chunk) > 100 and not chunk.startswith('#')]
    
    if len(content_chunks) < 3:
        # If we can't identify enough chunks, return the whole text as one paragraph
        return {
            'intro': content_chunks[0] if content_chunks else "",
            'paragraphs': content_chunks[1:-1] if len(content_chunks) > 2 else [],
            'conclusion': content_chunks[-1] if len(content_chunks) > 1 else ""
        }
    
    # Assume first chunk is intro, last is conclusion, rest are body paragraphs
    return {
        'intro': content_chunks[0],
        'paragraphs': content_chunks[1:-1],
        'conclusion': content_chunks[-1]
    }

def generate_article_metrics(article_text: str, model_name: str = "gpt-4") -> Dict[str, Any]:
    """
    Generate metrics for an article, including token counts for each section.
    
    Args:
        article_text: The full article text
        model_name: The model name for tokenization
        
    Returns:
        Dictionary with article metrics
    """
    sections = split_article_into_sections(article_text)
    
    # Count tokens in each section
    intro_tokens = count_tokens(sections['intro'], model_name)
    conclusion_tokens = count_tokens(sections['conclusion'], model_name)
    
    paragraph_metrics = []
    for i, para in enumerate(sections['paragraphs']):
        tokens = count_tokens(para, model_name)
        paragraph_metrics.append({
            'paragraph_number': i + 1,
            'tokens': tokens,
            'meets_requirement': tokens >= MIN_PARAGRAPH_TOKENS
        })
    
    total_tokens = count_tokens(article_text, model_name)
    
    return {
        'total_tokens': total_tokens,
        'intro': {
            'tokens': intro_tokens,
            'meets_requirement': intro_tokens >= MIN_INTRO_TOKENS
        },
        'conclusion': {
            'tokens': conclusion_tokens,
            'meets_requirement': conclusion_tokens >= MIN_CONCLUSION_TOKENS
        },
        'paragraphs': paragraph_metrics,
        'all_requirements_met': (
            intro_tokens >= MIN_INTRO_TOKENS and
            conclusion_tokens >= MIN_CONCLUSION_TOKENS and
            all(p['meets_requirement'] for p in paragraph_metrics)
        )
    }

def format_metrics_report(metrics: Dict[str, Any]) -> str:
    """
    Format article metrics into a human-readable report.
    
    Args:
        metrics: The metrics dictionary from generate_article_metrics
        
    Returns:
        Formatted report as a string
    """
    report = [
        "RAPORT ANALIZY DŁUGOŚCI ARTYKUŁU",
        "=" * 40,
        f"Łączna liczba tokenów: {metrics['total_tokens']}",
        "",
        f"WSTĘP: {metrics['intro']['tokens']} tokenów " +
        ("✅" if metrics['intro']['meets_requirement'] else "❌"),
        ""
    ]
    
    for p in metrics['paragraphs']:
        report.append(
            f"AKAPIT {p['paragraph_number']}: {p['tokens']} tokenów " +
            ("✅" if p['meets_requirement'] else "❌")
        )
    
    report.extend([
        "",
        f"ZAKOŃCZENIE: {metrics['conclusion']['tokens']} tokenów " +
        ("✅" if metrics['conclusion']['meets_requirement'] else "❌"),
        "",
        "PODSUMOWANIE: " + 
        ("✅ Wszystkie sekcje spełniają wymagania długości" 
         if metrics['all_requirements_met'] 
         else "❌ Niektóre sekcje nie spełniają wymagań długości")
    ])
    
    return "\n".join(report)

# Main function to generate content with long paragraphs
def generate_long_paragraph_content(topic: str, 
                                   num_paragraphs: int = TARGET_PARAGRAPHS,
                                   ai_service=None) -> Dict[str, Any]:
    """
    Generate article content with long paragraphs.
    
    Args:
        topic: The article topic
        num_paragraphs: Number of paragraphs to generate
        ai_service: The AI service to use for generation (needs a generate method)
        
    Returns:
        Dictionary with the generated content and metrics
    """
    if ai_service is None:
        raise ValueError("AI service must be provided")
    
    # Create the generation prompt
    prompt = create_article_generation_prompt(topic, num_paragraphs)
    
    # Generate the initial content
    logger.info(f"Generating article with {num_paragraphs} long paragraphs on topic: {topic}")
    article_text = ai_service.generate(prompt)
    
    # Analyze the generated content
    metrics = generate_article_metrics(article_text)
    
    # If all requirements are met, return the content
    if metrics['all_requirements_met']:
        logger.info(f"Article meets all length requirements: {metrics['total_tokens']} tokens")
        return {
            'content': article_text,
            'metrics': metrics,
            'report': format_metrics_report(metrics)
        }
    
    # Otherwise, fix any sections that are too short
    logger.info("Some sections do not meet length requirements. Extending...")
    sections = split_article_into_sections(article_text)
    
    # Fix introduction if needed
    if not metrics['intro']['meets_requirement']:
        extension_prompt = create_paragraph_extension_prompt(
            sections['intro'], 
            f"Wprowadzenie do artykułu o {topic}"
        )
        sections['intro'] = ai_service.generate(extension_prompt)
    
    # Fix each paragraph if needed
    for i, para_metric in enumerate(metrics['paragraphs']):
        if not para_metric['meets_requirement']:
            extension_prompt = create_paragraph_extension_prompt(
                sections['paragraphs'][i], 
                f"Akapit {i+1} artykułu o {topic}"
            )
            sections['paragraphs'][i] = ai_service.generate(extension_prompt)
    
    # Fix conclusion if needed
    if not metrics['conclusion']['meets_requirement']:
        extension_prompt = create_paragraph_extension_prompt(
            sections['conclusion'], 
            f"Podsumowanie artykułu o {topic}"
        )
        sections['conclusion'] = ai_service.generate(extension_prompt)
    
    # Reassemble the article
    improved_article = (
        sections['intro'] + "\n\n" + 
        "\n\n".join(sections['paragraphs']) + "\n\n" + 
        sections['conclusion']
    )
    
    # Re-analyze the improved content
    final_metrics = generate_article_metrics(improved_article)
    
    logger.info(f"Article extended to {final_metrics['total_tokens']} tokens")
    return {
        'content': improved_article,
        'metrics': final_metrics,
        'report': format_metrics_report(final_metrics)
    }