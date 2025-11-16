# Phase 2: Logistics & Delivery System Design

## Overview

Phase 2 introduces a **decentralized courier network** where individual transporters can register to deliver packages within their jurisdiction. The system supports:
- Individual courier operator registration
- Multi-city warehouse hubs for inter-city transfers
- Real-time delivery tracking
- Time-based delivery windows (same-day, next-day)
- Automated order routing based on location
- Courier earnings and performance metrics

## Architecture

### Delivery Model

```
Customer Order (Harare)
    ↓
Order Router (Find optimal courier)
    ↓
├─ Same City → Direct Courier Pickup
│   └─ Courier Delivery → Customer (Same day / Next day)
│
└─ Different City → Multi-Warehouse Transfer
    ├─ Harare Courier → Harare Warehouse (Warehouse A)
    ├─ Warehouse A → Warehouse B (Inter-city transfer)
    ├─ Warehouse B → Destination Courier (Bulawayo)
    └─ Bulawayo Courier → Customer (Bulawayo)
```

## Database Schema (Phase 2)

### 1. Transporters (Courier Operators)

```sql
CREATE TABLE transporters (
    id TEXT PRIMARY KEY,
    user_id TEXT UNIQUE,                    -- Link to users table
    full_name TEXT,
    phone TEXT,
    email TEXT,
    vehicle_type TEXT,                      -- bike, car, van, truck
    license_plate TEXT UNIQUE,
    vehicle_capacity INT,                   -- kg or items
    
    -- Location & Jurisdiction
    operating_city TEXT,                    -- Primary city (Harare, Bulawayo, etc)
    operating_suburbs TEXT,                 -- JSON: ["Avondale", "Borrowdale", ...]
    
    -- Credentials & Verification
    national_id TEXT UNIQUE,
    license_number TEXT UNIQUE,
    insurance_number TEXT,
    insurance_expiry DATE,
    verified BOOLEAN DEFAULT FALSE,
    verification_date TIMESTAMP,
    
    -- Performance Metrics
    total_deliveries INT DEFAULT 0,
    successful_deliveries INT DEFAULT 0,
    failed_deliveries INT DEFAULT 0,
    cancelled_deliveries INT DEFAULT 0,
    avg_rating DECIMAL(3,2) DEFAULT 0.0,
    total_reviews INT DEFAULT 0,
    
    -- Availability & Status
    status TEXT DEFAULT 'pending',          -- pending, active, inactive, suspended
    available BOOLEAN DEFAULT FALSE,        -- Currently accepting deliveries
    last_active TIMESTAMP,
    
    -- Financial
    bank_account TEXT,
    account_holder TEXT,
    bank_name TEXT,
    swift_code TEXT,
    
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX idx_transporters_city ON transporters(operating_city);
CREATE INDEX idx_transporters_status ON transporters(status);
CREATE INDEX idx_transporters_available ON transporters(available);
CREATE INDEX idx_transporters_user ON transporters(user_id);
```

### 2. Warehouses (City Distribution Hubs)

```sql
CREATE TABLE warehouses (
    id TEXT PRIMARY KEY,
    city TEXT UNIQUE,                       -- Harare, Bulawayo, Mutare, etc
    location_name TEXT,                     -- "Downtown Hub", "Industrial Park"
    address TEXT,
    phone TEXT,
    email TEXT,
    
    -- Storage Capacity
    total_capacity INT,                     -- in items
    current_capacity INT,
    
    -- Operating Hours
    opening_time TIME,
    closing_time TIME,
    operating_days TEXT,                    -- JSON: ["Monday", "Tuesday", ...]
    
    -- Contact
    manager_name TEXT,
    manager_phone TEXT,
    
    created_at TIMESTAMP
);

CREATE INDEX idx_warehouses_city ON warehouses(city);
```

### 3. Delivery Routes (City-to-City)

