"""
Comprehensive test script to explore rail freight operations models
This will check x_rail_freight_order and related models for data and relationships
"""
import os
import sys
from dotenv import load_dotenv
import xmlrpc.client
from datetime import datetime, timedelta, timezone
import json

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

class RailFreightExplorer:
    def __init__(self):
        self.url = os.getenv('ODOO_URL')
        self.db = os.getenv('ODOO_DB')
        self.username = os.getenv('ODOO_USERNAME')
        self.api_key = os.getenv('ODOO_API_KEY')
        
        if not all([self.url, self.db, self.username, self.api_key]):
            raise ValueError("Missing required environment variables")
        
        print(f"\n{'='*80}")
        print(f"RAIL FREIGHT OPERATIONS EXPLORER")
        print(f"{'='*80}")
        print(f"Connecting to: {self.url}")
        print(f"Database: {self.db}")
        print(f"{'='*80}\n")
        
        self.common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
        self.models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
        self.uid = None
        self.uae_tz = timezone(timedelta(hours=4))
        
    def authenticate(self):
        """Authenticate with Odoo"""
        try:
            self.uid = self.common.authenticate(self.db, self.username, self.api_key, {})
            if not self.uid:
                raise Exception("Authentication failed")
            print(f"✅ Authenticated successfully (UID: {self.uid})\n")
            return True
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    def execute_kw(self, model, method, args=None, kwargs=None):
        """Execute Odoo API call"""
        if not self.uid:
            if not self.authenticate():
                raise Exception("Failed to authenticate")
        
        try:
            return self.models.execute_kw(
                self.db, self.uid, self.api_key,
                model, method,
                args or [],
                kwargs or {}
            )
        except Exception as e:
            print(f"❌ Error executing {method} on {model}: {e}")
            return None
    
    def explore_model(self, model_name, description=""):
        """Get basic info about a model"""
        print(f"\n{'─'*80}")
        print(f"📦 Model: {model_name}")
        if description:
            print(f"   {description}")
        print(f"{'─'*80}")
        
        try:
            # Get record count
            count = self.execute_kw(model_name, 'search_count', [[]])
            print(f"   Total Records: {count}")
            
            if count > 0:
                # Get a sample record
                records = self.execute_kw(
                    model_name, 'search_read',
                    [[]],
                    {'limit': 1, 'order': 'id desc'}
                )
                if records:
                    print(f"   Latest Record ID: {records[0].get('id')}")
                    if 'x_name' in records[0]:
                        print(f"   Latest Name: {records[0].get('x_name')}")
                    if 'create_date' in records[0]:
                        print(f"   Created: {records[0].get('create_date')}")
            
            return count > 0
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    def check_forwarding_order_relationship(self):
        """Check the relationship between rail freight orders and forwarding orders"""
        print(f"\n{'='*80}")
        print(f"🔗 CHECKING FORWARDING ORDER RELATIONSHIP")
        print(f"{'='*80}\n")
        
        # Get forwarding orders
        fwo_count = self.execute_kw('x_fwo', 'search_count', [[]])
        print(f"Forwarding Orders (x_fwo): {fwo_count} records")
        
        if fwo_count > 0:
            # Get sample forwarding orders with train info
            fwo_records = self.execute_kw(
                'x_fwo', 'search_read',
                [[]],
                {
                    'fields': ['id', 'x_name', 'x_studio_train_id', 'x_studio_actual_train_departure'],
                    'limit': 5,
                    'order': 'id desc'
                }
            )
            
            print(f"\nSample Forwarding Orders:")
            for fwo in fwo_records:
                print(f"  ID: {fwo.get('id')}")
                print(f"    Name: {fwo.get('x_name')}")
                print(f"    Train ID: {fwo.get('x_studio_train_id')}")
                print(f"    Departure: {fwo.get('x_studio_actual_train_departure')}")
                print()
            
            # Check if any forwarding orders reference rail freight orders
            print("\nChecking for rail freight order references in forwarding orders...")
            fields = self.execute_kw('x_fwo', 'fields_get', [], {})
            rail_freight_fields = [k for k in fields.keys() if 'rail' in k.lower() or 'freight' in k.lower()]
            
            if rail_freight_fields:
                print(f"Found potential rail freight fields in x_fwo:")
                for field in rail_freight_fields:
                    print(f"  - {field}: {fields[field].get('string')}")
            else:
                print("  No direct rail freight fields found in forwarding orders")
    
    def check_load_list(self):
        """Try to find the load list model"""
        print(f"\n{'='*80}")
        print(f"📋 CHECKING LOAD LIST MODEL")
        print(f"{'='*80}\n")
        
        potential_models = [
            'x_load_list',
            'x_rail_load_list',
            'x_wagon_load',
            'x_rail_freight_load',
            'x.load.list',
        ]
        
        for model in potential_models:
            try:
                count = self.execute_kw(model, 'search_count', [[]])
                if count is not None:
                    print(f"✅ Found model: {model} ({count} records)")
                    return model
            except:
                continue
        
        print("❌ Could not find load list model")
        return None
    
    def get_selection_values(self, model, field_name):
        """Get selection field options"""
        try:
            fields = self.execute_kw(model, 'fields_get', [], {'attributes': ['selection']})
            if field_name in fields and 'selection' in fields[field_name]:
                return fields[field_name]['selection']
        except:
            pass
        return None
    
    def show_important_selections(self):
        """Show selection field values for rail freight order"""
        print(f"\n{'='*80}")
        print(f"🎯 SELECTION FIELD OPTIONS")
        print(f"{'='*80}\n")
        
        model = 'x_rail_freight_order'
        important_fields = [
            'x_studio_terminal',
            'x_studio_loading_method',
            'x_studio_number_of_material',
            'x_studio_selection_field_572_1j09lmu81',
        ]
        
        for field in important_fields:
            values = self.get_selection_values(model, field)
            if values:
                print(f"{field}:")
                for value in values:
                    print(f"  - {value[0]}: {value[1]}")
                print()
            else:
                print(f"{field}: No selection values found\n")
    
    def check_all_rail_models(self):
        """Check all models that might be related to rail operations"""
        print(f"\n{'='*80}")
        print(f"🚂 CHECKING ALL RAIL-RELATED MODELS")
        print(f"{'='*80}\n")
        
        models_to_check = {
            'x_rail_freight_order': 'Rail Freight Orders',
            'x_fwo': 'Forwarding Orders',
            'x_first_mile_freight': 'First Mile Truck Orders',
            'x_last_mile_freight': 'Last Mile Truck Orders',
            'x_stockpile': 'Stockpile/Inventory',
            'x_material': 'Bulk Materials',
            'x_stock_adj': 'Stock Adjustments',
            'x_shipper': 'Customers/Shippers',
            'x_transporter': 'Transporters/Carriers',
        }
        
        results = {}
        for model, desc in models_to_check.items():
            has_data = self.explore_model(model, desc)
            results[model] = has_data
        
        print(f"\n{'='*80}")
        print(f"SUMMARY")
        print(f"{'='*80}\n")
        
        print("Models with data:")
        for model, has_data in results.items():
            status = "✅" if has_data else "⚠️ "
            print(f"  {status} {model}: {models_to_check[model]}")
        print()
    
    def analyze_terminal_distribution(self):
        """Analyze which terminals have data in various models"""
        print(f"\n{'='*80}")
        print(f"🏭 TERMINAL DISTRIBUTION ANALYSIS")
        print(f"{'='*80}\n")
        
        models_with_terminal = [
            ('x_first_mile_freight', 'First Mile Trucks'),
            ('x_last_mile_freight', 'Last Mile Trucks'),
            ('x_stockpile', 'Stockpiles'),
        ]
        
        terminals = ['NDP', 'ICAD', 'DIC']
        
        for model, desc in models_with_terminal:
            print(f"\n{desc} ({model}):")
            for terminal in terminals:
                try:
                    count = self.execute_kw(
                        model, 'search_count',
                        [[['x_studio_terminal', '=', terminal]]]
                    )
                    if count is not None:
                        print(f"  {terminal}: {count} records")
                except Exception as e:
                    print(f"  {terminal}: Error - {e}")


def main():
    explorer = RailFreightExplorer()
    
    if not explorer.authenticate():
        print("Failed to authenticate. Exiting.")
        sys.exit(1)
    
    # 1. Check all rail-related models
    explorer.check_all_rail_models()
    
    # 2. Check terminal distribution
    explorer.analyze_terminal_distribution()
    
    # 3. Check forwarding order relationship
    explorer.check_forwarding_order_relationship()
    
    # 4. Show selection field options
    explorer.show_important_selections()
    
    # 5. Try to find load list
    explorer.check_load_list()
    
    print(f"\n{'='*80}")
    print(f"✅ EXPLORATION COMPLETE")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
