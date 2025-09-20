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
        """Get start and end of today in UAE timezone, converted to UTC for Odoo queries"""
        # Get current time in UAE timezone
        now_uae = datetime.now(self.uae_tz)
        today = now_uae.date()
        
        start_of_day_uae = datetime.combine(today, datetime.min.time()).replace(tzinfo=self.uae_tz)
        end_of_day_uae = datetime.combine(today, datetime.max.time()).replace(tzinfo=self.uae_tz)
        
        # Convert to UTC for Odoo queries (Odoo stores times in UTC)
        start_of_day_utc = start_of_day_uae.astimezone(timezone.utc)
        end_of_day_utc = end_of_day_uae.astimezone(timezone.utc)
        
        return start_of_day_utc, end_of_day_utc
    
    def _enrich_orders_with_weight_data(self, orders):
        """Enrich forwarding orders with weight data from freight orders"""
        try:
            # Get all first mile freight orders for weight data
            # We'll try to match by train ID or forwarding order reference
            
            # First, collect all train IDs and order names from forwarding orders
            train_ids = set()
            order_names = set()
            
            for order in orders:
                if order.get('x_studio_train_id'):
                    train_ids.add(order['x_studio_train_id'])
                if order.get('x_name'):
                    order_names.add(order['x_name'])
            
            if not train_ids and not order_names:
                logger.warning("No train IDs or order names found to match freight data")
                return
            
            # Get freight orders that might be related
            # We'll search for freight orders with matching train IDs or forwarding order references
            freight_domain = []
            
            # Try to find freight orders by forwarding order reference
            if order_names:
                freight_domain.append(['x_studio_forwarding_order', 'in', list(order_names)])
            
            if not freight_domain:
                # If we can't match by forwarding order, get recent freight data
                # and try to match by time proximity and train ID
                now_uae = datetime.now(self.uae_tz)
                thirty_days_ago = now_uae - timedelta(days=30)
                thirty_days_ago_utc = thirty_days_ago.astimezone(timezone.utc)
                freight_domain = [
                    ['x_studio_actual_date_and_time_of_gate_out', '>=', thirty_days_ago_utc.strftime('%Y-%m-%d %H:%M:%S')]
                ]
            
            if freight_domain:
                freight_orders = self.execute_kw(
                    'x_first_mile_freight', 'search_read',
                    [freight_domain],
                    {'fields': [
                        'x_studio_net_weight_ton',
                        'x_studio_forwarding_order',
                        'x_studio_forwarding_order_selectable',
                        'x_studio_actual_date_and_time_of_gate_out',
                        'x_name'
                    ]}
                )
                
                # Create lookup dictionaries
                weight_by_fwo_name = {}
                weight_by_train_time = {}  # For time-based matching if direct matching fails
                
                for freight in freight_orders:
                    weight = freight.get('x_studio_net_weight_ton', 0)
                    if weight > 0:
                        # Direct match by forwarding order name
                        fwo_ref = freight.get('x_studio_forwarding_order')
                        if fwo_ref:
                            if fwo_ref not in weight_by_fwo_name:
                                weight_by_fwo_name[fwo_ref] = 0
                            weight_by_fwo_name[fwo_ref] += weight
                        
                        # Store for potential time-based matching
                        gate_out_time = freight.get('x_studio_actual_date_and_time_of_gate_out')
                        if gate_out_time:
                            weight_by_train_time[gate_out_time] = weight_by_train_time.get(gate_out_time, 0) + weight
                
                # Enrich the forwarding orders with weight data
                for order in orders:
                    order['x_studio_total_weight_tons'] = 0  # Default value
                    
                    # Try direct match first
                    order_name = order.get('x_name')
                    if order_name and order_name in weight_by_fwo_name:
                        order['x_studio_total_weight_tons'] = weight_by_fwo_name[order_name]
                        logger.debug(f"Matched weight {order['x_studio_total_weight_tons']} tons for order {order_name}")
                    else:
                        # Try time-based matching as fallback
                        # This is more complex and might not be as accurate
                        departure_time = order.get('x_studio_actual_train_departure')
                        if departure_time and weight_by_train_time:
                            # Find closest freight gate-out time (within reasonable window)
                            departure_dt = datetime.strptime(departure_time, '%Y-%m-%d %H:%M:%S')
                            
                            closest_weight = 0
                            min_time_diff = float('inf')
                            
                            for gate_out_time, weight in weight_by_train_time.items():
                                try:
                                    gate_out_dt = datetime.strptime(gate_out_time, '%Y-%m-%d %H:%M:%S')
                                    time_diff = abs((departure_dt - gate_out_dt).total_seconds())
                                    
                                    # Only consider matches within 24 hours
                                    if time_diff < 24 * 3600 and time_diff < min_time_diff:
                                        min_time_diff = time_diff
                                        closest_weight = weight
                                except:
                                    continue
                            
                            if closest_weight > 0:
                                order['x_studio_total_weight_tons'] = closest_weight
                                logger.debug(f"Time-matched weight {closest_weight} tons for order {order_name} (time diff: {min_time_diff/3600:.1f} hours)")
                
                logger.info(f"Enriched {len(orders)} orders with weight data. Found weights for {len([o for o in orders if o.get('x_studio_total_weight_tons', 0) > 0])} orders")
                
        except Exception as e:
            logger.error(f"Error enriching orders with weight data: {e}")
            # Add default weight field to all orders even if enrichment fails
            for order in orders:
                if 'x_studio_total_weight_tons' not in order:
                    order['x_studio_total_weight_tons'] = 0
    
    def get_forwarding_orders_train_data(self):
        """1st Item: Forwarding orders with train departure this week and last week"""
        last_14_days_start, current_week_start = self.get_date_ranges()
        
        # Get current time in UAE timezone and calculate actual 14 days ago
        now_uae = datetime.now(self.uae_tz)
        fourteen_days_ago = now_uae - timedelta(days=14)
        
        # Convert to UTC for Odoo queries (Odoo stores times in UTC)
        fourteen_days_ago_utc = fourteen_days_ago.astimezone(timezone.utc)
        current_week_start_utc = current_week_start.astimezone(timezone.utc)
        now_utc = now_uae.astimezone(timezone.utc)
        
        # Format dates for Odoo - use 14 days ago instead of just 2 weeks
        last_14_days_str = fourteen_days_ago_utc.strftime('%Y-%m-%d %H:%M:%S')
        current_week_str = current_week_start_utc.strftime('%Y-%m-%d %H:%M:%S')
        now_str = now_utc.strftime('%Y-%m-%d %H:%M:%S')
        
        domain = [
            ['x_studio_selection_field_83c_1ig067df9', 'in', ['NDP Train Departed', 'Train Arrived at Destination']],
            ['x_studio_actual_train_departure', '>=', last_14_days_str],
            ['x_studio_actual_train_departure', '<', now_str]
        ]
        
        orders = self.execute_kw(
            'x_fwo', 'search_read',
            [domain],
            {'fields': [
                'x_studio_actual_train_departure', 
                'x_studio_selection_field_83c_1ig067df9',
                'x_studio_destination_terminal',
                'x_studio_origin_terminal',
                'x_name',
                'x_studio_train_id'
            ]}
        )
        
        # Enrich orders with weight data from freight
        self._enrich_orders_with_weight_data(orders)
        
        # Group by week and day
        current_week_orders = []
        last_week_orders = []
        today_orders = []
        yesterday_orders = []
        daily_counts = {}
        
        # Calculate last week start (Monday of previous week)
        last_week_start = current_week_start - timedelta(weeks=1)
        
        # Get today's date and yesterday's date for filtering
        today_date = now_uae.date()
        yesterday_date = today_date - timedelta(days=1)
        
        for order in orders:
            departure_str = order['x_studio_actual_train_departure']
            if departure_str:
                # Parse datetime and assume it's in UAE timezone
                departure_dt = datetime.strptime(departure_str, '%Y-%m-%d %H:%M:%S')
                departure_dt = departure_dt.replace(tzinfo=self.uae_tz)
                
                # Check if this order is from today
                if departure_dt.date() == today_date:
                    today_orders.append(order)
                # Check if this order is from yesterday
                elif departure_dt.date() == yesterday_date:
                    yesterday_orders.append(order)
                
                # Determine week - only count orders within specific week ranges
                if departure_dt >= current_week_start:
                    # Current week (from Monday of this week onwards)
                    current_week_orders.append(order)
                elif departure_dt >= last_week_start and departure_dt < current_week_start:
                    # Last week (from Monday of last week to Sunday of last week)
                    last_week_orders.append(order)
                
                # Count by day (for all orders in the 14-day period)
                day_key = departure_dt.strftime('%Y-%m-%d')
                daily_counts[day_key] = daily_counts.get(day_key, 0) + 1
        
        # Calculate weight totals
        current_week_weight = sum(order.get('x_studio_total_weight_tons', 0) for order in current_week_orders)
        last_week_weight = sum(order.get('x_studio_total_weight_tons', 0) for order in last_week_orders)
        today_weight = sum(order.get('x_studio_total_weight_tons', 0) for order in today_orders)
        yesterday_weight = sum(order.get('x_studio_total_weight_tons', 0) for order in yesterday_orders)
        
        return {
            'current_week_count': len(current_week_orders),
            'last_week_count': len(last_week_orders),
            'today_count': len(today_orders),
            'yesterday_count': len(yesterday_orders),
            'current_week_weight': current_week_weight,
            'last_week_weight': last_week_weight,
            'today_weight': today_weight,
            'yesterday_weight': yesterday_weight,
            'daily_counts': daily_counts,
            'current_week_orders': current_week_orders,
            'last_week_orders': last_week_orders,
            'today_orders': today_orders,
            'yesterday_orders': yesterday_orders,
            'orders': orders  # Add the raw orders list here
        }
    
    def get_first_mile_truck_data(self, target_date: Optional[datetime.date] = None):
        """2nd Item: First mile truck orders at NDP terminal today and yesterday"""
        # If no date provided, use today
        if target_date is None:
            start_of_today, end_of_today = self.get_today_range()
        else:
            # Use the provided date
            now_uae = datetime.now(self.uae_tz)
            start_of_day_uae = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=self.uae_tz)
            end_of_day_uae = datetime.combine(target_date, datetime.max.time()).replace(tzinfo=self.uae_tz)
            
            # Convert to UTC for Odoo queries
            start_of_today = start_of_day_uae.astimezone(timezone.utc)
            end_of_today = end_of_day_uae.astimezone(timezone.utc)
        
        # Get yesterday's range (relative to target date)
        if target_date is None:
            now_uae = datetime.now(self.uae_tz)
            yesterday = now_uae - timedelta(days=1)
        else:
            yesterday_date_obj = target_date - timedelta(days=1)
            yesterday = datetime.combine(yesterday_date_obj, datetime.min.time()).replace(tzinfo=self.uae_tz)
        
        yesterday_date = yesterday.date() if target_date is None else target_date - timedelta(days=1)
        
        start_of_yesterday_uae = datetime.combine(yesterday_date, datetime.min.time()).replace(tzinfo=self.uae_tz)
        end_of_yesterday_uae = datetime.combine(yesterday_date, datetime.max.time()).replace(tzinfo=self.uae_tz)
        
        # Convert to UTC for Odoo queries
        start_of_yesterday_utc = start_of_yesterday_uae.astimezone(timezone.utc)
        end_of_yesterday_utc = end_of_yesterday_uae.astimezone(timezone.utc)
        
        # Get today's orders
        today_domain = [
            ['x_studio_terminal', '=', 'NDP'],
            ['x_studio_selection_field_1d4_1icdknqu2', 'in', ['Gate-out Completed', 'Train Departed', 'Exception']],
            ['x_studio_actual_date_and_time_of_gate_out', '>=', start_of_today.strftime('%Y-%m-%d %H:%M:%S')],
            ['x_studio_actual_date_and_time_of_gate_out', '<=', end_of_today.strftime('%Y-%m-%d %H:%M:%S')]
        ]
        
        today_orders = self.execute_kw(
            'x_first_mile_freight', 'search_read',
            [today_domain],
            {'fields': ['x_studio_net_weight_ton', 'x_studio_actual_date_and_time_of_gate_out', 'x_studio_selection_field_1d4_1icdknqu2']}
        )
        
        # Get yesterday's orders
        yesterday_domain = [
            ['x_studio_terminal', '=', 'NDP'],
            ['x_studio_selection_field_1d4_1icdknqu2', 'in', ['Gate-out Completed', 'Train Departed', 'Exception']],
            ['x_studio_actual_date_and_time_of_gate_out', '>=', start_of_yesterday_utc.strftime('%Y-%m-%d %H:%M:%S')],
            ['x_studio_actual_date_and_time_of_gate_out', '<=', end_of_yesterday_utc.strftime('%Y-%m-%d %H:%M:%S')]
        ]
        
        yesterday_orders = self.execute_kw(
            'x_first_mile_freight', 'search_read',
            [yesterday_domain],
            {'fields': ['x_studio_net_weight_ton', 'x_studio_actual_date_and_time_of_gate_out', 'x_studio_selection_field_1d4_1icdknqu2']}
        )
        
        # Calculate totals for today
        total_orders_today = len(today_orders)
        total_weight_today = sum(order.get('x_studio_net_weight_ton', 0) for order in today_orders)
        
        # Calculate totals for yesterday
        total_orders_yesterday = len(yesterday_orders)
        total_weight_yesterday = sum(order.get('x_studio_net_weight_ton', 0) for order in yesterday_orders)
        
        return {
            'total_orders': total_orders_today,
            'total_weight': total_weight_today,
            'orders': today_orders,
            'yesterday': {
                'total_orders': total_orders_yesterday,
                'total_weight': total_weight_yesterday,
                'orders': yesterday_orders
            }
        }
    
    def get_last_mile_truck_data(self, terminal: str, target_date: Optional[datetime.date] = None):
        """3rd & 4th Item: Last mile truck orders at ICAD/DIC terminal today and yesterday"""
        # If no date provided, use today
        if target_date is None:
            start_of_today, end_of_today = self.get_today_range()
        else:
            # Use the provided date
            now_uae = datetime.now(self.uae_tz)
            start_of_day_uae = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=self.uae_tz)
            end_of_day_uae = datetime.combine(target_date, datetime.max.time()).replace(tzinfo=self.uae_tz)
            
            # Convert to UTC for Odoo queries
            start_of_today = start_of_day_uae.astimezone(timezone.utc)
            end_of_today = end_of_day_uae.astimezone(timezone.utc)
        
        # Get yesterday's range (relative to target date)
        if target_date is None:
            now_uae = datetime.now(self.uae_tz)
            yesterday = now_uae - timedelta(days=1)
        else:
            yesterday_date_obj = target_date - timedelta(days=1)
            yesterday = datetime.combine(yesterday_date_obj, datetime.min.time()).replace(tzinfo=self.uae_tz)
        
        yesterday_date = yesterday.date() if target_date is None else target_date - timedelta(days=1)
        
        start_of_yesterday_uae = datetime.combine(yesterday_date, datetime.min.time()).replace(tzinfo=self.uae_tz)
        end_of_yesterday_uae = datetime.combine(yesterday_date, datetime.max.time()).replace(tzinfo=self.uae_tz)
        
        # Convert to UTC for Odoo queries
        start_of_yesterday_utc = start_of_yesterday_uae.astimezone(timezone.utc)
        end_of_yesterday_utc = end_of_yesterday_uae.astimezone(timezone.utc)
        
        # Get today's orders
        today_domain = [
            ['x_studio_terminal', '=', terminal],
            ['x_studio_selection_field_Vik7G', 'in', ['Gate-out Completed', 'Order Completed and Closed']],
            ['x_studio_actual_date_and_time_of_gate_out', '>=', start_of_today.strftime('%Y-%m-%d %H:%M:%S')],
            ['x_studio_actual_date_and_time_of_gate_out', '<=', end_of_today.strftime('%Y-%m-%d %H:%M:%S')]
        ]
        
        today_orders = self.execute_kw(
            'x_last_mile_freight', 'search_read',
            [today_domain],
            {'fields': ['x_studio_net_weight_ton', 'x_studio_actual_date_and_time_of_gate_out', 'x_studio_selection_field_Vik7G']}
        )
        
        # Get yesterday's orders
        yesterday_domain = [
            ['x_studio_terminal', '=', terminal],
            ['x_studio_selection_field_Vik7G', 'in', ['Gate-out Completed', 'Order Completed and Closed']],
            ['x_studio_actual_date_and_time_of_gate_out', '>=', start_of_yesterday_utc.strftime('%Y-%m-%d %H:%M:%S')],
            ['x_studio_actual_date_and_time_of_gate_out', '<=', end_of_yesterday_utc.strftime('%Y-%m-%d %H:%M:%S')]
        ]
        
        yesterday_orders = self.execute_kw(
            'x_last_mile_freight', 'search_read',
            [yesterday_domain],
            {'fields': ['x_studio_net_weight_ton', 'x_studio_actual_date_and_time_of_gate_out', 'x_studio_selection_field_Vik7G']}
        )
        
        # Calculate totals for today
        total_orders_today = len(today_orders)
        total_weight_today = sum(order.get('x_studio_net_weight_ton', 0) for order in today_orders)
        
        # Calculate totals for yesterday
        total_orders_yesterday = len(yesterday_orders)
        total_weight_yesterday = sum(order.get('x_studio_net_weight_ton', 0) for order in yesterday_orders)
        
        return {
            'total_orders': total_orders_today,
            'total_weight': total_weight_today,
            'orders': today_orders,
            'terminal': terminal,
            'yesterday': {
                'total_orders': total_orders_yesterday,
                'total_weight': total_weight_yesterday,
                'orders': yesterday_orders
            }
        }
    
    def get_stockpile_utilization(self):
        """5th Item: Stockpile utilization for ICAD, DIC and NDP terminals"""
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
        ndp_stockpiles = []
        
        for stockpile in stockpiles:
            # Check if stockpile should be shown in dashboard
            show_in_dashboard = stockpile.get('x_studio_show_in_dashboard', False)
            terminal = stockpile.get('x_studio_terminal', '')
            
            # Skip stockpiles that shouldn't be shown in dashboard
            if not show_in_dashboard:
                continue
            
            # Use the actual field names from Odoo
            name = stockpile.get('x_name') or stockpile.get('display_name') or f"Stockpile {stockpile.get('id', '')}"
            capacity = stockpile.get('x_studio_capacity', 5000.0)
            quantity = stockpile.get('x_studio_quantity_in_stock_t', 0.0)
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
            
            # Handle zero capacity for NDP stockpiles - use quantity as capacity if capacity is 0
            display_capacity = float(capacity)
            if display_capacity == 0 and 'NDP' in str(terminal).upper() and float(quantity) > 0:
                display_capacity = float(quantity)  # Use quantity as capacity for NDP silos
            
            stockpile_data = {
                'name': str(name),
                'capacity': display_capacity,
                'quantity': float(quantity),
                'material_name': material_name,
                'utilization_percent': (float(quantity) / max(display_capacity, 1)) * 100
            }
            
            # Only include age for non-NDP terminals
            if 'NDP' not in str(terminal).upper():
                stockpile_data['material_age_hours'] = float(age)
            
            if 'ICAD' in str(terminal).upper():
                icad_stockpiles.append(stockpile_data)
            elif 'DIC' in str(terminal).upper():
                dic_stockpiles.append(stockpile_data)
            elif 'NDP' in str(terminal).upper():
                ndp_stockpiles.append(stockpile_data)
            else:
                # Log unknown terminals for debugging
                logger.warning(f"Unknown terminal '{terminal}' for stockpile {name}")
        
        return {
            'ICAD': icad_stockpiles,
            'DIC': dic_stockpiles,
            'NDP': ndp_stockpiles
        }
