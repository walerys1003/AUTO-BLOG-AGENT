"""
AI Adapter Module

This module provides a unified interface for making requests to various AI completion models through
OpenRouter, with fallback to direct provider APIs when needed. Also includes a MockAdapter for testing.

The module also provides factory functions for obtaining appropriate AI service instances.
"""
import json
import logging
import os
import random
import requests
from typing import Dict, Any, Optional, List

from config import Config

# Configure logging
logger = logging.getLogger(__name__)

def get_openrouter_api_key():
    """Get OpenRouter API key from environment or config"""
    # Check environment first
    key = os.environ.get('OPENROUTER_API_KEY')
    if key:
        return key
    
    # Fallback to config
    if hasattr(Config, 'OPENROUTER_API_KEY') and Config.OPENROUTER_API_KEY:
        return Config.OPENROUTER_API_KEY
    
    # No hardcoded key - raise error if not found
    raise ValueError("OPENROUTER_API_KEY not found in environment or config")

def get_ai_completion(
    system_prompt: str,
    user_prompt: str,
    model: str = "anthropic/claude-3.5-sonnet",
    max_tokens: int = 2000,
    temperature: float = 0.7,
    response_format: Optional[Dict[str, str]] = None,
) -> str:
    """
    Get completion from AI model, with fallback to mock responses if needed.
    
    Args:
        system_prompt: System instructions for the AI
        user_prompt: User message/query
        model: Model to use (default: anthropic/claude-3.5-sonnet)
        max_tokens: Maximum tokens to generate
        temperature: Temperature for generation
        response_format: Optional response format specification (e.g. {"type": "json_object"})
        
    Returns:
        Generated text as string
    """
    try:
        # First try OpenRouter API
        response = openrouter_call(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            response_format=response_format
        )
        
        if response:
            return response
            
    except Exception as e:
        error_msg = str(e)
        logger.warning(f"OpenRouter API call failed: {error_msg}. Using fallback content generation.")
        
        # For rate limits, provide user-friendly message
        if "rate limit" in error_msg.lower():
            logger.info("Using MockAdapter due to OpenRouter rate limit")
        elif "temporarily unavailable" in error_msg.lower():
            logger.info("Using MockAdapter due to OpenRouter service issues")
        else:
            logger.info("Using MockAdapter due to OpenRouter API error")
    
    # If OpenRouter call fails, fallback to mock adapter with enhanced content
    logger.info("Generating content using fallback MockAdapter")
    mock = MockAdapter()
    return mock.get_completion(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature
    )

def openrouter_call(
    system_prompt: str,
    user_prompt: str,
    model: str = "anthropic/claude-3.5-sonnet",
    max_tokens: int = 2000,
    temperature: float = 0.7,
    response_format: Optional[Dict[str, str]] = None,
) -> str:
    """
    Make a request to OpenRouter API.
    
    Args:
        system_prompt: System instructions for the AI
        user_prompt: User message/query
        model: Model to use
        max_tokens: Maximum tokens to generate
        temperature: Temperature for generation
        response_format: Optional response format specification (e.g. {"type": "json_object"})
        
    Returns:
        Generated text as string
    """
    api_key = get_openrouter_api_key()
    if not api_key:
        raise ValueError("OpenRouter API key not found")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://blog-automation-master.ai/"
    }
    
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    
    # Add response format if specified
    if response_format:
        data["response_format"] = response_format
    
    try:
        logger.info(f"Making OpenRouter API request with model: {model}")
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=120  # 2 minute timeout for long requests
        )
        
        # Check response status
        if response.status_code != 200:
            logger.error(f"OpenRouter API error: {response.status_code}")
            logger.error(f"Response text: {response.text[:500]}")
            raise Exception(f"OpenRouter API error: {response.status_code}")
        
        # Validate response content type and content
        response_text = response.text.strip()
        content_type = response.headers.get('content-type', '').lower()
        
        # Check if response looks like HTML (common for error pages)
        if response_text.lower().startswith('<!doctype html') or response_text.lower().startswith('<html'):
            logger.error(f"OpenRouter returned HTML error page. Status: {response.status_code}")
            logger.error(f"HTML preview: {response_text[:500]}")
            if response.status_code == 429:
                raise Exception("OpenRouter API rate limit exceeded - please try again in a few minutes")
            elif response.status_code >= 500:
                raise Exception("OpenRouter service is temporarily unavailable - please try again later")
            else:
                raise Exception(f"OpenRouter returned error page (HTTP {response.status_code})")
        
        # Check content type
        if not content_type.startswith('application/json') and not response_text.startswith(('{', '[')):
            logger.error(f"OpenRouter returned non-JSON response. Content-Type: {content_type}")
            logger.error(f"Response text preview: {response_text[:300]}")
            if 'rate limit' in response_text.lower():
                raise Exception("OpenRouter API rate limit exceeded - please try again in a few minutes")
            else:
                raise Exception("OpenRouter returned unexpected response format")
        
        # Parse JSON response
        try:
            response_data = response.json()
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response from OpenRouter: {str(e)}")
            logger.error(f"Response text: {response.text[:300]}")
            raise Exception(f"Invalid JSON response from OpenRouter: {str(e)}")
        
        # Extract content
        if "choices" not in response_data or not response_data["choices"]:
            logger.error("No choices in OpenRouter response")
            logger.error(f"Response data: {response_data}")
            raise Exception("No choices in OpenRouter response")
        
        content = response_data["choices"][0]["message"]["content"]
        logger.info(f"Successfully received response from OpenRouter (length: {len(content)} chars)")
        return content
        
    except requests.exceptions.Timeout:
        logger.error("OpenRouter API request timed out")
        raise Exception("OpenRouter API request timed out - please try again")
    except requests.exceptions.ConnectionError:
        logger.error("Connection error to OpenRouter API")
        raise Exception("Connection error to OpenRouter API - please check network")
    except Exception as e:
        logger.error(f"OpenRouter API call failed: {str(e)}")
        raise

