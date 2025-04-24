import logging
import json
import re
import requests
import os
from typing import Dict, Any, Optional, List, Union
from config import Config
import traceback

# Setup logging
logger = logging.getLogger(__name__)

def get_ai_response(
    prompt: str, 
    model: str = None, 
    temperature: float = 0.7,
    system_prompt: str = None,
    response_format: Optional[Dict[str, str]] = None
) -> Any:
    """
    Get a response from AI model via OpenRouter API
    
    Args:
        prompt: The prompt to send to the AI
        model: Model identifier (e.g., "anthropic/claude-3-sonnet")
        temperature: Temperature setting (0.0 to 1.0)
        system_prompt: Optional system prompt
        response_format: Optional response format specification
        
    Returns:
        Response content (parsed JSON or text)
    """
    try:
        # Get API key
        api_key = Config.OPENROUTER_API_KEY
        
        if not api_key:
            logger.error("OpenRouter API key not found")
            return None
        
        # Use default model if none specified
        if not model:
            model = Config.DEFAULT_CONTENT_MODEL
        
        # Prepare the request data
        request_data = {
            "model": model,
            "messages": []
        }
        
        # Add system prompt if provided
        if system_prompt:
            request_data["messages"].append({
                "role": "system",
                "content": system_prompt
            })
        
        # Add user prompt
        request_data["messages"].append({
            "role": "user",
            "content": prompt
        })
        
        # Add temperature
        request_data["temperature"] = temperature
        
        # Add response format if provided
        if response_format:
            request_data["response_format"] = response_format
        
        # Make the API request
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=request_data
        )
        
        # Check if request was successful
        if response.status_code != 200:
            logger.error(f"OpenRouter API request failed: {response.status_code}, {response.text}")
            return None
        
        # Parse the response
        response_data = response.json()
        
        # Extract the content
        if "choices" in response_data and len(response_data["choices"]) > 0:
            message = response_data["choices"][0]["message"]
            content = message.get("content", "")
            
            # Try to parse as JSON if response_format was requested as JSON
            if response_format and response_format.get("type") == "json_object" and content:
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse response as JSON: {content}")
                    return content
            
            return content
        else:
            logger.warning("No choices in OpenRouter response")
            return None
    
    except Exception as e:
        logger.error(f"Error getting AI response: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def clean_html(html_content: str) -> str:
    """
    Clean and sanitize HTML content
    
    Args:
        html_content: Raw HTML content
        
    Returns:
        Cleaned HTML content
    """
    try:
        # Remove potentially harmful tags and attributes
        # This is a very basic implementation - a real solution would use a proper HTML sanitizer
        
        # Remove script tags and their content
        html_content = re.sub(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', '', html_content)
        
        # Remove iframe tags
        html_content = re.sub(r'<iframe\b[^<]*(?:(?!<\/iframe>)<[^<]*)*<\/iframe>', '', html_content)
        
        # Remove event handlers
        html_content = re.sub(r'\son\w+="[^"]*"', '', html_content)
        
        # Remove style attributes
        html_content = re.sub(r'\sstyle="[^"]*"', '', html_content)
        
        # Fix common issues
        
        # Fix unclosed paragraph tags
        html_content = re.sub(r'<p>([^<]*?)(?=<p>)', r'<p>\1</p>', html_content)
        
        # Fix duplicate closing tags
        html_content = re.sub(r'<\/(\w+)><\/\1>', r'</\1>', html_content)
        
        # Add breaks for plain newlines not in tags
        html_content = re.sub(r'(?<!\>)\n(?!\<)', '<br />', html_content)
        
        return html_content
        
    except Exception as e:
        logger.error(f"Error cleaning HTML: {str(e)}")
        logger.error(traceback.format_exc())
        return html_content  # Return original if cleaning fails