"""
Notion API integration for task and knowledge management.
Real API implementation using official Notion SDK.
"""

import os
from datetime import datetime
from typing import List, Dict, Any, Optional

try:
    from notion_client import Client
    NOTION_AVAILABLE = True
except ImportError:
    NOTION_AVAILABLE = False


class NotionClient:
    """
    Notion API client for syncing tasks and assignments.
    Uses official Notion SDK with real API calls.
    """
    
    def __init__(self, api_token: Optional[str] = None):
        """Initialize Notion client with API token."""
        self.api_token = api_token or os.getenv('NOTION_API_TOKEN')
        self.database_id = os.getenv('NOTION_DATABASE_ID')
        
        if not NOTION_AVAILABLE:
            print("Warning: notion-client not installed. Using manual mode.")
            self.client = None
            return
            
        if self.api_token:
            self.client = Client(auth=self.api_token)
        else:
            print("Warning: No Notion API token provided. Using manual mode.")
            self.client = None
    
    def query_database(self, database_id: Optional[str] = None, 
                      filter_dict: Optional[Dict] = None) -> List[Dict]:
        """
        Query Notion database for tasks.
        
        Args:
            database_id: Database ID to query (uses default if not provided)
            filter_dict: Notion filter object
            
        Returns:
            List of database items
        """
        if not self.client:
            return []
            
        db_id = database_id or self.database_id
        if not db_id:
            return []
            
        try:
            response = self.client.databases.query(
                database_id=db_id,
                filter=filter_dict if filter_dict else {}
            )
            return response.get('results', [])
        except Exception as e:
            print(f"Error querying Notion database: {e}")
            return []
    
    def create_page(self, database_id: Optional[str], properties: Dict, 
                   content: Optional[List[Dict]] = None) -> Optional[Dict]:
        """
        Create a new page in Notion database.
        
        Args:
            database_id: Parent database ID
            properties: Page properties (title, date, select, etc.)
            content: Page content blocks
            
        Returns:
            Created page object
        """
        if not self.client:
            return None
            
        db_id = database_id or self.database_id
        if not db_id:
            return None
            
        try:
            page_data = {
                'parent': {'database_id': db_id},
                'properties': properties
            }
            
            if content:
                page_data['children'] = content
                
            response = self.client.pages.create(**page_data)
            return response
        except Exception as e:
            print(f"Error creating Notion page: {e}")
            return None
    
    def update_page(self, page_id: str, properties: Dict) -> Optional[Dict]:
        """
        Update an existing Notion page.
        
        Args:
            page_id: Page ID to update
            properties: Updated properties
            
        Returns:
            Updated page object
        """
        if not self.client:
            return None
            
        try:
            response = self.client.pages.update(
                page_id=page_id,
                properties=properties
            )
            return response
        except Exception as e:
            print(f"Error updating Notion page: {e}")
            return None
    
    def extract_tasks(self, database_id: Optional[str] = None) -> List[Dict]:
        """
        Extract tasks from Notion database.
        
        Args:
            database_id: Database to extract from
            
        Returns:
            List of task dictionaries
        """
        items = self.query_database(database_id)
        tasks = []
        
        for item in items:
            task = self._parse_notion_task(item)
            if task:
                tasks.append(task)
                
        return tasks
    
    def _parse_notion_task(self, notion_page: Dict) -> Optional[Dict]:
        """Parse Notion page into task dict."""
        try:
            props = notion_page.get('properties', {})
            
            # Extract title
            title_prop = props.get('Name') or props.get('Title')
            title = ''
            if title_prop and title_prop['type'] == 'title':
                title = ''.join([t['plain_text'] for t in title_prop['title']])
            
            # Extract due date
            due_date = None
            date_prop = props.get('Due') or props.get('Date')
            if date_prop and date_prop['type'] == 'date' and date_prop['date']:
                due_date = date_prop['date'].get('start')
            
            # Extract status/priority
            priority = 'medium'
            priority_prop = props.get('Priority')
            if priority_prop and priority_prop['type'] == 'select':
                notion_priority = priority_prop['select']['name'].lower() if priority_prop['select'] else 'medium'
                priority_map = {
                    'high': 'high',
                    'urgent': 'critical',
                    'medium': 'medium',
                    'low': 'low'
                }
                priority = priority_map.get(notion_priority, 'medium')
            
            return {
                'id': notion_page['id'],
                'title': title,
                'due_date': due_date,
                'priority': priority,
                'source': 'notion',
                'url': notion_page['url']
            }
        except Exception as e:
            print(f"Error parsing Notion task: {e}")
            return None
    
    def sync_task_to_notion(self, task: Dict, database_id: Optional[str] = None) -> bool:
        """
        Sync task from OsMEN to Notion.
        
        Args:
            task: Task dictionary
            database_id: Target database
            
        Returns:
            Success boolean
        """
        if not self.client:
            return False
            
        properties = {
            'Name': {
                'title': [{'text': {'content': task.get('title', 'Untitled')}}]
            }
        }
        
        if task.get('due_date'):
            properties['Due'] = {
                'date': {'start': task['due_date']}
            }
        
        if task.get('priority'):
            priority_map = {
                'critical': 'Urgent',
                'high': 'High',
                'medium': 'Medium',
                'low': 'Low'
            }
            properties['Priority'] = {
                'select': {'name': priority_map.get(task['priority'], 'Medium')}
            }
        
        if task.get('notion_id'):
            # Update existing
            result = self.update_page(task['notion_id'], properties)
        else:
            # Create new
            result = self.create_page(database_id, properties)
        
        return result is not None
