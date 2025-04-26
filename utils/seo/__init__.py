"""
SEO Module for Google Trends and SerpAPI integration

This module provides functionality for:
1. Fetching trending topics from Google Trends
2. Getting related questions from SerpAPI
3. Generating blog topics based on SEO data
4. Scheduling daily SEO analysis
"""
import logging

# Setup logging
logger = logging.getLogger(__name__)

# Apply monkey patches to fix compatibility issues
from . import monkey_patch
if monkey_patch.apply_patches():
    logger.info("Successfully applied SEO module patches")
else:
    logger.warning("Failed to apply some SEO module patches")

# Make all modules available through the package
from . import trends
from . import serp
from . import topic_generator
from . import scheduler
from . import analyzer

# Initialize SEO module when imported
# Note: This is commented out to prevent circular imports
# To initialize, call analyzer.initialize_seo_module() from main.py
# analyzer.initialize_seo_module()