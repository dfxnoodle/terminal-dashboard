# x_rail_freight_order Permission Test Results

**Date:** October 13, 2025  
**Test Subject:** x_rail_freight_order model access  
**API User:** dashboard@linus.services (UID 63)  
**Status:** ⚠️ **PERMISSION ISSUE CONFIRMED**

---

## Executive Summary

**The x_rail_freight_order model IS NOT EMPTY - it contains at least 10 records.**

However, the API user (`dashboard@linus.services`, UID 63) **DOES NOT have read access** to these records directly, even though the access rights check says "READ: GRANTED".

### The Evidence

✅ **Records Exist:**
- FWO model references 10 unique Rail Freight Order IDs: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
- Each FWO shows rail freight order as: `[ID, "6100000XXX | TrainID"]`
- Example: RF Order 1 = "6100000001 | 4ID77"

❌ **Cannot Access Directly:**
- `search_count([])` returns: **0**
- `search([])` returns: **[]**
- `read([1,2,3,4,5])` fails with error: **"Dashboard (Read-only) doesn't have 'read' access to Rail Freight Order"**

### The Paradox

```python
# Access rights check says we CAN read:
check_access_rights('read') → True ✓

# But actual read operations fail:
read([1, 2, 3]) → Fault 4: "doesn't have 'read' access" ✗
```

This suggests **record-level security rules** are blocking access, not model-level permissions.

---

## Detailed Test Results

### TEST 1: Model Metadata Access
**Result:** ✓ SUCCESS
```
Model exists with 116 fields
We CAN access model metadata
```

### TEST 2: Search Count
**Result:** ⚠️ Returns 0 (but records exist)
```python
search_count([]) → 0
```

### TEST 3: Search for IDs
**Result:** ⚠️ Returns empty list
```python
search([]) → []
```

### TEST 4: Access Rights Check
**Result:** ✓ Model-level permissions granted
```
READ:   ✓ GRANTED
WRITE:  ✓ GRANTED
CREATE: ✓ GRANTED
UNLINK: ✗ DENIED
```

**Note:** This check is at the **model level**, not record level. It only confirms we're allowed to perform these operations in general, but doesn't guarantee access to specific records.

### TEST 5: Search Read Minimal
**Result:** ⚠️ Returns 0 records
```python
search_read([], fields=['id', 'create_date'], limit=5) → []
```

### TEST 6: Access via FWO Linkage ⭐ **CRITICAL**
**Result:** ✓ Can see references, ✗ Cannot read

Found 10 FWOs with rail freight order links:

| FWO Train | RF Order ID | RF Order Name & Train |
|-----------|-------------|----------------------|
| 4ID77 | 1 | 6100000001 \| 4ID77 |
| 4ID04 | 2 | 6100000002 \| 4ID04 |
| 4ID64 | 3 | 6100000003 \| 4ID64 |
| 4ID00 | 4 | 6100000004 \| 4ID00 |
| 4DC20 | 5 | 6100000005 \| 4DC20 |
| 4ID02 | 6 | 6100000006 \| 4ID02 |
| 4ID04 | 7 | 6100000007 \| 4ID04 |
| 4DC22 | 8 | 6100000008 \| 4DC22 |
| 4ID00 | 9 | 6100000009 \| 4ID00 |
| 4ID30 | 10 | 6100000010 \| 4ID30 |

**Attempting direct read of IDs [1-10]:**
```
Error: Uh-oh! Looks like you have stumbled upon some top-secret records.

Sorry, Dashboard (Read-only) (id=63) doesn't have 'read' access to:
- Rail Freight Order (x_rail_freight_order)

If you really, really need access, perhaps you can win over your 
friendly administrator with a batch of freshly baked cookies.
```

### TEST 7: Model Schema
**Result:** ✓ Full schema accessible

```
Total fields: 116
Stored fields: 67
Required fields: 1

Field Types:
  datetime: 24
  float: 37
  char: 19
  integer: 8
  selection: 6
  boolean: 6
  one2many: 5
  many2one: 5
  date: 3
  text: 2
  many2many: 1

Key Fields Confirmed:
  ✓ x_studio_terminal (selection)
  ✓ x_studio_departure_train_id (char)
  ✓ x_studio_selection_field_572_1j09lmu81 (selection) - Pipeline status
  ✓ x_studio_one2many_field_3qn_1j34hmlba (one2many) - Load List → x_wagon_trip
```

---

## Why This Happens: Odoo Record Rules

Odoo has two levels of access control:

### 1. **Model-Level Permissions (ACL)**
What `check_access_rights()` checks:
- Can this user type access this model at all?
- Configured in: `ir.model.access`
- Result: ✓ Dashboard user CAN read x_rail_freight_order (in theory)

### 2. **Record-Level Security (Record Rules)**
What actually blocks our access:
- Can this specific user access these specific records?
- Configured in: `ir.rule`
- Filters records based on domain conditions
- Result: ✗ Dashboard user's record rule filters out ALL records

