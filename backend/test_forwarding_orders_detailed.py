"""
Test script to find and analyze forwarding orders WITH actual train departure data
This will help us understand which forwarding orders have complete data
"""
import os
from dotenv import load_dotenv
import xmlrpc.client
from datetime import datetime, timedelta, timezone

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

class ForwardingOrderAnalyzer:
    def __init__(self):
        self.url = os.getenv('ODOO_URL')
        self.db = os.getenv('ODOO_DB')
        self.username = os.getenv('ODOO_USERNAME')
        self.api_key = os.getenv('ODOO_API_KEY')
        
        self.common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
        self.models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
        self.uid = None
        self.uae_tz = timezone(timedelta(hours=4))
        
    def authenticate(self):
        try:
            self.uid = self.common.authenticate(self.db, self.username, self.api_key, {})
            print(f"✅ Authenticated (UID: {self.uid})\n")
            return bool(self.uid)
        except Exception as e:
            print(f"❌ Auth error: {e}")
            return False
    
    def execute_kw(self, model, method, args=None, kwargs=None):
        if not self.uid and not self.authenticate():
            raise Exception("Authentication failed")
        return self.models.execute_kw(
            self.db, self.uid, self.api_key,
            model, method, args or [], kwargs or {}
        )
    
    def find_orders_with_train_data(self):
        """Find forwarding orders that have train IDs and departure dates"""
        print("="*80)
        print("SEARCHING FOR FORWARDING ORDERS WITH TRAIN DATA")
        print("="*80 + "\n")
        
        # Search for orders with train IDs
        print("1. Looking for orders with Train IDs...")
        domain = [['x_studio_train_id', '!=', False]]
        count = self.execute_kw('x_fwo', 'search_count', [domain])
        print(f"   Found: {count} orders with train IDs\n")
        
        if count > 0:
            records = self.execute_kw('x_fwo', 'search_read', [domain], {
                'fields': ['id', 'x_name', 'x_studio_train_id', 'x_studio_actual_train_departure'],
                'limit': 10,
                'order': 'id desc'
            })
            
            print("   Sample records:")
            for rec in records:
                print(f"   - ID: {rec.get('id')} | Name: {rec.get('x_name')} | Train: {rec.get('x_studio_train_id')} | Departure: {rec.get('x_studio_actual_train_departure')}")
            print()
        
        # Search for orders with actual departure
        print("2. Looking for orders with Actual Train Departure dates...")
        domain = [['x_studio_actual_train_departure', '!=', False]]
        count = self.execute_kw('x_fwo', 'search_count', [domain])
        print(f"   Found: {count} orders with departure dates\n")
        
        if count > 0:
            records = self.execute_kw('x_fwo', 'search_read', [domain], {
                'fields': ['id', 'x_name', 'x_studio_train_id', 'x_studio_actual_train_departure'],
                'limit': 10,
                'order': 'id desc'
            })
            
            print("   Most recent departures:")
            for rec in records:
                print(f"   - {rec.get('x_studio_actual_train_departure')} | Train: {rec.get('x_studio_train_id')} | {rec.get('x_name')}")
            print()
        
        # Search for orders in specific statuses
        print("3. Looking for orders in 'Train Departed' status...")
        domain = [['x_studio_selection_field_83c_1ig067df9', '=', 'NDP Train Departed']]
        count = self.execute_kw('x_fwo', 'search_count', [domain])
        print(f"   Found: {count} orders\n")
        
        if count > 0:
            records = self.execute_kw('x_fwo', 'search_read', [domain], {
                'fields': ['id', 'x_name', 'x_studio_train_id', 'x_studio_actual_train_departure'],
                'limit': 10,
                'order': 'id desc'
            })
            
            print("   Sample departed trains:")
            for rec in records:
                print(f"   - ID: {rec.get('id')} | {rec.get('x_name')} | Train: {rec.get('x_studio_train_id')} | Dep: {rec.get('x_studio_actual_train_departure')}")
            print()
        
        # Check this week's data
        print("4. Looking for orders this week...")
        now_uae = datetime.now(self.uae_tz)
        days_since_monday = now_uae.weekday()
        week_start = (now_uae - timedelta(days=days_since_monday)).replace(
            hour=0, minute=0, second=0, microsecond=0
        ).astimezone(timezone.utc)
        
        domain = [
            ['x_studio_actual_train_departure', '>=', week_start.strftime('%Y-%m-%d %H:%M:%S')]
        ]
        count = self.execute_kw('x_fwo', 'search_count', [domain])
        print(f"   Found: {count} trains this week\n")
        
        if count > 0:
            records = self.execute_kw('x_fwo', 'search_read', [domain], {
                'fields': ['id', 'x_name', 'x_studio_train_id', 'x_studio_actual_train_departure'],
                'order': 'id desc'
            })
            
            print("   This week's trains:")
            for rec in records[:10]:
                print(f"   - {rec.get('x_studio_actual_train_departure')} | Train: {rec.get('x_studio_train_id')} | {rec.get('x_name')}")
            print()
    
    def get_status_field_options(self):
        """Get all possible status values"""
        print("="*80)
        print("STATUS FIELD OPTIONS")
        print("="*80 + "\n")
        
        fields = self.execute_kw('x_fwo', 'fields_get', [], {'attributes': ['selection']})
        status_field = 'x_studio_selection_field_83c_1ig067df9'
        
        if status_field in fields and 'selection' in fields[status_field]:
            print(f"Field: {fields[status_field].get('string', status_field)}")
            print("Options:")
            for value, label in fields[status_field]['selection']:
                count = self.execute_kw('x_fwo', 'search_count', [[[status_field, '=', value]]])
                print(f"  - '{value}': {label} ({count} records)")
            print()
    
    def analyze_date_fields(self):
        """Check which date fields have data"""
        print("="*80)
        print("DATE FIELD ANALYSIS")
        print("="*80 + "\n")
        
        fields = self.execute_kw('x_fwo', 'fields_get', [], {'attributes': ['type', 'string']})
        
        date_fields = {k: v for k, v in fields.items() 
                      if v.get('type') in ['date', 'datetime'] 
                      and 'studio' in k.lower()}
        
        print("Checking date fields for data...\n")
        for field_name, field_info in sorted(date_fields.items()):
            count = self.execute_kw('x_fwo', 'search_count', [[[field_name, '!=', False]]])
            percentage = (count / 1079) * 100 if count > 0 else 0
            status = "✅" if count > 0 else "⚠️ "
            print(f"{status} {field_name}")
            print(f"   Label: {field_info.get('string')}")
            print(f"   Records with data: {count} ({percentage:.1f}%)")
            print()
    
    def get_complete_sample(self):
        """Get a complete sample record with all fields"""
        print("="*80)
        print("COMPLETE SAMPLE RECORD")
        print("="*80 + "\n")
        
        # Find an order with the most data
        domain = [['x_studio_actual_train_departure', '!=', False]]
        records = self.execute_kw('x_fwo', 'search_read', [domain], {
            'limit': 1,
            'order': 'id desc'
        })
        
        if records:
            print("Most recent forwarding order with train departure:\n")
            record = records[0]
            for key, value in sorted(record.items()):
                if value and value != False:
                    print(f"{key}: {value}")
        else:
            print("No records found with train departure data")


def main():
    print("\n" + "="*80)
    print("FORWARDING ORDER DATA ANALYSIS")
    print("="*80 + "\n")
    
    analyzer = ForwardingOrderAnalyzer()
    
    if not analyzer.authenticate():
        return
    
    # Run all analyses
    analyzer.get_status_field_options()
    analyzer.find_orders_with_train_data()
    analyzer.analyze_date_fields()
    analyzer.get_complete_sample()
    
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
