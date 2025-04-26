"""
Monkey patch utility for Google Trends API

This module patches the TrendReq class from pytrends to work with newer versions of urllib3
by replacing the deprecated method_whitelist parameter with allowed_methods.
"""

import logging
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

# Setup logging
logger = logging.getLogger(__name__)

def apply_patches():
    """
    Apply monkey patches to work around compatibility issues
    """
    logger.info("Applying compatibility patches...")
    # Patch pytrends TrendReq to use allowed_methods instead of method_whitelist
    try:
        import pytrends.request
        original_init = pytrends.request.TrendReq.__init__
        
        def patched_init(self, hl='en-US', tz=360, geo='', timeout=(2, 5), proxies='',
                        retries=0, backoff_factor=0, requests_args=None):
            """Patched initialization with fixed retry params"""
            # Call all original init except for setting up retry session
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
            
            # Use safer requests_args implementation
            self.requests_args = requests_args or {}
            self.requests = self.requests_args.pop('session', self.get_new_session())
            
            # Get Google cookies
            self.get_google_cookies()
        
        def get_new_session(self):
            """Get a new custom requests session with updated retry config"""
            import requests
            session = requests.Session()
            
            # Only set up retries if requested
            if hasattr(self, 'retries') and self.retries > 0:
                # Use allowed_methods instead of method_whitelist in Retry configuration
                retry_obj = Retry(
                    total=self.retries,
                    connect=self.retries,
                    read=self.retries,
                    status=self.retries,
                    backoff_factor=self.backoff_factor,
                    status_forcelist=[500, 503, 504],
                    allowed_methods=frozenset(['GET', 'POST'])  # Use new parameter name
                )
                
                session.mount(
                    'https://',
                    HTTPAdapter(max_retries=retry_obj)
                )
            
            return session
        
        # Add the new method
        pytrends.request.TrendReq.get_new_session = get_new_session
        
        # Replace the init method
        pytrends.request.TrendReq.__init__ = patched_init
        
        logger.info("Successfully patched pytrends.request.TrendReq to use allowed_methods")
        return True
        
    except (ImportError, AttributeError) as e:
        logger.error(f"Failed to patch pytrends: {str(e)}")
        return False