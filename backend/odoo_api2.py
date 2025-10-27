import os
import xmlrpc.client
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
import logging

# Load environment variables from parent directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

logger = logging.getLogger(__name__)

class OdooAPI2:
    """
    API class for Odoo Config 2 (AL TOS System)
    Used for Intermodal dashboard
    """
    def __init__(self):
        self.url = os.getenv('ODOO2_URL')
        self.db = os.getenv('ODOO2_DB')
        self.username = os.getenv('ODOO2_USERNAME')
        self.api_key = os.getenv('ODOO2_API_KEY')
        
        if not all([self.url, self.db, self.username, self.api_key]):
            raise ValueError("Missing required environment variables for Odoo2 connection")
        
        self.common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
        self.models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
        self.uid = None
        
        # UAE timezone (UTC+4)
        self.uae_tz = timezone(timedelta(hours=4))
        
    def authenticate(self):
        """Authenticate with Odoo and get user ID"""
        try:
            self.uid = self.common.authenticate(self.db, self.username, self.api_key, {})
            if not self.uid:
                raise Exception("Authentication failed")
            logger.info(f"Successfully authenticated with Odoo2, UID: {self.uid}")
            return True
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    def execute_kw(self, model: str, method: str, args: List = None, kwargs: Dict = None):
        """Execute Odoo API call with error handling"""
        if not self.uid:
            if not self.authenticate():
                raise Exception("Failed to authenticate with Odoo2")
        
        try:
            return self.models.execute_kw(
                self.db, self.uid, self.api_key,
                model, method,
                args or [],
                kwargs or {}
            )
        except Exception as e:
            logger.error(f"Error executing {method} on {model}: {e}")
            raise
    
    def test_connection(self):
        """Test connection to Odoo"""
        try:
            if not self.uid:
                return self.authenticate()
            
            # Try a simple query to test the connection
            result = self.execute_kw('res.users', 'search_read', 
                                   [[['id', '=', self.uid]]], 
                                   {'fields': ['name'], 'limit': 1})
            return bool(result)
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def get_ruw_container_stats(self):
        """
        Get container statistics for RUW location
        Returns counts of loaded and empty containers
        """
        try:
            # Get total containers at RUW
            total_count = self.execute_kw(
                'x_container', 'search_count',
                [[['x_studio_location', '=', 'RUW']]]
            )
            
            # Get loaded containers at RUW
            loaded_count = self.execute_kw(
                'x_container', 'search_count',
                [[['x_studio_location', '=', 'RUW'], ['x_studio_filled', '=', True]]]
            )
            
            # Get empty containers at RUW
            empty_count = self.execute_kw(
                'x_container', 'search_count',
                [[['x_studio_location', '=', 'RUW'], ['x_studio_filled', '=', False]]]
            )
            
            # Get some sample containers for additional details
            sample_containers = self.execute_kw(
                'x_container', 'search_read',
                [[['x_studio_location', '=', 'RUW']]],
                {'fields': ['id', 'x_name', 'x_studio_location', 'x_studio_filled', 'create_date', 'write_date'], 
                 'limit': 10,
                 'order': 'write_date desc'}
            )
            
            return {
                'location': 'RUW',
                'total': total_count,
                'loaded': loaded_count,
                'empty': empty_count,
                'loaded_percentage': round((loaded_count / total_count * 100) if total_count > 0 else 0, 1),
                'empty_percentage': round((empty_count / total_count * 100) if total_count > 0 else 0, 1),
                'recent_containers': sample_containers,
                'last_updated': datetime.now(self.uae_tz).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting RUW container stats: {e}")
            raise
    
    def get_all_locations_container_stats(self):
        """
        Get container statistics for all locations
        """
        try:
            # Get all unique locations
            all_containers = self.execute_kw(
                'x_container', 'search_read',
                [[]],
                {'fields': ['x_studio_location', 'x_studio_filled']}
            )
            
            # Group by location
            location_stats = {}
            for container in all_containers:
                location = container.get('x_studio_location', 'Unknown')
                if location not in location_stats:
                    location_stats[location] = {'total': 0, 'loaded': 0, 'empty': 0}
                
                location_stats[location]['total'] += 1
                if container.get('x_studio_filled'):
                    location_stats[location]['loaded'] += 1
                else:
                    location_stats[location]['empty'] += 1
            
            # Format the results
            results = []
            for location, stats in location_stats.items():
                results.append({
                    'location': location,
                    'total': stats['total'],
                    'loaded': stats['loaded'],
                    'empty': stats['empty'],
                    'loaded_percentage': round((stats['loaded'] / stats['total'] * 100) if stats['total'] > 0 else 0, 1),
                    'empty_percentage': round((stats['empty'] / stats['total'] * 100) if stats['total'] > 0 else 0, 1)
                })
            
            # Sort by total containers descending
            results.sort(key=lambda x: x['total'], reverse=True)
            
            return {
                'locations': results,
                'last_updated': datetime.now(self.uae_tz).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting all locations container stats: {e}")
            raise
    
    def get_train_departures(self, days: int = 14):
        """
        Get train departure data for the last N days
        Only includes trains with status 'Departed from Origin' or 'Arrived at Destination'
        
        Args:
            days: Number of days to look back (default 14)
            
        Returns:
            List of train departure records with origin, destination, and time data
        """
        try:
            # Calculate date N days ago
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            # Search for trains that departed or arrived in the last N days
            # Using & (AND) operator to ensure both conditions are met
            train_ids = self.execute_kw(
                'x_scheduled_train', 'search',
                [[
                    '&',
                    '|',
                    ['x_studio_selection_field_mojWp', '=', 'Departed from Origin'],
                    ['x_studio_selection_field_mojWp', '=', 'Arrived at Destination'],
                    ['x_studio_actual_departure', '>=', cutoff_date]
                ]],
                {'order': 'x_studio_actual_departure desc'}
            )
            
            if not train_ids:
                return {
                    'trains': [],
                    'total_count': 0,
                    'days': days,
                    'last_updated': datetime.now(self.uae_tz).isoformat()
                }
            
            # Get full train records
            trains = self.execute_kw(
                'x_scheduled_train', 'read',
                [train_ids],
                {'fields': [
                    'id',
                    'display_name',
                    'x_name',
                    'x_studio_from',
                    'x_studio_to_1',
                    'x_studio_actual_departure',
                    'x_studio_selection_field_mojWp',
                    'x_studio_train_set'
                ]}
            )
            
            # Format the results
            formatted_trains = []
            for train in trains:
                # Parse the departure time
                departure_str = train.get('x_studio_actual_departure')
                if departure_str and departure_str != False:
                    formatted_trains.append({
                        'id': train['id'],
                        'train_id': train.get('x_name') or train.get('display_name', 'N/A'),
                        'origin': train.get('x_studio_from', 'Unknown'),
                        'destination': train.get('x_studio_to_1', 'Unknown'),
                        'actual_departure': departure_str,
                        'status': train.get('x_studio_selection_field_mojWp', 'Unknown'),
                        'train_set': train.get('x_studio_train_set', '')
                    })
            
            return {
                'trains': formatted_trains,
                'total_count': len(formatted_trains),
                'days': days,
                'last_updated': datetime.now(self.uae_tz).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting train departures: {e}")
            raise

# Create a singleton instance
odoo_api2 = OdooAPI2()

