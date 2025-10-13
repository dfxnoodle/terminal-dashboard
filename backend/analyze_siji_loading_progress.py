#!/usr/bin/env python3
"""
Explore Siji Departed Trains - NOW WITH FULL ACCESS!
Focus on wagon loading progress tracking
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv
import xmlrpc.client

# Load environment variables
load_dotenv()

class OdooAPI:
    def __init__(self):
        self.url = os.getenv('ODOO_URL')
        self.db = os.getenv('ODOO_DB')
        self.username = os.getenv('ODOO_USERNAME')
        self.api_key = os.getenv('ODOO_API_KEY')
        
        self.common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
        self.models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
        self.uid = None
        
    def authenticate(self):
        """Authenticate with Odoo"""
        self.uid = self.common.authenticate(self.db, self.username, self.api_key, {})
        print(f"✓ Authenticated as UID: {self.uid}")
        return self.uid
        
    def execute_kw(self, model, method, args, kwargs=None):
        """Execute Odoo API call"""
        if kwargs is None:
            kwargs = {}
        return self.models.execute_kw(
            self.db, self.uid, self.api_key,
            model, method, args, kwargs
        )

def get_siji_rail_freight_orders(api):
    """Get Siji rail freight orders - DIRECT ACCESS!"""
    print("\n" + "="*80)
    print("QUERYING SIJI RAIL FREIGHT ORDERS")
    print("="*80)
    
    try:
        # First, check all possible status values
        print("\nChecking all Siji records (any status)...")
        domain_all = [['x_studio_terminal', '=', 'Siji']]
        count_all = api.execute_kw('x_rail_freight_order', 'search_count', [domain_all])
        print(f"Total Siji rail freight orders: {count_all}")
        
        # Get some samples to see status values
        samples = api.execute_kw('x_rail_freight_order', 'search_read', [domain_all], {
            'fields': ['x_name', 'x_studio_selection_field_572_1j09lmu81', 'x_studio_terminal'],
            'limit': 10
        })
        
        print(f"\nSample status values:")
        status_values = set()
        for rec in samples:
            status = rec.get('x_studio_selection_field_572_1j09lmu81')
            status_values.add(status)
            print(f"  - {rec.get('x_name')}: {status}")
        
        print(f"\nUnique status values found: {status_values}")
        
        # Now query with Draft or Train Departed status
        print("\nQuerying Draft or Train Departed records...")
        domain_filtered = [
            ['x_studio_terminal', '=', 'Siji'],
            ['x_studio_selection_field_572_1j09lmu81', 'in', ['Draft', 'Train Departed']]
        ]
        
        count_filtered = api.execute_kw('x_rail_freight_order', 'search_count', [domain_filtered])
        print(f"Siji records with 'Draft' or 'Train Departed' status: {count_filtered}")
        
        if count_filtered == 0:
            print("\n⚠️ No records with exact 'Draft' or 'Train Departed' status")
            print("Let's get the most recent Siji record regardless of status...")
            domain_filtered = domain_all
        
        # Get records with key fields
        fields = [
            'x_name',
            'x_studio_terminal',
            'x_studio_departure_train_id',
            'x_studio_arrival_train_id',
            'x_studio_selection_field_572_1j09lmu81',  # Pipeline status
            'x_studio_date_of_loading',
            'x_studio_loaded_wagons',
            'x_studio_number_of_material',
            'x_studio_one2many_field_3qn_1j34hmlba',  # Load List -> x_wagon_trip
            'x_studio_forwarding_order',
            'create_date',
            'write_date'
        ]
        
        records = api.execute_kw('x_rail_freight_order', 'search_read', [domain_filtered], {
            'fields': fields,
            'order': 'create_date desc',
            'limit': 10
        })
        
        print(f"\n✓ Found {len(records)} Siji rail freight orders")
        
        print("\nMost Recent Records:")
        print("-" * 80)
        for i, rec in enumerate(records[:5], 1):
            print(f"\n{i}. {rec.get('x_name')}")
            print(f"   Status: {rec.get('x_studio_selection_field_572_1j09lmu81')}")
            print(f"   Departure Train ID: {rec.get('x_studio_departure_train_id')}")
            print(f"   Loading Date: {rec.get('x_studio_date_of_loading')}")
            print(f"   Loaded Wagons: {rec.get('x_studio_loaded_wagons')}")
            print(f"   Number of Materials: {rec.get('x_studio_number_of_material')}")
            print(f"   Wagon Trip IDs: {len(rec.get('x_studio_one2many_field_3qn_1j34hmlba', []))} wagons")
            print(f"   Created: {rec.get('create_date')}")
        
        return records
        
    except Exception as e:
        print(f"✗ Error querying Siji records: {e}")
        import traceback
        traceback.print_exc()
        return []

def analyze_wagon_loading_progress(api, rail_freight_record):
    """Analyze wagon loading progress for a specific rail freight order"""
    print("\n" + "="*80)
    print("ANALYZING WAGON LOADING PROGRESS")
    print("="*80)
    
    print(f"\nRail Freight Order: {rail_freight_record.get('x_name')}")
    print(f"Status: {rail_freight_record.get('x_studio_selection_field_572_1j09lmu81')}")
    
    wagon_trip_ids = rail_freight_record.get('x_studio_one2many_field_3qn_1j34hmlba', [])
    
    if not wagon_trip_ids:
        print("\n⚠️ No wagon trips found for this record")
        print("This train may not have started loading yet.")
        return None
    
    print(f"\nWagon Trip IDs: {wagon_trip_ids}")
    print(f"Total wagons: {len(wagon_trip_ids)}")
    
    try:
        # Query wagon trips (removed x_studio_product - invalid field)
        fields = [
            'x_name',
            'x_studio_start_time',
            'x_studio_end_time',
            'x_studio_material',
            'x_studio_wagon',
            'create_date'
        ]
        
        wagons = api.execute_kw('x_wagon_trip', 'search_read', [[['id', 'in', wagon_trip_ids]]], {
            'fields': fields,
            'order': 'create_date asc'
        })
        
        print(f"\n✓ Retrieved {len(wagons)} wagon records")
        
        # Analyze loading status
        loaded = []  # Both start and end time set
        being_loaded = []  # Only start time set
        not_started = []  # No start time
        
        # Group by material
        material_stats = {}
        
        for wagon in wagons:
            start_time = wagon.get('x_studio_start_time')
            end_time = wagon.get('x_studio_end_time')
            material = wagon.get('x_studio_material')
            
            # Material grouping
            material_key = material[1] if material else 'Unknown'
            if material_key not in material_stats:
                material_stats[material_key] = {
                    'loaded': 0,
                    'being_loaded': 0,
                    'not_started': 0,
                    'total': 0,
                    'wagons': []
                }
            
            material_stats[material_key]['total'] += 1
            material_stats[material_key]['wagons'].append(wagon)
            
            # Loading status
            if start_time and end_time:
                loaded.append(wagon)
                material_stats[material_key]['loaded'] += 1
            elif start_time and not end_time:
                being_loaded.append(wagon)
                material_stats[material_key]['being_loaded'] += 1
            else:
                not_started.append(wagon)
                material_stats[material_key]['not_started'] += 1
        
        # Print summary
        print("\n" + "="*80)
        print("LOADING PROGRESS SUMMARY")
        print("="*80)
        print(f"\nTotal Wagons: {len(wagons)}")
        print(f"  ✓ Loaded (Complete): {len(loaded)}")
        print(f"  ⏳ Being Loaded: {len(being_loaded)}")
        print(f"  ⭕ Not Started: {len(not_started)}")
        
        if len(wagons) > 0:
            overall_progress = (len(loaded) / len(wagons)) * 100
            print(f"  Overall Progress: {overall_progress:.1f}%")
        
        print("\n" + "="*80)
        print("PER-MATERIAL BREAKDOWN")
        print("="*80)
        for material, stats in material_stats.items():
            print(f"\n📦 {material}:")
            print(f"   Total Wagons: {stats['total']}")
            print(f"   ✓ Loaded: {stats['loaded']}")
            print(f"   ⏳ Being Loaded: {stats['being_loaded']}")
            print(f"   ⭕ Not Started: {stats['not_started']}")
            if stats['total'] > 0:
                pct_complete = (stats['loaded'] / stats['total']) * 100
                print(f"   Progress: {pct_complete:.1f}%")
                
                # Progress bar
                bar_length = 20
                filled = int(bar_length * pct_complete / 100)
                bar = '█' * filled + '░' * (bar_length - filled)
                print(f"   [{bar}]")
        
        # Show sample wagon details
        print("\n" + "="*80)
        print("SAMPLE WAGON DETAILS (First 10)")
        print("="*80)
        for i, wagon in enumerate(wagons[:10], 1):
            print(f"\nWagon {i}:")
            print(f"  Name: {wagon.get('x_name')}")
            print(f"  Wagon: {wagon.get('x_studio_wagon', ['', 'Unknown'])[1] if wagon.get('x_studio_wagon') else 'Unknown'}")
            print(f"  Material: {wagon.get('x_studio_material', ['', 'Unknown'])[1] if wagon.get('x_studio_material') else 'Unknown'}")
            print(f"  Start Time: {wagon.get('x_studio_start_time') or 'Not started'}")
            print(f"  End Time: {wagon.get('x_studio_end_time') or 'Not finished'}")
            
            if wagon.get('x_studio_start_time') and wagon.get('x_studio_end_time'):
                status = "✓ LOADED"
            elif wagon.get('x_studio_start_time'):
                status = "⏳ BEING LOADED"
            else:
                status = "⭕ NOT STARTED"
            print(f"  Status: {status}")
        
        # Create dashboard data structure
        dashboard_data = {
            'train_id': rail_freight_record.get('x_studio_departure_train_id'),
            'status': rail_freight_record.get('x_studio_selection_field_572_1j09lmu81'),
            'loading_date': rail_freight_record.get('x_studio_date_of_loading'),
            'last_updated': rail_freight_record.get('write_date'),
            'materials': [],
            'overall': {
                'total_wagons': len(wagons),
                'loaded': len(loaded),
                'being_loaded': len(being_loaded),
                'not_started': len(not_started),
                'progress_percent': round((len(loaded) / len(wagons)) * 100, 1) if len(wagons) > 0 else 0
            }
        }
        
        for material, stats in material_stats.items():
            dashboard_data['materials'].append({
                'name': material,
                'total_wagons': stats['total'],
                'loaded': stats['loaded'],
                'being_loaded': stats['being_loaded'],
                'not_started': stats['not_started'],
                'progress_percent': round((stats['loaded'] / stats['total']) * 100, 1) if stats['total'] > 0 else 0
            })
        
        # Export dashboard data
        with open('siji_loading_progress_sample.json', 'w') as f:
            json.dump(dashboard_data, f, indent=2, default=str)
        
        print("\n" + "="*80)
        print("DASHBOARD DATA STRUCTURE")
        print("="*80)
        print(json.dumps(dashboard_data, indent=2, default=str))
        
        print("\n✓ Dashboard data exported to: siji_loading_progress_sample.json")
        
        return {
            'total': len(wagons),
            'loaded': len(loaded),
            'being_loaded': len(being_loaded),
            'not_started': len(not_started),
            'material_stats': material_stats,
            'wagons': wagons,
            'dashboard_data': dashboard_data
        }
        
    except Exception as e:
        print(f"✗ Error analyzing wagon trips: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    print("="*80)
    print("SIJI RAIL FREIGHT ORDER - WAGON LOADING PROGRESS ANALYSIS")
    print("WITH FULL ACCESS GRANTED! 🎉")
    print("="*80)
    
    api = OdooAPI()
    api.authenticate()
    
    # Get Siji rail freight orders
    rail_freight_records = get_siji_rail_freight_orders(api)
    
    if not rail_freight_records:
        print("\n⚠️ No Siji rail freight orders found")
        return
    
    # Analyze the most recent one
    print("\n" + "="*80)
    print("ANALYZING MOST RECENT SIJI RAIL FREIGHT ORDER")
    print("="*80)
    
    most_recent = rail_freight_records[0]
    progress = analyze_wagon_loading_progress(api, most_recent)
    
    if progress:
        print("\n" + "="*80)
        print("✓ ANALYSIS COMPLETE!")
        print("="*80)
        print("\nReady for dashboard implementation!")
        print("Dashboard data structure saved to: siji_loading_progress_sample.json")
    
    print("\n" + "="*80)
    print("NEXT STEPS")
    print("="*80)
    print("""
1. Review the dashboard data structure in siji_loading_progress_sample.json
2. Create backend API endpoint: GET /api/siji-loading-progress
3. Implement frontend component to display loading progress
4. Add real-time updates (auto-refresh every 30 seconds)
5. Test with different train statuses (Draft, Being Loaded, Train Departed)
    """)

if __name__ == "__main__":
    main()
