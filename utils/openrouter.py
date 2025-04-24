import logging
import json
import re
import requests
from typing import Dict, Any, Optional, Union, List
import traceback
from config import Config

# Setup logging
logger = logging.getLogger(__name__)

class OpenRouterClient:
    """Client for interacting with OpenRouter API"""
    
    BASE_URL = "https://openrouter.ai/api/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the OpenRouter client
        
        Args:
            api_key: OpenRouter API key (defaults to Config.OPENROUTER_API_KEY)
        """
        self.api_key = api_key or Config.OPENROUTER_API_KEY
        if not self.api_key:
            logger.error("OpenRouter API key not found")
            raise ValueError("OpenRouter API key is required")
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Get list of available models from OpenRouter
        
        Returns:
            List of model data with name, pricing, context size, etc.
        """
        try:
            url = f"{self.BASE_URL}/models"
            headers = self._get_headers()
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("data", [])
            else:
                logger.error(f"Failed to get models: {response.status_code}, {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting models: {str(e)}")
            logger.error(traceback.format_exc())
            return []
    
    def generate_completion(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None
    ) -> Union[str, Dict[str, Any], None]:
        """
        Generate a completion using OpenRouter
        
        Args:
            prompt: The prompt to send
            model: Model identifier (e.g., "anthropic/claude-3-opus-20240229")
            temperature: Creativity level (0.0-1.0)
            max_tokens: Maximum tokens to generate
            response_format: Format specification for response
            system_prompt: Optional system prompt for context
            
        Returns:
            Generated text or parsed JSON response
        """
        try:
            url = f"{self.BASE_URL}/chat/completions"
            headers = self._get_headers()
            
            messages = []
            
            # Add system prompt if provided
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            # Add user prompt
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature
            }
            
            # Add max tokens if specified
            if max_tokens:
                payload["max_tokens"] = max_tokens
            
            # Add response format if specified
            if response_format:
                payload["response_format"] = response_format
            
            logger.debug(f"OpenRouter request: {json.dumps(payload)}")
            
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                
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
                logger.error(f"OpenRouter API error: {response.status_code}, {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error with OpenRouter completion: {str(e)}")
            logger.error(traceback.format_exc())
            return None
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get headers for OpenRouter API requests
        
        Returns:
            Dictionary of HTTP headers
        """
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://blogautomationagent.com"  # Replace with your domain
        }

# Singleton instance for easy access
openrouter = OpenRouterClient()

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
    try:
        return openrouter.generate_completion(
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