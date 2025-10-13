# Rail Freight Order Model Analysis

**Model Name:** `x_rail_freight_order`  
**Exploration Date:** October 13, 2025  
**Total Fields:** 116  
**Current Records:** 0 (empty model)

---

## Model Purpose
This model tracks **rail freight operations** at terminals, specifically monitoring train loading operations from arrival through departure. It includes comprehensive tracking of:
- Train arrival and departure timelines
- Product loading operations (supports up to 2 products)
- Planned vs actual performance metrics
- Terminal operations workflow

---

## Key Fields Analysis

### **Identification Fields**
- `x_name` (char) - **Rail Freight Order | Train ID** ⭐ **REQUIRED**
- `x_studio_arrival_train_id` - Incoming train identifier
- `x_studio_departure_train_id` - Outgoing train identifier
- `x_studio_uid` - Unique identifier

### **Terminal & Status**
- `x_studio_terminal` (selection) - Which terminal (ICAD/DIC/NDP)
- `x_studio_selection_field_572_1j09lmu81` (selection) - Pipeline status bar
- `x_active` (boolean) - Active status
- `x_studio_date_of_loading` (date) - Loading date

### **Train Configuration**
- `x_studio_loaded_wagons` (integer) - Number of wagons loaded
- `x_studio_lead_locomotive` (integer) - Lead locomotive number
- `x_studio_rear_locomotive` (integer) - Rear locomotive number
- `x_studio_trainset_assigned` (many2one) - Assigned trainset
- `x_studio_loading_method` (selection) - Loading methodology
- `x_studio_number_of_material` (selection) - How many materials (1 or 2)

### **Timeline Tracking - Train Movement**

Each milestone has both **PLANNED** and **ACTUAL** datetime fields:

1. **Train Arrival at RCLB** (Rail Car Loading Bay)
   - `x_studio_train_arrival_at_rclb_planned`
   - `x_studio_train_arrival_at_rclb_actual`

2. **Train Entered Facility**
   - `x_studio_train_entered_facility_planned`
   - `x_studio_train_entered_facility_actual`

3. **Train Entered BM** (Bulk Material area)
   - `x_studio_train_entered_bm_planned`
   - `x_studio_train_entered_bm_actual`

4. **Train Departed from Head Shunt**
   - `x_studio_train_departure_from_head_shunt_planned`
   - `x_studio_train_departure_from_head_shunt_actual`

5. **Train Arrived in Departure Road**
   - `x_studio_train_arrived_in_departure_road_planned`
   - `x_studio_train_arrived_in_departure_road_actual`

6. **Departure from Exit BM**
   - `x_studio_departure_from_exit_bm_planned`
   - `x_studio_departure_from_exit_bm_actual`

### **Loading Operations - Product 1**

- `x_studio_product_1_loading_commenced_planned` (datetime)
- `x_studio_product_1_loading_commenced_actual` (datetime)
- `x_studio_product_1_loading_finished_planned` (datetime)
- `x_studio_product_1_loading_finished_actual` (datetime)

### **Loading Operations - Product 2**

- `x_studio_product_2_loading_commenced_planned` (datetime)
- `x_studio_product_2_loading_commenced_actual` (datetime)
- `x_studio_product_2_loading_finished_planned` (datetime)
- `x_studio_product_2_loading_finished_actual` (datetime)

### **Load Report**

- `x_studio_load_report_issued_planned` (datetime)
- `x_studio_load_report_issued_actual` (datetime)

### **Duration Tracking (Planned)**

All planned durations are stored in **float** (likely hours or minutes):

- `x_studio_planned_duration_rclb_p1_start` - RCLB to Product 1 Start
- `x_studio_planned_duration_product_1_loading` - Product 1 loading time
- `x_studio_planned_duration_clean_cycle_and_silo_reset` - Cleanup between products
- `x_studio_planned_duration_product_2_loading` - Product 2 loading time
- `x_studio_planned_duration_issuing_load_report` - Report preparation
- `x_studio_planned_duration_report_head_shunt` - Move to head shunt
- `x_studio_planned_duration_train_safety_check` - Safety inspection
- `x_studio_planned_duration_depr_bm` - Departure road to BM exit
- `x_studio_planned_duration_facility_rclb` - Facility to RCLB
- `x_studio_planned_duration_bm_facility` - BM to Facility

### **Duration Tracking (Actual)**

Corresponding actual duration fields (computed/readonly):

- `x_studio_actual_duration_rclb_p1_start`
- `x_studio_actual_duration_product_1_loading`
- `x_studio_actual_duration_clean_cycle_and_silo_reset`
- `x_studio_actual_duration_product_2_loading`
- `x_studio_actual_duration_issuing_load_report`
- `x_studio_actual_duration_report_head_shunt`
- `x_studio_actual_duration_train_safety_check`
- `x_studio_actual_duration_depr_bm`
- `x_studio_actual_duration_facility_rclb`
- `x_studio_actual_duration_bm_facility`

