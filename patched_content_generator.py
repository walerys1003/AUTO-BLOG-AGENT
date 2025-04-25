import logging
import sys
import os
import re
import importlib.util
import inspect

# Setup logger
logger = logging.getLogger(__name__)

def patch_content_generator():
    """Patch the content_generator.py file to use increased max_tokens for all calls"""
    
    # Path to content_generator.py
    content_generator_path = 'utils/writing/content_generator.py'
    
    try:
        # Read the content of the file
        with open(content_generator_path, 'r') as file:
            content = file.read()
        
        # Replace the max_tokens=1000 in _generate_paragraph function
        pattern1 = r"(content = openrouter\.generate_completion\(\s+prompt=user_prompt,\s+model=model,\s+system_prompt=system_prompt,\s+temperature=0\.7,\s+max_tokens=)1000"
        replacement1 = r"\g<1>4000  # Increased for longer paragraphs"
        content = re.sub(pattern1, replacement1, content)
        
        # Replace the max_tokens=1000 in generate_article function
        pattern2 = r"(content = openrouter\.generate_completion\(\s+prompt=user_prompt,\s+model=model,\s+system_prompt=system_prompt,\s+temperature=0\.7,\s+max_tokens=)1000"
        replacement2 = r"\g<1>4000  # Increased for longer paragraphs"
        content = re.sub(pattern2, replacement2, content)
        
        # Write the modified content back to the file
        with open(content_generator_path, 'w') as file:
            file.write(content)
        
        logger.info(f"Successfully patched {content_generator_path} to use max_tokens=4000")
        return True
    
    except Exception as e:
        logger.error(f"Error patching content_generator.py: {str(e)}")
        return False

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Execute the patch
    success = patch_content_generator()
    
    if success:
        print("Content generator patched successfully")
    else:
        print("Failed to patch content generator")
        sys.exit(1)