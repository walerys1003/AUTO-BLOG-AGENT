import logging
import re
import json
from typing import Dict, List, Any, Optional, Tuple
from bs4 import BeautifulSoup
from config import Config
from utils.openrouter import openrouter
import requests
import traceback

# Setup logging
logger = logging.getLogger(__name__)

class SEOAnalyzer:
    """
    Real-time SEO analyzer and optimization suggestion engine
    
    This class provides methods to analyze content for SEO issues
    and generate suggestions to improve search engine rankings.
    """
    
    def __init__(self):
        """Initialize the SEO analyzer with default parameters"""
        # Minimum word count for good SEO performance
        self.min_word_count = 600
        
        # Optimal word count range
        self.optimal_word_count_min = 1200
        self.optimal_word_count_max = 1800
        
        # Keyword density targets (%)
        self.primary_keyword_density_min = 0.5
        self.primary_keyword_density_max = 2.5
        self.secondary_keyword_density_min = 0.3
        self.secondary_keyword_density_max = 1.5
        
        # Meta constraints
        self.meta_title_min_length = 30
        self.meta_title_max_length = 60
        self.meta_description_min_length = 120
        self.meta_description_max_length = 160
        
        # Scoring weights for different SEO factors
        self.score_weights = {
            "content_length": 15,
            "keyword_usage": 25, 
            "headings": 15,
            "meta_tags": 15,
            "links": 10,
            "readability": 10,
            "media": 10
        }
        
    def analyze_content(self, 
                       html_content: str, 
                       primary_keyword: str,
                       secondary_keywords: List[str],
                       meta_title: Optional[str] = None,
                       meta_description: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze HTML content for SEO issues and calculate an overall score
        
        Args:
            html_content: The HTML content to analyze
            primary_keyword: The main target keyword for the content
            secondary_keywords: Additional target keywords
            meta_title: Optional meta title to analyze
            meta_description: Optional meta description to analyze
            
        Returns:
            Dictionary containing analysis results and score
        """
        try:
            # Parse the HTML content
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract text content (excluding scripts and styles)
            for script in soup(['script', 'style']):
                script.extract()
                
            # Get clean text content
            text_content = soup.get_text(separator=' ', strip=True)
            
            # Basic analysis
            word_count = len(text_content.split())
            
            # Find title from HTML if not provided
            if not meta_title:
                title_tag = soup.find('title')
                meta_title = title_tag.get_text() if title_tag else ""
                if not meta_title:
                    h1_tag = soup.find('h1')
                    meta_title = h1_tag.get_text() if h1_tag else ""
            
            # Find meta description from HTML if not provided
            if not meta_description:
                meta_desc_tag = soup.find('meta', attrs={'name': 'description'})
                meta_description = meta_desc_tag.get('content', '') if meta_desc_tag else ""
            
            # Analyze headings
            headings = {
                'h1': [h.get_text() for h in soup.find_all('h1')],
                'h2': [h.get_text() for h in soup.find_all('h2')],
                'h3': [h.get_text() for h in soup.find_all('h3')],
                'h4': [h.get_text() for h in soup.find_all('h4')]
            }
            
            # Analyze links
            internal_links = len(soup.find_all('a', href=lambda href: href and not href.startswith(('http', 'https', '//'))))
            external_links = len(soup.find_all('a', href=lambda href: href and href.startswith(('http', 'https', '//'))))
            
            # Analyze images
            images = soup.find_all('img')
            images_with_alt = [img for img in images if img.get('alt')]
            
            # Keyword analysis for primary keyword
            primary_keyword_lower = primary_keyword.lower()
            text_content_lower = text_content.lower()
            
            # Count keyword occurrences
            primary_keyword_count = text_content_lower.count(primary_keyword_lower)
            
            # Calculate keyword density
            primary_keyword_density = (primary_keyword_count * len(primary_keyword.split())) / word_count * 100 if word_count > 0 else 0
            
            # Analyze secondary keywords
            secondary_keyword_analysis = []
            for keyword in secondary_keywords:
                keyword_lower = keyword.lower()
                count = text_content_lower.count(keyword_lower)
                density = (count * len(keyword.split())) / word_count * 100 if word_count > 0 else 0
                
                secondary_keyword_analysis.append({
                    'keyword': keyword,
                    'count': count,
                    'density': density,
                    'in_title': keyword_lower in meta_title.lower() if meta_title else False,
                    'in_headings': any(keyword_lower in h.lower() for heading_list in headings.values() for h in heading_list)
                })
            
            # Analyze keyword placement
            keyword_in_first_para = primary_keyword_lower in ' '.join(soup.find_all('p')[0].get_text().lower()) if soup.find_all('p') else False
            
            keyword_in_headings = {
                'h1': any(primary_keyword_lower in h.lower() for h in headings['h1']),
                'h2': any(primary_keyword_lower in h.lower() for h in headings['h2']),
                'any_heading': any(primary_keyword_lower in h.lower() for heading_list in headings.values() for h in heading_list)
            }
            
            # Calculate score for each factor
            content_length_score = self._score_content_length(word_count)
            keyword_usage_score = self._score_keyword_usage(
                primary_keyword_density, 
                [k['density'] for k in secondary_keyword_analysis],
                keyword_in_first_para,
                keyword_in_headings
            )
            headings_score = self._score_headings(headings, primary_keyword_lower, [k.lower() for k in secondary_keywords])
            meta_score = self._score_meta_tags(meta_title, meta_description, primary_keyword_lower)
            links_score = self._score_links(internal_links, external_links)
            media_score = self._score_media(images, images_with_alt)
            
            # Calculate overall score (weighted)
            overall_score = (
                content_length_score * self.score_weights["content_length"] +
                keyword_usage_score * self.score_weights["keyword_usage"] +
                headings_score * self.score_weights["headings"] +
                meta_score * self.score_weights["meta_tags"] +
                links_score * self.score_weights["links"] +
                media_score * self.score_weights["media"]
            ) / sum([self.score_weights[k] for k in ["content_length", "keyword_usage", "headings", "meta_tags", "links", "media"]])
            
            # Generate issues and recommendations
            issues, recommendations = self._generate_recommendations(
                word_count,
                primary_keyword_density,
                secondary_keyword_analysis,
                headings,
                meta_title,
                meta_description,
                internal_links,
                external_links,
                images,
                images_with_alt,
                keyword_in_first_para,
                keyword_in_headings
            )
            
            # Return the complete analysis
            return {
                "overall_score": round(overall_score, 1),
                "content_stats": {
                    "word_count": word_count,
                    "primary_keyword": primary_keyword,
                    "primary_keyword_count": primary_keyword_count,
                    "primary_keyword_density": round(primary_keyword_density, 2),
                    "secondary_keywords": secondary_keyword_analysis,
                    "headings": headings,
                    "internal_links": internal_links,
                    "external_links": external_links,
                    "images": len(images),
                    "images_with_alt": len(images_with_alt)
                },
                "scores": {
                    "content_length": round(content_length_score, 1),
                    "keyword_usage": round(keyword_usage_score, 1),
                    "headings": round(headings_score, 1),
                    "meta_tags": round(meta_score, 1),
                    "links": round(links_score, 1),
                    "media": round(media_score, 1)
                },
                "issues": issues,
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"Error analyzing SEO content: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Return a basic error response
            return {
                "overall_score": 0,
                "error": str(e),
                "issues": ["Error analyzing content"],
                "recommendations": ["Please check the HTML content and try again"]
            }
    
    def _score_content_length(self, word_count: int) -> float:
        """Score the content length on a scale of 0-10"""
        if word_count < self.min_word_count:
            # Poor score for too short content
            return max(3.0, (word_count / self.min_word_count) * 5.0)
        elif word_count < self.optimal_word_count_min:
            # Medium score for acceptable but not optimal length
            return 5.0 + ((word_count - self.min_word_count) / 
                          (self.optimal_word_count_min - self.min_word_count)) * 3.0
        elif word_count <= self.optimal_word_count_max:
            # Best score for optimal length
            return 8.0 + ((word_count - self.optimal_word_count_min) / 
                          (self.optimal_word_count_max - self.optimal_word_count_min)) * 2.0
        else:
            # Slightly lower score for very long content
            return 10.0 - min(2.0, ((word_count - self.optimal_word_count_max) / 
                                    1000) * 1.0)
    
    def _score_keyword_usage(self, 
                            primary_density: float, 
                            secondary_densities: List[float],
                            keyword_in_first_para: bool,
                            keyword_in_headings: Dict[str, bool]) -> float:
        """Score the keyword usage on a scale of 0-10"""
        # Primary keyword density score (0-5)
        if primary_density < self.primary_keyword_density_min:
            primary_score = (primary_density / self.primary_keyword_density_min) * 3.0
        elif primary_density <= self.primary_keyword_density_max:
            primary_score = 3.0 + ((primary_density - self.primary_keyword_density_min) / 
                                  (self.primary_keyword_density_max - self.primary_keyword_density_min)) * 2.0
        else:
            # Penalty for keyword stuffing
            excess = primary_density - self.primary_keyword_density_max
            primary_score = max(0, 5.0 - (excess * 0.5))
        
        # Secondary keywords score (0-2)
        sec_scores = []
        for density in secondary_densities:
            if density < self.secondary_keyword_density_min:
                sec_scores.append((density / self.secondary_keyword_density_min) * 1.0)
            elif density <= self.secondary_keyword_density_max:
                sec_scores.append(1.0 + ((density - self.secondary_keyword_density_min) / 
                                        (self.secondary_keyword_density_max - self.secondary_keyword_density_min)) * 1.0)
            else:
                # Slight penalty for stuffing
                excess = density - self.secondary_keyword_density_max
                sec_scores.append(max(0, 2.0 - (excess * 0.25)))
        
        # Average secondary score, max 2
        secondary_score = min(2.0, sum(sec_scores) / max(1, len(sec_scores)))
        
        # Placement score (0-3)
        placement_score = 0
        if keyword_in_first_para:
            placement_score += 1.0
        if keyword_in_headings['h1']:
            placement_score += 1.0
        elif keyword_in_headings['any_heading']:
            placement_score += 0.5
        
        # Combine scores
        return primary_score + secondary_score + placement_score
    
    def _score_headings(self, 
                       headings: Dict[str, List[str]], 
                       primary_keyword: str,
                       secondary_keywords: List[str]) -> float:
        """Score the heading structure on a scale of 0-10"""
        # Check for H1 (0-3)
        if not headings['h1']:
            h1_score = 0
        elif len(headings['h1']) > 1:
            h1_score = 1  # Penalty for multiple H1s
        else:
            h1_score = 3
        
        # Check for H2s (0-2)
        h2_count = len(headings['h2'])
        if h2_count == 0:
            h2_score = 0
        elif h2_count < 2:
            h2_score = 1
        else:
            h2_score = min(2, 1 + h2_count * 0.2)
        
        # Check for H3s (0-1)
        h3_score = min(1, len(headings['h3']) * 0.2)
        
        # Check keyword in headings (0-4)
        keyword_score = 0
        
        # Primary keyword in headings
        if any(primary_keyword in h.lower() for h in headings['h1']):
            keyword_score += 2
        elif any(primary_keyword in h.lower() for h in headings['h2']):
            keyword_score += 1
        
        # Secondary keywords in headings
        sec_in_headings = 0
        for kw in secondary_keywords:
            if any(kw in h.lower() for heading_type in headings.values() for h in heading_type):
                sec_in_headings += 1
        
        keyword_score += min(2, sec_in_headings * 0.5)
        
        return h1_score + h2_score + h3_score + keyword_score
    
    def _score_meta_tags(self, 
                        title: Optional[str], 
                        description: Optional[str],
                        primary_keyword: str) -> float:
        """Score the meta tags on a scale of 0-10"""
        # Title score (0-5)
        if not title:
            title_score = 0
        else:
            # Length check
            title_len = len(title)
            if title_len < self.meta_title_min_length:
                length_score = (title_len / self.meta_title_min_length) * 2
            elif title_len <= self.meta_title_max_length:
                length_score = 2 + ((self.meta_title_max_length - title_len) / 
                                   (self.meta_title_max_length - self.meta_title_min_length)) * 1
            else:
                # Penalty for too long title
                excess = title_len - self.meta_title_max_length
                length_score = max(0, 3 - (excess * 0.1))
            
            # Keyword in title
            keyword_score = 2 if primary_keyword in title.lower() else 0
            
            title_score = length_score + keyword_score
        
        # Description score (0-5)
        if not description:
            desc_score = 0
        else:
            # Length check
            desc_len = len(description)
            if desc_len < self.meta_description_min_length:
                length_score = (desc_len / self.meta_description_min_length) * 2
            elif desc_len <= self.meta_description_max_length:
                length_score = 2 + ((self.meta_description_max_length - desc_len) / 
                                   (self.meta_description_max_length - self.meta_description_min_length)) * 1
            else:
                # Penalty for too long description
                excess = desc_len - self.meta_description_max_length
                length_score = max(0, 3 - (excess * 0.05))
            
            # Keyword in description
            keyword_score = 2 if primary_keyword in description.lower() else 0
            
            desc_score = length_score + keyword_score
        
        return title_score + desc_score
    
    def _score_links(self, internal_links: int, external_links: int) -> float:
        """Score the link structure on a scale of 0-10"""
        # Internal links score (0-6)
        if internal_links == 0:
            internal_score = 0
        elif internal_links < 3:
            internal_score = internal_links * 1.0
        else:
            internal_score = min(6, 3 + (internal_links - 3) * 0.5)
        
        # External links score (0-4)
        if external_links == 0:
            external_score = 0
        elif external_links < 2:
            external_score = external_links * 1.0
        else:
            external_score = min(4, 2 + (external_links - 2) * 0.5)
        
        return internal_score + external_score
    
    def _score_media(self, images: List[Any], images_with_alt: List[Any]) -> float:
        """Score the media elements on a scale of 0-10"""
        # Image count score (0-5)
        image_count = len(images)
        if image_count == 0:
            count_score = 0
        elif image_count == 1:
            count_score = 2
        else:
            count_score = min(5, 2 + (image_count - 1) * 0.5)
        
        # Alt text score (0-5)
        if image_count == 0:
            alt_score = 0
        else:
            alt_ratio = len(images_with_alt) / image_count
            alt_score = alt_ratio * 5
        
        return count_score + alt_score
    
    def _generate_recommendations(self,
                                 word_count: int,
                                 primary_density: float,
                                 secondary_analysis: List[Dict[str, Any]],
                                 headings: Dict[str, List[str]],
                                 meta_title: Optional[str],
                                 meta_description: Optional[str],
                                 internal_links: int,
                                 external_links: int,
                                 images: List[Any],
                                 images_with_alt: List[Any],
                                 keyword_in_first_para: bool,
                                 keyword_in_headings: Dict[str, bool]) -> Tuple[List[str], List[str]]:
        """Generate a list of issues and recommendations based on the analysis"""
        issues = []
        recommendations = []
        
        # Content length issues
        if word_count < self.min_word_count:
            issues.append(f"Content length ({word_count} words) is below minimum recommended length ({self.min_word_count} words)")
            recommendations.append(f"Increase content length to at least {self.min_word_count} words for better search rankings")
        elif word_count < self.optimal_word_count_min:
            recommendations.append(f"Consider expanding content to {self.optimal_word_count_min}-{self.optimal_word_count_max} words for optimal rankings")
        
        # Keyword usage issues
        if primary_density < self.primary_keyword_density_min:
            issues.append(f"Primary keyword density ({primary_density:.2f}%) is below recommended minimum ({self.primary_keyword_density_min}%)")
            recommendations.append(f"Increase primary keyword usage to achieve {self.primary_keyword_density_min}-{self.primary_keyword_density_max}% density")
        elif primary_density > self.primary_keyword_density_max:
            issues.append(f"Primary keyword density ({primary_density:.2f}%) indicates possible keyword stuffing (above {self.primary_keyword_density_max}%)")
            recommendations.append(f"Reduce primary keyword usage to avoid keyword stuffing (aim for {self.primary_keyword_density_min}-{self.primary_keyword_density_max}%)")
        
        # Secondary keyword issues
        low_secondary = []
        for kw_analysis in secondary_analysis:
            if kw_analysis['density'] < self.secondary_keyword_density_min:
                low_secondary.append(kw_analysis['keyword'])
        
        if low_secondary:
            issues.append(f"Low usage of secondary keywords: {', '.join(low_secondary)}")
            recommendations.append(f"Increase usage of secondary keywords: {', '.join(low_secondary)}")
        
        # Keyword placement
        if not keyword_in_first_para:
            issues.append("Primary keyword not found in first paragraph")
            recommendations.append("Include primary keyword in the first paragraph for better SEO")
        
        if not keyword_in_headings['any_heading']:
            issues.append("Primary keyword not found in any heading")
            recommendations.append("Include primary keyword in at least one heading (preferably H1 or H2)")
        
        # Heading structure
        if not headings['h1']:
            issues.append("Missing H1 heading")
            recommendations.append("Add an H1 heading that includes the primary keyword")
        elif len(headings['h1']) > 1:
            issues.append(f"Multiple H1 headings found ({len(headings['h1'])})")
            recommendations.append("Use only one H1 heading per page")
        
        if not headings['h2']:
            issues.append("No H2 headings found")
            recommendations.append("Add H2 headings to structure content and include keywords")
        
        # Meta tags
        if not meta_title:
            issues.append("Missing meta title")
            recommendations.append("Add a meta title that includes the primary keyword")
        elif len(meta_title) < self.meta_title_min_length:
            issues.append(f"Meta title too short ({len(meta_title)} chars)")
            recommendations.append(f"Expand meta title to {self.meta_title_min_length}-{self.meta_title_max_length} characters")
        elif len(meta_title) > self.meta_title_max_length:
            issues.append(f"Meta title too long ({len(meta_title)} chars)")
            recommendations.append(f"Reduce meta title to {self.meta_title_max_length} characters maximum")
        
        if not meta_description:
            issues.append("Missing meta description")
            recommendations.append("Add a meta description that includes the primary keyword")
        elif len(meta_description) < self.meta_description_min_length:
            issues.append(f"Meta description too short ({len(meta_description)} chars)")
            recommendations.append(f"Expand meta description to {self.meta_description_min_length}-{self.meta_description_max_length} characters")
        elif len(meta_description) > self.meta_description_max_length:
            issues.append(f"Meta description too long ({len(meta_description)} chars)")
            recommendations.append(f"Reduce meta description to {self.meta_description_max_length} characters maximum")
        
        # Links
        if internal_links < 3:
            issues.append(f"Low number of internal links ({internal_links})")
            recommendations.append("Add more internal links to related content (aim for at least 3-5)")
        
        if external_links == 0:
            issues.append("No external links found")
            recommendations.append("Add 1-3 external links to authoritative sources")
        
        # Images
        if len(images) == 0:
            issues.append("No images found in content")
            recommendations.append("Add at least one relevant image to improve engagement")
        
        # Alt text
        if len(images) > len(images_with_alt):
            missing_alt = len(images) - len(images_with_alt)
            issues.append(f"Missing alt text on {missing_alt} images")
            recommendations.append("Add descriptive alt text to all images, including keywords where natural")
        
        return issues, recommendations

    def generate_seo_suggestions_ai(self, 
                                   content: str, 
                                   analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use AI to generate intelligent SEO improvement suggestions
        
        Args:
            content: The HTML or text content
            analysis_result: Result from analyze_content
            
        Returns:
            Dictionary with AI-enhanced suggestions
        """
        try:
            # Format prompt with content and analysis
            prompt = self._format_seo_prompt(content, analysis_result)
            
            # Get the model for SEO analysis (using topic model as it's faster)
            model = openrouter.get_topic_model()
            
            # System message for SEO expertise
            system_message = """You are an expert SEO analyzer specializing in content optimization.
Your goal is to provide actionable, specific suggestions to improve SEO performance.
Focus on high-impact changes and explain why they matter.
Format your response as JSON."""
            
            # Get response from AI
            response = openrouter.generate_json_response(
                prompt=prompt,
                model=model,
                system_prompt=system_message,
                temperature=0.4  # Lower temperature for more focused suggestions
            )
            
            if not response:
                logger.error("Failed to get AI SEO suggestions")
                return {
                    "suggestions": analysis_result["recommendations"],
                    "ai_enhanced": False
                }
            
            # Return the enhanced suggestions
            return {
                "suggestions": response.get("suggestions", analysis_result["recommendations"]),
                "improved_content": response.get("improved_content", None),
                "improved_headings": response.get("improved_headings", None), 
                "keyword_recommendations": response.get("keyword_recommendations", None),
                "ai_enhanced": True
            }
            
        except Exception as e:
            logger.error(f"Error generating AI SEO suggestions: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Return the original recommendations as fallback
            return {
                "suggestions": analysis_result["recommendations"],
                "ai_enhanced": False
            }
    
    def _format_seo_prompt(self, content: str, analysis: Dict[str, Any]) -> str:
        """Format a prompt for AI analysis of SEO content"""
        # Truncate content if too long
        content_preview = content[:5000] + "..." if len(content) > 5000 else content
        
        # Format scores for readability
        scores = analysis.get("scores", {})
        scores_formatted = "\n".join([f"- {key.replace('_', ' ').title()}: {value}/10" for key, value in scores.items()])
        
        # Format issues and recommendations
        issues = "\n".join([f"- {issue}" for issue in analysis.get("issues", [])])
        recommendations = "\n".join([f"- {rec}" for rec in analysis.get("recommendations", [])])
        
        # Create the prompt
        return f"""
Analyze this content and SEO data, then provide detailed improvement suggestions:

CONTENT PREVIEW:
{content_preview}

SEO ANALYSIS:
Overall Score: {analysis.get("overall_score", 0)}/10

Individual Scores:
{scores_formatted}

Key Issues:
{issues}

Current Recommendations:
{recommendations}

Based on this analysis, provide:
1. A prioritized list of 3-5 specific, actionable SEO improvements
2. Suggested rewrites for problematic sections (if needed)
3. Improved heading structure recommendations
4. Additional keyword suggestions that would complement the current ones

Format your response as a JSON object with these fields:
- suggestions: array of specific improvement suggestions
- improved_content: suggested rewrites for specific sections (if needed)
- improved_headings: suggested heading structure
- keyword_recommendations: additional keywords that would improve SEO
"""
        
    def analyze_keyword_competition(self, 
                                   keyword: str, 
                                   related_keywords: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Analyze the competition level for a keyword and related terms
        
        Args:
            keyword: Primary keyword to analyze
            related_keywords: Additional related keywords
            
        Returns:
            Dictionary with competition analysis
        """
        try:
            # For MVP, use AI to generate a competition analysis
            # In a production environment, this would connect to SEO APIs
            
            # Format the prompt
            prompt = f"""
Analyze the competition level for this primary keyword and related terms:

Primary Keyword: {keyword}
Related Keywords: {', '.join(related_keywords) if related_keywords else 'None provided'}

Provide a detailed competition analysis including:
1. Estimated competition level (low, medium, high)
2. Search volume category (low, medium, high)
3. Keyword difficulty score (0-100)
4. Content recommendations to rank for this keyword
5. Suggested long-tail alternatives with lower competition

Format your response as a structured JSON object.
"""
            
            # Get the model for SEO analysis
            model = openrouter.get_topic_model()
            
            # System message for SEO expertise
            system_message = """You are an expert SEO analyst with deep knowledge of keyword research.
Your analysis should be data-driven and realistic, reflecting current search trends.
Provide actionable insights for content creators looking to rank for these keywords."""
            
            # Get response from AI
            response = openrouter.generate_json_response(
                prompt=prompt,
                model=model,
                system_prompt=system_message,
                temperature=0.4
            )
            
            if not response:
                logger.error("Failed to get keyword competition analysis")
                return {
                    "keyword": keyword,
                    "competition_level": "unknown",
                    "estimated_difficulty": 50,
                    "recommendations": [
                        "Consider using long-tail variations of this keyword",
                        "Focus on high-quality, comprehensive content",
                        "Build backlinks from relevant sites"
                    ]
                }
            
            # Add the original keyword to the response
            response["keyword"] = keyword
            
            return response
            
        except Exception as e:
            logger.error(f"Error analyzing keyword competition: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Return basic fallback data
            return {
                "keyword": keyword,
                "competition_level": "unknown",
                "estimated_difficulty": 50,
                "recommendations": [
                    "Consider using long-tail variations of this keyword",
                    "Focus on high-quality, comprehensive content",
                    "Build backlinks from relevant sites"
                ]
            }

# Create a singleton instance
seo_analyzer = SEOAnalyzer()