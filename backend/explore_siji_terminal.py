"""
Deep dive into Siji Terminal operations
Exploring trains departed from Siji terminal
"""
import os
from dotenv import load_dotenv
import xmlrpc.client
from datetime import datetime, timedelta, timezone
from collections import defaultdict

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

class SijiTerminalExplorer:
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
    
    def get_siji_overview(self):
        """Get overview of Siji terminal operations"""
        print("="*80)
        print("SIJI TERMINAL OVERVIEW")
        print("="*80 + "\n")
        
        # Check forwarding orders from Siji
        print("1. Forwarding Orders from Siji:")
        print("-" * 80)
        
        domain = [['x_studio_origin_terminal', '=', 'Siji']]
        count = self.execute_kw('x_fwo', 'search_count', [domain])
        print(f"   Total forwarding orders from Siji: {count}")
        
        # With train departed status
        domain_departed = [
            ['x_studio_origin_terminal', '=', 'Siji'],
            ['x_studio_selection_field_83c_1ig067df9', '=', 'NDP Train Departed']
        ]
        count_departed = self.execute_kw('x_fwo', 'search_count', [domain_departed])
        print(f"   Orders with 'NDP/Siji Train Departed' status: {count_departed}")
        
        # With actual departure dates
        domain_with_departure = [
            ['x_studio_origin_terminal', '=', 'Siji'],
            ['x_studio_actual_train_departure', '!=', False]
        ]
        count_with_departure = self.execute_kw('x_fwo', 'search_count', [domain_with_departure])
        print(f"   Orders with actual departure dates: {count_with_departure}\n")
    
    def get_siji_train_details(self):
        """Get detailed train information from Siji"""
        print("="*80)
        print("SIJI TRAIN DEPARTURES - DETAILED ANALYSIS")
        print("="*80 + "\n")
        
        domain = [
            ['x_studio_origin_terminal', '=', 'Siji'],
            ['x_studio_actual_train_departure', '!=', False]
        ]
        
        records = self.execute_kw('x_fwo', 'search_read', [domain], {
            'fields': [
                'id', 'x_name', 'x_studio_train_id',
                'x_studio_actual_train_departure',
                'x_studio_etd_origin',
                'x_studio_origin_terminal',
                'x_studio_destination_terminal',
                'x_studio_material_01',
                'x_studio_material_02',
                'x_studio_quantity_01_t',
                'x_studio_quantity_02_t',
                'x_studio_no_of_materials',
                'x_studio_shipper',
                'x_studio_01_locomotive_id',
                'x_studio_02_locomotive_id',
                'x_studio_rail_freight_order',
                'x_studio_selection_field_83c_1ig067df9',
                'create_date',
            ],
            'order': 'id desc'
        })
        
        print(f"Found {len(records)} trains departed from Siji\n")
        
        if not records:
            print("⚠️  No trains found with departure data from Siji terminal\n")
            return []
        
        # Display recent trains
        print("RECENT TRAINS (Last 20):")
        print("-" * 80)
        for i, rec in enumerate(records[:20], 1):
            print(f"\n{i}. Train ID: {rec.get('x_studio_train_id', 'N/A')}")
            print(f"   FWO: {rec.get('x_name')}")
            
            # Rail Freight Order
            rfo = rec.get('x_studio_rail_freight_order')
            if rfo and isinstance(rfo, list) and len(rfo) >= 2:
                print(f"   Rail Freight Order: {rfo[1]} (ID: {rfo[0]})")
            
            print(f"   Departure: {rec.get('x_studio_actual_train_departure')}")
            print(f"   ETD: {rec.get('x_studio_etd_origin', 'N/A')}")
            print(f"   Route: Siji → {rec.get('x_studio_destination_terminal', 'N/A')}")
            print(f"   Status: {rec.get('x_studio_selection_field_83c_1ig067df9', 'N/A')}")
            
            # Materials
            material_01 = rec.get('x_studio_material_01')
            material_02 = rec.get('x_studio_material_02')
            num_materials = rec.get('x_studio_no_of_materials', 1)
            
            print(f"   Materials: {num_materials}")
            if material_01:
                mat_name = material_01[1] if isinstance(material_01, list) else material_01
                qty_01 = rec.get('x_studio_quantity_01_t', 0)
                print(f"     - Material 1: {mat_name} ({qty_01} tons)")
            
            if material_02:
                mat_name = material_02[1] if isinstance(material_02, list) else material_02
                qty_02 = rec.get('x_studio_quantity_02_t', 0)
                print(f"     - Material 2: {mat_name} ({qty_02} tons)")
            
            # Shipper
            shipper = rec.get('x_studio_shipper')
            if shipper:
                shipper_name = shipper[1] if isinstance(shipper, list) else shipper
                print(f"   Shipper: {shipper_name}")
            
            # Locomotives
            loco_01 = rec.get('x_studio_01_locomotive_id')
            loco_02 = rec.get('x_studio_02_locomotive_id')
            if loco_01 or loco_02:
                print(f"   Locomotives: {loco_01 or 'N/A'} / {loco_02 or 'N/A'}")
        
        return records
    
    def analyze_siji_statistics(self, records):
        """Analyze statistics for Siji trains"""
        print("\n" + "="*80)
        print("SIJI TERMINAL STATISTICS")
        print("="*80 + "\n")
        
        if not records:
            print("No data to analyze\n")
            return
        
        # Destination analysis
        destinations = defaultdict(int)
        for rec in records:
            dest = rec.get('x_studio_destination_terminal', 'Unknown')
            destinations[dest] += 1
        
        print("1. DESTINATIONS:")
        print("-" * 80)
        for dest, count in sorted(destinations.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(records)) * 100
            print(f"   {dest}: {count} trains ({percentage:.1f}%)")
        
        # Material analysis
        print("\n2. MATERIALS:")
        print("-" * 80)
        materials = defaultdict(int)
        total_tonnage = 0
        single_material_count = 0
        dual_material_count = 0
        
        for rec in records:
            num_materials = rec.get('x_studio_no_of_materials', 1)
            
            if num_materials == 1:
                single_material_count += 1
            elif num_materials == 2:
                dual_material_count += 1
            
            material_01 = rec.get('x_studio_material_01')
            if material_01:
                mat_name = material_01[1] if isinstance(material_01, list) else str(material_01)
                materials[mat_name] += 1
                total_tonnage += rec.get('x_studio_quantity_01_t', 0)
            
            material_02 = rec.get('x_studio_material_02')
            if material_02:
                mat_name = material_02[1] if isinstance(material_02, list) else str(material_02)
                materials[mat_name] += 1
                total_tonnage += rec.get('x_studio_quantity_02_t', 0)
        
        print(f"   Single material trains: {single_material_count}")
        print(f"   Dual material trains: {dual_material_count}")
        print(f"   Total tonnage: {total_tonnage:,.0f} tons")
        if records:
            print(f"   Average per train: {total_tonnage / len(records):,.0f} tons")
        
        print("\n   Top Materials Transported:")
        for mat, count in sorted(materials.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"   - {mat}: {count} occurrences")
        
        # Shipper analysis
        print("\n3. SHIPPERS:")
        print("-" * 80)
        shippers = defaultdict(int)
        for rec in records:
            shipper = rec.get('x_studio_shipper')
            if shipper:
                shipper_name = shipper[1] if isinstance(shipper, list) else str(shipper)
                shippers[shipper_name] += 1
        
        for shipper, count in sorted(shippers.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(records)) * 100
            print(f"   {shipper}: {count} trains ({percentage:.1f}%)")
        
        # Timeline analysis
        print("\n4. DEPARTURE TIMELINE:")
        print("-" * 80)
        
        # Group by month
        monthly = defaultdict(int)
        weekly = defaultdict(int)
        
        for rec in records:
            dep_date = rec.get('x_studio_actual_train_departure')
            if dep_date:
                try:
                    dt = datetime.strptime(dep_date, '%Y-%m-%d %H:%M:%S')
                    month_key = dt.strftime('%Y-%m')
                    monthly[month_key] += 1
                    
                    # Get week number
                    week_key = dt.strftime('%Y-W%U')
                    weekly[week_key] += 1
                except:
                    pass
        
        print("   By Month:")
        for month, count in sorted(monthly.items(), reverse=True)[:6]:
            print(f"   {month}: {count} trains")
        
        print("\n   By Week (Recent 8 weeks):")
        for week, count in sorted(weekly.items(), reverse=True)[:8]:
            print(f"   {week}: {count} trains")
    
    def check_siji_first_mile_trucks(self):
        """Check first mile truck operations at Siji"""
        print("\n" + "="*80)
        print("SIJI FIRST MILE TRUCK OPERATIONS")
        print("="*80 + "\n")
        
        domain = [['x_studio_terminal', '=', 'Siji']]
        count = self.execute_kw('x_first_mile_freight', 'search_count', [domain])
        print(f"Total first mile truck orders at Siji: {count}")
        
        if count > 0:
            # Get sample
            records = self.execute_kw('x_first_mile_freight', 'search_read', [domain], {
                'fields': ['id', 'x_name', 'x_studio_terminal', 'x_studio_net_weight_ton'],
                'limit': 5,
                'order': 'id desc'
            })
            
            print("\nSample recent truck orders:")
            for rec in records:
                print(f"  - {rec.get('x_name')}: {rec.get('x_studio_net_weight_ton', 0)} tons")
    
    def check_siji_stockpiles(self):
        """Check stockpile status at Siji"""
        print("\n" + "="*80)
        print("SIJI STOCKPILE STATUS")
        print("="*80 + "\n")
        
        domain = [['x_studio_terminal', '=', 'Siji']]
        records = self.execute_kw('x_stockpile', 'search_read', [domain], {
            'fields': [
                'id', 'x_name', 'x_studio_terminal',
                'x_studio_capacity', 'x_studio_quantity_in_stock_t',
                'x_studio_material', 'x_studio_stockpile_material_age'
            ],
            'order': 'x_name'
        })
        
        print(f"Stockpiles at Siji: {len(records)}")
        
        if records:
            print("\nStockpile Details:")
            for rec in records:
                print(f"\n  {rec.get('x_name')}")
                
                material = rec.get('x_studio_material')
                if material:
                    mat_name = material[1] if isinstance(material, list) else material
                    print(f"    Material: {mat_name}")
                
                capacity = rec.get('x_studio_capacity', 0)
                quantity = rec.get('x_studio_quantity_in_stock_t', 0)
                utilization = (quantity / capacity * 100) if capacity > 0 else 0
                
                print(f"    Capacity: {capacity:,.0f} tons")
                print(f"    Current Stock: {quantity:,.0f} tons")
                print(f"    Utilization: {utilization:.1f}%")
                
                age = rec.get('x_studio_stockpile_material_age')
                if age:
                    print(f"    Material Age: {age:.1f} hours")
        else:
            print("⚠️  No stockpiles found at Siji terminal")
    
    def compare_siji_vs_ndp(self):
        """Compare Siji vs NDP operations"""
        print("\n" + "="*80)
        print("COMPARISON: SIJI vs NDP TERMINALS")
        print("="*80 + "\n")
        
        terminals = ['Siji', 'NDP']
        
        print("FORWARDING ORDERS:")
        print("-" * 80)
        for terminal in terminals:
            domain = [
                ['x_studio_origin_terminal', '=', terminal],
                ['x_studio_actual_train_departure', '!=', False]
            ]
            count = self.execute_kw('x_fwo', 'search_count', [domain])
            print(f"  {terminal}: {count} trains departed")
        
        print("\nFIRST MILE TRUCKS:")
        print("-" * 80)
        for terminal in terminals:
            domain = [['x_studio_terminal', '=', terminal]]
            count = self.execute_kw('x_first_mile_freight', 'search_count', [domain])
            print(f"  {terminal}: {count} truck orders")
        
        print("\nSTOCKPILES:")
        print("-" * 80)
        for terminal in terminals:
            domain = [['x_studio_terminal', '=', terminal]]
            count = self.execute_kw('x_stockpile', 'search_count', [domain])
            print(f"  {terminal}: {count} stockpiles")


def main():
    print("\n" + "="*80)
    print("SIJI TERMINAL DEEP DIVE ANALYSIS")
    print("="*80 + "\n")
    
    explorer = SijiTerminalExplorer()
    
    if not explorer.authenticate():
        print("Failed to authenticate. Exiting.")
        return
    
    # 1. Overview
    explorer.get_siji_overview()
    
    # 2. Detailed train information
    records = explorer.get_siji_train_details()
    
    # 3. Statistical analysis
    explorer.analyze_siji_statistics(records)
    
    # 4. First mile trucks
    explorer.check_siji_first_mile_trucks()
    
    # 5. Stockpile status
    explorer.check_siji_stockpiles()
    
    # 6. Comparison with NDP
    explorer.compare_siji_vs_ndp()
    
    print("\n" + "="*80)
    print("SIJI ANALYSIS COMPLETE")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
