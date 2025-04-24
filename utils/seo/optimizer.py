import logging
import json
import re
from typing import Dict, List, Any, Optional, Tuple, Union
from bs4 import BeautifulSoup
from utils.openrouter import openrouter
from utils.seo.analyzer import seo_analyzer
import traceback

# Setup logging
logger = logging.getLogger(__name__)

class SEOOptimizer:
    """
    SEO optimization tools for improving content rankings
    
    This class provides methods to optimize content based on
    SEO analysis and best practices.
    """
    
    def __init__(self):
        """Initialize the SEO optimizer"""
        pass
    
    def optimize_article_content(self, 
                                html_content: str, 
                                primary_keyword: str,
                                secondary_keywords: List[str],
                                meta_title: Optional[str] = None,
                                meta_description: Optional[str] = None) -> Dict[str, Any]:
        """
        Optimize article content for SEO using AI assistance
        
        Args:
            html_content: The HTML content to optimize
            primary_keyword: The main target keyword
            secondary_keywords: Additional target keywords
            meta_title: Optional meta title
            meta_description: Optional meta description
            
        Returns:
            Dictionary with optimized content and suggestions
        """
        try:
            # First analyze the existing content
            analysis = seo_analyzer.analyze_content(
                html_content=html_content,
                primary_keyword=primary_keyword,
                secondary_keywords=secondary_keywords,
                meta_title=meta_title,
                meta_description=meta_description
            )
            
            # If score is already excellent (>85%), skip optimization
            if analysis.get("overall_score", 0) >= 8.5:
                return {
                    "optimized_content": html_content,
                    "meta_title": meta_title,
                    "meta_description": meta_description,
                    "analysis": analysis,
                    "changes_made": [],
                    "already_optimized": True
                }
            
            # Generate AI-enhanced suggestions
            ai_suggestions = seo_analyzer.generate_seo_suggestions_ai(
                content=html_content,
                analysis_result=analysis
            )
            
            # Apply optimization based on analysis and suggestions
            optimized_content, meta_title, meta_description, changes = self._apply_optimizations(
                html_content, 
                analysis, 
                ai_suggestions,
                primary_keyword,
                secondary_keywords,
                meta_title,
                meta_description
            )
            
            # Re-analyze the optimized content
            new_analysis = seo_analyzer.analyze_content(
                html_content=optimized_content,
                primary_keyword=primary_keyword,
                secondary_keywords=secondary_keywords,
                meta_title=meta_title,
                meta_description=meta_description
            )
            
            return {
                "optimized_content": optimized_content,
                "meta_title": meta_title,
                "meta_description": meta_description,
                "original_analysis": analysis,
                "new_analysis": new_analysis,
                "improvement": round(new_analysis.get("overall_score", 0) - analysis.get("overall_score", 0), 1),
                "changes_made": changes,
                "already_optimized": False
            }
            
        except Exception as e:
            logger.error(f"Error optimizing article content: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Return original content with error
            return {
                "optimized_content": html_content,
                "meta_title": meta_title,
                "meta_description": meta_description,
                "error": str(e),
                "changes_made": [],
                "already_optimized": False
            }
    
    def _apply_optimizations(self,
                           html_content: str,
                           analysis: Dict[str, Any],
                           ai_suggestions: Dict[str, Any],
                           primary_keyword: str,
                           secondary_keywords: List[str],
                           meta_title: Optional[str],
                           meta_description: Optional[str]) -> Tuple[str, Optional[str], Optional[str], List[str]]:
        """Apply SEO optimizations to content based on analysis"""
        changes_made = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Track if we need to apply AI-suggested content improvements
        apply_ai_content = ("improved_content" in ai_suggestions and 
                           ai_suggestions["improved_content"] and 
                           ai_suggestions["ai_enhanced"])
        
        # 1. Fix heading structure if needed
        if not soup.find('h1'):
            # Create H1 with primary keyword if missing
            body_tag = soup.find('body')
            if body_tag:
                new_h1 = soup.new_tag('h1')
                new_h1.append(meta_title or f"Complete Guide to {primary_keyword}")
                
                # Find good insertion point (before first paragraph or at start of body)
                first_p = soup.find('p')
                if first_p:
                    first_p.insert_before(new_h1)
                else:
                    body_tag.insert(0, new_h1)
                
                changes_made.append("Added missing H1 heading with primary keyword")
        
        # 2. Improve keyword density if too low
        if analysis["content_stats"]["primary_keyword_density"] < seo_analyzer.primary_keyword_density_min:
            # Only apply if we're not using AI content improvements (which would address this)
            if not apply_ai_content:
                # Find paragraphs that don't contain the keyword
                paragraphs = soup.find_all('p')
                keyword_added = False
                
                for p in paragraphs[:3]:  # Focus on early paragraphs
                    if primary_keyword.lower() not in p.get_text().lower():
                        # Add keyword to this paragraph
                        text = p.get_text()
                        # Simple approach: replace first sentence with one containing keyword
                        sentences = re.split(r'(?<=[.!?])\s+', text)
                        if sentences:
                            new_sentence = f"When it comes to {primary_keyword}, {sentences[0]}"
                            p.string = new_sentence + " " + " ".join(sentences[1:])
                            keyword_added = True
                            break
                
                if keyword_added:
                    changes_made.append(f"Increased primary keyword ({primary_keyword}) density in early paragraph")
        
        # 3. Add meta description if missing
        if not meta_description:
            # Extract first paragraph for meta description
            first_p = soup.find('p')
            if first_p:
                text = first_p.get_text()
                # Ensure primary keyword is included
                if primary_keyword.lower() not in text.lower():
                    meta_description = f"Learn about {primary_keyword}. {text[:120]}..."
                else:
                    meta_description = text[:160] + "..." if len(text) > 160 else text
                changes_made.append("Created meta description from first paragraph")
        
        # 4. Optimize meta title if needed
        if not meta_title:
            h1 = soup.find('h1')
            if h1:
                meta_title = h1.get_text()
            else:
                meta_title = f"{primary_keyword} - Complete Guide and Tips"
            changes_made.append("Created meta title from H1 heading")
        
        # 5. Add keywords to headings if missing
        keyword_in_headings = False
        for heading in soup.find_all(['h1', 'h2', 'h3']):
            if primary_keyword.lower() in heading.get_text().lower():
                keyword_in_headings = True
                break
        
        if not keyword_in_headings:
            # Add keyword to first H2 if it exists
            h2 = soup.find('h2')
            if h2:
                h2_text = h2.get_text()
                h2.clear()
                h2.append(f"{primary_keyword}: {h2_text}")
                changes_made.append("Added primary keyword to H2 heading")
        
        # 6. Apply AI content improvements if available
        if apply_ai_content:
            # This would require more sophisticated HTML manipulation
            # For now, we'll just note that AI suggestions were received
            changes_made.append("Received AI content improvement suggestions")
        
        # Return the optimized content
        return str(soup), meta_title, meta_description, changes_made
    
    def generate_seo_title_variations(self, 
                                     topic: str, 
                                     primary_keyword: str,
                                     secondary_keywords: Optional[List[str]] = None,
                                     count: int = 5) -> List[str]:
        """
        Generate SEO-optimized title variations for a topic
        
        Args:
            topic: The general topic or title idea
            primary_keyword: The main keyword to include
            secondary_keywords: Optional secondary keywords to consider
            count: Number of variations to generate
            
        Returns:
            List of SEO-optimized title variations
        """
        try:
            # Format prompt for title generation
            sec_keywords_text = ", ".join(secondary_keywords) if secondary_keywords else ""
            
            prompt = f"""
Generate {count} SEO-optimized title variations for a blog post about: {topic}

Primary keyword (must include): {primary_keyword}
Secondary keywords (include at least one if possible): {sec_keywords_text}

The titles should:
1. Be 50-60 characters long (optimal for search engines)
2. Include the primary keyword, preferably near the beginning
3. Be compelling and clickable (high CTR potential)
4. Use power words and numbers where appropriate
5. Address search intent clearly

Format your response as a JSON array of strings, with each string being a complete title.
"""
            
            # Get the model for title generation
            model = openrouter.get_topic_model()
            
            # System message for SEO expertise
            system_message = """You are an expert SEO copywriter specializing in creating
high-performing article titles that rank well in search engines and
generate high click-through rates. Your titles are both algorithm-friendly and appealing to human readers."""
            
            # Get response from AI
            response = openrouter.generate_json_response(
                prompt=prompt,
                model=model,
                system_prompt=system_message,
                temperature=0.7  # Higher temperature for creativity
            )
            
            if not response or not isinstance(response, list):
                logger.error("Failed to get SEO title variations")
                return self._generate_fallback_titles(topic, primary_keyword, count)
            
            return response[:count]
            
        except Exception as e:
            logger.error(f"Error generating SEO title variations: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Return basic fallback titles
            return self._generate_fallback_titles(topic, primary_keyword, count)
    
    def _generate_fallback_titles(self, topic: str, keyword: str, count: int) -> List[str]:
        """Generate basic SEO title variations as fallback"""
        templates = [
            f"{count} Essential Tips for {keyword}: The Ultimate Guide",
            f"How to Master {keyword}: A Complete {topic} Guide",
            f"{keyword} 101: Everything You Need to Know About {topic}",
            f"The Complete Guide to {keyword} in {topic}",
            f"Why {keyword} Matters: Essential {topic} Strategies"
        ]
        
        # Return available templates up to requested count
        return templates[:count]
    
    def optimize_meta_description(self, 
                                 content_snippet: str, 
                                 primary_keyword: str,
                                 max_length: int = 160) -> str:
        """
        Create an SEO-optimized meta description
        
        Args:
            content_snippet: A snippet of content to base the description on
            primary_keyword: The primary keyword to include
            max_length: Maximum description length
            
        Returns:
            Optimized meta description
        """
        try:
            # Format prompt for meta description optimization
            prompt = f"""
Create an SEO-optimized meta description based on this content snippet:

Content: {content_snippet[:500]}

Primary keyword (must include): {primary_keyword}

The meta description should:
1. Be under {max_length} characters (currently Google displays ~155-160 characters)
2. Include the primary keyword naturally
3. Be compelling and accurately summarize the content
4. Include a call-to-action if possible
5. Avoid truncation (don't end mid-sentence)

Provide just the meta description itself, without quotes or explanations.
"""
            
            # Get the model for meta description generation
            model = openrouter.get_topic_model()
            
            # Get response from AI
            response = openrouter.generate_completion(
                prompt=prompt,
                model=model,
                temperature=0.5
            )
            
            if not response:
                logger.error("Failed to optimize meta description")
                return self._generate_fallback_meta_description(content_snippet, primary_keyword, max_length)
            
            # Ensure length limit
            if len(response) > max_length:
                response = response[:max_length-3] + "..."
            
            return response
            
        except Exception as e:
            logger.error(f"Error optimizing meta description: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Return basic fallback description
            return self._generate_fallback_meta_description(content_snippet, primary_keyword, max_length)
    
    def _generate_fallback_meta_description(self, content: str, keyword: str, max_length: int) -> str:
        """Generate a basic meta description as fallback"""
        # Extract first sentence or fragment
        first_sentence = re.split(r'(?<=[.!?])\s+', content.strip())[0]
        
        # Ensure keyword is included
        if keyword.lower() not in first_sentence.lower():
            description = f"Learn about {keyword}. {first_sentence}"
        else:
            description = first_sentence
        
        # Truncate if needed
        if len(description) > max_length:
            description = description[:max_length-3] + "..."
        
        return description

# Create a singleton instance
seo_optimizer = SEOOptimizer()