### Example Record Rule (likely applied):
```python
# Hypothetical rule blocking dashboard user
Domain: [('create_uid', '=', user.id)]  # Only see records you created
# Dashboard user created 0 rail freight orders → sees 0 records

# OR
Domain: [('state', '=', 'published')]  # Only see published records
# No rail freight orders are 'published' → sees 0 records

# OR
Domain: [('terminal', 'in', ['NDP'])]  # Only see specific terminals
# User is restricted to NDP → can't see Siji records
```

---

## Implications for Dashboard Development

### ❌ What We CANNOT Do
1. **Query x_rail_freight_order directly** for any data
2. **Read individual rail freight order records** by ID
3. **Implement wagon loading progress** using x_rail_freight_order data
4. **Access x_wagon_trip records** (same permission issue likely applies)

### ✅ What We CAN Do
1. **See rail freight order references via FWO**
   - Field: `x_studio_rail_freight_order` returns `[ID, "Name | TrainID"]`
   - Example: `[1, "6100000001 | 4ID77"]`
   
2. **Extract train IDs from the reference string**
   ```python
   rf_ref = fwo['x_studio_rail_freight_order']  # [1, "6100000001 | 4ID77"]
   rf_id = rf_ref[0]  # 1
   rf_name_and_train = rf_ref[1]  # "6100000001 | 4ID77"
   train_id = rf_name_and_train.split('|')[1].strip()  # "4ID77"
   ```

3. **Use FWO data as primary source**
   - All train departure information is in FWO
   - No need for x_rail_freight_order if we just want basic tracking

---

## Recommended Solutions

### Option 1: Request Permission Change (Best)
**Action:** Contact Odoo administrator to grant record-level read access

**What to request:**
```
Please add a record rule for user group "Dashboard Users" 
to allow read access to x_rail_freight_order records.

Current user: dashboard@linus.services (UID 63)
Model: x_rail_freight_order
Required access: READ

Suggested record rule domain:
  [('id', '!=', False)]  # Allow all records
  
OR if filtering needed:
  [('x_studio_terminal', 'in', ['Siji', 'NDP'])]  # Allow specific terminals
```

**Benefit:** Full access to wagon loading progress data

### Option 2: Create API Endpoint in Backend (Workaround)
**Action:** Create a backend API endpoint that uses Odoo admin credentials

```python
# In backend/main.py
from backend.odoo_api import OdooAPI

@app.get("/api/rail-freight/{train_id}")
async def get_rail_freight_order(train_id: str):
    # This uses admin-level Odoo credentials from .env
    odoo = OdooAPI()  # Has full access
    
    # Can read x_rail_freight_order with admin credentials
    records = odoo.execute_kw('x_rail_freight_order', 'search_read', 
        [[['x_studio_departure_train_id', '=', train_id]]], {
        'fields': ['x_name', 'x_studio_one2many_field_3qn_1j34hmlba', ...]
    })
    
    return records
```

**Benefit:** Frontend can access data via backend proxy

### Option 3: Use FWO Only (Current State)
**Action:** Implement dashboard using only FWO data (no wagon detail)

**Available data:**
- Train ID
- Departure datetime
- Origin/destination terminals
- Total tonnage (from linked first-mile freight)

**Limitation:** No wagon-level loading progress

---

## Next Steps

### Immediate (Manual Investigation)
1. Log into Odoo web interface with admin account
2. Navigate to Settings → Users & Companies → Record Rules
3. Search for rules affecting `x_rail_freight_order`
4. Check if dashboard user group has restrictive domain

### Short Term (Dashboard Development)
1. **Implement Phase 1** using FWO data only
2. Show Siji train departures without wagon detail
3. Display train ID, departure time, tonnage

### Long Term (Full Feature)
1. Request admin to grant record-level access
2. Test with `test_rail_freight_permissions.py` script
3. Once access granted, implement wagon loading progress
4. Use prepared queries from `SIJI_RAIL_FREIGHT_DISCOVERY.md`

---

## Test Script for Future Use

Once permissions are granted, re-run:
```bash
uv run python test_rail_freight_permissions.py
```

Expected results after permission fix:
```
TEST 2: Search Count → Should return > 0
TEST 3: Search for IDs → Should return list of IDs
TEST 5: Read Specific IDs → Should return record data ✓
TEST 6: Search Read → Should return records ✓
```

---

## Conclusion

**The x_rail_freight_order model:**
- ✅ Exists with proper schema (116 fields)
- ✅ Contains at least 10 records (referenced by FWO)
- ✅ Has wagon loading data we need (`x_studio_one2many_field_3qn_1j34hmlba`)
- ❌ **Is blocked by record-level security rules for dashboard user**

**Action Required:**
Contact Odoo administrator to grant read access to x_rail_freight_order records for the dashboard user account.

**Workaround Available:**
Use FWO data for basic train tracking until permissions are resolved.
