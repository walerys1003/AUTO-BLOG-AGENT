"""
AI-Driven Content Strategy - Topic Generator

This module provides functionality for generating blog post topics for categories
using Claude 3.5 via OpenRouter.
"""

import os
import json
import logging
import requests
from datetime import datetime
from typing import List, Dict, Optional, Any

# Setup logging
logger = logging.getLogger(__name__)

def get_openrouter_api_key() -> str:
    """Get OpenRouter API key from environment"""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        logger.error("OpenRouter API key not found in environment variables")
        raise EnvironmentError("OpenRouter API key not found in environment variables")
    return api_key

def generate_topics_for_category(category_name: str, count: int = 40) -> List[str]:
    """
    Generate blog post topics for a specific category using Claude 3.5 via OpenRouter.
    
    Args:
        category_name: The category name to generate topics for
        count: Number of topics to generate (default: 40)
        
    Returns:
        List of generated topic strings
    """
    try:
        # Prepare prompt for topic generation
        prompt = f"""
        Wygeneruj {count} unikalnych, kreatywnych i wartościowych tematów artykułów blogowych dla kategorii: "{category_name}". 
        Tematy mają być interesujące, zróżnicowane, przydatne dla czytelników bloga. Każdy temat w jednym zdaniu.
        
        Odpowiedź sformatuj jako listę ponumerowaną od 1 do {count}, każdy temat w nowej linii.
        """
        
        # Call OpenRouter API with Claude 3.5
        response = openrouter_call(prompt, model="anthropic/claude-3-5-sonnet-20241022")
        
        # Parse the topics from the response
        topics = parse_topics(response)
        
        # Validate that we have the correct number of topics
        if len(topics) < count:
            logger.warning(f"Only generated {len(topics)} topics for category '{category_name}', expected {count}")
            
        return topics
        
    except Exception as e:
        logger.error(f"Error generating topics for category '{category_name}': {str(e)}")
        # Return a smaller list of basic topics as fallback
        return [f"Article about {category_name} - Part {i+1}" for i in range(min(5, count))]

def openrouter_call(prompt: str, model: str = "anthropic/claude-3-5-sonnet-20241022", max_tokens: int = 4000) -> str:
    """
    Call OpenRouter API with the given prompt
    
    Args:
        prompt: The prompt to send to the AI
        model: The model to use (default: claude-3-5-sonnet)
        max_tokens: Maximum tokens in the response
        
    Returns:
        The text response from the API
    """
    # the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
    api_key = get_openrouter_api_key()
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://blog.automationmaster.ai"  # Your site URL
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_tokens
    }
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload
        )
        
        # Check if the request was successful
        response.raise_for_status()
        
        # Parse the JSON response
        data = response.json()
        
        # Extract the AI's response
        if 'choices' in data and len(data['choices']) > 0:
            return data['choices'][0]['message']['content']
        else:
            logger.error(f"Unexpected response format from OpenRouter: {data}")
            return ""
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling OpenRouter API: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response content: {e.response.text}")
        raise
        
def parse_topics(response: str) -> List[str]:
    """
    Parse topics from the AI response
    
    Args:
        response: The text response from OpenRouter
        
    Returns:
        List of parsed topics
    """
    # Initialize list for topics
    topics = []
    
    # Split the response by lines
    lines = response.strip().split('\n')
    
    # Pattern recognition for numbered lists: "1. Topic", "1) Topic", "1 - Topic", etc.
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Try to detect if it's a numbered list item
        if (line[0].isdigit() or 
           (len(line) > 2 and line[:2].isdigit()) or
           (len(line) > 3 and line[:3].isdigit())):
            
            # Remove the numbering and potential formatting
            # This handles formats like "1. ", "1) ", "1 - ", "1: ", etc.
            parts = line.split('.', 1)
            if len(parts) > 1:
                topic = parts[1].strip()
                topics.append(topic)
                continue
                
            parts = line.split(')', 1)
            if len(parts) > 1:
                topic = parts[1].strip()
                topics.append(topic)
                continue
                
            parts = line.split(' - ', 1)
            if len(parts) > 1:
                topic = parts[1].strip()
                topics.append(topic)
                continue
                
            parts = line.split(':', 1)
            if len(parts) > 1:
                topic = parts[1].strip()
                topics.append(topic)
                continue
        
        # If we couldn't parse it as a numbered item but it's not empty,
        # it might be a plain topic without numbering
        if len(topics) == 0 or line.lower() not in [t.lower() for t in topics]:
            topics.append(line)
    
    return topics

def save_topics_to_json(topics_data: Dict[str, List[str]], filepath: str = "data/ai_topics.json") -> bool:
    """
    Save generated topics to a JSON file
    
    Args:
        topics_data: Dictionary with categories as keys and lists of topics as values
        filepath: Path to save the JSON file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Read existing data if file exists
        existing_data = {}
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        
        # Merge new data with existing data
        merged_data = {**existing_data, **topics_data}
        
        # Add timestamp for tracking
        merged_data['_last_updated'] = datetime.now().isoformat()
        
        # Write back to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(merged_data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Successfully saved topics to {filepath}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving topics to JSON: {str(e)}")
        return False

def load_topics_from_json(filepath: str = "data/ai_topics.json") -> Dict[str, List[str]]:
    """
    Load topics from a JSON file
    
    Args:
        filepath: Path to the JSON file
        
    Returns:
        Dictionary with categories as keys and lists of topics as values
    """
    try:
        if not os.path.exists(filepath):
            logger.info(f"Topics file not found at {filepath}, returning empty dict")
            return {}
            
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Remove metadata keys that start with underscore
        return {k: v for k, v in data.items() if not k.startswith('_')}
        
    except Exception as e:
        logger.error(f"Error loading topics from JSON: {str(e)}")
        return {}