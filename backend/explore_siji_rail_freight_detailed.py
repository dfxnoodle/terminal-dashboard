#!/usr/bin/env python3
"""
Explore Siji Departed Trains in x_rail_freight_order Model
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

def explore_wagon_trip_model(api):
    """Explore the x_wagon_trip model structure"""
    print("\n" + "="*80)
    print("EXPLORING x_wagon_trip MODEL STRUCTURE")
    print("="*80)
    
    try:
        fields_info = api.execute_kw('x_wagon_trip', 'fields_get', [], {
            'attributes': ['string', 'type', 'required', 'readonly', 'help', 'relation']
        })
        
        print(f"\nTotal fields in x_wagon_trip: {len(fields_info)}")
        
        # Key fields we're looking for
        key_fields = [
            'x_studio_start_time',
            'x_studio_end_time',
            'x_studio_material',
            'x_studio_wagon',
            'x_studio_wagon_number',
            'x_studio_product',
            'x_name',
            'create_date',
            'x_studio_rail_freight_order'
        ]
        
        print("\nKey Fields for Loading Progress:")
        print("-" * 80)
        for field in key_fields:
            if field in fields_info:
                info = fields_info[field]
                print(f"✓ {field}")
                print(f"  Type: {info.get('type')}")
                print(f"  Label: {info.get('string')}")
                if info.get('relation'):
                    print(f"  Relation: {info.get('relation')}")
                if info.get('help'):
                    print(f"  Help: {info.get('help')}")
                print()
        
        # Export full field list
        with open('x_wagon_trip_fields.json', 'w') as f:
            json.dump(fields_info, f, indent=2, default=str)
        print(f"✓ Full field list exported to x_wagon_trip_fields.json")
        
        # Get a count of records
        count = api.execute_kw('x_wagon_trip', 'search_count', [[]])
        print(f"\nTotal x_wagon_trip records: {count:,}")
        
        return fields_info
        
    except Exception as e:
        print(f"✗ Error exploring x_wagon_trip: {e}")
        return None

def get_siji_rail_freight_orders_direct(api):
    """Try to get Siji rail freight orders directly"""
    print("\n" + "="*80)
    print("QUERYING SIJI RAIL FREIGHT ORDERS (DIRECT)")
    print("="*80)
    
    try:
        # Try to search directly with minimal domain
        domain = [
            ['x_studio_terminal', '=', 'Siji']
        ]
        
        # First, just count
        count = api.execute_kw('x_rail_freight_order', 'search_count', [domain])
        print(f"\nTotal Siji rail freight orders: {count}")
        
        if count == 0:
            print("No records found. Let's check all terminals...")
            all_count = api.execute_kw('x_rail_freight_order', 'search_count', [[]])
            print(f"Total rail freight orders (all terminals): {all_count}")
            
            if all_count > 0:
                # Get some samples to see what terminals exist
                samples = api.execute_kw('x_rail_freight_order', 'search_read', [[]], {
                    'fields': ['x_name', 'x_studio_terminal', 'create_date'],
                    'limit': 10
                })
                print(f"\nSample records:")
                for rec in samples:
                    print(f"  - {rec.get('x_name')} | Terminal: {rec.get('x_studio_terminal')} | Created: {rec.get('create_date')}")
            return []
        
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
            'create_date'
        ]
        
        records = api.execute_kw('x_rail_freight_order', 'search_read', [domain], {
            'fields': fields,
            'order': 'create_date desc',
            'limit': 20
        })
        
        print(f"\n✓ Found {len(records)} Siji rail freight orders")
        
        return records
        
    except Exception as e:
        print(f"✗ Error with direct query: {e}")
        print("\nTrying alternative approach via FWO...")
        return get_siji_rail_freight_orders_via_fwo(api)

def get_siji_rail_freight_orders_via_fwo(api):
    """Get Siji rail freight orders via forwarding orders workaround"""
    print("\n" + "="*80)
    print("QUERYING SIJI RAIL FREIGHT ORDERS (via FWO)")
    print("="*80)
    
    try:
        # Query forwarding orders for Siji with rail freight orders
        domain = [
            ['x_studio_rail_freight_order', '!=', False],
            ['x_studio_origin_terminal', '=', 'Siji']
        ]
        
        fields = [
            'x_studio_rail_freight_order',  # Returns [ID, "Name | TrainID"]
            'x_studio_actual_train_departure',
            'x_studio_train_id',
            'create_date',
            'x_studio_origin_terminal'
        ]
        
        fwos = api.execute_kw('x_fwo', 'search_read', [domain], {
            'fields': fields,
            'order': 'create_date desc',
            'limit': 20
        })
        
        print(f"\nFound {len(fwos)} Siji FWOs with Rail Freight Orders")
        
        # Extract unique rail freight order IDs
        rail_freight_ids = []
        for fwo in fwos:
            if fwo.get('x_studio_rail_freight_order'):
                rf_id = fwo['x_studio_rail_freight_order'][0]
                rail_freight_ids.append(rf_id)
        
        unique_rf_ids = list(set(rail_freight_ids))
        print(f"Unique Rail Freight Order IDs: {unique_rf_ids}")
        
        return unique_rf_ids, fwos
        
    except Exception as e:
        print(f"✗ Error querying FWOs: {e}")
        return [], []

def try_direct_rail_freight_access(api, rf_ids):
    """Attempt direct access to x_rail_freight_order records"""
    print("\n" + "="*80)
    print("ATTEMPTING DIRECT x_rail_freight_order ACCESS")
    print("="*80)
    
    if not rf_ids:
        print("No Rail Freight Order IDs to query")
        return []
    
    try:
        # Try with basic fields only (avoid computed fields)
        fields = [
            'x_name',
            'x_studio_terminal',
            'x_studio_departure_train_id',
            'x_studio_arrival_train_id',
            'x_studio_date_of_loading',
            'x_studio_loaded_wagons',
            'x_studio_number_of_material',
            'x_studio_selection_field_572_1j09lmu81',  # Pipeline status
            'x_studio_one2many_field_3qn_1j34hmlba',  # Load List -> x_wagon_trip
            'x_studio_forwarding_order',
            'create_date'
        ]
        
        domain = [['id', 'in', rf_ids]]
        
        records = api.execute_kw('x_rail_freight_order', 'search_read', [domain], {
            'fields': fields,
            'order': 'create_date desc'
        })
        
        print(f"\n✓ Successfully retrieved {len(records)} Rail Freight Orders!")
        
        for i, rec in enumerate(records, 1):
            print(f"\n--- Record {i} ---")
            print(f"ID: {rec.get('id')}")
            print(f"Name: {rec.get('x_name')}")
            print(f"Terminal: {rec.get('x_studio_terminal')}")
            print(f"Status: {rec.get('x_studio_selection_field_572_1j09lmu81')}")
            print(f"Departure Train ID: {rec.get('x_studio_departure_train_id')}")
            print(f"Arrival Train ID: {rec.get('x_studio_arrival_train_id')}")
            print(f"Loading Date: {rec.get('x_studio_date_of_loading')}")
            print(f"Loaded Wagons: {rec.get('x_studio_loaded_wagons')}")
            print(f"Number of Materials: {rec.get('x_studio_number_of_material')}")
            print(f"Wagon Trip IDs: {rec.get('x_studio_one2many_field_3qn_1j34hmlba')}")
            print(f"Forwarding Orders: {rec.get('x_studio_forwarding_order')}")
            print(f"Created: {rec.get('create_date')}")
        
        return records
        
    except Exception as e:
        print(f"✗ Error with direct access: {e}")
        print("\nAttempting workaround with minimal fields...")
        
        try:
            # Try with even fewer fields
            minimal_fields = ['x_name', 'x_studio_terminal', 'create_date']
            records = api.execute_kw('x_rail_freight_order', 'search_read', [domain], {
                'fields': minimal_fields
            })
            print(f"✓ Minimal query worked: {len(records)} records")
            return records
        except Exception as e2:
            print(f"✗ Even minimal query failed: {e2}")
            return []

def analyze_wagon_loading_progress(api, rail_freight_record):
    """Analyze wagon loading progress for a specific rail freight order"""
    print("\n" + "="*80)
    print("ANALYZING WAGON LOADING PROGRESS")
    print("="*80)
    
    wagon_trip_ids = rail_freight_record.get('x_studio_one2many_field_3qn_1j34hmlba', [])
    
    if not wagon_trip_ids:
        print("No wagon trips found for this record")
        return None
    
    print(f"\nWagon Trip IDs: {wagon_trip_ids}")
    print(f"Total wagons: {len(wagon_trip_ids)}")
    
    try:
        # Query wagon trips
        fields = [
            'x_name',
            'x_studio_start_time',
            'x_studio_end_time',
            'x_studio_material',
            'x_studio_product',
            'x_studio_wagon',
            'x_studio_wagon_number',
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
                    'total': 0
                }
            
            material_stats[material_key]['total'] += 1
            
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
        print("\n" + "-"*80)
        print("LOADING PROGRESS SUMMARY")
        print("-"*80)
        print(f"Total Wagons: {len(wagons)}")
        print(f"✓ Loaded (Complete): {len(loaded)}")
        print(f"⏳ Being Loaded: {len(being_loaded)}")
        print(f"⭕ Not Started: {len(not_started)}")
        
        print("\n" + "-"*80)
        print("PER-MATERIAL BREAKDOWN")
        print("-"*80)
        for material, stats in material_stats.items():
            print(f"\n{material}:")
            print(f"  Total Wagons: {stats['total']}")
            print(f"  ✓ Loaded: {stats['loaded']}")
            print(f"  ⏳ Being Loaded: {stats['being_loaded']}")
            print(f"  ⭕ Not Started: {stats['not_started']}")
            if stats['total'] > 0:
                pct_complete = (stats['loaded'] / stats['total']) * 100
                print(f"  Progress: {pct_complete:.1f}%")
        
        # Show sample wagon details
        print("\n" + "-"*80)
        print("SAMPLE WAGON DETAILS (First 5)")
        print("-"*80)
        for i, wagon in enumerate(wagons[:5], 1):
            print(f"\nWagon {i}:")
            print(f"  Name: {wagon.get('x_name')}")
            print(f"  Wagon Number: {wagon.get('x_studio_wagon_number')}")
            print(f"  Material: {wagon.get('x_studio_material')}")
            print(f"  Product: {wagon.get('x_studio_product')}")
            print(f"  Start Time: {wagon.get('x_studio_start_time')}")
            print(f"  End Time: {wagon.get('x_studio_end_time')}")
            
            if wagon.get('x_studio_start_time') and wagon.get('x_studio_end_time'):
                status = "✓ LOADED"
            elif wagon.get('x_studio_start_time'):
                status = "⏳ BEING LOADED"
            else:
                status = "⭕ NOT STARTED"
            print(f"  Status: {status}")
        
        return {
            'total': len(wagons),
            'loaded': len(loaded),
            'being_loaded': len(being_loaded),
            'not_started': len(not_started),
            'material_stats': material_stats,
            'wagons': wagons
        }
        
    except Exception as e:
        print(f"✗ Error analyzing wagon trips: {e}")
        return None

def main():
    print("="*80)
    print("SIJI RAIL FREIGHT ORDER - WAGON LOADING PROGRESS EXPLORER")
    print("="*80)
    
    api = OdooAPI()
    api.authenticate()
    
    # Step 1: Explore x_wagon_trip model
    wagon_trip_fields = explore_wagon_trip_model(api)
    
    # Step 2: Get Siji rail freight orders directly
    rail_freight_records = get_siji_rail_freight_orders_direct(api)
    
    # Step 3: Analyze wagon loading for the most recent record
    if rail_freight_records:
        print("\n" + "="*80)
        print("ANALYZING MOST RECENT SIJI RAIL FREIGHT ORDER")
        print("="*80)
        
        # Sort by create_date and get most recent
        sorted_records = sorted(rail_freight_records, 
                               key=lambda x: x.get('create_date', ''), 
                               reverse=True)
        
        most_recent = sorted_records[0]
        print(f"\nMost Recent Record:")
        print(f"Name: {most_recent.get('x_name')}")
        print(f"Status: {most_recent.get('x_studio_selection_field_572_1j09lmu81')}")
        print(f"Created: {most_recent.get('create_date')}")
        
        # Analyze its wagon loading progress
        progress = analyze_wagon_loading_progress(api, most_recent)
        
        if progress:
            print("\n" + "="*80)
            print("DASHBOARD PRESENTATION RECOMMENDATION")
            print("="*80)
            print("""
