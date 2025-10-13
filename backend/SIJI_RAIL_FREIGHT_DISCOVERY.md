# Siji Rail Freight Order Discovery

**Date:** October 13, 2025  
**Focus:** Train loading progress tracking for Siji terminal  
**Status:** ⚠️ **CRITICAL FINDINGS**

---

## Executive Summary

The `x_rail_freight_order` model, which should contain detailed train loading operations data including wagon-level tracking, currently has **ZERO records** in the system. Similarly, the `x_wagon_trip` model (which tracks individual wagon loading progress) also has **0 records**.

### Key Finding: Model Structure Exists, But No Data Yet

✅ **Models Exist:**
- `x_rail_freight_order` - 116 fields defined
- `x_wagon_trip` - 39 fields defined

❌ **No Data:**
- x_rail_freight_order: 0 records (all terminals)
- x_wagon_trip: 0 records

---

## Current Siji Data Sources

Based on previous exploration, the only available Siji data comes from:

### 1. Forwarding Orders (`x_fwo`)
- **35 Siji trains departed** (vs 599 from NDP)
- Available fields:
  - `x_studio_train_id` - Train identifier (e.g., "4DC14", "4ID70")
  - `x_studio_actual_train_departure` - Departure datetime
  - `x_studio_origin_terminal` - Origin terminal (Siji)
  - `x_studio_destination_terminal` - Destination (DIC/ICAD)
  - `x_studio_rail_freight_order` - Link to rail freight (currently returns [ID, "Name"] but record doesn't exist)

### 2. First Mile Freight (`x_first_mile_freight`)
- **1,603 truck orders at Siji**
- Shows material loading operations:
  - FALA Drainage Blanket 0-40mm (77% of shipments)
  - Aggregates and other materials
  - Shipper: FALA BMT (80% of orders)

### 3. No Stockpile Data
- Siji operates as a **direct loading terminal** (no stockpile storage)
- Materials go directly from truck → train

---

## What the x_rail_freight_order Model SHOULD Track

Based on the field analysis, this model is designed to track:

### 1. **Wagon Loading Progress**
Via `x_studio_one2many_field_3qn_1j34hmlba` → `x_wagon_trip`:
- Individual wagon loading start time (`x_studio_start_time`)
- Individual wagon loading end time (`x_studio_end_time`)
- Material per wagon (`x_studio_material`)
- Wagon identifier (`x_name`, `x_studio_wagon`)

**Loading Status Logic:**
- ✓ **Loaded:** `x_studio_start_time` IS NOT NULL AND `x_studio_end_time` IS NOT NULL
- ⏳ **Being Loaded:** `x_studio_start_time` IS NOT NULL AND `x_studio_end_time` IS NULL
- ⭕ **Not Started:** `x_studio_start_time` IS NULL

### 2. **Train Configuration**
- `x_studio_departure_train_id` - Train ID for departing train
- `x_studio_arrival_train_id` - Train ID when arriving
- `x_studio_loaded_wagons` - Total wagons loaded (integer)
- `x_studio_number_of_material` - How many materials (1 or 2)
- `x_studio_terminal` - Terminal location (Siji/NDP/ICAD/DIC)

### 3. **Pipeline Status**
- `x_studio_selection_field_572_1j09lmu81` - Workflow status
  - Expected values: "Draft", "Train Departed", etc.

### 4. **Timeline Tracking**
Planned vs Actual times for:
- Train arrival at RCLB (Rail Car Loading Bay)
- Product 1 loading commenced/finished
- Product 2 loading commenced/finished
- Train departure from head shunt
- Load report issued
- And 15+ other milestones

### 5. **Performance Metrics**
- Total loading time (planned vs actual)
- Total terminal time
- Delay reasons for each milestone
- Duration calculations for each operation phase

---

## Recommended Next Steps

### Option A: Use Existing FWO Data (Available Now)

Since `x_rail_freight_order` is empty, implement the dashboard section using `x_fwo` (Forwarding Orders):

```json
{
  "train_id": "4DC14",
  "status": "NDP/Siji Train Departed",
  "departure_time": "2025-10-12 15:30:00",
  "origin": "Siji",
  "destination": "DIC"
}
```

**Pros:**
- Data exists right now (35 Siji trains)
- Can show train departures immediately
- Provides basic tracking

**Cons:**
- No wagon-level loading progress
- No real-time loading status
- No per-material breakdown

### Option B: Wait for x_rail_freight_order Population

Monitor when the `x_rail_freight_order` model gets populated with actual data.

**Implementation Plan:**
1. Create monitoring script to check record count daily
2. Once records appear, verify field structure matches expectations
3. Test wagon loading progress calculations
4. Implement full dashboard feature

**Pros:**
- Will have complete wagon-level tracking
- Real-time loading progress
- Per-material wagon counts
- All planned vs actual metrics

**Cons:**
- Unknown timeline for when data will be available
- May require Odoo administrator to populate data
- Potential field structure changes

### Option C: Hybrid Approach (Recommended)

1. **Phase 1 (Immediate):** Implement basic train tracking using `x_fwo`
   - Show most recent Siji departed train
   - Display train ID, departure time, destination
   - Show total tonnage from first-mile freight

2. **Phase 2 (When Available):** Add wagon loading progress
   - Monitor `x_rail_freight_order` record count
   - When data appears, add loading progress visualization
   - Show per-wagon, per-material status
   - Display planned vs actual timelines

---

## Data Structure Verification

### x_wagon_trip Fields (39 total)

**Key Fields Verified:**
```json
{
  "x_studio_start_time": {
    "type": "datetime",
    "label": "Start Time"
  },
  "x_studio_end_time": {
    "type": "datetime",
    "label": "End Time"
  },
  "x_studio_material": {
    "type": "many2one",
    "label": "Material",
    "relation": "x_material"
  },
  "x_studio_wagon": {
    "type": "many2one",
    "label": "Wagon",
    "relation": "x_wagon"
  },
  "x_name": {
    "type": "char",
    "label": "Wagon ID"
  },
  "x_studio_rail_freight_order": {
    "type": "many2one",
    "label": "Rail Freight Order",
    "relation": "x_rail_freight_order"
  }
}
```

**Full export:** `/backend/x_wagon_trip_fields.json`

---

## Dashboard Mockup (Phase 2 - When Data Available)

```
┌─────────────────────────────────────────────────────────┐
│ 🚂 Train Loading Progress - Siji Terminal              │
├─────────────────────────────────────────────────────────┤
│ Train: 4DC14                                            │
│ Status: Being Loaded                                    │
│ Loading Date: 2025-10-12                                │
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
│ Estimated Completion: 2 hours                           │
│ Last Updated: 2 minutes ago                             │
└─────────────────────────────────────────────────────────┘
```

---

## Testing Queries for When Data Becomes Available

```python
# Query most recent Siji train in Draft or Train Departed status
domain = [
    ['x_studio_terminal', '=', 'Siji'],
    ['x_studio_selection_field_572_1j09lmu81', 'in', ['Draft', 'Train Departed']]
]

rail_freight_orders = api.execute_kw('x_rail_freight_order', 'search_read', [domain], {
    'fields': [
        'x_name',
        'x_studio_departure_train_id',
        'x_studio_selection_field_572_1j09lmu81',
        'x_studio_date_of_loading',
        'x_studio_loaded_wagons',
        'x_studio_number_of_material',
        'x_studio_one2many_field_3qn_1j34hmlba',  # Wagon trip IDs
        'create_date'
    ],
    'order': 'create_date desc',
    'limit': 1
})

# Get wagon loading details
wagon_ids = rail_freight_orders[0]['x_studio_one2many_field_3qn_1j34hmlba']

wagons = api.execute_kw('x_wagon_trip', 'search_read', [[['id', 'in', wagon_ids]]], {
    'fields': [
        'x_name',
        'x_studio_start_time',
        'x_studio_end_time',
        'x_studio_material',
        'x_studio_wagon'
    ]
})

# Calculate loading progress per material
material_stats = {}
for wagon in wagons:
    material_name = wagon['x_studio_material'][1] if wagon['x_studio_material'] else 'Unknown'
    
    if material_name not in material_stats:
        material_stats[material_name] = {'loaded': 0, 'loading': 0, 'pending': 0}
    
    if wagon['x_studio_start_time'] and wagon['x_studio_end_time']:
        material_stats[material_name]['loaded'] += 1
    elif wagon['x_studio_start_time']:
        material_stats[material_name]['loading'] += 1
    else:
        material_stats[material_name]['pending'] += 1
```

---

## Conclusion

**Current Reality:**
- The `x_rail_freight_order` and `x_wagon_trip` models are **not yet populated** with data
- Cannot implement real-time wagon loading progress tracking at this time

**Immediate Action:**
- Recommend **Phase 1 approach** using existing `x_fwo` data
- Show Siji train departures without wagon-level detail
- Monitor for when rail freight order data becomes available

**Future Implementation:**
- Once data is available, all field structures and logic are ready
- Can implement complete wagon loading progress visualization
- Full testing queries are prepared and documented

**Question for Stakeholder:**
When is the `x_rail_freight_order` model expected to be populated with operational data? Is this a future enhancement planned by the Odoo team, or should we request data population?
