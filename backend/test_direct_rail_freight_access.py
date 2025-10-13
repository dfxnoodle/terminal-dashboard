"""
Test script to directly access Rail Freight Order by discovered ID
We found that Forwarding Order 1373 links to Rail Freight Order ID 395
Let's try to access it directly
"""
import os
from dotenv import load_dotenv
import xmlrpc.client
import json

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

def main():
    print("\n" + "="*80)
    print("DIRECT ACCESS TO RAIL FREIGHT ORDER ID 395")
    print("="*80 + "\n")
    
    # Setup connection
    url = os.getenv('ODOO_URL')
    db = os.getenv('ODOO_DB')
    username = os.getenv('ODOO_USERNAME')
    api_key = os.getenv('ODOO_API_KEY')
    
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
    
    # Authenticate
    uid = common.authenticate(db, username, api_key, {})
    print(f"✅ Authenticated (UID: {uid})\n")
    
    # Method 1: Read by specific ID
    print("METHOD 1: Direct read by ID 395")
    print("-" * 80)
    try:
        record = models.execute_kw(
            db, uid, api_key,
            'x_rail_freight_order', 'read',
            [[395]],  # The ID we discovered
            {}
        )
        
        if record:
            print("✅ SUCCESS! Rail Freight Order ID 395 found!\n")
            print("Complete Record Data:")
            print(json.dumps(record, indent=2, default=str))
        else:
            print("❌ No record found with ID 395")
    except Exception as e:
        print(f"❌ Error: {e}\n")
    
    # Method 2: Search for records with active filter
    print("\n" + "="*80)
    print("METHOD 2: Search with various filters")
    print("="*80 + "\n")
    
    filters_to_try = [
        ([['id', '=', 395]], "ID equals 395"),
        ([['id', 'in', [395]]], "ID in list [395]"),
        ([['x_active', '=', True]], "Active = True"),
        ([['x_active', '!=', False]], "Active != False"),
        ([], "No filter (all records)"),
    ]
    
    for domain, description in filters_to_try:
        print(f"Trying: {description}")
        print(f"Domain: {domain}")
        try:
            count = models.execute_kw(
                db, uid, api_key,
                'x_rail_freight_order', 'search_count',
                [domain]
            )
            print(f"  Result: {count} records found")
            
            if count > 0:
                # Get the records
                records = models.execute_kw(
                    db, uid, api_key,
                    'x_rail_freight_order', 'search_read',
                    [domain],
                    {'fields': ['id', 'x_name', 'x_studio_train_id'], 'limit': 5}
                )
                print("  Sample records:")
                for rec in records:
                    print(f"    - ID: {rec.get('id')} | Name: {rec.get('x_name')} | Train: {rec.get('x_studio_train_id')}")
            print()
        except Exception as e:
            print(f"  ❌ Error: {e}\n")
    
    # Method 3: Get all rail freight order IDs from forwarding orders
    print("="*80)
    print("METHOD 3: Get all Rail Freight Order IDs from Forwarding Orders")
    print("="*80 + "\n")
    
    try:
        fwo_records = models.execute_kw(
            db, uid, api_key,
            'x_fwo', 'search_read',
            [[['x_studio_rail_freight_order', '!=', False]]],
            {'fields': ['id', 'x_name', 'x_studio_rail_freight_order'], 'limit': 20}
        )
        
        print(f"Found {len(fwo_records)} forwarding orders with rail freight links:\n")
        
        rail_freight_ids = set()
        for fwo in fwo_records:
            rfo = fwo.get('x_studio_rail_freight_order')
            if rfo and isinstance(rfo, list) and len(rfo) >= 2:
                rfo_id = rfo[0]
                rfo_name = rfo[1]
                rail_freight_ids.add(rfo_id)
                print(f"  FWO {fwo['id']}: {fwo['x_name']} → RFO {rfo_id}: {rfo_name}")
        
        print(f"\nUnique Rail Freight Order IDs: {sorted(rail_freight_ids)}")
        print(f"Total unique RFOs: {len(rail_freight_ids)}")
        
        # Try to access these IDs directly
        if rail_freight_ids:
            print(f"\n" + "="*80)
            print(f"METHOD 4: Batch read using discovered IDs")
            print("="*80 + "\n")
            
            id_list = sorted(list(rail_freight_ids))[:10]  # Try first 10
            print(f"Attempting to read IDs: {id_list}\n")
            
            try:
                rfo_records = models.execute_kw(
                    db, uid, api_key,
                    'x_rail_freight_order', 'read',
                    [id_list],
                    {'fields': ['id', 'x_name', 'x_studio_train_id', 'x_studio_terminal', 
                               'x_studio_loaded_wagons', 'x_studio_departure_train_id']}
                )
                
                print(f"✅ Successfully read {len(rfo_records)} Rail Freight Orders!\n")
                for rec in rfo_records:
                    print(f"  ID: {rec.get('id')}")
                    print(f"    Name: {rec.get('x_name')}")
                    print(f"    Train ID: {rec.get('x_studio_train_id')}")
                    print(f"    Departure Train ID: {rec.get('x_studio_departure_train_id')}")
                    print(f"    Terminal: {rec.get('x_studio_terminal')}")
                    print(f"    Loaded Wagons: {rec.get('x_studio_loaded_wagons')}")
                    print()
                
                # Save to file
                filename = 'rail_freight_orders_sample.json'
                with open(filename, 'w') as f:
                    json.dumps(rfo_records, f, indent=2, default=str)
                print(f"💾 Saved sample data to: {filename}")
                
            except Exception as e:
                print(f"❌ Batch read failed: {e}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "="*80)
    print("EXPLORATION COMPLETE")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
