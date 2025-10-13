#!/usr/bin/env python3
"""
Test x_rail_freight_order permissions vs actual emptiness
"""

import os
import json
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
        print(f"✓ Authenticated as UID: {self.uid} ({self.username})")
        return self.uid
        
    def execute_kw(self, model, method, args, kwargs=None):
        """Execute Odoo API call"""
        if kwargs is None:
            kwargs = {}
        return self.models.execute_kw(
            self.db, self.uid, self.api_key,
            model, method, args, kwargs
        )

def test_model_access(api):
    """Test various access methods to x_rail_freight_order"""
    print("\n" + "="*80)
    print("TEST 1: Check Model Exists")
    print("="*80)
    
    try:
        # Test if we can get field info (this tests read access to metadata)
        fields = api.execute_kw('x_rail_freight_order', 'fields_get', [], {
            'attributes': ['string', 'type']
        })
        print(f"✓ SUCCESS: Model exists with {len(fields)} fields")
        print(f"  We CAN access model metadata")
    except Exception as e:
        print(f"✗ FAILED: Cannot access model metadata")
        print(f"  Error: {e}")
        return False
    
    return True

def test_search_count(api):
    """Test search_count with various domains"""
    print("\n" + "="*80)
    print("TEST 2: Search Count (No Filter)")
    print("="*80)
    
    try:
        # Empty domain = count all records
        count = api.execute_kw('x_rail_freight_order', 'search_count', [[]])
        print(f"✓ SUCCESS: search_count returned {count}")
        if count == 0:
            print(f"  → Model is EMPTY (or we can't see any records)")
        else:
            print(f"  → Model has {count} records visible to us")
        return count
    except Exception as e:
        print(f"✗ FAILED: Cannot execute search_count")
        print(f"  Error: {e}")
        print(f"  → This suggests NO READ ACCESS to records")
        return None

def test_search_ids(api):
    """Test search to get IDs"""
    print("\n" + "="*80)
    print("TEST 3: Search for Record IDs")
    print("="*80)
    
    try:
        # Get first 10 record IDs
        ids = api.execute_kw('x_rail_freight_order', 'search', [[]], {
            'limit': 10
        })
        print(f"✓ SUCCESS: search returned {len(ids)} IDs")
        if ids:
            print(f"  IDs: {ids}")
            return ids
        else:
            print(f"  → No record IDs found (empty model or no access)")
            return []
    except Exception as e:
        print(f"✗ FAILED: Cannot execute search")
        print(f"  Error: {e}")
        return None

def test_check_access_rights(api):
    """Test check_access_rights method"""
    print("\n" + "="*80)
    print("TEST 4: Check Access Rights")
    print("="*80)
    
    operations = ['read', 'write', 'create', 'unlink']
    
    for operation in operations:
        try:
            has_access = api.execute_kw('x_rail_freight_order', 'check_access_rights', 
                                       [operation], {'raise_exception': False})
            status = "✓ GRANTED" if has_access else "✗ DENIED"
            print(f"  {operation.upper()}: {status}")
        except Exception as e:
            print(f"  {operation.upper()}: ✗ ERROR - {e}")

def test_read_specific_ids(api, ids):
    """Try to read specific record IDs"""
    print("\n" + "="*80)
    print("TEST 5: Read Specific Record IDs")
    print("="*80)
    
    if not ids:
        print("  Skipping: No IDs to test")
        return
    
    try:
        # Try to read just the ID and name
        records = api.execute_kw('x_rail_freight_order', 'read', [ids], {
            'fields': ['id', 'x_name']
        })
        print(f"✓ SUCCESS: Read {len(records)} records")
        for rec in records[:3]:  # Show first 3
            print(f"  - ID {rec['id']}: {rec.get('x_name', 'N/A')}")
    except Exception as e:
        print(f"✗ FAILED: Cannot read records")
        print(f"  Error: {e}")
        if "access" in str(e).lower():
            print(f"  → This is a PERMISSION ISSUE")
        else:
            print(f"  → This may be another type of error")

def test_search_read_minimal(api):
    """Test search_read with minimal fields"""
    print("\n" + "="*80)
    print("TEST 6: Search Read with Minimal Fields")
    print("="*80)
    
    try:
        records = api.execute_kw('x_rail_freight_order', 'search_read', [[]], {
            'fields': ['id', 'create_date'],
            'limit': 5
        })
        print(f"✓ SUCCESS: search_read returned {len(records)} records")
        if records:
            print(f"  Sample records:")
            for rec in records:
                print(f"    - ID {rec['id']}: Created {rec.get('create_date', 'N/A')}")
            return records
        else:
            print(f"  → No records found (model is empty)")
            return []
    except Exception as e:
        print(f"✗ FAILED: Cannot execute search_read")
        print(f"  Error: {e}")
        if "access" in str(e).lower() or "read" in str(e).lower():
            print(f"  → This is a PERMISSION ISSUE")
        return None