```sql
CREATE TABLE delivery_routes (
    id TEXT PRIMARY KEY,
    origin_city TEXT,                       -- Source warehouse city
    destination_city TEXT,                  -- Destination warehouse city
    distance_km INT,
    estimated_hours INT,                    -- Travel time
    
    -- Default transporters for this route
    assigned_transporter_id TEXT,           -- Truck/van for inter-city
    backup_transporter_id TEXT,
    
    -- Cost
    base_cost DECIMAL(10,2),                -- Per shipment
    cost_per_kg DECIMAL(10,2),
    
    -- Schedule
    departure_time TIME,                    -- When transfer happens daily
    arrival_time TIME,                      -- Estimated arrival
    frequency TEXT DEFAULT 'daily',         -- daily, twice_daily, weekly
    
    status TEXT DEFAULT 'active',           -- active, suspended, inactive
    
    created_at TIMESTAMP
);

CREATE INDEX idx_routes_origin ON delivery_routes(origin_city);
CREATE INDEX idx_routes_destination ON delivery_routes(destination_city);
```

### 4. Shipments (Warehouse Transfers)

```sql
CREATE TABLE shipments (
    id TEXT PRIMARY KEY,
    route_id TEXT,                          -- Delivery route reference
    origin_warehouse_id TEXT,
    destination_warehouse_id TEXT,
    transporter_id TEXT,                    -- Truck operator
    
    -- Items
    item_count INT,
    total_weight DECIMAL(10,2),             -- kg
    tracking_number TEXT UNIQUE,
    
    -- Status & Timeline
    status TEXT DEFAULT 'pending',          -- pending, picked_up, in_transit, delivered
    scheduled_departure TIMESTAMP,
    actual_departure TIMESTAMP,
    estimated_arrival TIMESTAMP,
    actual_arrival TIMESTAMP,
    
    -- Cost
    shipping_cost DECIMAL(10,2),
    
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX idx_shipments_route ON shipments(route_id);
CREATE INDEX idx_shipments_origin ON shipments(origin_warehouse_id);
CREATE INDEX idx_shipments_destination ON shipments(destination_warehouse_id);
CREATE INDEX idx_shipments_transporter ON shipments(transporter_id);
CREATE INDEX idx_shipments_status ON shipments(status);
CREATE INDEX idx_shipments_tracking ON shipments(tracking_number);
```

### 5. Deliveries (Customer Deliveries)

```sql
CREATE TABLE deliveries (
    id TEXT PRIMARY KEY,
    order_id TEXT UNIQUE,                   -- Link to order
    order_number TEXT,
    
    -- Courier Assignment
    transporter_id TEXT,                    -- Delivery courier
    warehouse_id TEXT,                      -- Pickup from warehouse or seller
    
    -- Recipient Info
    recipient_name TEXT,
    recipient_phone TEXT,
    delivery_address TEXT,
    delivery_city TEXT,
    delivery_suburb TEXT,
    latitude DECIMAL(10,8),                 -- For location tracking
    longitude DECIMAL(11,8),
    
    -- Delivery Details
    item_count INT,
    total_weight DECIMAL(10,2),
    package_dimensions TEXT,                -- JSON: {length, width, height}
    
    -- Status & Timeline
    status TEXT DEFAULT 'pending',          -- pending, picked_up, in_transit, delivered, failed, returned
    delivery_window_date DATE,              -- Target delivery date
    delivery_window_start TIME,             -- e.g., 9:00 AM
    delivery_window_end TIME,               -- e.g., 5:00 PM
    
    picked_up_at TIMESTAMP,
    delivered_at TIMESTAMP,
    delivery_photo_url TEXT,                -- Proof of delivery
    recipient_signature TEXT,               -- Digital signature
    
    -- Failure Handling
    failure_reason TEXT,                    -- If failed
    return_to_warehouse BOOLEAN,
    
    -- Cost
    delivery_cost DECIMAL(10,2),
    tip_amount DECIMAL(10,2),
    
    -- Tracking
    last_location_update TIMESTAMP,
    last_known_location TEXT,               -- City/suburb
    
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX idx_deliveries_order ON deliveries(order_id);
CREATE INDEX idx_deliveries_transporter ON deliveries(transporter_id);
CREATE INDEX idx_deliveries_status ON deliveries(status);
CREATE INDEX idx_deliveries_date ON deliveries(delivery_window_date);
CREATE INDEX idx_deliveries_city ON deliveries(delivery_city);
CREATE INDEX idx_deliveries_warehouse ON deliveries(warehouse_id);
```

