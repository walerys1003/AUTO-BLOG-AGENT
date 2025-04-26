"""
AI Service Adapter

This module provides adapters for different AI services to be used with the content generator.
"""

import logging
import json
import os
import requests
from typing import Dict, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)

class AIServiceAdapter:
    """Base class for AI service adapters"""
    
    def generate(self, prompt: str) -> str:
        """Generate text based on a prompt"""
        raise NotImplementedError("Subclasses must implement this method")


class OpenRouterAdapter(AIServiceAdapter):
    """Adapter for OpenRouter API"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "anthropic/claude-3.5-sonnet-20241022"):
        """
        Initialize the OpenRouter adapter
        
        Args:
            api_key: OpenRouter API key (defaults to environment variable)
            model: Model to use for generation
        """
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OpenRouter API key is required")
        
        self.model = model
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
    
    def generate(self, prompt: str) -> str:
        """
        Generate text using OpenRouter API
        
        Args:
            prompt: The prompt to generate from
            
        Returns:
            Generated text
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 4000
        }
        
        logger.info(f"Sending request to OpenRouter API using model {self.model}")
        
        try:
            response = requests.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                logger.error(f"Unexpected API response format: {result}")
                raise ValueError("Unexpected API response format")
            
        except Exception as e:
            logger.error(f"Error generating text with OpenRouter: {str(e)}")
            raise


class AnthropicAdapter(AIServiceAdapter):
    """Adapter for Anthropic Claude API"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3.5-sonnet-20241022"):
        """
        Initialize the Anthropic adapter
        
        Args:
            api_key: Anthropic API key (defaults to environment variable)
            model: Model to use for generation
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key is required")
        
        self.model = model
        self.api_url = "https://api.anthropic.com/v1/messages"
    
    def generate(self, prompt: str) -> str:
        """
        Generate text using Anthropic API
        
        Args:
            prompt: The prompt to generate from
            
        Returns:
            Generated text
        """
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 4000
        }
        
        logger.info(f"Sending request to Anthropic API using model {self.model}")
        
        try:
            response = requests.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            
            if "content" in result and len(result["content"]) > 0:
                # Extract text content from Anthropic's response
                text_blocks = [
                    block["text"] for block in result["content"]
                    if block["type"] == "text"
                ]
                return "\n".join(text_blocks)
            else:
                logger.error(f"Unexpected API response format: {result}")
                raise ValueError("Unexpected API response format")
            
        except Exception as e:
            logger.error(f"Error generating text with Anthropic: {str(e)}")
            raise


class OpenAIAdapter(AIServiceAdapter):
    """Adapter for OpenAI API"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        """
        Initialize the OpenAI adapter
        
        Args:
            api_key: OpenAI API key (defaults to environment variable)
            model: Model to use for generation
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.model = model
        self.api_url = "https://api.openai.com/v1/chat/completions"
    
    def generate(self, prompt: str) -> str:
        """
        Generate text using OpenAI API
        
        Args:
            prompt: The prompt to generate from
            
        Returns:
            Generated text
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 4000
        }
        
        logger.info(f"Sending request to OpenAI API using model {self.model}")
        
        try:
            response = requests.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                logger.error(f"Unexpected API response format: {result}")
                raise ValueError("Unexpected API response format")
            
        except Exception as e:
            logger.error(f"Error generating text with OpenAI: {str(e)}")
            raise


def get_default_ai_service() -> AIServiceAdapter:
    """
    Get the default AI service based on available API keys
    
    Returns:
        An instance of AIServiceAdapter
    """
    # Try OpenRouter first (preferred service)
    if os.environ.get("OPENROUTER_API_KEY"):
        try:
            model = os.environ.get("DEFAULT_CONTENT_MODEL", "anthropic/claude-3.5-sonnet")
            return OpenRouterAdapter(model=model)
        except Exception as e:
            logger.warning(f"Failed to initialize OpenRouter adapter: {str(e)}")
    
    # Try Anthropic next
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            model = "claude-3.5-sonnet-20241022"  # Use latest model
            return AnthropicAdapter(model=model)
        except Exception as e:
            logger.warning(f"Failed to initialize Anthropic adapter: {str(e)}")
    
    # Fall back to OpenAI
    if os.environ.get("OPENAI_API_KEY"):
        try:
            model = "gpt-4o"  # Use latest model
            return OpenAIAdapter(model=model)
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI adapter: {str(e)}")
    
    # If all else fails, raise an error
    raise ValueError("No suitable AI service found. Please provide at least one API key.")