Recommended Dashboard Layout:
            
┌─────────────────────────────────────────────────────────┐
│ 🚂 Train Loading Progress - Siji Terminal              │
├─────────────────────────────────────────────────────────┤
│ Train: {departure_train_id}                             │
│ Status: {pipeline_status}                               │
│ Loading Date: {date_of_loading}                         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ Material 1: FALA Drainage Blanket 0-40mm               │
│ Progress: ████████████░░░░  75% (15/20 wagons)         │
│ ✓ Loaded: 15  ⏳ Loading: 3  ⭕ Pending: 2              │
│                                                          │
│ Material 2: Aggregates 20-40mm                         │
│ Progress: ██████████████░░  85% (17/20 wagons)         │
│ ✓ Loaded: 17  ⏳ Loading: 2  ⭕ Pending: 1              │
│                                                          │
├─────────────────────────────────────────────────────────┤
│ Total: 32/40 wagons loaded (80%)                        │
│ Last Updated: 2 minutes ago                             │
└─────────────────────────────────────────────────────────┘

Data Structure for Frontend:
{
  "train_id": "4DC14",
  "status": "Train Departed",
  "loading_date": "2025-10-12",
  "last_updated": "2025-10-13T10:30:00Z",
  "materials": [
    {
      "name": "FALA Drainage Blanket 0-40mm",
      "total_wagons": 20,
      "loaded": 15,
      "being_loaded": 3,
      "not_started": 2,
      "progress_percent": 75
    },
    {
      "name": "Aggregates 20-40mm",
      "total_wagons": 20,
      "loaded": 17,
      "being_loaded": 2,
      "not_started": 1,
      "progress_percent": 85
    }
  ],
  "overall": {
    "total_wagons": 40,
    "loaded": 32,
    "being_loaded": 5,
    "not_started": 3,
    "progress_percent": 80
  }
}
            """)
    
    print("\n" + "="*80)
    print("EXPLORATION COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()