### 6. Delivery Tracking (Real-time Updates)

```sql
CREATE TABLE delivery_tracking (
    id TEXT PRIMARY KEY,
    delivery_id TEXT,                       -- Reference to delivery
    status TEXT,                            -- Current status
    location TEXT,                          -- Current location
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    notes TEXT,                             -- Status notes (e.g., "Package delayed due to traffic")
    timestamp TIMESTAMP,
    
    created_at TIMESTAMP
);

CREATE INDEX idx_tracking_delivery ON delivery_tracking(delivery_id);
CREATE INDEX idx_tracking_timestamp ON delivery_tracking(timestamp);
```

### 7. Transporter Performance

```sql
CREATE TABLE transporter_ratings (
    id TEXT PRIMARY KEY,
    transporter_id TEXT,
    order_id TEXT,
    user_id TEXT,                           -- Customer who rated
    
    delivery_timeliness INT,                -- 1-5 stars
    professionalism INT,                    -- 1-5 stars
    vehicle_cleanliness INT,                -- 1-5 stars
    communication INT,                      -- 1-5 stars
    overall_rating INT,                     -- 1-5 stars
    
    comment TEXT,
    photo_url TEXT,
    
    created_at TIMESTAMP
);

CREATE INDEX idx_ratings_transporter ON transporter_ratings(transporter_id);
CREATE INDEX idx_ratings_overall ON transporter_ratings(overall_rating);
```

### 8. Transporter Earnings

```sql
CREATE TABLE transporter_earnings (
    id TEXT PRIMARY KEY,
    transporter_id TEXT,
    delivery_id TEXT,                       -- Or shipment_id for inter-city
    
    delivery_fee DECIMAL(10,2),
    bonus_earned DECIMAL(10,2),             -- Performance bonus
    tips_received DECIMAL(10,2),
    total_earned DECIMAL(10,2),
    
    payment_status TEXT DEFAULT 'pending',  -- pending, paid, failed
    payment_date TIMESTAMP,
    
    created_at TIMESTAMP
);

CREATE INDEX idx_earnings_transporter ON transporter_earnings(transporter_id);
CREATE INDEX idx_earnings_status ON transporter_earnings(payment_status);
CREATE INDEX idx_earnings_date ON transporter_earnings(payment_date);
```

## API Routes (Phase 2)

### Transporter Management

```python
# Transporter Registration & Profile
POST   /api/transporters/register              # Register as courier
GET    /api/transporters/profile               # Get own profile
PUT    /api/transporters/profile               # Update profile
GET    /api/transporters/<id>                  # Public transporter info
GET    /api/transporters/<id>/ratings          # Transporter reviews
GET    /api/transporters/<id>/earnings         # Earnings summary

# Transporter Dashboard
GET    /api/transporters/dashboard             # Overview stats
GET    /api/transporters/deliveries/pending    # Pending deliveries
GET    /api/transporters/deliveries/history    # Delivery history
GET    /api/transporters/availability          # Set availability
PUT    /api/transporters/availability          # Toggle online/offline

# Deliveries
POST   /api/deliveries/<id>/accept             # Accept delivery
POST   /api/deliveries/<id>/pickup             # Confirm pickup
POST   /api/deliveries/<id>/update-location    # GPS tracking
POST   /api/deliveries/<id>/deliver            # Mark delivered
POST   /api/deliveries/<id>/fail               # Report failure
GET    /api/deliveries/<id>/tracking           # Real-time tracking
```

