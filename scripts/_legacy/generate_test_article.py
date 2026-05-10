"""
Script to generate a test article using the modified content generator
"""

import os
import sys
import logging
import json
from flask import Flask
from app import app, db
import utils.writing.content_generator as content_generator
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_test_article():
    """Generate a test article using the paragraph-based approach"""
    with app.app_context():
        logger.info("Generating test article with enhanced content generator")
        
        # Topic for the article
        topic = "Effective Strategies for Time Management in the Digital Age"
        
        # Keywords for the article
        keywords = ["time management", "productivity", "digital age", "work-life balance", "planning"]
        
        # Generate article with 4 paragraphs
        article_data = content_generator.generate_article_by_paragraphs(
            topic=topic,
            keywords=keywords,
            style="informative",
            paragraph_count=4
        )
        
        # Save the result to a file for analysis
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"test_article_{timestamp}.html"
        
        with open(output_path, "w") as f:
            f.write("<html><head><title>Test Article</title></head><body>")
            f.write(f"<h1>Test Article: {topic}</h1>")
            f.write("<div>Article generated using enhanced content generator with paragraph-based approach</div>")
            f.write("<div>Keywords: " + ", ".join(keywords) + "</div>")
            f.write("<hr>")
            f.write(article_data.get("content", "No content generated"))
            f.write("</body></html>")
        
        logger.info(f"Article generated and saved to {output_path}")
        
        # Also save the raw article data
        with open(f"test_article_data_{timestamp}.json", "w") as f:
            json.dump(article_data, f, indent=2)
        
        return article_data

if __name__ == "__main__":
    # Run the test generator
    article = generate_test_article()
    
    # Print some stats
    content = article.get("content", "")
    word_count = len(content.split())
    paragraph_count = content.count("<p>")
    
    print(f"Article generated with {word_count} words and {paragraph_count} paragraphs")
    print(f"Meta description length: {len(article.get('meta_description', ''))}")
    print(f"Excerpt length: {len(article.get('excerpt', ''))}")
    print(f"Number of tags: {len(article.get('tags', []))}")