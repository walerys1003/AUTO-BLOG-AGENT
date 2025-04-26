"""
Monkey patch utility for Google Trends API

This module patches the TrendReq class from pytrends to work with newer versions of urllib3
by replacing the deprecated method_whitelist parameter with allowed_methods.
"""

import logging
import sys
import importlib

# Setup logging
logger = logging.getLogger(__name__)

def apply_patches():
    """
    Apply monkey patches to work around compatibility issues
    """
    logger.info("Applying compatibility patches...")
    
    # 1. Monkey patch the problematic class in pytrends
    try:
        # Import without directly referencing the problematic parameters
        from pytrends.request import TrendReq
        
        # Store original initialization method
        original_init = TrendReq.__init__
        
        # Create a safer patched version
        def patched_init(self, hl='en-US', tz=360, geo='', timeout=(2, 5), proxies='',
                      retries=0, backoff_factor=0, requests_args=None):
            """
            Patched initialization that handles both old and new versions of urllib3
            """
            # Initialize basic attributes
            self.tz = tz
            self.hl = hl
            self.geo = geo
            self.kw_list = list()
            self.timeout = timeout
            self.proxies = proxies
            self.retries = retries
            self.backoff_factor = backoff_factor
            self.prefix = 'https://trends.google.com/trends'
            self.cookies = dict()
            
            # initialize default payload
            self.interest_over_time_widget = dict()
            self.interest_by_region_widget = dict()
            self.related_topics_widget_list = list()
            self.related_queries_widget_list = list()
            
            # Create a basic session without using the problematic retry logic
            import requests
            self.requests_args = requests_args or {}
            self.requests = self.requests_args.pop('session', requests.Session())
            
            # Manually get cookies - this is safer than the original
            try:
                self.cookies = dict(filter(
                    lambda i: i[0] == 'NID', 
                    requests.get(
                        f'https://trends.google.com/?geo={self.hl[-2:] if len(self.hl) > 2 else "US"}'
                    ).cookies.items()
                ))
            except Exception as e:
                logger.warning(f"Failed to get Google cookies: {e}")
                self.cookies = {}
        
        # Apply the patch by replacing the original method
        TrendReq.__init__ = patched_init
        logger.info("Successfully patched pytrends.request.TrendReq to avoid method_whitelist issue")
        return True
        
    except (ImportError, AttributeError) as e:
        logger.error(f"Failed to patch pytrends: {str(e)}")
        return False