def get_default_ai_service():
    """
    Factory function to get the default AI service for the application.
    
    Currently returns OpenRouterService with appropriate fallback mechanisms.
    This function is used by other modules to get a consistent AI service.
    
    Returns:
        AI service object with completion capabilities
    """
    return OpenRouterService()

class OpenRouterService:
    """Service class for OpenRouter AI API with fallback capabilities"""
    
    def __init__(self, model=None):
        """Initialize the OpenRouter service with optional model override"""
        self.default_model = model or Config.DEFAULT_CONTENT_MODEL
    
    def complete(self, prompt, system_prompt=None, max_tokens=2000, temperature=0.7):
        """
        Generate a completion for the given prompt.
        
        Args:
            prompt: The user prompt/query
            system_prompt: Optional system instructions (defaults to a generic helper)
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation
            
        Returns:
            Generated text as string
        """
        if system_prompt is None:
            system_prompt = "Jesteś pomocnym asystentem AI, który dostarcza wartościowe i dokładne informacje."
            
        return get_ai_completion(
            system_prompt=system_prompt,
            user_prompt=prompt,
            model=self.default_model,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
    def complete_json(self, prompt, system_prompt=None, max_tokens=2000, temperature=0.7):
        """
        Generate a JSON completion for the given prompt.
        
        Args:
            prompt: The user prompt/query
            system_prompt: Optional system instructions (defaults to a generic helper)
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation
            
        Returns:
            Generated JSON as Python dict
        """
        if system_prompt is None:
            system_prompt = "Jesteś pomocnym asystentem AI, który dostarcza odpowiedzi w formacie JSON."
            
        response = get_ai_completion(
            system_prompt=system_prompt,
            user_prompt=prompt,
            model=self.default_model,
            max_tokens=max_tokens,
            temperature=temperature,
            response_format={"type": "json_object"}
        )
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON response: {response[:200]}...")
            return {"error": "Invalid JSON response", "text": response}

class MockAdapter:
    """Mock adapter for AI completions when API access fails"""
    
    def get_completion(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        model: str = "anthropic/claude-3.5-sonnet", 
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> str:
        """
        Provide a deterministic mock response based on the type of prompt.
        
        Args:
            system_prompt: System instructions for the AI
            user_prompt: User message/query
            model: Model to use (ignored in mock)
            max_tokens: Maximum tokens to generate (ignored in mock)
            temperature: Temperature for generation (ignored in mock)
            
        Returns:
            Generated text as string
        """
        # Clean up prompts to analyze what's being requested
        system_lower = system_prompt.lower()
        user_lower = user_prompt.lower()
        
        # Check if JSON format is expected
        json_format = "json" in system_lower and ("{" in system_lower or "}" in system_lower)
        
        # Detect prompt type
        if "plan" in system_lower and "tytuł" in system_lower:
            # Article title and plan generation
            return self._generate_mock_title_and_plan(user_prompt, json_format)
            
        elif "wstęp" in system_lower or "introduction" in system_lower:
            # Article introduction
            return self._generate_mock_intro(user_prompt)
            
        elif "zakończ" in system_lower or "conclusion" in system_lower:
            # Article conclusion
            return self._generate_mock_conclusion(user_prompt)
            
        elif "topic" in system_lower or "temat" in system_lower:
            # Topic generation
            return self._generate_mock_topics(user_prompt, json_format)
            
        elif "paragrafy" in system_lower or "paragraphs" in system_lower:
            # Paragraph generation
            return self._generate_mock_paragraph(user_prompt)
            
        else:
            # Generic response
            return "To jest przykładowa odpowiedź wygenerowana przez MockAdapter, ponieważ połączenie z API AI nie było dostępne."
    
    def _generate_mock_title_and_plan(self, user_prompt: str, json_format: bool) -> str:
        """Generate a mock title and article plan"""
        # Extract category and topic
        category = ""
        topic = ""
        
        for line in user_prompt.split("\n"):
            if "kategoria:" in line.lower():
                category = line.split(":", 1)[1].strip()
            elif "temat:" in line.lower():
                topic = line.split(":", 1)[1].strip()
        
        if not category:
            category = "Ogólna"
        if not topic:
            topic = "Przykładowy temat"
            
        # Create a deterministic title based on topic
        title = f"{topic.capitalize()} - kompletny przewodnik dla początkujących"
        
        # Create a simple plan
        plan = [
            f"Wprowadzenie do {topic}",
            f"Najważniejsze aspekty {topic}",
            f"Korzyści wynikające z {topic}",
            f"Praktyczne zastosowania {topic}",
            f"Podsumowanie i wnioski"
        ]
        
        if json_format:
            return json.dumps({
                "title": title,
                "plan": plan
            }, ensure_ascii=False)
        else:
            plan_text = "\n".join([f"- {item}" for item in plan])
            return f"Tytuł: {title}\n\nPlan:\n{plan_text}"
    
    def _generate_mock_intro(self, user_prompt: str) -> str:
        """Generate a mock article introduction"""
        # Extract topic
        topic = ""
        for line in user_prompt.split("\n"):
            if "temat:" in line.lower():
                topic = line.split(":", 1)[1].strip()
            elif "tytuł:" in line.lower() and not topic:
                topic = line.split(":", 1)[1].strip()
                
        if not topic:
            topic = "tego tematu"
            
        # Generate mock introduction
        return f"""<p>W dzisiejszych czasach coraz więcej osób interesuje się tematyką związaną z {topic}. Nie jest to zaskakujące, biorąc pod uwagę rosnące znaczenie tego obszaru w codziennym życiu. Od podstawowych zastosowań po zaawansowane techniki - wiedza z tego zakresu staje się niezbędna dla wielu profesjonalistów. W tym artykule przyjrzymy się najważniejszym aspektom {topic}, które warto poznać, niezależnie od poziomu doświadczenia.</p>

<p>Zrozumienie fundamentalnych zasad {topic} pozwala nie tylko na efektywniejsze działanie, ale również otwiera drzwi do nowych możliwości rozwoju. W kolejnych sekcjach omówimy zarówno praktyczne zastosowania, jak i teoretyczne podstawy, które pomogą Ci lepiej zrozumieć tę fascynującą dziedzinę.</p>"""
    
    def _generate_mock_conclusion(self, user_prompt: str) -> str:
        """Generate a mock article conclusion"""
        # Extract topic
        topic = ""
        for line in user_prompt.split("\n"):
            if "temat:" in line.lower():
                topic = line.split(":", 1)[1].strip()
            elif "tytuł:" in line.lower() and not topic:
                topic = line.split(":", 1)[1].strip()
                
        if not topic:
            topic = "tego tematu"
            
        # Generate mock conclusion
        return f"""<p>Zagadnienia związane z {topic} są niezwykle istotne w dzisiejszym świecie. Jak pokazaliśmy w tym artykule, odpowiednie podejście do tego tematu może przynieść liczne korzyści zarówno w życiu zawodowym, jak i prywatnym. Warto poświęcić czas na głębsze zrozumienie omawianych zagadnień.</p>

<p>Zachęcamy do praktycznego zastosowania zdobytej wiedzy. Najlepszym sposobem na pełne przyswojenie informacji o {topic} jest regularne ćwiczenie i eksperymentowanie z poznanymi technikami. Pamiętaj, że rozwój w tej dziedzinie to proces ciągły – bądź otwarty na nowe informacje i nie bój się zadawać pytań. Twoje zaangażowanie z pewnością przyniesie oczekiwane rezultaty!</p>"""
    
    def _generate_mock_topics(self, user_prompt: str, json_format: bool) -> str:
        """Generate mock topics for a category"""
        # Extract category
        category = ""
        for line in user_prompt.split("\n"):
            if "kategoria:" in line.lower():
                category = line.split(":", 1)[1].strip()
                
        if not category:
            category = "Ogólna"
            
        # Generate deterministic topics based on category
        base_topics = [
            f"Podstawy {category} dla początkujących",
            f"Zaawansowane techniki w {category}",
            f"Historia rozwoju {category} na przestrzeni lat",
            f"Najnowsze trendy w {category} w 2025 roku",
            f"Jak efektywnie wykorzystać {category} w codziennym życiu",
            f"10 najczęstszych błędów popełnianych przy {category}",
            f"Porównanie różnych podejść do {category}",
            f"Przyszłość {category} - prognozy ekspertów",
            f"Wpływ technologii na rozwój {category}",
            f"Praktyczny przewodnik po {category}"
        ]
        
        # Generate 20 topics by adding variations
        all_topics = base_topics.copy()
        for topic in base_topics:
            variations = [
                f"Jak {topic.lower()}",
                f"{topic} - praktyczne wskazówki",
                f"{topic} w kontekście biznesowym",
                f"{topic} dla profesjonalistów",
                f"{topic} - mity i fakty"
            ]
            all_topics.extend(variations[:2])  # Add only first 2 variations to avoid too many
            
        # Shuffle and limit to 20
        random.shuffle(all_topics)
        topics = all_topics[:20]
        
        if json_format:
            return json.dumps(topics, ensure_ascii=False)
        else:
            return "\n".join([f"- {topic}" for topic in topics])
    
    def _generate_mock_paragraph(self, user_prompt: str) -> str:
        """Generate a mock paragraph for an article section"""
        # Extract topic and section
        topic = ""
        section = ""
        
        for line in user_prompt.split("\n"):
            if "temat:" in line.lower():
                topic = line.split(":", 1)[1].strip()
            elif "sekcja:" in line.lower() or "section:" in line.lower():
                section = line.split(":", 1)[1].strip()
            elif "tytuł sekcji:" in line.lower():
                section = line.split(":", 1)[1].strip()
                
        if not topic:
            topic = "tego tematu"
        if not section:
            section = "tej sekcji"
            
        # Generate mock paragraph
        return f"""<p>W kontekście {topic}, {section} stanowi jeden z kluczowych elementów, który warto dokładnie przeanalizować. Eksperci w tej dziedzinie podkreślają, że zrozumienie podstawowych zasad jest niezbędne do osiągnięcia sukcesu. Badania pokazują, że osoby, które systematycznie rozwijają swoje umiejętności w tym zakresie, osiągają znacznie lepsze rezultaty niż ci, którzy podchodzą do tematu powierzchownie.</p>

<p>Istnieje kilka sprawdzonych metod, które mogą pomóc w efektywnym opanowaniu {section}. Po pierwsze, regularna praktyka jest niezastąpiona - nawet 15 minut dziennie może przynieść znaczące efekty w dłuższej perspektywie. Po drugie, warto korzystać z dostępnych zasobów edukacyjnych, takich jak kursy online, książki czy poradniki. Po trzecie, cenna jest wymiana doświadczeń z innymi osobami zainteresowanymi tematyką {topic}.</p>

<p>W praktycznym zastosowaniu {section} możemy wyróżnić trzy główne podejścia. Pierwsze koncentruje się na teoretycznych aspektach i budowaniu solidnych podstaw. Drugie podejście kładzie nacisk na praktyczne ćwiczenia i rozwiązywanie konkretnych problemów. Trzecie łączy oba wcześniejsze, tworząc zrównoważoną metodę nauki. Wybór odpowiedniego podejścia zależy od indywidualnych preferencji oraz specyfiki zagadnień związanych z {topic}.</p>"""