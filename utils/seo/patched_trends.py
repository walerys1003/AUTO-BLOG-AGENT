"""
Patched Google Trends Module

This module provides a patched version of TrendReq to handle the deprecated method_whitelist
parameter in newer versions of urllib3.
"""
import logging
import requests
from pytrends.request import TrendReq as OriginalTrendReq
from requests.packages.urllib3.util.retry import Retry

# Setup logging
logger = logging.getLogger(__name__)

class PatchedTrendReq(OriginalTrendReq):
    """
    Patched version of TrendReq that uses allowed_methods instead of method_whitelist
    in the Retry configuration.
    """
    
    def __init__(self, hl='en-US', tz=360, geo='', timeout=(2, 5), proxies='',
                retries=0, backoff_factor=0, requests_args=None):
        """
        Initialize request parameters and headers
        """
        # Override parent initialization to patch the method_whitelist
        self.tz = tz
        self.hl = hl
        self.geo = geo
        self.kw_list = list()
        self.timeout = timeout
        self.proxies = proxies
        self.retries = retries
        self.backoff_factor = backoff_factor
        self.prefix = 'https://trends.google.com/trends'
        self.cookies = dict(filter(lambda i: i[0] == 'NID', requests.get(
            'https://trends.google.com/?geo={geo}'.format(geo=hl[-2:])
        ).cookies.items()))
        # intialize default payload
        self.interest_over_time_widget = dict()
        self.interest_by_region_widget = dict()
        self.related_topics_widget_list = list()
        self.related_queries_widget_list = list()
        
        # Create a custom requests session with retry configuration
        self.requests_args = requests_args or {}
        self.requests = requests.Session()
        if retries > 0:
            # Use allowed_methods instead of method_whitelist in Retry configuration
            retry_obj = Retry(total=retries,
                             connect=retries,
                             read=retries,
                             status=retries,
                             backoff_factor=backoff_factor,
                             status_forcelist=[500, 503, 504],
                             allowed_methods=frozenset(['GET', 'POST']))  # Updated parameter name
            
            self.requests.mount(
                'https://',
                requests.adapters.HTTPAdapter(max_retries=retry_obj)
            )