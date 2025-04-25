import os
import json
import time
import logging
import requests
from typing import Dict, List, Any, Optional, Union
from config import Config

# Setup logging
logger = logging.getLogger(__name__)

class OpenRouterClient:
    """Client for interacting with OpenRouter API"""
    
    def __init__(self):
        """Initialize the OpenRouter client"""
        self.api_key = Config.OPENROUTER_API_KEY
        self.api_base = "https://openrouter.ai/api/v1"
        self.fallback_model = "anthropic/claude-3.5-sonnet"
        self.default_topic_model = Config.DEFAULT_TOPIC_MODEL or "anthropic/claude-3.5-haiku"
        self.default_content_model = Config.DEFAULT_CONTENT_MODEL or "anthropic/claude-3.5-sonnet"
        self.default_social_model = Config.DEFAULT_SOCIAL_MODEL or "anthropic/claude-3.5-haiku"

    def _get_headers(self) -> Dict[str, str]:
        """Get the headers for API requests"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://blog-automation-agent.replit.app",  # Replace with your actual domain
            "X-Title": "BlogAutomationAgent"
        }
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models from OpenRouter"""
        if not self.api_key:
            logger.warning("OpenRouter API key not set")
            return []
        
        try:
            response = requests.get(
                f"{self.api_base}/models",
                headers=self._get_headers()
            )
            response.raise_for_status()
            
            data = response.json()
            return data.get("data", [])
        except Exception as e:
            logger.error(f"Error fetching models from OpenRouter: {str(e)}")
            return []
    
    def generate_completion(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,  # Zwiększony limit tokenów dla dłuższych akapitów
        response_format: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Generate a completion from the specified model
        
        Args:
            prompt: The user prompt to send
            model: Model ID (e.g., "anthropic/claude-3.5-sonnet")
            system_prompt: Optional system prompt
            temperature: Temperature setting (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            response_format: Optional response format specification
            
        Returns:
            Response object with content in choices[0].message.content
        """
        if not self.api_key:
            logger.warning("OpenRouter API key not set")
            return {
                "choices": [
                    {
                        "message": {
                            "content": "API key not configured. Please set OPENROUTER_API_KEY in environment variables."
                        }
                    }
                ]
            }
        
        # Use default model if not specified
        if not model:
            model = self.fallback_model
            logger.info(f"Using fallback model: {model}")
        
        # Prepare request data
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "timeout": 90  # Zwiększony timeout dla dłuższych żądań
        }
        
        # Add system prompt if provided
        if system_prompt:
            data["messages"].insert(0, {"role": "system", "content": system_prompt})
        
        # Add response format if provided
        if response_format:
            data["response_format"] = response_format
        
        # Make the API request
        response = None
        retry_count = 0
        max_retries = 3
        backoff_factor = 2
        
        while retry_count < max_retries:
            try:
                logger.info(f"Sending request to OpenRouter with model: {model} (Attempt {retry_count + 1}/{max_retries})")
                logger.debug(f"Request data: {json.dumps(data)}")
                response = requests.post(
                    f"{self.api_base}/chat/completions",
                    headers=self._get_headers(),
                    json=data,
                    timeout=60  # Zmniejszony timeout do 60 sekund dla szybszego wykrywania błędów
                )
                response.raise_for_status()
                # If successful, break out of retry loop
                break
            except requests.exceptions.Timeout:
                retry_count += 1
                logger.warning(f"Timeout error on attempt {retry_count}/{max_retries}. Retrying with exponential backoff.")
                if retry_count < max_retries:
                    # Exponential backoff
                    time.sleep(backoff_factor ** retry_count)
                else:
                    logger.error(f"Timeout error after {max_retries} attempts. Giving up.")
                    return {
                        "choices": [
                            {
                                "message": {
                                    "content": "Error: Request to AI service timed out. Please try again."
                                }
                            }
                        ]
                    }
            except requests.exceptions.ConnectionError:
                retry_count += 1
                logger.warning(f"Connection error on attempt {retry_count}/{max_retries}. Retrying with exponential backoff.")
                if retry_count < max_retries:
                    time.sleep(backoff_factor ** retry_count)
                else:
                    logger.error(f"Connection error after {max_retries} attempts. Giving up.")
                    return {
                        "choices": [
                            {
                                "message": {
                                    "content": "Error: Connection to AI service failed. Please check your network and try again."
                                }
                            }
                        ]
                    }
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                return {
                    "choices": [
                        {
                            "message": {
                                "content": f"Error: Unexpected problem with AI service: {str(e)}"
                            }
                        }
                    ]
                }
                
        # Process successful response
        if response and response.status_code == 200:
            try:
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                logger.info(f"Successfully received response from OpenRouter (length: {len(content)} chars)")
                return result
            except Exception as e:
                logger.error(f"Error processing OpenRouter response: {str(e)}")
                return {
                    "choices": [
                        {
                            "message": {
                                "content": f"Error processing API response: {str(e)}"
                            }
                        }
                    ]
                }
                
        # If we reached here with no successful response after retries
        logger.error("Failed to get response from OpenRouter after maximum retries")
        
        # Try to extract error message from response
        error_message = "Unknown error occurred"
        try:
            if response and hasattr(response, 'json'):
                error_data = response.json()
                error_message = error_data.get("error", {}).get("message", "API error")
        except Exception as ex:
            error_message = f"Could not process response: {str(ex)}"
        
        return {
            "choices": [
                {
                    "message": {
                        "content": f"Error: {error_message}"
                    }
                }
            ]
        }
    
    def generate_json_response(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7
    ) -> Any:
        """
        Generate a JSON response from the model
        
        Args:
            prompt: The user prompt to send
            model: Model ID (e.g., "anthropic/claude-3-sonnet")
            system_prompt: Optional system prompt
            temperature: Temperature setting (0.0 to 1.0)
            
        Returns:
            Parsed JSON response or None on error
        """
        # Add instruction to return JSON in prompt
        if system_prompt:
            system_prompt += "\nYou must respond with valid JSON only."
        else:
            system_prompt = "You must respond with valid JSON only."
        
        response_format = {"type": "json_object"}
        
        response_obj = self.generate_completion(
            prompt=prompt,
            model=model,
            system_prompt=system_prompt,
            temperature=temperature,
            response_format=response_format
        )
        
        # Extract content from response
        response_text = ""
        if response_obj and "choices" in response_obj and len(response_obj["choices"]) > 0:
            response_text = response_obj["choices"][0].get("message", {}).get("content", "")
        
        if not response_text:
            logger.error("Empty response from OpenRouter")
            return {}
            
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            logger.error(f"Response text: {response_text}")
            return {}
    
    def get_topic_model(self) -> str:
        """Get the configured topic generation model"""
        return self.default_topic_model
    
    def get_content_model(self) -> str:
        """Get the configured content generation model"""
        return self.default_content_model
    
    def get_social_model(self) -> str:
        """Get the configured social media content model"""
        return self.default_social_model