### **Performance Metrics (Computed)**

Variance calculations (Planned vs Actual):

- `x_studio_planned_vs_actual_train_arrival_at_rclb`
- `x_studio_planned_vs_actual_train_entered_facility`
- `x_studio_planned_vs_actual_train_entered_bm`
- `x_studio_planned_vs_actual_product_1_loading_commenced`
- `x_studio_planned_vs_actual_product_1_loading_finished`
- `x_studio_planned_vs_actual_product_2_loading_commenced`
- `x_studio_planned_vs_actual_product_2_loading_finished`
- `x_studio_planned_vs_actual_load_report_issued`
- `x_studio_planned_vs_actual_train_departure_from_head_shunt`
- `x_studio_planned_vs_actual_train_arrived_in_departure_road`
- `x_studio_planned_vs_actual_departure_from_exit_bm`

**Summary Metrics:**

- `x_studio_total_loading_time_planned` (float, readonly)
- `x_studio_total_loading_time_actual` (float, readonly)
- `x_studio_total_terminal_time_planned` (float, readonly)
- `x_studio_total_terminal_time_actual` (float, readonly)
- `x_studio_train_delay_actual_vs_planned` (float, readonly)

### **Delay Tracking & Reasons**

Reason fields for each delay:

- `x_studio_reason_for_delay_train_arrival_at_rclb`
- `x_studio_reason_for_delay_train_entered_facility`
- `x_studio_reason_for_delay_train_entered_bm`
- `x_studio_reason_for_delay_product_1_loading_commenced`
- `x_studio_reason_for_delay_product_1_loading_finished`
- `x_studio_reason_for_delay_product_2_loading_commenced`
- `x_studio_reason_for_delay_product_2_loading_finished`
- `x_studio_reason_for_delay_load_report_issued`
- `x_studio_reason_for_delay_train_departure_from_head_shunt`
- `x_studio_reason_for_delay_train_arrived_in_departure_road`
- `x_studio_reason_for_delay_departure_from_exit_bm`

General fields:
- `x_studio_reason` (text) - General reason field
- `x_studio_remarks` (text) - Additional remarks

### **Relationships**

- `x_studio_forwarding_order` (one2many) - Links to forwarding orders
- `x_studio_one2many_field_3qn_1icdknqu2` - **Load List** (detailed wagon/load data)
- `x_studio_trainset_assigned` (many2one) - Link to trainset master data

---

## Operational Workflow

Based on the fields, the typical workflow appears to be:

1. **Train Arrival** → Arrives at RCLB
2. **Entry** → Enters facility → Enters BM area
3. **Loading Product 1** → Commence → Finish
4. **Clean Cycle** → Silo reset between products (if 2 materials)
5. **Loading Product 2** → Commence → Finish (optional)
6. **Load Report** → Documentation issued
7. **Departure** → Head shunt → Departure road → Exit BM
8. **Safety Check** → Before final departure

---

## Potential Dashboard Metrics

From this model, you could track:

### **Efficiency Metrics**
- Average loading time per train (planned vs actual)
- Total terminal time per train
- On-time performance (% of trains meeting planned schedule)
- Delay analysis by milestone

### **Operational Metrics**
- Trains processed per day/week
- Number of loaded wagons
- Products loaded (single vs dual material trains)
- Terminal utilization (ICAD vs DIC vs NDP)

### **Performance Analytics**
- Most common delay reasons
- Average delay per milestone
- Loading efficiency (tons per hour)
- Train turnaround time

### **Visual Representations**
- Timeline Gantt chart (planned vs actual)
- Delay heat map by terminal
- Loading duration trends
- Throughput by terminal

---

## Integration with Existing Models

This model appears to complement:

- **`x_fwo`** (Forwarding Orders) - Referenced via `x_studio_forwarding_order`
- **Load List** - Detailed wagon-level data
- **Trainset Master** - Train configuration data

---

## Current Status

⚠️ **Note:** The model currently has **0 records**, suggesting either:
1. It's a newly created model not yet in use
2. Data is archived/deleted regularly
3. The operations tracked by this model are in a different production environment

---

## Recommended Next Steps

1. Check if there's test data in a staging environment
2. Verify the relationship with `x_fwo` (forwarding orders)
3. Understand the Load List structure (`x_studio_one2many_field_3qn_1icdknqu2`)
4. Determine which fields are auto-calculated vs manually entered
5. Identify the selection field options for:
   - `x_studio_terminal`
   - `x_studio_loading_method`
   - `x_studio_number_of_material`
   - `x_studio_selection_field_572_1j09lmu81` (status pipeline)
