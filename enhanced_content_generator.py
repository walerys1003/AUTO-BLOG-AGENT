"""
Enhanced Content Generator with Extra Features for Longer Paragraphs
"""

import logging
import sys
import os
import re

# Setup logger
logger = logging.getLogger(__name__)

def update_content_generator():
    """
    Updates the content_generator.py file to generate significantly longer content
    with more advanced configuration.
    """
    # Path to content_generator.py
    content_generator_path = 'utils/writing/content_generator.py'
    
    try:
        # Read the content of the file
        with open(content_generator_path, 'r') as file:
            content = file.read()
        
        # 1. Update the paragraph length in the intro prompt (current: 700-1000 words)
        pattern1 = r"6\. Write at least 700-1000 words with multiple paragraphs for readability"
        replacement1 = r"6. Write at least 1500-2000 words with multiple paragraphs for readability"
        content = re.sub(pattern1, replacement1, content)
        
        # 2. Update the paragraph length in the conclusion prompt
        pattern2 = r"6\. Write at least 700-1000 words with multiple paragraphs for readability"
        replacement2 = r"6. Write at least 1500-2000 words with multiple paragraphs for readability"
        content = re.sub(pattern2, replacement2, content)
        
        # 3. Update the paragraph length in the main content prompt
        pattern3 = r"7\. Ensure the section is comprehensive - MUST be at least 700-1000 words minimum"
        replacement3 = r"7. Ensure the section is comprehensive - MUST be at least 1500-2000 words minimum"
        content = re.sub(pattern3, replacement3, content)
        
        # 4. Increase the max_tokens for all OpenRouter API calls to 8000
        pattern4 = r"max_tokens=4000  # Increased for longer paragraphs"
        replacement4 = r"max_tokens=8000  # Drastically increased for much longer paragraphs"
        content = re.sub(pattern4, replacement4, content)
        
        # 5. Modify system prompt to emphasize length requirements
        pattern5 = r"You are an expert content writer specializing in creating comprehensive, engaging, well-structured blog content\."
        replacement5 = r"You are an expert content writer specializing in creating extremely comprehensive, engaging, well-structured blog content with significant length and depth."
        content = re.sub(pattern5, replacement5, content)
        
        # 6. Add stronger emphasis in the system prompt
        pattern6 = r"Provide ONLY the content in proper HTML format with <p> tags\. Do not include any explanations or notes\."
        replacement6 = r"Provide ONLY the content in proper HTML format with <p> tags. Do not include any explanations or notes. Write very long, detailed paragraphs with at least 1500-2000 words total per section."
        content = re.sub(pattern6, replacement6, content)
        
        # Write the modified content back to the file
        with open(content_generator_path, 'w') as file:
            file.write(content)
        
        logger.info(f"Successfully enhanced {content_generator_path} for much longer content generation")
        return True
    
    except Exception as e:
        logger.error(f"Error enhancing content_generator.py: {str(e)}")
        return False

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Execute the update
    success = update_content_generator()
    
    if success:
        print("Content generator enhanced successfully")
    else:
        print("Failed to enhance content generator")
        sys.exit(1)