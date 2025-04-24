"""
EmailOctopus API client for newsletter management
"""
import os
import json
import logging
import requests
from typing import Dict, List, Any, Optional, Union

logger = logging.getLogger(__name__)

class EmailOctopusClient:
    """Client for EmailOctopus API"""
    
    def __init__(self, api_key: Optional[str] = None, list_id: Optional[str] = None):
        """
        Initialize EmailOctopus client
        
        Args:
            api_key: EmailOctopus API key
            list_id: Default list ID for operations
        """
        self.api_key = api_key or os.environ.get('EMAILOCTOPUS_API_KEY')
        self.list_id = list_id or os.environ.get('EMAILOCTOPUS_LIST_ID')
        self.base_url = "https://emailoctopus.com/api/1.6"
        
        if not self.api_key:
            logger.warning("EmailOctopus API key not set. Functionality will be limited.")
            
        if not self.list_id:
            logger.warning("EmailOctopus list ID not set. Some operations will require explicit list_id parameter.")
    
    def get_lists(self) -> Dict[str, Any]:
        """
        Get all lists in the account
        
        Returns:
            API response with lists data
        """
        endpoint = f"{self.base_url}/lists"
        params = {'api_key': self.api_key}
        
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting lists: {str(e)}")
            return {"error": str(e)}
    
    def get_list(self, list_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get information about a specific list
        
        Args:
            list_id: List ID (defaults to self.list_id)
            
        Returns:
            API response with list data
        """
        list_id = list_id or self.list_id
        if not list_id:
            return {"error": "List ID not provided"}
        
        endpoint = f"{self.base_url}/lists/{list_id}"
        params = {'api_key': self.api_key}
        
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting list details: {str(e)}")
            return {"error": str(e)}
    
    def add_subscriber(
        self, 
        email: str, 
        fields: Optional[Dict[str, str]] = None,
        list_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        status: str = "SUBSCRIBED"
    ) -> Dict[str, Any]:
        """
        Add a subscriber to a list
        
        Args:
            email: Subscriber email
            fields: Optional fields like first_name, last_name
            list_id: List ID (defaults to self.list_id)
            tags: Optional tags to apply to the contact
            status: Status (SUBSCRIBED, UNSUBSCRIBED, PENDING)
            
        Returns:
            API response with subscription status
        """
        list_id = list_id or self.list_id
        if not list_id:
            return {"error": "List ID not provided"}
        
        endpoint = f"{self.base_url}/lists/{list_id}/contacts"
        params = {'api_key': self.api_key}
        
        data = {
            'email_address': email,
            'status': status
        }
        
        if fields:
            data['fields'] = fields
            
        if tags:
            data['tags'] = tags
        
        try:
            response = requests.post(endpoint, params=params, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 409:
                # Contact already exists
                logger.info(f"Contact {email} already exists")
                return {"error": "already_exists", "message": "Contact already exists"}
            else:
                logger.error(f"Error adding subscriber: {str(e)}")
                return {"error": str(e)}
        except Exception as e:
            logger.error(f"Error adding subscriber: {str(e)}")
            return {"error": str(e)}
    
    def update_subscriber(
        self,
        contact_id: str, 
        fields: Dict[str, str],
        list_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update a subscriber's details
        
        Args:
            contact_id: Contact ID to update
            fields: Fields to update
            list_id: List ID (defaults to self.list_id)
            tags: Optional tags to apply to the contact
            status: Optional new status
            
        Returns:
            API response with update status
        """
        list_id = list_id or self.list_id
        if not list_id:
            return {"error": "List ID not provided"}
        
        endpoint = f"{self.base_url}/lists/{list_id}/contacts/{contact_id}"
        params = {'api_key': self.api_key}
        
        data = {}
        if fields:
            data['fields'] = fields
            
        if tags:
            data['tags'] = tags
            
        if status:
            data['status'] = status
        
        try:
            response = requests.put(endpoint, params=params, json=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error updating subscriber: {str(e)}")
            return {"error": str(e)}
    
    def get_subscriber_by_email(self, email: str, list_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Find a subscriber by email
        
        Args:
            email: Email address to search for
            list_id: List ID (defaults to self.list_id)
            
        Returns:
            Subscriber data if found, error otherwise
        """
        list_id = list_id or self.list_id
        if not list_id:
            return {"error": "List ID not provided"}
        
        # First, get all members with pagination
        page = 1
        limit = 100
        
        while True:
            endpoint = f"{self.base_url}/lists/{list_id}/contacts"
            params = {
                'api_key': self.api_key,
                'page': page,
                'limit': limit
            }
            
            try:
                response = requests.get(endpoint, params=params)
                response.raise_for_status()
                data = response.json()
                
                for contact in data.get('data', []):
                    if contact.get('fields', {}).get('email_address') == email:
                        return contact
                
                # Check if there are more pages
                if len(data.get('data', [])) < limit:
                    break
                    
                page += 1
                
            except Exception as e:
                logger.error(f"Error searching for subscriber: {str(e)}")
                return {"error": str(e)}
        
        return {"error": "not_found", "message": "Subscriber not found"}
    
    def create_campaign(
        self,
        subject: str,
        content_html: str,
        from_name: str,
        from_email: str,
        list_id: Optional[str] = None,
        content_text: Optional[str] = None,
        reply_to: Optional[str] = None,
        send_at: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new campaign
        
        Args:
            subject: Email subject
            content_html: HTML content
            from_name: Sender name
            from_email: Sender email
            list_id: List ID (defaults to self.list_id)
            content_text: Plain text content
            reply_to: Reply-to email
            send_at: ISO 8601 datetime to send the campaign
            
        Returns:
            API response with campaign data
        """
        list_id = list_id or self.list_id
        if not list_id:
            return {"error": "List ID not provided"}
        
        endpoint = f"{self.base_url}/campaigns"
        params = {'api_key': self.api_key}
        
        data = {
            'subject': subject,
            'from': {
                'name': from_name,
                'email_address': from_email
            },
            'content': {
                'html': content_html
            },
            'lists': [list_id]
        }
        
        if content_text:
            data['content']['plain_text'] = content_text
            
        if reply_to:
            data['reply_to'] = {'email_address': reply_to}
            
        if send_at:
            data['send_at'] = send_at
        
        try:
            response = requests.post(endpoint, params=params, json=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error creating campaign: {str(e)}")
            return {"error": str(e)}
    
    def delete_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """
        Delete a campaign
        
        Args:
            campaign_id: Campaign ID to delete
            
        Returns:
            API response
        """
        endpoint = f"{self.base_url}/campaigns/{campaign_id}"
        params = {'api_key': self.api_key}
        
        try:
            response = requests.delete(endpoint, params=params)
            response.raise_for_status()
            return {"success": True}
        except Exception as e:
            logger.error(f"Error deleting campaign: {str(e)}")
            return {"error": str(e)}
    
    def get_campaign_stats(self, campaign_id: str) -> Dict[str, Any]:
        """
        Get campaign statistics
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            Campaign statistics
        """
        endpoint = f"{self.base_url}/campaigns/{campaign_id}"
        params = {'api_key': self.api_key}
        
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting campaign stats: {str(e)}")
            return {"error": str(e)}