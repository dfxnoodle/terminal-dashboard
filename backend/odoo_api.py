import os
import xmlrpc.client
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
import logging

# Load environment variables from parent directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

logger = logging.getLogger(__name__)

class OdooAPI:
    def __init__(self):
        self.url = os.getenv('ODOO_URL')
        self.db = os.getenv('ODOO_DB')
        self.username = os.getenv('ODOO_USERNAME')
        self.api_key = os.getenv('ODOO_API_KEY')
        
        if not all([self.url, self.db, self.username, self.api_key]):
            raise ValueError("Missing required environment variables for Odoo connection")
        
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
            logger.info(f"Successfully authenticated with Odoo, UID: {self.uid}")
            return True
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    def execute_kw(self, model: str, method: str, args: List = None, kwargs: Dict = None):
        """Execute Odoo API call with error handling"""
        if not self.uid:
            if not self.authenticate():
                raise Exception("Failed to authenticate with Odoo")
        
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
        except Exception as e:
            logger.error(f"API call failed: {e}")
            raise
    
    def get_date_ranges(self):
        """Get start dates for current week and last week (Monday 00:00) in UAE timezone"""
        # Get current time in UAE timezone
        now_uae = datetime.now(self.uae_tz)
        today = now_uae.date()
        days_since_monday = today.weekday()
        
        # Current week start (Monday 00:00) in UAE timezone
        current_week_start = datetime.combine(
            today - timedelta(days=days_since_monday),
            datetime.min.time()
        ).replace(tzinfo=self.uae_tz)
        
        # Last 14 days start
        last_14_days_start = current_week_start - timedelta(weeks=1)
        
        return last_14_days_start, current_week_start
    
    def get_today_range(self):
        """Get start and end of today in UAE timezone"""
        # Get current time in UAE timezone
        now_uae = datetime.now(self.uae_tz)
        today = now_uae.date()
        
        start_of_day = datetime.combine(today, datetime.min.time()).replace(tzinfo=self.uae_tz)
        end_of_day = datetime.combine(today, datetime.max.time()).replace(tzinfo=self.uae_tz)
        
        return start_of_day, end_of_day
    
    def get_forwarding_orders_train_data(self):
        """1st Item: Forwarding orders with train departure this week and last week"""
        last_14_days_start, current_week_start = self.get_date_ranges()
        current_week_end = current_week_start + timedelta(weeks=1)
        
        # Format dates for Odoo
        last_14_days_str = last_14_days_start.strftime('%Y-%m-%d %H:%M:%S')
        current_week_str = current_week_start.strftime('%Y-%m-%d %H:%M:%S')
        current_week_end_str = current_week_end.strftime('%Y-%m-%d %H:%M:%S')
        
        domain = [
            ['x_studio_selection_field_83c_1ig067df9', 'in', ['NDP Train Departed', 'Train Arrived at Destination']],
            ['x_studio_actual_train_departure', '>=', last_14_days_str],
            ['x_studio_actual_train_departure', '<', current_week_end_str]
        ]
        
        orders = self.execute_kw(
            'x_fwo', 'search_read',
            [domain],
            {'fields': [
                'x_studio_actual_train_departure', 
                'x_studio_selection_field_83c_1ig067df9',
                'x_studio_destination_terminal',
                'x_name',
                'x_studio_train_id'
            ]}
        )
        
        # Group by week and day
        current_week_orders = []
        last_week_orders = []
        daily_counts = {}
        
        for order in orders:
            departure_str = order['x_studio_actual_train_departure']
            if departure_str:
                # Parse datetime and assume it's in UAE timezone
                departure_dt = datetime.strptime(departure_str, '%Y-%m-%d %H:%M:%S')
                departure_dt = departure_dt.replace(tzinfo=self.uae_tz)
                
                # Determine week
                if departure_dt >= current_week_start:
                    current_week_orders.append(order)
                else:
                    last_week_orders.append(order)
                
                # Count by day
                day_key = departure_dt.strftime('%Y-%m-%d')
                daily_counts[day_key] = daily_counts.get(day_key, 0) + 1
        
        return {
            'current_week_count': len(current_week_orders),
            'last_week_count': len(last_week_orders),
            'daily_counts': daily_counts,
            'current_week_orders': current_week_orders,
            'last_week_orders': last_week_orders,
            'orders': orders  # Add the raw orders list here
        }
    
    def get_first_mile_truck_data(self):
        """2nd Item: First mile truck orders at NDP terminal today"""
        start_of_day, end_of_day = self.get_today_range()
        
        domain = [
            ['x_studio_terminal', '=', 'NDP'],
            ['x_studio_selection_field_1d4_1icdknqu2', 'in', ['Gate-out Completed', 'Train Departed', 'Exception']],
            ['x_studio_actual_date_and_time_of_gate_out', '>=', start_of_day.strftime('%Y-%m-%d %H:%M:%S')],
            ['x_studio_actual_date_and_time_of_gate_out', '<=', end_of_day.strftime('%Y-%m-%d %H:%M:%S')]
        ]
        
        orders = self.execute_kw(
            'x_first_mile_freight', 'search_read',
            [domain],
            {'fields': ['x_studio_net_weight_ton', 'x_studio_actual_date_and_time_of_gate_out', 'x_studio_selection_field_1d4_1icdknqu2']}
        )
        
        total_orders = len(orders)
        total_weight = sum(order.get('x_studio_net_weight_ton', 0) for order in orders)
        
        return {
            'total_orders': total_orders,
            'total_weight': total_weight,
            'orders': orders
        }
    
    def get_last_mile_truck_data(self, terminal: str):
        """3rd & 4th Item: Last mile truck orders at ICAD/DIC terminal today"""
        start_of_day, end_of_day = self.get_today_range()
        
        domain = [
            ['x_studio_terminal', '=', terminal],
            ['x_studio_selection_field_Vik7G', 'in', ['Gate-out Completed', 'Order Completed and Closed']],
            ['x_studio_actual_date_and_time_of_gate_out', '>=', start_of_day.strftime('%Y-%m-%d %H:%M:%S')],
            ['x_studio_actual_date_and_time_of_gate_out', '<=', end_of_day.strftime('%Y-%m-%d %H:%M:%S')]
        ]
        
        orders = self.execute_kw(
            'x_last_mile_freight', 'search_read',
            [domain],
            {'fields': ['x_studio_net_weight_ton', 'x_studio_actual_date_and_time_of_gate_out', 'x_studio_selection_field_Vik7G']}
        )
        
        total_orders = len(orders)
        total_weight = sum(order.get('x_studio_net_weight_ton', 0) for order in orders)
        
        return {
            'total_orders': total_orders,
            'total_weight': total_weight,
            'orders': orders,
            'terminal': terminal
        }
    
    def get_stockpile_utilization(self):
        """5th Item: Stockpile utilization for ICAD and DIC terminals"""
        try:
            # Fetch stockpile records
            stockpiles = self.execute_kw(
                'x_stockpile', 'search_read',
                [[]],  # Empty domain to get all records
                {
                    'limit': 50,
                    'fields': [
                        'id', 'x_name', 'display_name', 'x_studio_capacity',
                        'x_studio_quantity_in_stock_t', 'x_studio_terminal',
                        'x_studio_stockpile_material_age', 'x_studio_material',
                        'x_studio_show_in_dashboard'
                    ]
                }
            )
            
            if not stockpiles:
                logger.warning("No stockpile records found")
                raise Exception("No stockpile records exist")
            
            logger.info(f"Fetched {len(stockpiles)} stockpile records")
                
        except Exception as e:
            logger.error(f"Error fetching stockpiles: {e}")
            logger.info("Returning mock data due to stockpile fetch failure")
            # Return mock data for demonstration purposes
            return {
                'ICAD': [
                    {
                        'name': 'ICAD-SP-01 (Demo)',
                        'capacity': 1000.0,
                        'quantity': 750.0,
                        'material_name': 'Iron Ore (Demo)',
                        'material_age_hours': 24.5,
                        'utilization_percent': 75.0
                    },
                    {
                        'name': 'ICAD-SP-02 (Demo)',
                        'capacity': 1200.0,
                        'quantity': 960.0,
                        'material_name': 'Coal (Demo)',
                        'material_age_hours': 48.2,
                        'utilization_percent': 80.0
                    },
                    {
                        'name': 'ICAD-SP-03 (Demo)',
                        'capacity': 800.0,
                        'quantity': 320.0,
                        'material_name': 'Limestone (Demo)',
                        'material_age_hours': 12.8,
                        'utilization_percent': 40.0
                    }
                ],
                'DIC': [
                    {
                        'name': 'DIC-SP-01 (Demo)',
                        'capacity': 1500.0,
                        'quantity': 1350.0,
                        'material_name': 'Iron Ore (Demo)',
                        'material_age_hours': 36.1,
                        'utilization_percent': 90.0
                    },
                    {
                        'name': 'DIC-SP-02 (Demo)',
                        'capacity': 1000.0,
                        'quantity': 600.0,
                        'material_name': 'Coal (Demo)',
                        'material_age_hours': 72.5,
                        'utilization_percent': 60.0
                    }
                ]
            }
        
        # Group by terminal
        icad_stockpiles = []
        dic_stockpiles = []
        
        for stockpile in stockpiles:
            # Check if stockpile should be shown in dashboard
            show_in_dashboard = stockpile.get('x_studio_show_in_dashboard', False)
            
            # Skip stockpiles that shouldn't be shown in dashboard
            if not show_in_dashboard:
                continue
            
            # Use the actual field names from Odoo
            name = stockpile.get('x_name') or stockpile.get('display_name') or f"Stockpile {stockpile.get('id', '')}"
            capacity = stockpile.get('x_studio_capacity', 5000.0)
            quantity = stockpile.get('x_studio_quantity_in_stock_t', 0.0)
            terminal = stockpile.get('x_studio_terminal', '')
            age = stockpile.get('x_studio_stockpile_material_age', 0.0)
            
            # Get material name from the material field
            material_name = ''
            material_field = stockpile.get('x_studio_material')
            
            if material_field:
                if isinstance(material_field, list) and len(material_field) > 1:
                    material_name = material_field[1]
                else:
                    try:
                        material_id = material_field
                        if isinstance(material_id, list):
                            material_id = material_id[0]
                        material = self.execute_kw(
                            'x_material', 'read',
                            [[material_id]],
                            {'fields': ['x_name', 'name']}
                        )
                        if material:
                            material_name = material[0].get('x_name') or material[0].get('name', 'Unknown')
                    except:
                        material_name = 'Unknown'
            
            stockpile_data = {
                'name': str(name),
                'capacity': float(capacity),
                'quantity': float(quantity),
                'material_name': material_name,
                'material_age_hours': float(age),
                'utilization_percent': (float(quantity) / max(float(capacity), 1)) * 100
            }
            
            if 'ICAD' in str(terminal).upper():
                icad_stockpiles.append(stockpile_data)
            elif 'DIC' in str(terminal).upper():
                dic_stockpiles.append(stockpile_data)
            else:
                # If no terminal specified, add some demo data
                icad_stockpiles.append({**stockpile_data, 'name': f"ICAD-{stockpile_data['name']}"})
        
        return {
            'ICAD': icad_stockpiles,
            'DIC': dic_stockpiles
        }
