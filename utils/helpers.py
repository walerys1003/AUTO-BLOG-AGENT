import logging
import json
import re
import requests
from typing import Dict, Any, Optional, Union
import traceback
from config import Config
from bs4 import BeautifulSoup

# Setup logging
logger = logging.getLogger(__name__)

def get_ai_response(
    prompt: str, 
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    response_format: Optional[Dict[str, Any]] = None,
    system_prompt: Optional[str] = None
) -> Union[str, Dict[str, Any], None]:
    """
    Get AI-generated response using OpenRouter or fallback providers
    
    Args:
        prompt: The prompt to send to the AI
        model: The model to use (defaults to Config.DEFAULT_CONTENT_MODEL)
        temperature: Creativity parameter (0.0-1.0)
        max_tokens: Maximum tokens to generate
        response_format: Format specification for JSON responses
        system_prompt: Optional system prompt for context
        
    Returns:
        Generated text or parsed JSON (if response_format is specified)
    """
    try:
        # Use specified model or default
        model = model or Config.DEFAULT_CONTENT_MODEL
        
        # Try OpenRouter first
        if Config.OPENROUTER_API_KEY:
            response = get_openrouter_response(
                prompt=prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format,
                system_prompt=system_prompt
            )
            
            if response:
                return response
            
            logger.warning("OpenRouter request failed, trying fallbacks")
        
        # Fallback to direct provider
        if "anthropic" in model.lower() and Config.ANTHROPIC_API_KEY:
            # For Anthropic, if system prompt was provided, prepend to user prompt
            if system_prompt:
                enhanced_prompt = f"{system_prompt}\n\n{prompt}"
            else:
                enhanced_prompt = prompt
                
            response = get_anthropic_response(
                prompt=enhanced_prompt, 
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format
            )
            if response:
                return response
        
        elif ("openai" in model.lower() or "gpt" in model.lower()) and Config.OPENAI_API_KEY:
            # For OpenAI, modify the call to include system prompt
            # Note: This would require updating get_openai_response to handle system_prompt
            # For simplicity, we're using a workaround here
            if system_prompt:
                enhanced_prompt = f"System instruction: {system_prompt}\n\nUser request: {prompt}"
            else:
                enhanced_prompt = prompt
                
            response = get_openai_response(
                prompt=enhanced_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format
            )
            if response:
                return response
        
        logger.error("All AI providers failed")
        return None
            
    except Exception as e:
        logger.error(f"Error getting AI response: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def get_openrouter_response(
    prompt: str, 
    model: str,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    response_format: Optional[Dict[str, Any]] = None,
    system_prompt: Optional[str] = None
) -> Union[str, Dict[str, Any], None]:
    """
    Get AI-generated response from OpenRouter
    
    Args:
        prompt: The prompt to send to the AI
        model: The model to use
        temperature: Creativity parameter (0.0-1.0)
        max_tokens: Maximum tokens to generate
        response_format: Format specification for JSON responses
        system_prompt: Optional system prompt for context
        
    Returns:
        Generated text or parsed JSON (if response_format is specified)
    """
    # Import here to avoid circular imports
    from utils.openrouter import get_openrouter_response as openrouter_response
    
    try:
        return openrouter_response(
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format,
            system_prompt=system_prompt
        )
            
    except Exception as e:
        logger.error(f"Error with OpenRouter: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def get_anthropic_response(
    prompt: str,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    response_format: Optional[Dict[str, Any]] = None
) -> Union[str, Dict[str, Any], None]:
    """
    Get AI-generated response from Anthropic directly
    
    Args:
        prompt: The prompt to send to the AI
        temperature: Creativity parameter (0.0-1.0)
        max_tokens: Maximum tokens to generate
        response_format: Format specification for JSON responses
        
    Returns:
        Generated text or parsed JSON (if response_format is specified)
    """
    try:
        api_key = Config.ANTHROPIC_API_KEY
        if not api_key:
            logger.error("Anthropic API key not found")
            return None
        
        # Anthropic endpoint
        url = "https://api.anthropic.com/v1/messages"
        
        # Prepare headers
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        # Prepare payload
        payload = {
            "model": "claude-3-sonnet-20240229",  # Use latest model
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature
        }
        
        # Add max tokens if specified
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        # Add response format if specified
        if response_format and response_format.get("type") == "json_object":
            # For Claude, we adjust the prompt to request JSON
            payload["messages"][0]["content"] += "\n\nPlease format your response as a valid JSON object."
        
        # Make API request
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            content = data.get("content", [{}])[0].get("text", "")
            
            # If content is JSON and response_format was specified, parse it
            if response_format and content:
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    # If it fails to parse as JSON but we expected JSON, try to extract JSON
                    json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
                    if json_match:
                        try:
                            return json.loads(json_match.group(1))
                        except:
                            pass
                    
                    logger.warning("Failed to parse JSON response")
                    return content
            
            return content
        else:
            logger.error(f"Anthropic API error: {response.status_code}, {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error with Anthropic: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def get_openai_response(
    prompt: str,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    response_format: Optional[Dict[str, Any]] = None
) -> Union[str, Dict[str, Any], None]:
    """
    Get AI-generated response from OpenAI directly
    
    Args:
        prompt: The prompt to send to the AI
        temperature: Creativity parameter (0.0-1.0)
        max_tokens: Maximum tokens to generate
        response_format: Format specification for JSON responses
        
    Returns:
        Generated text or parsed JSON (if response_format is specified)
    """
    try:
        api_key = Config.OPENAI_API_KEY
        if not api_key:
            logger.error("OpenAI API key not found")
            return None
        
        # OpenAI endpoint
        url = "https://api.openai.com/v1/chat/completions"
        
        # Prepare headers
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Prepare payload
        payload = {
            "model": "gpt-4-turbo",  # Use latest model
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature
        }
        
        # Add max tokens if specified
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        # Add response format if specified
        if response_format:
            payload["response_format"] = response_format
        
        # Make API request
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # If content is JSON and response_format was specified, parse it
            if response_format and content:
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    logger.warning("Failed to parse JSON response")
                    return content
            
            return content
        else:
            logger.error(f"OpenAI API error: {response.status_code}, {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error with OpenAI: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def clean_html(html_content: str) -> str:
    """
    Clean and sanitize HTML content
    
    Args:
        html_content: HTML content to clean
        
    Returns:
        Cleaned HTML content
    """
    try:
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Fix empty paragraphs
        for p in soup.find_all("p"):
            if not p.text.strip():
                p.decompose()
        
        # Ensure all links open in new tab and have rel attributes
        for a in soup.find_all("a"):
            a["target"] = "_blank"
            a["rel"] = "noopener noreferrer"
        
        # Return clean HTML
        return str(soup)
        
    except Exception as e:
        logger.error(f"Error cleaning HTML: {str(e)}")
        
        # Return original content if cleaning fails
        return html_content
