"""
Content Validation System
Implements validation rules from user specifications to ensure content quality
"""
import logging
import re
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)

class ContentValidator:
    """
    Validates article content before publication according to specifications.
    Ensures Polish-only content, proper structure, and quality standards.
    """
    
    # Common English words to detect (excluding words that exist in Polish)
    ENGLISH_WORDS = {
        'the', 'and', 'but', 'common', 'mistakes', 'tips', 'guide',
        'how', 'what', 'when', 'where', 'why', 'best', 'top', 'most', 'avoid',
        'you', 'your', 'with', 'from', 'this', 'that', 'have', 'been', 'will',
        'should', 'could', 'would', 'pregnancy', 'baby', 'mother', 'father'
    }
    
    def __init__(self):
        self.validation_rules = [
            self._validate_language,
            self._validate_title,
            self._validate_excerpt, 
            self._validate_content,
            self._validate_structure,
            self._validate_length,
            self._validate_html_format
        ]
    
    def validate_article(self, title: str, excerpt: str, content: str, category: str = "") -> Tuple[bool, List[str]]:
        """
        Comprehensive article validation.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        logger.info(f"Validating article: {title[:50]}...")
        
        # Run all validation rules
        for rule in self.validation_rules:
            try:
                rule_errors = rule(title, excerpt, content, category)
                errors.extend(rule_errors)
            except Exception as e:
                logger.error(f"Validation rule failed: {str(e)}")
                errors.append(f"Błąd walidacji: {str(e)}")
        
        is_valid = len(errors) == 0
        
        if is_valid:
            logger.info("✅ Article validation passed")
        else:
            logger.warning(f"❌ Article validation failed with {len(errors)} errors")
            for error in errors:
                logger.warning(f"   - {error}")
        
        return is_valid, errors
    
    def _validate_language(self, title: str, excerpt: str, content: str, category: str) -> List[str]:
        """Validate 100% Polish language requirement"""
        errors = []
        
        # Check for English words in title
        title_words = set(re.findall(r'\b\w+\b', title.lower()))
        english_in_title = title_words.intersection(self.ENGLISH_WORDS)
        if english_in_title:
            errors.append(f"Tytuł zawiera angielskie słowa: {', '.join(english_in_title)}")
        
        # Check for English words in content (sample first 500 chars)
        content_sample = content[:500].lower()
        content_words = set(re.findall(r'\b\w+\b', content_sample))
        english_in_content = content_words.intersection(self.ENGLISH_WORDS)
        if english_in_content:
            errors.append(f"Treść zawiera angielskie słowa: {', '.join(list(english_in_content)[:3])}")
        
        return errors
    
    def _validate_title(self, title: str, excerpt: str, content: str, category: str) -> List[str]:
        """Validate title requirements"""
        errors = []
        
        # Length check (max 60 characters)
        if len(title) > 60:
            errors.append(f"Tytuł za długi: {len(title)} znaków (max 60)")
        
        if len(title) < 10:
            errors.append(f"Tytuł za krótki: {len(title)} znaków (min 10)")
        
        # Check for forbidden characters
        forbidden_chars = ['"', '"', '„', ':', '{', '}', '[', ']']
        for char in forbidden_chars:
            if char in title:
                errors.append(f"Tytuł zawiera niedozwolony znak: {char}")
        
        # Check for clickbait patterns
        clickbait_patterns = [
            r'\d+\s+(shocking|amazing|incredible|unbelievable)',
            r'you won\'t believe',
            r'doctors hate',
            r'this one trick'
        ]
        
        for pattern in clickbait_patterns:
            if re.search(pattern, title.lower()):
                errors.append("Tytuł zawiera elementy clickbaitu")
                break
        
        return errors
    
    def _validate_excerpt(self, title: str, excerpt: str, content: str, category: str) -> List[str]:
        """Validate excerpt requirements"""
        errors = []
        
        # Length check (max 160 characters)
        if len(excerpt) > 160:
            errors.append(f"Excerpt za długi: {len(excerpt)} znaków (max 160)")
        
        if len(excerpt) < 20:
            errors.append(f"Excerpt za krótki: {len(excerpt)} znaków (min 20)")
        
        # Check for JSON artifacts
        json_artifacts = ['"title":', '"excerpt":', '"content":', '{"', '"}']
        for artifact in json_artifacts:
            if artifact in excerpt:
                errors.append(f"Excerpt zawiera artefakt JSON: {artifact}")
        
        # Check if excerpt is identical to first paragraph
        if '<p>' in content:
            first_p_start = content.find('<p>') + 3
            first_p_end = content.find('</p>')
            if first_p_end > first_p_start:
                first_paragraph = content[first_p_start:first_p_end][:160]
                if excerpt.strip() == first_paragraph.strip():
                    errors.append("Excerpt jest identyczny z pierwszym akapitem")
        
        return errors
    
    def _validate_content(self, title: str, excerpt: str, content: str, category: str) -> List[str]:
        """Validate content quality and structure"""
        errors = []
        
        # Check for JSON artifacts
        json_artifacts = ['"title":', '"excerpt":', '"content":', '{"', '"}', '\\"title\\":', '\\"content\\"']
        for artifact in json_artifacts:
            if artifact in content:
                errors.append(f"Treść zawiera artefakt JSON: {artifact}")
        
        # Check for placeholder content
        placeholders = ['lorem ipsum', 'placeholder', 'TODO', 'XXX', '[insert', '{insert']
        for placeholder in placeholders:
            if placeholder.lower() in content.lower():
                errors.append(f"Treść zawiera placeholder: {placeholder}")
        
        return errors
    
    def _validate_structure(self, title: str, excerpt: str, content: str, category: str) -> List[str]:
        """Validate HTML structure requirements"""
        errors = []
        
        # Check for required H2 headers (minimum 3)
        h2_count = len(re.findall(r'<h2[^>]*>', content))
        if h2_count < 3:
            errors.append(f"Za mało nagłówków H2: {h2_count} (min 3)")
        
        # Check for proper paragraph structure
        p_count = len(re.findall(r'<p[^>]*>', content))
        if p_count < 8:
            errors.append(f"Za mało akapitów: {p_count} (min 8)")
        
        # Check for malformed HTML
        if content.count('<p>') != content.count('</p>'):
            errors.append("Niezamknięte tagi <p>")
        
        if content.count('<h2>') != content.count('</h2>'):
            errors.append("Niezamknięte tagi <h2>")
        
        return errors
    
    def _validate_length(self, title: str, excerpt: str, content: str, category: str) -> List[str]:
        """Validate minimum content length (1200 words / 4 pages A4)"""
        errors = []
        
        # Remove HTML tags for word count
        text_content = re.sub(r'<[^>]+>', '', content)
        word_count = len(text_content.split())
        char_count = len(text_content)
        
        # Minimum requirements
        MIN_WORDS = 800  # Adjusted for Polish (shorter words)
        MIN_CHARS = 4000  # Approximately 4 pages A4
        
        if word_count < MIN_WORDS:
            errors.append(f"Za mało słów: {word_count} (min {MIN_WORDS})")
        
        if char_count < MIN_CHARS:
            errors.append(f"Za mało znaków: {char_count} (min {MIN_CHARS})")
        
        return errors
    
    def _validate_html_format(self, title: str, excerpt: str, content: str, category: str) -> List[str]:
        """Validate proper HTML formatting"""
        errors = []
        
        # Content should start with <p> and end with </p>
        if not content.strip().startswith('<p'):
            errors.append("Treść powinna zaczynać się od <p>")
        
        if not content.strip().endswith('</p>'):
            errors.append("Treść powinna kończyć się na </p>")
        
        # Check for proper nesting
        if '<p><h2>' in content or '<h2><p>' in content:
            errors.append("Nieprawidłowa struktura HTML - zagnieżdżone tagi")
        
        return errors

def validate_before_publication(title: str, excerpt: str, content: str, category: str = "") -> Tuple[bool, List[str]]:
    """
    Convenience function for validating content before WordPress publication.
    
    Args:
        title: Article title
        excerpt: Article excerpt  
        content: Article content (HTML)
        category: Article category
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    validator = ContentValidator()
    return validator.validate_article(title, excerpt, content, category)

def check_duplicate_content(title: str, blog_id: int) -> bool:
    """
    Check if article with similar title already exists.
    
    Args:
        title: Article title to check
        blog_id: Blog ID to check against
        
    Returns:
        True if duplicate found, False otherwise
    """
    try:
        from models import ContentLog  # Import here to avoid circular import
        
        # Normalize title for comparison
        normalized_title = re.sub(r'[^\w\s]', '', title.lower()).strip()
        
        # Check for exact or very similar titles
        existing = ContentLog.query.filter_by(blog_id=blog_id).all()
        
        for article in existing:
            if article.title:
                existing_normalized = re.sub(r'[^\w\s]', '', article.title.lower()).strip()
                
                # Check for 80% similarity
                similarity = len(set(normalized_title.split()) & set(existing_normalized.split())) / max(len(normalized_title.split()), len(existing_normalized.split()))
                
                if similarity > 0.8:
                    logger.warning(f"Potential duplicate found: '{title}' vs '{article.title}'")
                    return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error checking duplicates: {str(e)}")
        return False