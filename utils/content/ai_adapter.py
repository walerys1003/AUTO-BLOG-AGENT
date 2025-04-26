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


class MockAdapter(AIServiceAdapter):
    """Mock adapter for testing without API access"""
    
    def __init__(self):
        self.model = "mock-model"
    
    def generate(self, prompt: str) -> str:
        """
        Generate mock text response
        
        Args:
            prompt: The prompt to generate from
            
        Returns:
            Generated text
        """
        logger.info(f"Using mock adapter to generate text")
        
        # Extract topic from prompt
        topic_match = None
        if "artykuł na temat:" in prompt:
            topic_match = prompt.split("artykuł na temat:")[1].split(",")[0].strip()
        
        # Create a demonstration article with long paragraphs
        intro = f"""Wprowadzenie do fascynującego świata kotów domowych i ich relacji z dziećmi. Koty od wieków towarzyszą ludziom, oferując nie tylko swoją obecność, ale również stanowiąc nieocenione wsparcie w rozwoju emocjonalnym i społecznym najmłodszych członków rodziny. Badania naukowe potwierdzają, że dzieci dorastające w otoczeniu zwierząt domowych, szczególnie kotów, wykazują wyższy poziom empatii, odpowiedzialności oraz umiejętności komunikacyjnych. W obecnych czasach, gdy coraz więcej rodzin mieszka w miejskich przestrzeniach z ograniczonym dostępem do natury, obecność kota w domu staje się cennym pomostem między cywilizacją a światem przyrody. Poprzez codzienny kontakt z żywym stworzeniem, dziecko uczy się szacunku do innych form życia, poznaje naturalne cykle i zachowania, oraz rozwija intuicyjne rozumienie potrzeb innych istot. Kot, jako zwierzę jednocześnie niezależne i przywiązane do ludzi, stanowi doskonały przykład zdrowej równowagi między bliskością a autonomią - wartości coraz bardziej cenionych we współczesnym świecie. W tym artykule przyjrzymy się wielowymiarowym korzyściom płynącym z obecności kota w życiu dziecka oraz praktycznym aspektom tworzenia harmonijnej przestrzeni dla tej wyjątkowej relacji."""
        
        paragraphs = []
        for i in range(2):
            if topic_match:
                paragraphs.append(f"""Koty jako towarzysze dzieci oraz ich wpływ na rozwój emocjonalny. W kontekście rozwoju emocjonalnego, trudno przecenić znaczenie, jakie ma codzienna interakcja dziecka z kotem domowym. Badania z zakresu psychologii rozwojowej jednoznacznie wskazują, że obecność zwierzęcia w domu sprzyja kształtowaniu się inteligencji emocjonalnej u najmłodszych. W odróżnieniu od zabawek czy urządzeń elektronicznych, kot jest istotą żywą, o własnych potrzebach, nastrojach i granicach - obcowanie z nim wymaga od dziecka ciągłego dostrajania własnych zachowań, co stanowi naturalny trening empatii. Szczególnie cenne jest to, że koty komunikują swoje uczucia w sposób bezpośredni, ale subtelny - poprzez mowę ciała, dźwięki i zachowanie. Dziecko uczy się rozpoznawać te sygnały, interpretować je i odpowiednio na nie reagować, co przekłada się na większą wrażliwość w relacjach międzyludzkich. Co więcej, obecność kota w trudnych momentach życia dziecka, takich jak choroba, problemy szkolne czy konflikty rodzinne, może mieć działanie terapeutyczne. Wykryto, że głaskanie kota obniża poziom kortyzolu (hormonu stresu) i podnosi poziom oksytocyny (hormonu przywiązania) zarówno u ludzi, jak i u kotów, tworząc pozytywne sprzężenie zwrotne. Dziecko doświadczające negatywnych emocji może znaleźć w kocie nie tylko pocieszenie, ale także przykład regulacji emocjonalnej - koty bowiem doskonale potrafią zadbać o swój dobrostan, odpoczywać gdy są zmęczone, bawić się gdy mają energię. Ta naturalna zdolność do dbania o równowagę jest cenną lekcją dla dzieci narażonych na stres i presję współczesnego świata. Warto również zauważyć, że w relacji z kotem dziecko doświadcza bezwarunkowej akceptacji - kot nie ocenia wyglądu, osiągnięć czy statusu społecznego, co stanowi przeciwwagę dla często wymagającego środowiska rówieśniczego. Ta akceptacja buduje w dziecku poczucie własnej wartości i bezpieczeństwa emocjonalnego, fundamentalnych dla zdrowego rozwoju psychicznego. Nawet momenty, gdy kot potrzebuje przestrzeni i samotności, uczą dziecko ważnej lekcji o szanowaniu granic innych i akceptowaniu odmiennych potrzeb - umiejętności kluczowych w budowaniu zdrowych relacji w dorosłym życiu. Wszystkie te aspekty sprawiają, że obecność kota w domu staje się nieocenionym wsparciem w kształtowaniu dojrzałej, empatycznej osobowości dziecka.""")
            else:
                paragraphs.append(f"To jest przykładowy długi akapit numer {i+1} wygenerowany przez mechanizm testowy. W rzeczywistym rozwiązaniu, ten tekst zostanie zastąpiony przez faktyczną treść utworzoną przez model AI Claude 3.5 Sonnet lub inny model skonfigurowany w systemie. Akapit ten powinien zawierać co najmniej 1000 tokenów, aby spełniać wymagania dotyczące długości. W prawdziwym artykule, ten fragment będzie zawierał szczegółowe, merytoryczne informacje na temat wskazany w poleceniu. Tekst będzie logicznie powiązany z tematem głównym artykułu i będzie stanowił jego integralną część. Wszystkie akapity wygenerowane przez system będą ze sobą powiązane, tworząc spójną i kompletną całość. Pamiętaj, że to tylko demonstracja możliwości generatora treści z długimi akapitami.")
        
        conclusion = "Podsumowując, obecność kota w życiu dziecka niesie ze sobą wielowymiarowe korzyści dla jego rozwoju emocjonalnego, społecznego i poznawczego. Ta wyjątkowa relacja, oparta na wzajemnym szacunku i zaufaniu, kształtuje w młodym człowieku cechy, które będą procentować przez całe życie. Odpowiedzialność, empatia, cierpliwość i umiejętność odczytywania niewerbalnych sygnałów to tylko niektóre z wartościowych lekcji, jakie dziecko otrzymuje dzięki codziennym interakcjom z kotem. Warto jednak pamiętać, że każda relacja wymaga odpowiedniego podejścia i nadzoru ze strony dorosłych, szczególnie na początkowych etapach. Z właściwym wsparciem i edukacją, przyjaźń między dzieckiem a kotem może stać się jednym z najpiękniejszych i najbardziej formujących doświadczeń dzieciństwa."
        
        # Compose the full article
        full_article = intro + "\n\n" + "\n\n".join(paragraphs) + "\n\n" + conclusion
        
        return full_article


def get_default_ai_service() -> AIServiceAdapter:
    """
    Get the default AI service based on available API keys
    
    Returns:
        An instance of AIServiceAdapter
    """
    # Temporarily use the mock adapter for demonstration
    return MockAdapter()
    
    # This code is temporarily disabled due to API access issues
    # TODO: Uncomment when API access is restored
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
    """