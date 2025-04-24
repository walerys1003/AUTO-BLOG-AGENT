import logging
import json
import re
from typing import Dict, List, Any, Optional, Tuple, Union
from bs4 import BeautifulSoup
from utils.openrouter import openrouter
import traceback

# Setup logging
logger = logging.getLogger(__name__)

class WritingAssistant:
    """
    Contextual AI writing assistant for content refinement
    
    This class provides methods to improve and refine content
    using AI-powered suggestions and enhancements.
    """
    
    def __init__(self):
        """Initialize the writing assistant"""
        # Available writing styles/tones
        self.available_tones = [
            "professional",
            "conversational",
            "educational",
            "persuasive",
            "entertaining",
            "casual",
            "formal",
            "technical"
        ]
        
        # Available content improvement types
        self.improvement_types = [
            "style_and_tone",
            "clarity",
            "readability",
            "engagement",
            "grammar_and_spelling",
            "fact_check",
            "vocabulary",
            "structure",
            "comprehensive"
        ]
    
    def improve_content(self, 
                       content: str, 
                       target_tone: str = "professional",
                       improvement_type: str = "comprehensive",
                       keywords: Optional[List[str]] = None,
                       context: Optional[str] = None) -> Dict[str, Any]:
        """
        Improve content based on specified parameters
        
        Args:
            content: The content to improve
            target_tone: Desired writing tone
            improvement_type: Type of improvement to focus on
            keywords: Keywords to maintain/emphasize
            context: Additional context for the improvements
            
        Returns:
            Dictionary with improved content and explanation
        """
        try:
            # Validate parameters
            if target_tone not in self.available_tones:
                target_tone = "professional"
                
            if improvement_type not in self.improvement_types:
                improvement_type = "comprehensive"
            
            # Limit content length to prevent token overflow
            if len(content) > 15000:
                logger.warning("Content too long, truncating for improvement")
                content = content[:15000] + "..."
            
            # Format prompt for content improvement
            prompt = self._format_improvement_prompt(
                content, target_tone, improvement_type, keywords, context
            )
            
            # Get the appropriate model - use the more powerful model for better quality
            model = openrouter.get_content_model()
            
            # System message for writing expertise
            system_message = f"""You are an expert writing assistant specializing in content refinement.
Your goal is to improve the quality, clarity, and effectiveness of the content while
maintaining its core message and purpose. Focus on making the content more engaging,
readable, and aligned with the desired tone ({target_tone}) and improvement goal ({improvement_type}).
Preserve the factual information and core arguments while enhancing the delivery."""
            
            # Get response from AI
            response = openrouter.generate_json_response(
                prompt=prompt,
                model=model,
                system_prompt=system_message,
                temperature=0.4
            )
            
            if not response:
                logger.error("Failed to improve content")
                return {
                    "improved_content": content,
                    "explanation": "Unable to generate improvements at this time.",
                    "success": False
                }
            
            # Format and return the improved content
            return {
                "improved_content": response.get("improved_content", content),
                "explanation": response.get("explanation", "Content improved according to requested parameters."),
                "changes": response.get("changes", []),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error improving content: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Return original content with error
            return {
                "improved_content": content,
                "explanation": f"Error improving content: {str(e)}",
                "success": False
            }
    
    def _format_improvement_prompt(self, 
                                  content: str, 
                                  tone: str, 
                                  improvement_type: str,
                                  keywords: Optional[List[str]] = None,
                                  context: Optional[str] = None) -> str:
        """Format prompt for content improvement"""
        # Get improvement instructions based on type
        improvement_instructions = self._get_improvement_instructions(improvement_type)
        
        # Format keywords if provided
        keywords_text = ""
        if keywords and len(keywords) > 0:
            keywords_text = f"Important keywords to maintain/emphasize: {', '.join(keywords)}"
        
        # Format context if provided
        context_text = ""
        if context:
            context_text = f"Additional context: {context}"
        
        # Create the prompt
        return f"""
Improve the following content to make it more effective and engaging.

CONTENT TO IMPROVE:
{content}

IMPROVEMENT PARAMETERS:
Target tone: {tone}
Improvement focus: {improvement_type}
{keywords_text}
{context_text}

SPECIFIC IMPROVEMENT INSTRUCTIONS:
{improvement_instructions}

Please provide:
1. The improved content
2. A brief explanation of the changes made
3. A list of the key improvements

Format your response as a JSON object with these fields:
- improved_content: the revised content
- explanation: summary of improvements
- changes: list of key changes made
"""
    
    def _get_improvement_instructions(self, improvement_type: str) -> str:
        """Get specific instructions based on improvement type"""
        instructions = {
            "style_and_tone": """
- Adjust the writing style to be more consistent with the target tone
- Replace generic language with more tone-appropriate vocabulary
- Modify sentence structures to better match the desired voice
- Ensure transitions flow naturally within the chosen style
- Maintain a consistent voice throughout the entire piece
""",
            "clarity": """
- Simplify complex sentences that might confuse readers
- Replace jargon or technical terms with clearer alternatives (unless writing for experts)
- Ensure each paragraph has a clear main point
- Add clarifying examples where concepts may be difficult to understand
- Use more precise language to avoid ambiguity
""",
            "readability": """
- Break up long paragraphs into more digestible chunks
- Vary sentence length (mix short and medium sentences)
- Add subheadings to organize content more effectively
- Use bullet points or numbered lists for series of items
- Add transition phrases to improve flow between sections
""",
            "engagement": """
- Add compelling questions or thought-provoking statements
- Include relevant anecdotes or scenarios readers can relate to
- Use more vivid language and sensory details
- Add hooks throughout the content to maintain interest
- Incorporate direct reader address where appropriate
""",
            "grammar_and_spelling": """
- Correct any grammatical errors
- Fix spelling mistakes
- Ensure proper punctuation throughout
- Check for consistent tense usage
- Review pronoun consistency and clarity
""",
            "fact_check": """
- Verify that factual claims are accurate
- Ensure statistics or data are presented correctly
- Add qualification to statements that aren't universally true
- Remove or rewrite any potentially misleading information
- Note where additional references might be needed
""",
            "vocabulary": """
- Replace generic words with more precise, descriptive alternatives
- Ensure vocabulary is appropriate for the target audience
- Eliminate redundant language and unnecessary repetition
- Add industry-appropriate terminology where it adds value
- Ensure consistent terminology use throughout
""",
            "structure": """
- Reorganize content for better logical flow
- Ensure a strong opening that clearly introduces the topic
- Add clear topic sentences at the beginning of paragraphs
- Improve the conclusion to reinforce key points
- Ensure appropriate transitions between topics and sections
""",
            "comprehensive": """
- Improve overall readability and flow
- Enhance clarity and precision of language
- Adjust style to match the target tone
- Fix grammatical issues and improve sentence structure
- Reorganize content if needed for better logical progression
- Add engaging elements while maintaining the core message
- Ensure keywords are appropriately incorporated
- Check for and improve potential factual or logical issues
"""
        }
        
        return instructions.get(improvement_type, instructions["comprehensive"])
    
    def suggest_improvements(self, 
                            content: str, 
                            focus_areas: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Analyze content and suggest improvements without changing the content
        
        Args:
            content: The content to analyze
            focus_areas: Optional areas to focus analysis on
            
        Returns:
            Dictionary with improvement suggestions
        """
        try:
            # Initialize valid_areas variable
            valid_areas = ["clarity", "engagement", "structure"]
            
            # Use default focus areas if none provided
            if not focus_areas or len(focus_areas) == 0:
                focus_areas = valid_areas
            else:
                # Filter to valid focus areas
                valid_areas = [area for area in focus_areas if area in self.improvement_types]
                if len(valid_areas) == 0:
                    valid_areas = ["clarity", "engagement", "structure"]
            
            # Limit content length
            if len(content) > 15000:
                logger.warning("Content too long, truncating for analysis")
                content = content[:15000] + "..."
            
            # Format the prompt
            prompt = f"""
Analyze this content and provide specific improvement suggestions:

CONTENT:
{content}

Focus on these areas:
{', '.join(valid_areas)}

For each focus area:
1. Identify 2-3 specific instances where improvements can be made
2. Provide actionable suggestions for each instance
3. Explain why these changes would make the content more effective

Also provide an overall assessment of the content's strengths and weaknesses.

Format your response as a JSON object with these fields:
- suggestions: object with focus areas as keys, each containing an array of specific suggestions
- strengths: array of content strengths
- weaknesses: array of content weaknesses
- overall_assessment: brief summary evaluation
"""
            
            # Get the model
            model = openrouter.get_topic_model()
            
            # System message for analysis expertise
            system_message = """You are an expert content analyst and writing coach
specializing in actionable feedback. Your suggestions should be specific, contextual,
and immediately applicable. Focus on concrete examples from the text
rather than general advice. Use a supportive, constructive tone that acknowledges
strengths while offering clear paths to improvement."""
            
            # Get response from AI
            response = openrouter.generate_json_response(
                prompt=prompt,
                model=model,
                system_prompt=system_message,
                temperature=0.3
            )
            
            if not response:
                logger.error("Failed to generate improvement suggestions")
                return {
                    "suggestions": {area: ["No specific suggestions available"] for area in valid_areas},
                    "overall_assessment": "Unable to analyze content at this time."
                }
            
            # Ensure response has required fields
            if not response.get("suggestions"):
                response["suggestions"] = {area: ["No specific suggestions available"] for area in valid_areas}
            
            if not response.get("overall_assessment"):
                response["overall_assessment"] = "Content analyzed. See specific suggestions for improvement areas."
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating improvement suggestions: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Return basic fallback
            return {
                "suggestions": {area: ["No specific suggestions available"] for area in valid_areas},
                "overall_assessment": f"Error analyzing content: {str(e)}"
            }
    
    def rewrite_section(self, 
                       original_text: str, 
                       instructions: str,
                       context: Optional[str] = None,
                       tone: str = "professional") -> Dict[str, str]:
        """
        Rewrite a specific section of content based on instructions
        
        Args:
            original_text: The original text to rewrite
            instructions: Specific rewriting instructions
            context: Optional context about the overall content
            tone: Desired writing tone
            
        Returns:
            Dictionary with rewritten section and explanation
        """
        try:
            # Validate tone
            if tone not in self.available_tones:
                tone = "professional"
            
            # Format the prompt
            prompt = f"""
Rewrite this content section according to the provided instructions:

ORIGINAL SECTION:
{original_text}

REWRITING INSTRUCTIONS:
{instructions}

DESIRED TONE:
{tone}
"""
            
            # Add context if provided
            if context:
                prompt += f"""
CONTENT CONTEXT:
{context}
"""
            
            prompt += """
Please provide:
1. The rewritten section
2. A brief explanation of how the rewrite addresses the instructions

Format your response as a JSON object with these fields:
- rewritten_text: the revised content section
- explanation: brief explanation of the changes
"""
            
            # Get the model - use more powerful model for quality rewrites
            model = openrouter.get_content_model()
            
            # System message
            system_message = f"""You are an expert content rewriter specializing in
targeted content revisions. Your goal is to rewrite the provided section 
according to the specific instructions while maintaining factual accuracy 
and improving overall quality. Match the {tone} tone throughout."""
            
            # Get response from AI
            response = openrouter.generate_json_response(
                prompt=prompt,
                model=model,
                system_prompt=system_message,
                temperature=0.4
            )
            
            if not response:
                logger.error("Failed to rewrite section")
                return {
                    "rewritten_text": original_text,
                    "explanation": "Unable to rewrite section at this time."
                }
            
            # Ensure response has required fields
            return {
                "rewritten_text": response.get("rewritten_text", original_text),
                "explanation": response.get("explanation", "Section rewritten according to instructions.")
            }
            
        except Exception as e:
            logger.error(f"Error rewriting section: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Return original with error
            return {
                "rewritten_text": original_text,
                "explanation": f"Error rewriting section: {str(e)}"
            }
    
    def generate_content_variations(self, 
                                  content: str, 
                                  variation_count: int = 3,
                                  instruction: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Generate variations of a piece of content
        
        Args:
            content: The original content
            variation_count: Number of variations to generate
            instruction: Optional specific instruction for variations
            
        Returns:
            List of content variations with explanations
        """
        try:
            # Limit number of variations
            variation_count = min(5, max(1, variation_count))
            
            # Default instruction if none provided
            if not instruction:
                instruction = "Create variations that maintain the same key information but use different phrasing, structure, or tone."
            
            # Format the prompt
            prompt = f"""
Generate {variation_count} different variations of this content:

ORIGINAL CONTENT:
{content}

VARIATION INSTRUCTIONS:
{instruction}

For each variation:
1. Create a complete rewrite that follows the instructions
2. Provide a brief explanation of how this variation differs from the original

Format your response as a JSON array of objects, with each object containing:
- variation: the rewritten content
- explanation: brief explanation of how it differs
"""
            
            # Get the model
            model = openrouter.get_content_model()
            
            # System message
            system_message = """You are an expert content creator specializing in
generating diverse variations of text while maintaining the core message.
Your variations should be substantively different from each other in structure,
style, or approach while preserving the essential information."""
            
            # Get response from AI
            response = openrouter.generate_json_response(
                prompt=prompt,
                model=model,
                system_prompt=system_message,
                temperature=0.7  # Higher temperature for more variation
            )
            
            if not response or not isinstance(response, list):
                logger.error("Failed to generate content variations")
                return [{
                    "variation": content,
                    "explanation": "Unable to generate variations at this time."
                }]
            
            # Return the variations, ensuring we don't exceed requested count
            return response[:variation_count]
            
        except Exception as e:
            logger.error(f"Error generating content variations: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Return original as fallback
            return [{
                "variation": content,
                "explanation": f"Error generating variations: {str(e)}"
            }]
    
    def check_grammar_and_style(self, content: str) -> Dict[str, Any]:
        """
        Check content for grammar, style, and readability issues
        
        Args:
            content: The content to check
            
        Returns:
            Dictionary with issues and suggestions
        """
        try:
            # Format the prompt
            prompt = f"""
Analyze this content for grammar, style, and readability issues:

CONTENT:
{content}

Please provide:
1. Grammar issues (spelling, punctuation, syntax errors)
2. Style issues (passive voice, wordiness, clichés, etc.)
3. Readability assessment (reading level, sentence structure, paragraph flow)
4. Specific corrections for each identified issue
5. Overall recommendations for improvement

Format your response as a JSON object with these fields:
- grammar_issues: array of objects containing {{"issue": "description", "correction": "suggested fix", "location": "context"}}
- style_issues: array of objects with the same structure
- readability: object with {{"score": 1-10 rating, "level": "description", "issues": array of issues}}
- recommendations: array of overall improvement suggestions
"""
            
            # Get the model
            model = openrouter.get_topic_model()
            
            # System message
            system_message = """You are an expert editor and proofreader specializing in
identifying and correcting writing issues. Your analysis should be thorough,
specific, and actionable. For each issue, provide the exact correction
and enough context to locate it in the original text."""
            
            # Get response from AI
            response = openrouter.generate_json_response(
                prompt=prompt,
                model=model,
                system_prompt=system_message,
                temperature=0.3
            )
            
            if not response:
                logger.error("Failed to check grammar and style")
                return {
                    "grammar_issues": [],
                    "style_issues": [],
                    "readability": {"score": 5, "level": "Unknown", "issues": []},
                    "recommendations": ["Unable to analyze content at this time."]
                }
            
            # Return the analysis
            return response
            
        except Exception as e:
            logger.error(f"Error checking grammar and style: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Return empty analysis
            return {
                "grammar_issues": [],
                "style_issues": [],
                "readability": {"score": 5, "level": "Unknown", "issues": []},
                "recommendations": [f"Error analyzing content: {str(e)}"]
            }

# Create a singleton instance
writing_assistant = WritingAssistant()