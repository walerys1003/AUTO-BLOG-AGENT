import os
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union

from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
    RunReportResponse,
)

logger = logging.getLogger(__name__)

class GA4Client:
    """Client for Google Analytics 4 API"""
    
    def __init__(self, measurement_id: Optional[str] = None, api_secret: Optional[str] = None):
        """
        Initialize GA4 client
        
        Args:
            measurement_id: GA4 measurement ID (G-XXXXXXXXXX)
            api_secret: GA4 API secret
        """
        self.measurement_id = measurement_id or os.environ.get('GA4_MEASUREMENT_ID')
        self.api_secret = api_secret or os.environ.get('GA4_API_SECRET')
        self.client = None
        
        if not self.measurement_id:
            logger.warning("GA4_MEASUREMENT_ID not set. Some functionality may be limited.")
        
        if not self.api_secret:
            logger.warning("GA4_API_SECRET not set. Some functionality may be limited.")
        
        try:
            # Initialize analytics data client
            self.client = BetaAnalyticsDataClient()
        except Exception as e:
            logger.error(f"Error initializing GA4 client: {str(e)}")
            self.client = None
    
    def get_tracking_code(self, custom_dimension_ids: Optional[List[str]] = None) -> str:
        """
        Get GA4 tracking code
        
        Args:
            custom_dimension_ids: Optional list of custom dimension IDs
            
        Returns:
            GA4 tracking code as string
        """
        if not self.measurement_id:
            return "<!-- GA4 tracking code not available: Measurement ID not set -->"
        
        custom_dims = ""
        if custom_dimension_ids:
            custom_dims = "\n" + "\n".join([
                f"  gtag('set', 'user_properties', {{'custom_dim_{i+1}': '{dim_id}'}});" 
                for i, dim_id in enumerate(custom_dimension_ids)
            ])
        
        return f"""
<!-- Google Analytics 4 (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id={self.measurement_id}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{self.measurement_id}');{custom_dims}
</script>
"""
    
    def send_event(self, event_name: str, params: Dict[str, Any], client_id: str = '555') -> bool:
        """
        Send event to GA4 using Measurement Protocol
        
        Args:
            event_name: Name of the event
            params: Event parameters
            client_id: Client ID (default: '555')
            
        Returns:
            True if event was sent successfully, False otherwise
        """
        if not self.measurement_id or not self.api_secret:
            logger.error("Cannot send event: Measurement ID or API Secret not set")
            return False
        
        import requests
        
        url = f"https://www.google-analytics.com/mp/collect?measurement_id={self.measurement_id}&api_secret={self.api_secret}"
        
        payload = {
            "client_id": client_id,
            "events": [{
                "name": event_name,
                "params": params
            }]
        }
        
        try:
            response = requests.post(url, data=json.dumps(payload))
            if response.status_code == 204:
                logger.info(f"Event {event_name} sent successfully to GA4")
                return True
            else:
                logger.error(f"Failed to send event to GA4: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error sending event to GA4: {str(e)}")
            return False
    
    def get_report(
        self, 
        property_id: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        metrics: List[str],
        dimensions: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10000
    ) -> Dict[str, Any]:
        """
        Get report from GA4
        
        Args:
            property_id: GA4 property ID
            start_date: Start date (YYYY-MM-DD or datetime)
            end_date: End date (YYYY-MM-DD or datetime)
            metrics: List of metrics (e.g., 'activeUsers', 'sessions')
            dimensions: Optional list of dimensions (e.g., 'date', 'country')
            filters: Optional filters
            limit: Row limit (default: 10000)
            
        Returns:
            Report data as dictionary
        """
        if not self.client:
            logger.error("GA4 client not initialized")
            return {"error": "GA4 client not initialized"}
        
        # Convert datetime to string if needed
        if isinstance(start_date, datetime):
            start_date = start_date.strftime('%Y-%m-%d')
        if isinstance(end_date, datetime):
            end_date = end_date.strftime('%Y-%m-%d')
        
        try:
            # Create dimensions list
            dimension_list = []
            if dimensions:
                dimension_list = [Dimension(name=dim) for dim in dimensions]
            
            # Create metrics list
            metric_list = [Metric(name=metric) for metric in metrics]
            
            # Build request
            request = RunReportRequest(
                property=f"properties/{property_id}",
                date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
                dimensions=dimension_list,
                metrics=metric_list,
                limit=limit
            )
            
            # Run report
            response = self.client.run_report(request)
            
            # Process response
            result = {
                "rows": [],
                "row_count": response.row_count,
                "metadata": {
                    "metrics": [metric.name for metric in response.metric_headers],
                    "dimensions": [dim.name for dim in response.dimension_headers] if dimensions else []
                }
            }
            
            # Extract data
            for row in response.rows:
                dimension_values = {}
                if dimensions:
                    for i, dim in enumerate(response.dimension_headers):
                        dimension_values[dim.name] = row.dimension_values[i].value
                
                metric_values = {}
                for i, metric in enumerate(response.metric_headers):
                    metric_values[metric.name] = row.metric_values[i].value
                
                result_row = {**dimension_values, **metric_values}
                result["rows"].append(result_row)
            
            return result
        
        except Exception as e:
            logger.error(f"Error getting report from GA4: {str(e)}")
            return {"error": str(e)}
    
    def get_page_metrics(
        self,
        property_id: str,
        page_path: str,
        start_date: Union[str, datetime] = None,
        end_date: Union[str, datetime] = None,
        include_demographics: bool = False
    ) -> Dict[str, Any]:
        """
        Get metrics for a specific page
        
        Args:
            property_id: GA4 property ID
            page_path: Page path (e.g., '/blog/post-1')
            start_date: Start date (default: 30 days ago)
            end_date: End date (default: today)
            include_demographics: Whether to include demographic data
            
        Returns:
            Page metrics as dictionary
        """
        # Set default dates if not provided
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Define metrics and dimensions
        metrics = [
            'screenPageViews',
            'totalUsers',
            'averageSessionDuration',
            'bounceRate',
            'engagementRate'
        ]
        
        dimensions = ['pagePath']
        if include_demographics:
            dimensions.extend(['country', 'deviceCategory', 'browser'])
        
        try:
            # Get report
            report = self.get_report(
                property_id=property_id,
                start_date=start_date,
                end_date=end_date,
                metrics=metrics,
                dimensions=dimensions,
                filters={'pagePath': page_path}
            )
            
            if 'error' in report:
                return report
            
            # Process page data
            page_data = {
                'page_views': 0,
                'unique_visitors': 0,
                'avg_time_on_page': 0,
                'bounce_rate': 0,
                'engagement_rate': 0,
                'demographics': {},
                'raw_data': report
            }
            
            # Extract metrics from first matching row
            for row in report.get('rows', []):
                if row.get('pagePath') == page_path:
                    page_data['page_views'] = int(row.get('screenPageViews', 0))
                    page_data['unique_visitors'] = int(row.get('totalUsers', 0))
                    page_data['avg_time_on_page'] = float(row.get('averageSessionDuration', 0))
                    page_data['bounce_rate'] = float(row.get('bounceRate', 0)) * 100  # Convert to percentage
                    page_data['engagement_rate'] = float(row.get('engagementRate', 0)) * 100  # Convert to percentage
                    break
            
            # Process demographics if included
            if include_demographics and report.get('rows'):
                demographics = {
                    'countries': {},
                    'devices': {},
                    'browsers': {}
                }
                
                for row in report.get('rows', []):
                    if row.get('pagePath') == page_path:
                        # Countries
                        country = row.get('country', 'Unknown')
                        if country in demographics['countries']:
                            demographics['countries'][country] += int(row.get('screenPageViews', 0))
                        else:
                            demographics['countries'][country] = int(row.get('screenPageViews', 0))
                        
                        # Devices
                        device = row.get('deviceCategory', 'Unknown')
                        if device in demographics['devices']:
                            demographics['devices'][device] += int(row.get('screenPageViews', 0))
                        else:
                            demographics['devices'][device] = int(row.get('screenPageViews', 0))
                        
                        # Browsers
                        browser = row.get('browser', 'Unknown')
                        if browser in demographics['browsers']:
                            demographics['browsers'][browser] += int(row.get('screenPageViews', 0))
                        else:
                            demographics['browsers'][browser] = int(row.get('screenPageViews', 0))
                
                page_data['demographics'] = demographics
            
            return page_data
        
        except Exception as e:
            logger.error(f"Error getting page metrics: {str(e)}")
            return {"error": str(e)}

    def get_top_pages(
        self,
        property_id: str,
        start_date: Union[str, datetime] = None,
        end_date: Union[str, datetime] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get top pages by page views
        
        Args:
            property_id: GA4 property ID
            start_date: Start date (default: 30 days ago)
            end_date: End date (default: today)
            limit: Number of pages to return
            
        Returns:
            List of top pages with metrics
        """
        # Set default dates if not provided
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        try:
            # Get report
            report = self.get_report(
                property_id=property_id,
                start_date=start_date,
                end_date=end_date,
                metrics=['screenPageViews', 'totalUsers', 'averageSessionDuration'],
                dimensions=['pagePath', 'pageTitle'],
                limit=limit
            )
            
            if 'error' in report:
                return []
            
            # Process and sort pages by views
            pages = []
            for row in report.get('rows', []):
                pages.append({
                    'path': row.get('pagePath', ''),
                    'title': row.get('pageTitle', ''),
                    'views': int(row.get('screenPageViews', 0)),
                    'visitors': int(row.get('totalUsers', 0)),
                    'avg_time': float(row.get('averageSessionDuration', 0))
                })
            
            # Sort by views descending
            pages.sort(key=lambda x: x['views'], reverse=True)
            
            return pages[:limit]
        
        except Exception as e:
            logger.error(f"Error getting top pages: {str(e)}")
            return []