# Analysis: x_studio_confirmed Field in x_last_mile_freight Model

**Date**: November 20, 2025  
**Model**: `x_last_mile_freight` (Last Mile Truck Orders)

## Field Details

- **Field Name**: `x_studio_confirmed`
- **Label**: "Confirmed?"
- **Type**: Boolean (True/False)
- **Purpose**: Manual confirmation flag indicating whether an order has been verified/confirmed by operations

## Current Statistics

- **Total Records**: 77,238
- **Confirmed (True)**: 57,230 records (74.1%)
- **Not Confirmed (False)**: 20,008 records (25.9%)

## Correlation with Status Field

### Status: "Gate-out Completed"
- Confirmed: 426 records
- Not Confirmed: 6 records
- **Result**: 98.6% of "Gate-out Completed" orders are confirmed

### Status: "Order Completed and Closed"
- Confirmed: 56,451 records
- Not Confirmed: 1,399 records
- **Result**: 97.6% of "Order Completed and Closed" orders are confirmed

## Sample Data Observations

### Confirmed Orders (x_studio_confirmed = True)
```
Example Records:
- Record: ALA6250030534
  Terminal: DIC
  Status: Order Completed and Closed
  Confirmed: True
  Weight: 78.52 tons
  Gate-out: 2025-07-01 04:03:00

- Record: ALA6250030555
  Terminal: DIC
  Status: Order Completed and Closed
  Confirmed: True
  Weight: 75.16 tons
  Gate-out: 2025-06-30 20:04:00
```

### Not Confirmed Orders (x_studio_confirmed = False)
```
Example Records:
- Record: ER25063000856124
  Terminal: DIC
  Status: Order Completed and Closed
  Confirmed: False
  Weight: 80.72 tons
  Gate-out: 2025-07-02 06:04:00

- Record: ER25070100856716
  Terminal: DIC
  Status: Order Completed and Closed
  Confirmed: False
  Weight: 76.76 tons
  Gate-out: 2025-06-30 20:33:00
```

## Key Findings

1. **Both confirmed and unconfirmed orders have complete data**: Gate-out times and weights are present regardless of confirmation status

2. **Confirmation is a separate verification step**: Orders can be in "Order Completed and Closed" or "Gate-out Completed" status but still be unconfirmed

3. **Most completed orders are confirmed**: Approximately 97-99% of completed orders have been confirmed

4. **Current dashboard does NOT use this field**: The existing implementation filters only by:
   - `x_studio_terminal` (terminal location)
   - `x_studio_selection_field_Vik7G` (status)
   - `x_studio_actual_date_and_time_of_gate_out` (date range)

## Implementation Recommendation (IMPLEMENTED - Updated Nov 20, 2025)

### ✓ Current Implementation: Use Scheduled Gate-In Date for Appointments

**Implemented Solution**: Count "Appt. made" from orders with `x_studio_confirmed = True` using `x_studio_scheduled_truck_gate_in_date_time` field.

**Rationale**: 
- Appointment date should reflect when the appointment is scheduled, not when it actually executes
- Includes orders with confirmed appointments that haven't started yet (status: "Booking Confirmed")
- Prevents counting trips from different days that happen to have actual gate-in/out today
- More accurate representation of appointment planning vs execution

**Previous Implementation Issue**:
- Used `x_studio_actual_date_and_time_of_gate_in OR x_studio_actual_date_and_time_of_gate_out`
- Problem: Could count trips not scheduled for today but happened to execute today
- Example: A trip scheduled for tomorrow might have actual gate-in today if it arrived early

**Backend Implementation** (`backend/odoo_api.py`):

In `get_last_mile_truck_data()` method:

```python
# Trips Executed: Count orders with gate-out completed today
today_domain = [
    ['x_studio_terminal', '=', terminal],
    ['x_studio_selection_field_Vik7G', 'in', ['Gate-out Completed', 'Order Completed and Closed']],
    ['x_studio_actual_date_and_time_of_gate_out', '>=', start_of_today.strftime('%Y-%m-%d %H:%M:%S')],
    ['x_studio_actual_date_and_time_of_gate_out', '<=', end_of_today.strftime('%Y-%m-%d %H:%M:%S')]
]

# Appt. made: Count confirmed orders with scheduled gate-in today
confirmed_today_domain = [
    ['x_studio_terminal', '=', terminal],
    ['x_studio_confirmed', '=', True],
    ['x_studio_scheduled_truck_gate_in_date_time', '>=', start_of_today.strftime('%Y-%m-%d %H:%M:%S')],
    ['x_studio_scheduled_truck_gate_in_date_time', '<=', end_of_today.strftime('%Y-%m-%d %H:%M:%S')]
]
```

**Result**: "Appt. made" represents confirmed appointments scheduled for today, regardless of execution status (not started, in progress, or completed).

## Impact Assessment (VERIFIED - Updated Nov 20, 2025)

Implementation verified on November 20, 2025 using scheduled gate-in date:

### Last Mile ICAD (Today)
- Trips Executed: 110
- Appt. made: 177
- **Result**: +67 confirmed appointments (60.9% more than trips)
- **Breakdown**:
  - Not started yet (Booking Confirmed): 62
  - In progress/completed: 115
- ✓ Appointment count significantly exceeds trips executed

### Last Mile DIC (Today)
- Trips Executed: 16
- Appt. made: 73
- **Result**: +57 confirmed appointments (356% more than trips)
- **Breakdown**:
  - Not started yet (Booking Confirmed): 59
  - In progress/completed: 14
- ✓ Appointment count significantly exceeds trips executed

### Why Appointments Exceed Trips
The appointment count is higher because it includes:
1. **Booking Confirmed** status: Orders with appointments scheduled for today but haven't started yet
2. **Gate-in Completed** status: Orders that arrived but haven't departed yet
3. **Gate-out Completed / Order Completed**: Orders that completed the full trip

### First Mile NDP
- **No change**: `x_studio_confirmed` field does not exist in `x_first_mile_freight` model
- First Mile brings materials TO terminal (no customer appointments needed)

## Next Steps

### ✓ Completed (Updated Nov 20, 2025)
1. ✓ **Initial Backend Implementation**: Used actual gate-in OR gate-out dates (had issues with counting wrong trips)
2. ✓ **Updated Backend Implementation**: Changed to use `x_studio_scheduled_truck_gate_in_date_time` field
3. ✓ **Testing**: Verified ICAD shows 177 appt. made vs 110 trips (67 more)
4. ✓ **Testing**: Verified DIC shows 73 appt. made vs 16 trips (57 more)
5. ✓ **First Mile Check**: Confirmed `x_first_mile_freight` doesn't have `x_studio_confirmed` field
6. ✓ **Documentation**: Updated analysis with latest implementation details

### Key Improvement
**Why we switched to scheduled gate-in date**:
- Previous method using actual gate-in/out could count trips not scheduled for today
- New method accurately reflects appointments scheduled for today
- Includes "Booking Confirmed" orders (scheduled but not started yet)
- Better alignment between appointment planning and execution tracking

### Ready for Production
- Backend changes deployed and tested with scheduled gate-in date
- Frontend displays confirmed counts correctly from backend API
- "Appt. made" shows appointments scheduled for today, regardless of execution status
- Accurately represents appointment planning vs trip execution

## Related Files

- `backend/odoo_api.py` - Lines ~500-560 (get_last_mile_truck_data methods)
- `frontend/src/views/Dashboard.vue` - Last Mile display sections
- Test script: `test_confirmed_field.py` (for future reference)