### Warehouse Management

```python
# Warehouse Operations
GET    /api/warehouses                         # List all warehouses
GET    /api/warehouses/<id>                    # Warehouse details
GET    /api/warehouses/<id>/inventory          # Current inventory
POST   /api/warehouses/<id>/receive-shipment   # Receive transfer
POST   /api/warehouses/<id>/dispatch-shipment  # Send transfer

# Inter-City Transfers
GET    /api/routes                             # List delivery routes
GET    /api/routes/<id>                        # Route details
POST   /api/shipments                          # Create transfer
GET    /api/shipments/<id>/tracking            # Shipment tracking
```

### Customer Delivery Tracking

```python
# Customer Tracking
GET    /api/order/<order_id>/delivery          # Delivery status
GET    /api/delivery/<tracking_number>         # Track by number
POST   /api/delivery/<id>/rate                 # Rate delivery/transporter
```

## Delivery Flow

### Same-City Delivery (Harare → Harare)

```
1. Order Created
   - Destination: Harare, Avondale
   - Calculate delivery_cost based on distance
   - Find available Harare couriers
   
2. Transporter Assigned
   - System auto-assigns or courier accepts
   - Creates delivery record
   - Set delivery_window_date to next day (or same day urgent)
   
3. Pickup
   - Courier picks up from seller/warehouse
   - Updates status: "picked_up"
   - Sends SMS/notification to customer
   
4. In Transit
   - Real-time GPS tracking (if mobile app)
   - Periodic location updates
   
5. Delivered
   - Photo proof + signature
   - Status: "delivered"
   - Send confirmation to customer
   
6. Payment
   - Calculate earnings
   - Queue for next payout
```

### Cross-City Delivery (Harare → Bulawayo)

```
1. Order Created (Harare)
   - Destination: Bulawayo
   
2. Harare Courier Assignment
   - Find Harare courier
   - Pickup location: Seller or Harare Warehouse
   - Delivery location: Harare Warehouse
   - Delivery window: Same day (by 5 PM)
   
3. Harare → Warehouse Transfer
   - Harare courier delivers to Harare Warehouse
   - Package consolidated with other Bulawayo orders
   
4. Inter-City Shipment
   - Route: Harare Warehouse → Bulawayo Warehouse
   - Assigned to truck/van operator (runs this route daily)
   - Scheduled: Tomorrow morning departure, afternoon arrival
   
5. Bulawayo Warehouse → Destination
   - Bulawayo courier picks up from warehouse
   - Delivers to customer in Bulawayo
   - Delivery window: Day after arrival (next day delivery)
   
6. Total Timeline
   - Order placed Monday 3 PM
   - Harare courier: Monday pickup → Harare warehouse
   - Inter-city truck: Tuesday morning → Tuesday afternoon in Bulawayo
   - Bulawayo courier: Wednesday morning → Customer by 5 PM
   - Total: 2-3 days for cross-city (or next-day for urgent premium)
```

## Implementation Plan

### Phase 2a: Transporter System (Week 1-2)
- [ ] Transporter registration and KYC
- [ ] Transporter dashboard
- [ ] Delivery assignment algorithm
- [ ] Real-time tracking infrastructure

### Phase 2b: Warehouse System (Week 2-3)
- [ ] Warehouse setup and management
- [ ] Delivery routes configuration
- [ ] Inter-city shipment processing
- [ ] Inventory management

### Phase 2c: Integration (Week 3-4)
- [ ] Order → Delivery routing logic
- [ ] Payment system for transporters
- [ ] Customer tracking UI
- [ ] Mobile app for couriers (future)

## Delivery Pricing

### Same-City Delivery
```
Base cost: 50 ZWL
Distance surcharge:
  - 0-5 km: +0 ZWL
  - 5-10 km: +25 ZWL
  - 10-20 km: +50 ZWL
  - 20+ km: +100 ZWL

Examples:
  Harare CBD → Avondale (5km): 50 ZWL
  Harare CBD → Borrowdale (15km): 100 ZWL
```