def test_via_fwo_linkage(api):
    """Test accessing via FWO linkage"""
    print("\n" + "="*80)
    print("TEST 7: Access via FWO Linkage (Known Workaround)")
    print("="*80)
    
    try:
        # Get FWOs that have rail freight orders
        fwos = api.execute_kw('x_fwo', 'search_read', 
            [[['x_studio_rail_freight_order', '!=', False]]], {
            'fields': ['x_studio_rail_freight_order', 'x_studio_train_id'],
            'limit': 10
        })
        
        if fwos:
            print(f"✓ SUCCESS: Found {len(fwos)} FWOs with rail freight order links")
            
            # Extract rail freight order IDs
            rf_ids = set()
            for fwo in fwos:
                if fwo.get('x_studio_rail_freight_order'):
                    rf_id = fwo['x_studio_rail_freight_order'][0]
                    rf_name = fwo['x_studio_rail_freight_order'][1]
                    rf_ids.add(rf_id)
                    print(f"  FWO Train {fwo.get('x_studio_train_id')}: RF Order {rf_id} ({rf_name})")
            
            print(f"\n  Total unique Rail Freight Order IDs referenced: {len(rf_ids)}")
            print(f"  IDs: {sorted(rf_ids)}")
            
            # Try to read those IDs directly
            if rf_ids:
                print(f"\n  Attempting to read these IDs directly...")
                try:
                    records = api.execute_kw('x_rail_freight_order', 'read', 
                                            [list(rf_ids)[:5]], {
                        'fields': ['id', 'x_name']
                    })
                    print(f"  ✓ SUCCESS: Can read {len(records)} records via FWO IDs")
                    for rec in records:
                        print(f"    - ID {rec['id']}: {rec.get('x_name')}")
                except Exception as e:
                    print(f"  ✗ FAILED: Cannot read even with known IDs")
                    print(f"    Error: {e}")
                    if "access" in str(e).lower():
                        print(f"    → PERMISSION ISSUE: FWO can link to it, but we can't read it")
            
            return rf_ids
        else:
            print(f"  No FWOs with rail freight orders found")
            return set()
    except Exception as e:
        print(f"✗ FAILED: Cannot query FWOs")
        print(f"  Error: {e}")
        return None

def test_model_schema(api):
    """Check if model has proper schema vs being disabled"""
    print("\n" + "="*80)
    print("TEST 8: Model Schema Analysis")
    print("="*80)
    
    try:
        fields = api.execute_kw('x_rail_freight_order', 'fields_get', [], {
            'attributes': ['string', 'type', 'required', 'readonly', 'store']
        })
        
        # Count different field types
        field_types = {}
        stored_fields = 0
        required_fields = 0
        
        for fname, finfo in fields.items():
            ftype = finfo.get('type', 'unknown')
            field_types[ftype] = field_types.get(ftype, 0) + 1
            
            if finfo.get('store'):
                stored_fields += 1
            if finfo.get('required'):
                required_fields += 1
        
        print(f"✓ Field Statistics:")
        print(f"  Total fields: {len(fields)}")
        print(f"  Stored fields: {stored_fields}")
        print(f"  Required fields: {required_fields}")
        print(f"\n  Field types breakdown:")
        for ftype, count in sorted(field_types.items()):
            print(f"    {ftype}: {count}")
        
        # Check for active field (common flag)
        if 'x_active' in fields or 'active' in fields:
            print(f"\n  ℹ Model has 'active' field - records might be archived")
        
        # Check key fields we need
        key_fields = [
            'x_studio_terminal',
            'x_studio_departure_train_id',
            'x_studio_selection_field_572_1j09lmu81',
            'x_studio_one2many_field_3qn_1j34hmlba'
        ]
        
        print(f"\n  Key fields status:")
        for field in key_fields:
            if field in fields:
                finfo = fields[field]
                print(f"    ✓ {field}: {finfo.get('type')} - {finfo.get('string')}")
            else:
                print(f"    ✗ {field}: NOT FOUND")
        
    except Exception as e:
        print(f"✗ FAILED: Cannot get field schema")
        print(f"  Error: {e}")

def main():
    print("="*80)
    print("TESTING x_rail_freight_order: PERMISSIONS vs EMPTY MODEL")
    print("="*80)
    
    api = OdooAPI()
    api.authenticate()
    
    # Run all tests
    model_exists = test_model_access(api)
    
    if not model_exists:
        print("\n" + "="*80)
        print("CONCLUSION: Model does not exist or no access to metadata")
        print("="*80)
        return
    
    count = test_search_count(api)
    ids = test_search_ids(api)
    test_check_access_rights(api)
    
    if ids:
        test_read_specific_ids(api, ids)
    
    records = test_search_read_minimal(api)
    rf_ids = test_via_fwo_linkage(api)
    test_model_schema(api)
    
    # Final analysis
    print("\n" + "="*80)
    print("FINAL ANALYSIS")
    print("="*80)
    
    if count is None:
        print("\n⚠️ PERMISSION ISSUE DETECTED")
        print("  - Cannot execute search_count")
        print("  - This suggests NO READ ACCESS to records")
    elif count == 0 and rf_ids and len(rf_ids) > 0:
        print("\n⚠️ PERMISSION ISSUE CONFIRMED")
        print(f"  - search_count returns: 0")
        print(f"  - But FWO references {len(rf_ids)} rail freight order IDs")
        print(f"  - Conclusion: Records exist but we cannot read them directly")
        print(f"\n  → API user (UID {api.uid}) has LIMITED READ ACCESS")
        print(f"  → Can see references via FWO but cannot query x_rail_freight_order directly")
    elif count == 0 and (rf_ids is None or len(rf_ids) == 0):
        print("\n✓ MODEL IS TRULY EMPTY")
        print(f"  - search_count returns: 0")
        print(f"  - FWO has no rail freight order references")
        print(f"  - Conclusion: The model exists but has never been populated with data")
    elif count and count > 0:
        print("\n✓ MODEL HAS DATA AND WE CAN ACCESS IT")
        print(f"  - Total records visible: {count}")
        print(f"  - We have READ ACCESS")
        print(f"\n  ⚠️ But earlier tests showed 0 - this is unexpected!")
        print(f"  → Investigate why different queries return different results")
    else:
        print("\n❓ UNCLEAR SITUATION")
        print(f"  - search_count: {count}")
        print(f"  - FWO references: {len(rf_ids) if rf_ids else 'N/A'}")
        print(f"  - Need manual investigation")

if __name__ == "__main__":
    main()
