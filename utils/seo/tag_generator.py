"""
SEO Tag Generator - Creates exactly 12 tags per article
Generates relevant Polish SEO tags based on article content and category
"""
import logging
import re
from typing import List, Set
from utils.content.ai_adapter import get_ai_completion
from config import Config

logger = logging.getLogger(__name__)

class SEOTagGenerator:
    """Generates exactly 12 SEO tags for articles"""
    
    # Base tags for different categories
    CATEGORY_BASE_TAGS = {
        'Planowanie ciąży': ['ciąża', 'planowanie', 'płodność', 'rodzina', 'zdrowie'],
        'Zdrowie w ciąży': ['ciąża', 'zdrowie', 'mama', 'rozwój', 'badania'],
        'Produkty dla dzieci': ['dzieci', 'produkty', 'testowanie', 'bezpieczeństwo', 'jakość'],
        'Kosmetyki': ['kosmetyki', 'uroda', 'pielęgnacja', 'skóra', 'makijaż'],
        'Lifestyle': ['lifestyle', 'życie', 'porady', 'trendy', 'inspiracje']
    }
    
    def __init__(self):
        pass
    
    def generate_tags(self, title: str, content: str, category: str = "") -> List[str]:
        """
        Generate exactly 12 SEO tags for an article.
        
        Args:
            title: Article title
            content: Article content (HTML)
            category: Article category
            
        Returns:
            List of exactly 12 unique Polish SEO tags
        """
        logger.info(f"Generating 12 SEO tags for article: {title[:50]}...")
        
        try:
            # Get base tags for category
            base_tags = self.CATEGORY_BASE_TAGS.get(category, ['artykuł', 'porady', 'informacje'])
            
            # Extract keywords from title and content
            extracted_tags = self._extract_keywords(title, content)
            
            # Use AI to generate contextual tags
            ai_tags = self._generate_ai_tags(title, content, category)
            
            # Combine and filter to exactly 12 tags
            all_tags = base_tags + extracted_tags + ai_tags
            final_tags = self._filter_to_12_tags(all_tags, title, content)
            
            logger.info(f"Generated 12 tags: {', '.join(final_tags)}")
            return final_tags
            
        except Exception as e:
            logger.error(f"Error generating tags: {str(e)}")
            # Fallback to basic tags
            return self._get_fallback_tags(category)
    
    def _extract_keywords(self, title: str, content: str) -> List[str]:
        """Extract potential keywords from title and content"""
        keywords = []
        
        # Remove HTML tags from content
        text_content = re.sub(r'<[^>]+>', '', content)
        combined_text = (title + " " + text_content).lower()
        
        # Common Polish keywords for parenting/health content
        potential_keywords = [
            'ciąża', 'dziecko', 'mama', 'tata', 'rodzina', 'zdrowie', 'rozwój',
            'poród', 'karmieniem', 'pielęgnacja', 'bezpieczeństwo', 'edukacja',
            'zabawki', 'ubranka', 'kosmetyki', 'suplementy', 'witaminy',
            'badania', 'lekarz', 'pediatra', 'ginekolog', 'porady', 'wskazówki',
            'przygotowanie', 'planowanie', 'organizm', 'odżywianie', 'dieta'
        ]
        
        # Find keywords present in the text
        for keyword in potential_keywords:
            if keyword in combined_text:
                keywords.append(keyword)
        
        return keywords[:8]  # Limit to 8 extracted keywords
    
    def _generate_ai_tags(self, title: str, content: str, category: str) -> List[str]:
        """Use AI to generate contextual tags"""
        try:
            # Remove HTML for cleaner AI processing
            text_content = re.sub(r'<[^>]+>', '', content)
            content_sample = text_content[:800]  # First 800 chars
            
            prompt = f"""Na podstawie poniższego artykułu wygeneruj 8 najlepszych tagów SEO w języku polskim.

Tytuł: {title}
Kategoria: {category}
Fragment treści: {content_sample}

Wymagania:
- Dokładnie 8 tagów
- Tylko język polski
- Krótkie, konkretne słowa kluczowe
- Związane z tematem artykułu
- Przydatne dla SEO

Odpowiedz tylko listą tagów oddzielonych przecinkami, bez dodatkowych słów."""

            response = get_ai_completion(
                system_prompt="Jesteś ekspertem SEO tworzącym tagi dla polskich blogów parentingowych.",
                user_prompt=prompt,
                model=Config.DEFAULT_CONTENT_MODEL,
                max_tokens=150,
                temperature=0.3
            )
            
            # Parse AI response
            tags = [tag.strip() for tag in response.split(',')]
            tags = [tag for tag in tags if tag and len(tag) > 2]
            
            return tags[:8]  # Ensure max 8 tags
            
        except Exception as e:
            logger.warning(f"AI tag generation failed: {str(e)}")
            return []
    
    def _filter_to_12_tags(self, all_tags: List[str], title: str, content: str) -> List[str]:
        """Filter and prioritize tags to exactly 12 unique tags"""
        # Remove duplicates while preserving order
        seen = set()
        unique_tags = []
        
        for tag in all_tags:
            tag_clean = tag.lower().strip()
            if tag_clean not in seen and len(tag_clean) > 2:
                unique_tags.append(tag_clean)
                seen.add(tag_clean)
        
        # If we have more than 12, prioritize by relevance
        if len(unique_tags) > 12:
            # Prioritize tags that appear in title
            title_lower = title.lower()
            title_tags = [tag for tag in unique_tags if tag in title_lower]
            other_tags = [tag for tag in unique_tags if tag not in title_lower]
            
            # Combine: title tags first, then others
            prioritized = title_tags + other_tags
            unique_tags = prioritized[:12]
        
        # If we have less than 12, add generic tags
        while len(unique_tags) < 12:
            generic_tags = [
                'porady', 'informacje', 'wskazówki', 'praktyczne', 'użyteczne',
                'eksperckie', 'sprawdzone', 'skuteczne', 'pomocne', 'ważne',
                'niezbędne', 'podstawowe'
            ]
            
            for generic in generic_tags:
                if generic not in unique_tags:
                    unique_tags.append(generic)
                    break
            else:
                break  # No more generic tags to add
        
        return unique_tags[:12]  # Ensure exactly 12
    
    def _get_fallback_tags(self, category: str) -> List[str]:
        """Get fallback tags if generation fails"""
        base = self.CATEGORY_BASE_TAGS.get(category, ['artykuł', 'porady', 'informacje'])
        fallback = ['zdrowie', 'rodzina', 'praktyczne', 'wskazówki', 'pomocne', 'ważne', 'eksperckie']
        
        all_fallback = base + fallback
        return all_fallback[:12]

def generate_seo_tags(title: str, content: str, category: str = "") -> List[str]:
    """
    Convenience function to generate exactly 12 SEO tags.
    
    Args:
        title: Article title
        content: Article content
        category: Article category
        
    Returns:
        List of exactly 12 SEO tags
    """
    generator = SEOTagGenerator()
    return generator.generate_tags(title, content, category)