### Cross-City Delivery
```
Base cost: 150 ZWL (Harare ↔ Bulawayo)
  + Local delivery in origin city: 50 ZWL
  + Local delivery in destination: 50 ZWL
  + Weight surcharge (if >10kg): +10 ZWL/kg

Example:
  Harare (CBD) → Bulawayo (Ascot): 250 ZWL
  (150 inter-city + 50 Harare pickup + 50 Bulawayo delivery)
```

## Courier Earnings

### Per-Delivery Model
```
Delivery Fee:
  - Same-city small (0-5km): 40 ZWL
  - Same-city medium (5-10km): 60 ZWL
  - Same-city large (10+km): 100 ZWL

Tips:
  - Customer can add tip at delivery
  - Courier receives 100% of tips

Bonuses:
  - 5 deliveries/day: 50 ZWL bonus
  - 10 deliveries/day: 100 ZWL bonus
  - >4.5 rating: +10% earnings bonus

Example Weekly Income:
  - 5 deliveries/day × 6 days = 30 deliveries
  - Average 70 ZWL/delivery = 2,100 ZWL
  + Bonuses: 300 ZWL
  + Tips: 200 ZWL
  = 2,600 ZWL/week (~520 ZWL/day)
```

## Quality Assurance

### Transporter Verification
- National ID verification
- Driver's license verification
- Vehicle registration
- Insurance verification
- Background check

### Delivery Quality Metrics
```
On-time delivery: 95%+ target
Customer satisfaction: 4.5+ stars target
Cancellation rate: <5% target
Failed delivery: <3% target
```

### Incentives
- Top performers: Feature on app
- Monthly leaderboard with prizes
- Loyalty bonuses (5+ months active)
- Referral bonuses (bring new couriers)

## Technology Requirements

### For Transporter
- Mobile app (Android/iOS) for delivery tracking
- Real-time GPS/location tracking
- Photo upload for proof of delivery
- Push notifications for new deliveries
- Earnings dashboard

### For Admin
- Transporter management dashboard
- Delivery assignment interface
- Real-time tracking map
- Financial reporting
- Performance analytics

### For Customer
- Delivery tracking map
- Real-time notifications
- Transporter rating and review
- SMS/Push notification updates

## Risks & Mitigation

| Risk | Mitigation |
|------|-----------|
| Courier fraud/theft | Insurance requirement, GPS tracking, photo proof |
| Poor delivery quality | Rating system, performance bonuses, verification |
| No couriers in area | Premium pricing for low-demand areas, encourage signup |
| Traffic delays | Buffer time in windows, real-time tracking updates |
| Vehicle breakdowns | Backup transporter assignment, insurance requirement |
| Customer disputes | Photo/signature proof, dispute resolution process |

## Timeline

**Phase 2 Development**: 4-6 weeks
- Week 1: Transporter registration system
- Week 2: Delivery assignment & tracking
- Week 3: Warehouse system setup
- Week 4: Inter-city routing
- Week 5-6: Testing, refinement, bug fixes

**Estimated Cost**: 15,000-20,000 ZWL (development + testing)

## Success Metrics (6 months post-launch)

```
Goals:
  - 100+ active transporters
  - 95% on-time delivery rate
  - 4.5+ average transporter rating
  - <5% cancellation rate
  - Same-day delivery in all major cities
  - Next-day delivery between Harare & Bulawayo
  - <48hr delivery for all cross-city orders
```

---

## Next Steps

1. **Review & Approval**: Get stakeholder sign-off on design
2. **Finalize Schema**: Database design review
3. **API Specification**: Create detailed API contracts
4. **Start Development**: Begin Phase 2a (Transporter system)
5. **Recruit Pilots**: Find 10-15 courier operators for beta

---

**Version**: 1.0  
**Status**: Design Complete - Ready for Development  
**Target Launch**: Q1 2025
