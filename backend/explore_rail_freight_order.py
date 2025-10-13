"""
Test script to explore the x_rail_freight_order model in Odoo
This script will help us understand the structure, fields, and data in this model
"""
import os
import sys
from dotenv import load_dotenv
import xmlrpc.client
from datetime import datetime, timedelta, timezone
import json

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

class OdooExplorer:
    def __init__(self):
        self.url = os.getenv('ODOO_URL')
        self.db = os.getenv('ODOO_DB')
        self.username = os.getenv('ODOO_USERNAME')
        self.api_key = os.getenv('ODOO_API_KEY')
        
        if not all([self.url, self.db, self.username, self.api_key]):
            raise ValueError("Missing required environment variables for Odoo connection")
        
        print(f"Connecting to Odoo at: {self.url}")
        print(f"Database: {self.db}")
        print(f"Username: {self.username}")
        print("-" * 80)
        
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
            print(f"✅ Successfully authenticated with Odoo, UID: {self.uid}\n")
            return True
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    def execute_kw(self, model: str, method: str, args=None, kwargs=None):
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
            print(f"❌ Error executing {method} on {model}: {e}")
            raise
    
    def get_model_fields(self, model_name):
        """Get all fields for a model"""
        print(f"\n{'='*80}")
        print(f"FIELDS FOR MODEL: {model_name}")
        print(f"{'='*80}\n")
        
        try:
            fields = self.execute_kw(
                model_name, 'fields_get',
                [],
                {'attributes': ['string', 'type', 'help', 'required', 'readonly']}
            )
            
            print(f"Total fields found: {len(fields)}\n")
            
            # Sort fields by name for easier reading
            sorted_fields = sorted(fields.items())
            
            for field_name, field_info in sorted_fields:
                print(f"Field: {field_name}")
                print(f"  Type: {field_info.get('type', 'N/A')}")
                print(f"  Label: {field_info.get('string', 'N/A')}")
                if field_info.get('help'):
                    print(f"  Help: {field_info.get('help')}")
                print(f"  Required: {field_info.get('required', False)}")
                print(f"  Readonly: {field_info.get('readonly', False)}")
                print()
            
            return fields
        except Exception as e:
            print(f"❌ Error getting fields: {e}")
            return None
    
    def get_record_count(self, model_name, domain=None):
        """Get total count of records in a model"""
        try:
            count = self.execute_kw(
                model_name, 'search_count',
                [domain or []]
            )
            return count
        except Exception as e:
            print(f"❌ Error counting records: {e}")
            return 0
    
    def get_sample_records(self, model_name, limit=5, domain=None, fields=None):
        """Get sample records from a model"""
        print(f"\n{'='*80}")
        print(f"SAMPLE RECORDS FROM: {model_name}")
        print(f"{'='*80}\n")
        
        try:
            # Get total count
            total_count = self.get_record_count(model_name, domain)
            print(f"Total records: {total_count}")
            print(f"Fetching {limit} sample records...\n")
            
            if total_count == 0:
                print("⚠️  No records found in this model")
                return []
            
            # Get sample records
            records = self.execute_kw(
                model_name, 'search_read',
                [domain or []],
                {'fields': fields, 'limit': limit, 'order': 'id desc'}
            )
            
            # Pretty print each record
            for i, record in enumerate(records, 1):
                print(f"\n--- Record {i} (ID: {record.get('id')}) ---")
                for key, value in sorted(record.items()):
                    if key == 'id':
                        continue
                    # Format the value nicely
                    if isinstance(value, (list, tuple)) and len(value) > 0 and isinstance(value[0], int):
                        # This is likely a Many2one or Many2many field
                        if len(value) == 2:
                            print(f"  {key}: {value[1]} (ID: {value[0]})")
                        else:
                            print(f"  {key}: {value}")
                    else:
                        print(f"  {key}: {value}")
            
            return records
        except Exception as e:
            print(f"❌ Error getting sample records: {e}")
            return []
    
    def get_recent_records(self, model_name, days=30, limit=10):
        """Get recent records based on creation date"""
        print(f"\n{'='*80}")
        print(f"RECENT RECORDS (Last {days} days) FROM: {model_name}")
        print(f"{'='*80}\n")
        
        try:
            # Calculate date range
            now_uae = datetime.now(self.uae_tz)
            days_ago = now_uae - timedelta(days=days)
            days_ago_utc = days_ago.astimezone(timezone.utc)
            
            # Try to find records with create_date
            domain = [['create_date', '>=', days_ago_utc.strftime('%Y-%m-%d %H:%M:%S')]]
            
            records = self.execute_kw(
                model_name, 'search_read',
                [domain],
                {'limit': limit, 'order': 'create_date desc'}
            )
            
            print(f"Found {len(records)} records created in the last {days} days\n")
            
            if len(records) == 0:
                print("⚠️  No recent records found. Trying without date filter...")
                return self.get_sample_records(model_name, limit=limit)
            
            # Pretty print each record
            for i, record in enumerate(records, 1):
                print(f"\n--- Recent Record {i} (ID: {record.get('id')}) ---")
                for key, value in sorted(record.items()):
                    if key == 'id':
                        continue
                    if isinstance(value, (list, tuple)) and len(value) > 0 and isinstance(value[0], int):
                        if len(value) == 2:
                            print(f"  {key}: {value[1]} (ID: {value[0]})")
                        else:
                            print(f"  {key}: {value}")
                    else:
                        print(f"  {key}: {value}")
            
            return records
        except Exception as e:
            print(f"❌ Error getting recent records: {e}")
            print("Trying to get sample records without date filter...")
            return self.get_sample_records(model_name, limit=limit)
    
    def export_fields_to_json(self, model_name, filename=None):
        """Export model fields to JSON file for documentation"""
        if filename is None:
            filename = f"{model_name.replace('.', '_')}_fields.json"
        
        fields = self.execute_kw(
            model_name, 'fields_get',
            [],
            {'attributes': ['string', 'type', 'help', 'required', 'readonly', 'relation']}
        )
        
        filepath = os.path.join(os.path.dirname(__file__), filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(fields, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Exported {len(fields)} fields to: {filepath}")
        return filepath


def main():
    """Main exploration function"""
    print("\n" + "="*80)
    print("ODOO MODEL EXPLORER - x_rail_freight_order")
    print("="*80 + "\n")
    
    explorer = OdooExplorer()
    
    # Authenticate
    if not explorer.authenticate():
        print("Failed to authenticate. Exiting.")
        sys.exit(1)
    
    model_name = 'x_rail_freight_order'
    
    # 1. Get and display all fields
    print("\n📋 Step 1: Exploring model fields...")
    fields = explorer.get_model_fields(model_name)
    
    if fields is None:
        print("\n❌ Model might not exist or you don't have access to it.")
        print("\nTrying alternative model names...")
        
        # Try alternative names
        alternative_names = [
            'x.rail.freight.order',
            'x_rail_freight',
            'rail.freight.order',
            'x_freight_order',
        ]
        
        for alt_name in alternative_names:
            print(f"\nTrying: {alt_name}")
            try:
                test_fields = explorer.get_model_fields(alt_name)
                if test_fields:
                    model_name = alt_name
                    print(f"\n✅ Found working model name: {model_name}")
                    fields = test_fields
                    break
            except:
                continue
    
    if fields is None:
        print("\n❌ Could not find the model. Please check the model name.")
        sys.exit(1)
    
    # 2. Get record count
    print("\n📊 Step 2: Checking record count...")
    total_records = explorer.get_record_count(model_name)
    print(f"Total records in {model_name}: {total_records}\n")
    
    # 3. Get sample records
    if total_records > 0:
        print("\n📝 Step 3: Fetching sample records...")
        explorer.get_sample_records(model_name, limit=3)
        
        # 4. Get recent records
        print("\n📅 Step 4: Fetching recent records...")
        explorer.get_recent_records(model_name, days=60, limit=5)
    
    # 5. Export fields to JSON
    print("\n💾 Step 5: Exporting field definitions...")
    explorer.export_fields_to_json(model_name)
    
    print("\n" + "="*80)
    print("EXPLORATION COMPLETE!")
    print("="*80 + "\n")
    
    # Summary
    print("\n📊 SUMMARY:")
    print(f"  Model Name: {model_name}")
    print(f"  Total Fields: {len(fields) if fields else 0}")
    print(f"  Total Records: {total_records}")
    print("\nCheck the generated JSON file for complete field definitions.")
    print("\n")


if __name__ == "__main__":
    main()
