"""
Script to fix token limits in the content generator
This will set more realistyczne limity tokenów for better stability
"""

import logging
import re
import sys

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_token_limits():
    """Fix token limits in the content generator for better stability"""
    
    # Path to content_generator.py
    content_generator_path = 'utils/writing/content_generator.py'
    
    try:
        # Read the content of the file
        with open(content_generator_path, 'r') as file:
            content = file.read()
        
        # Fix max_tokens limits - 8000 is too high and causes connection issues
        # Setting to 3000 which is more reasonable for most API providers
        pattern1 = r"max_tokens=8000  # Drastically increased for much longer paragraphs"
        replacement1 = r"max_tokens=3000  # Balanced limit for longer paragraphs while maintaining stability"
        content = re.sub(pattern1, replacement1, content)
        
        # Fix word count requirements in prompts - 1500-2000 may be too high for a single paragraph
        # Set to 800-1200 which is still substantial but more achievable
        pattern2 = r"at least 1500-2000 words"
        replacement2 = r"at least 800-1200 words"
        content = re.sub(pattern2, replacement2, content)
        
        # Update system prompt to be more realistic about length requirements
        pattern3 = r"Write very long, detailed paragraphs with at least 1500-2000 words total per section."
        replacement3 = r"Write substantial, detailed paragraphs with at least 800-1200 words total per section."
        content = re.sub(pattern3, replacement3, content)
        
        # Write the modified content back to the file
        with open(content_generator_path, 'w') as file:
            file.write(content)
        
        # Also fix timeout and error handling in OpenRouter client
        openrouter_client_path = 'utils/openrouter/client.py'
        with open(openrouter_client_path, 'r') as file:
            client_content = file.read()
        
        # Update timeout values to be more reasonable
        pattern4 = r'"timeout": 120'
        replacement4 = r'"timeout": 60'
        client_content = re.sub(pattern4, replacement4, client_content)
        
        # Also adjust the HTTP timeout
        pattern5 = r'timeout=120'
        replacement5 = r'timeout=60'
        client_content = re.sub(pattern5, replacement5, client_content)
        
        # Write the modified client content back to the file
        with open(openrouter_client_path, 'w') as file:
            file.write(client_content)
        
        logger.info(f"Successfully fixed token limits and timeouts for better stability")
        return True
    
    except Exception as e:
        logger.error(f"Error fixing token limits: {str(e)}")
        return False

if __name__ == "__main__":
    success = fix_token_limits()
    
    if success:
        print("Token limits fixed successfully for better stability")
    else:
        print("Failed to fix token limits")
        sys.exit(1)