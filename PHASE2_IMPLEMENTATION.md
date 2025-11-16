# Phase 2: Logistics Implementation Roadmap

## High-Level Architecture

```
ZimClassifieds Logistics System
│
├── Transporter Layer (Individual Couriers)
│   ├── Registration & KYC Verification
│   ├── Availability Status Management
│   ├── Real-time Location Tracking
│   └── Earnings & Rating System
│
├── Delivery Layer (Order Fulfillment)
│   ├── Delivery Assignment Algorithm
│   ├── Real-time Status Tracking
│   ├── Proof of Delivery (Photo/Signature)
│   └── Customer Communication
│
├── Warehouse Layer (City Hubs)
│   ├── Harare Warehouse (Hub A)
│   ├── Bulawayo Warehouse (Hub B)
│   ├── Mutare Warehouse (Hub C)
│   └── Other cities (Future)
│
└── Inter-City Transfer Layer
    ├── Route Management
    ├── Shipment Consolidation
    ├── Transporter Assignment
    └── Tracking & Status Updates
```

## Phase 2 Implementation Phases

### Phase 2a: Core Transporter System (Weeks 1-2)

#### 1. Database Schema Setup

```python
# app.py - Add to init_db() function

CREATE TABLE IF NOT EXISTS transporters (
    id TEXT PRIMARY KEY,
    user_id TEXT UNIQUE,
    full_name TEXT NOT NULL,
    phone TEXT NOT NULL,
    email TEXT NOT NULL,
    vehicle_type TEXT,
    license_plate TEXT UNIQUE,
    vehicle_capacity INT DEFAULT 50,
    
    operating_city TEXT NOT NULL,
    operating_suburbs TEXT,
    
    national_id TEXT UNIQUE,
    license_number TEXT UNIQUE,
    verified BOOLEAN DEFAULT FALSE,
    
    total_deliveries INT DEFAULT 0,
    successful_deliveries INT DEFAULT 0,
    avg_rating DECIMAL(3,2) DEFAULT 0.0,
    
    status TEXT DEFAULT 'pending',
    available BOOLEAN DEFAULT FALSE,
    
    bank_account TEXT,
    account_holder TEXT,
    bank_name TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

CREATE TABLE IF NOT EXISTS deliveries (
    id TEXT PRIMARY KEY,
    order_id TEXT UNIQUE,
    order_number TEXT,
    
    transporter_id TEXT,
    warehouse_id TEXT,
    
    recipient_name TEXT,
    recipient_phone TEXT,
    delivery_address TEXT,
    delivery_city TEXT,
    delivery_suburb TEXT,
    
    delivery_window_date DATE,
    delivery_window_start TIME,
    delivery_window_end TIME,
    
    status TEXT DEFAULT 'pending',
    picked_up_at TIMESTAMP,
    delivered_at TIMESTAMP,
    
    delivery_cost DECIMAL(10,2),
    
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)

CREATE TABLE IF NOT EXISTS delivery_tracking (
    id TEXT PRIMARY KEY,
    delivery_id TEXT,
    status TEXT,
    location TEXT,
    timestamp TIMESTAMP
)

CREATE TABLE IF NOT EXISTS transporter_earnings (
    id TEXT PRIMARY KEY,
    transporter_id TEXT,
    delivery_id TEXT,
    delivery_fee DECIMAL(10,2),
    tips_received DECIMAL(10,2),
    total_earned DECIMAL(10,2),
    payment_status TEXT DEFAULT 'pending',
    created_at TIMESTAMP
)
```

#### 2. Transporter Blueprint

Create `transporters.py`:

```python
from flask import Blueprint, render_template, request, session, jsonify, redirect, url_for
from functools import wraps
import sqlite3
import uuid
import os
from datetime import datetime
from werkzeug.security import generate_password_hash

transporter_bp = Blueprint('transporter', __name__, url_prefix='/transporters')

def get_db():
    conn = sqlite3.connect('zimclassifieds.db')
    conn.row_factory = sqlite3.Row
    return conn

def transporter_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'transporter_id' not in session:
            return redirect(url_for('transporter.register'))
        return f(*args, **kwargs)
    return decorated_function

# Registration
@transporter_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Transporter registration."""
    if request.method == 'POST':
        data = request.form
        
        # Validation
        if not all([data.get('full_name'), data.get('phone'), data.get('operating_city'),
                   data.get('vehicle_type'), data.get('license_plate')]):
            return render_template('transporters/register.html',
                                 error='All fields required'), 400
        
        db = get_db()
        
        # Check if already registered
        existing = db.execute(
            'SELECT id FROM transporters WHERE phone = ?', 
            (data['phone'],)
        ).fetchone()
        
        if existing:
            db.close()
            return render_template('transporters/register.html',
                                 error='Phone already registered'), 400
        
        # Create user account first
        user_id = str(uuid.uuid4())
        db.execute('''
            INSERT INTO users (user_id, full_name, email, phone, location)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, data['full_name'], data.get('email', ''), 
              data['phone'], data['operating_city']))
        
        # Create transporter record
        transporter_id = str(uuid.uuid4())
        db.execute('''
            INSERT INTO transporters 
            (id, user_id, full_name, phone, email, vehicle_type, license_plate,
             operating_city, operating_suburbs, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            transporter_id,
            user_id,
            data['full_name'],
            data['phone'],
            data.get('email', ''),
            data['vehicle_type'],
            data['license_plate'].upper(),
            data['operating_city'],
            ','.join(data.getlist('suburbs')) if data.getlist('suburbs') else None,
            'pending',  # Requires verification
            datetime.now().isoformat()
        ))
        
        db.commit()
        db.close()
        
        # Auto-login
        session['transporter_id'] = transporter_id
        session['user_id'] = user_id
        
        return redirect(url_for('transporter.dashboard'))
    
    # GET request - show form
    zimbabwe_cities = ['Harare', 'Bulawayo', 'Mutare', 'Gweru', 'Kwekwe', 'Chinhoyi']
    return render_template('transporters/register.html', cities=zimbabwe_cities)

# Dashboard
@transporter_bp.route('/dashboard')
@transporter_required
def dashboard():
    """Transporter dashboard."""
    transporter_id = session['transporter_id']
    db = get_db()
    
    transporter = db.execute(
        'SELECT * FROM transporters WHERE id = ?', 
        (transporter_id,)
    ).fetchone()
    
    # Get today's deliveries
    today = datetime.now().strftime('%Y-%m-%d')
    deliveries_today = db.execute('''
        SELECT COUNT(*) as count FROM deliveries 
        WHERE transporter_id = ? AND date(created_at) = ?
    ''', (transporter_id, today)).fetchone()
    
    # Get earnings
    earnings = db.execute('''
        SELECT 
            COALESCE(SUM(total_earned), 0) as total_earnings,
            COALESCE(SUM(CASE WHEN payment_status = 'pending' THEN total_earned ELSE 0 END), 0) as pending
        FROM transporter_earnings 
        WHERE transporter_id = ?
    ''', (transporter_id,)).fetchone()
    
    # Get pending deliveries
    pending_deliveries = db.execute('''
        SELECT COUNT(*) as count FROM deliveries 
        WHERE transporter_id = ? AND status IN ('pending', 'picked_up')
    ''', (transporter_id,)).fetchone()
    
    db.close()
    
    return render_template('transporters/dashboard.html',
                         transporter=transporter,
                         deliveries_today=deliveries_today['count'],
                         total_earnings=earnings['total_earnings'],
                         pending_earnings=earnings['pending'],
                         pending_deliveries=pending_deliveries['count'])

# Deliveries
@transporter_bp.route('/deliveries/available')
@transporter_required
def available_deliveries():
    """List available deliveries in transporter's city."""
    transporter_id = session['transporter_id']
    db = get_db()
    
    transporter = db.execute(
        'SELECT operating_city FROM transporters WHERE id = ?',
        (transporter_id,)
    ).fetchone()
    
    # Find unassigned deliveries in same city
    deliveries = db.execute('''
        SELECT d.*, o.order_number, o.total_amount
        FROM deliveries d
        JOIN orders o ON d.order_id = o.id
        WHERE d.status = 'pending' 
        AND d.transporter_id IS NULL
        AND d.delivery_city = ?
        ORDER BY d.created_at DESC
    ''', (transporter['operating_city'],)).fetchall()
    
    db.close()
    
    return render_template('transporters/available_deliveries.html',
                         deliveries=deliveries)

@transporter_bp.route('/deliveries/<delivery_id>/accept', methods=['POST'])
@transporter_required
def accept_delivery(delivery_id):
    """Accept a delivery assignment."""
    transporter_id = session['transporter_id']
    db = get_db()
    
    # Check if already assigned
    delivery = db.execute(
        'SELECT transporter_id FROM deliveries WHERE id = ?',
        (delivery_id,)
    ).fetchone()
    
    if delivery and delivery['transporter_id']:
        db.close()
        return jsonify({'success': False, 'message': 'Already assigned'}), 400
    
    # Assign to transporter
    db.execute(
        'UPDATE deliveries SET transporter_id = ? WHERE id = ?',
        (transporter_id, delivery_id)
    )
    
    db.commit()
    db.close()
    
    return jsonify({'success': True, 'message': 'Delivery accepted'})

@transporter_bp.route('/deliveries/<delivery_id>/pickup', methods=['POST'])
@transporter_required
def pickup_delivery(delivery_id):
    """Mark delivery as picked up."""
    transporter_id = session['transporter_id']
    db = get_db()
    
    db.execute('''
        UPDATE deliveries 
        SET status = 'picked_up', picked_up_at = ?
        WHERE id = ? AND transporter_id = ?
    ''', (datetime.now().isoformat(), delivery_id, transporter_id))
    
    db.commit()
    db.close()
    
    return jsonify({'success': True, 'message': 'Pickup confirmed'})

@transporter_bp.route('/deliveries/<delivery_id>/deliver', methods=['POST'])
@transporter_required
def deliver(delivery_id):
    """Mark delivery as completed."""
    transporter_id = session['transporter_id']
    data = request.get_json()
    
    db = get_db()
    
    # Update delivery
    db.execute('''
        UPDATE deliveries 
        SET status = 'delivered', delivered_at = ?
        WHERE id = ? AND transporter_id = ?
    ''', (datetime.now().isoformat(), delivery_id, transporter_id))
    
    # Get order for payment calculation
    delivery = db.execute(
        'SELECT order_id FROM deliveries WHERE id = ?',
        (delivery_id,)
    ).fetchone()
    
    order = db.execute(
        'SELECT total_amount FROM orders WHERE order_id = ?',
        (delivery['order_id'],)
    ).fetchone()
    
    # Calculate earnings (10% of order value)
    delivery_fee = min(order['total_amount'] * 0.10, 200)  # Cap at 200 ZWL
    
    # Create earnings record
    earnings_id = str(uuid.uuid4())
    db.execute('''
        INSERT INTO transporter_earnings 
        (id, transporter_id, delivery_id, delivery_fee, total_earned, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (earnings_id, transporter_id, delivery_id, delivery_fee, 
          delivery_fee, datetime.now().isoformat()))
    
    # Update delivery count
    db.execute(
        'UPDATE transporters SET successful_deliveries = successful_deliveries + 1 WHERE id = ?',
        (transporter_id,)
    )
    
    db.commit()
    db.close()
    
    return jsonify({'success': True, 'message': 'Delivery completed', 
                   'earnings': delivery_fee})

# Availability
@transporter_bp.route('/availability', methods=['GET', 'POST'])
@transporter_required
def availability():
    """Set online/offline status."""
    transporter_id = session['transporter_id']
    db = get_db()
    
    if request.method == 'POST':
        available = request.json.get('available', False)
        
        db.execute(
            'UPDATE transporters SET available = ?, last_active = ? WHERE id = ?',
            (available, datetime.now().isoformat(), transporter_id)
        )
        
        db.commit()
        db.close()
        
        return jsonify({'success': True, 'available': available})
    
    transporter = db.execute(
        'SELECT available FROM transporters WHERE id = ?',
        (transporter_id,)
    ).fetchone()
    
    db.close()
    
    return jsonify({'available': transporter['available']})

# Earnings
@transporter_bp.route('/earnings')
@transporter_required
def earnings():
    """View earnings and payout history."""
    transporter_id = session['transporter_id']
    db = get_db()
    
    earnings_data = db.execute('''
        SELECT 
            SUM(total_earned) as total_earned,
            SUM(CASE WHEN payment_status = 'pending' THEN total_earned ELSE 0 END) as pending,
            SUM(CASE WHEN payment_status = 'paid' THEN total_earned ELSE 0 END) as paid,
            COUNT(*) as total_deliveries
        FROM transporter_earnings
        WHERE transporter_id = ?
    ''', (transporter_id,)).fetchone()
    
    recent_earnings = db.execute('''
        SELECT te.*, d.delivery_window_date
        FROM transporter_earnings te
        LEFT JOIN deliveries d ON te.delivery_id = d.id
        WHERE te.transporter_id = ?
        ORDER BY te.created_at DESC
        LIMIT 20
    ''', (transporter_id,)).fetchall()
    
    db.close()
    
    return render_template('transporters/earnings.html',
                         earnings_data=earnings_data,
                         recent_earnings=recent_earnings)
```

#### 3. Register Blueprint in app.py

```python
# In app.py, add to imports
from transporters import transporter_bp

# Register blueprint
app.register_blueprint(transporter_bp)
```

### Phase 2b: Delivery Assignment & Tracking (Weeks 2-3)

#### Delivery Router Algorithm

```python
def assign_delivery(order_id, delivery_location_city):
    """
    Automatically assign delivery to available transporter.
    
    Rules:
    1. Find available transporters in same city
    2. Prefer transporters with highest ratings
    3. Consider current delivery count (load balancing)
    4. Check vehicle capacity
    """
    db = get_db()
    
    # Find best available transporter
    transporter = db.execute('''
        SELECT * FROM transporters
        WHERE operating_city = ?
        AND available = TRUE
        AND status = 'verified'
        AND verified = TRUE
        ORDER BY avg_rating DESC, successful_deliveries ASC
        LIMIT 1
    ''', (delivery_location_city,)).fetchone()
    
    if not transporter:
        # No transporter available - queue for manual assignment
        return None
    
    # Create delivery record
    delivery_id = str(uuid.uuid4())
    db.execute('''
        INSERT INTO deliveries 
        (id, order_id, transporter_id, delivery_city, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (delivery_id, order_id, transporter['id'], 
          delivery_location_city, 'pending', datetime.now().isoformat()))
    
    db.commit()
    db.close()
    
    return delivery_id
```

#### Update Order Creation to Trigger Delivery

```python
# In app.py - modify create_order function

@app.route('/api/orders', methods=['POST'])
@login_required
def create_order():
    # ... existing order creation code ...
    
    # After order is created, create delivery
    if payment_method in ['bank_transfer', 'cod']:
        # Non-Stripe: immediately create delivery
        delivery_id = assign_delivery(order_id, shipping_city)
        
        if delivery_id:
            # Notify transporter
            send_transporter_notification(delivery_id)
```

### Phase 2c: Warehouse System (Weeks 3-4)

#### Warehouse Setup

```python
# Add to init_db() for warehouse setup

CREATE TABLE IF NOT EXISTS warehouses (
    id TEXT PRIMARY KEY,
    city TEXT UNIQUE NOT NULL,
    location_name TEXT,
    address TEXT,
    phone TEXT,
    manager_name TEXT,
    opening_time TIME DEFAULT '08:00',
    closing_time TIME DEFAULT '17:00',
    created_at TIMESTAMP
)

# Insert initial warehouses
INSERT INTO warehouses VALUES
    ('wh_harare', 'Harare', 'Harare Central Hub', '123 Main Street, Harare', '+263712345678', 'John Mutendi', '08:00', '17:00', CURRENT_TIMESTAMP),
    ('wh_bulawayo', 'Bulawayo', 'Bulawayo Hub', '456 Main Road, Bulawayo', '+263712345679', 'Grace Nyoni', '08:00', '17:00', CURRENT_TIMESTAMP),
    ('wh_mutare', 'Mutare', 'Mutare Distribution Centre', '789 Leopold Takawira, Mutare', '+263712345680', 'David Chiparwa', '08:00', '17:00', CURRENT_TIMESTAMP)
```

#### Warehouse Blueprint

```python
# Create warehouses.py

@app.route('/api/warehouses')
def list_warehouses():
    """List all warehouses."""
    db = get_db()
    warehouses = db.execute('SELECT * FROM warehouses').fetchall()
    db.close()
    return jsonify([dict(w) for w in warehouses])

@app.route('/api/warehouses/<warehouse_id>/inventory')
def warehouse_inventory(warehouse_id):
    """Get warehouse current inventory."""
    db = get_db()
    items = db.execute('''
        SELECT p.name, COUNT(*) as count, p.price
        FROM deliveries d
        JOIN order_items oi ON d.order_id = oi.order_id
        JOIN products p ON oi.product_id = p.id
        WHERE d.warehouse_id = ? AND d.status = 'in_warehouse'
        GROUP BY p.id
    ''', (warehouse_id,)).fetchall()
    db.close()
    return jsonify([dict(i) for i in items])
```

## Templates

### Transporter Registration Template

```html
<!-- templates/transporters/register.html -->
{% extends "base.html" %}

{% block title %}Become a Courier - ZimClassifieds{% endblock %}

{% block content %}
<div class="container py-4">
    <div class="row justify-content-center">
        <div class="col-md-6">
            <div class="card border-0 shadow-sm">
                <div class="card-header bg-primary text-white">
                    <h4 class="mb-0">Become a Courier</h4>
                </div>
                <div class="card-body">
                    {% if error %}
                    <div class="alert alert-danger">{{ error }}</div>
                    {% endif %}
                    
                    <form method="POST">
                        <div class="mb-3">
                            <label class="form-label">Full Name *</label>
                            <input type="text" name="full_name" class="form-control" required>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Phone Number *</label>
                            <input type="tel" name="phone" class="form-control" placeholder="+263..." required>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Email</label>
                            <input type="email" name="email" class="form-control">
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Primary Operating City *</label>
                            <select name="operating_city" class="form-select" required>
                                <option value="">Select city...</option>
                                {% for city in cities %}
                                <option value="{{ city }}">{{ city }}</option>
                                {% endfor %}
                            </select>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Vehicle Type *</label>
                            <select name="vehicle_type" class="form-select" required>
                                <option value="">Select type...</option>
                                <option value="motorcycle">Motorcycle/Bike</option>
                                <option value="car">Car (Sedan)</option>
                                <option value="van">Van (Multiple deliveries)</option>
                                <option value="truck">Truck (Inter-city)</option>
                            </select>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Vehicle License Plate *</label>
                            <input type="text" name="license_plate" class="form-control" placeholder="ABC 1234" required>
                        </div>
                        
                        <button type="submit" class="btn btn-primary w-100">
                            Register as Courier
                        </button>
                    </form>
                    
                    <hr>
                    
                    <p class="text-muted small">
                        ✓ Earn 40-100 ZWL per delivery<br>
                        ✓ Keep 100% of tips<br>
                        ✓ Performance bonuses<br>
                        ✓ Flexible hours
                    </p>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

## Testing Checklist

- [ ] Transporter registration (all vehicle types)
- [ ] Dashboard display with stats
- [ ] Accept delivery from available list
- [ ] Pickup and delivery status updates
- [ ] Earnings calculation and display
- [ ] Availability toggle (online/offline)
- [ ] Real-time delivery tracking (map view)
- [ ] Customer notifications
- [ ] Rating and review system

## Next Steps

1. Review and approve design
2. Set up development database
3. Implement Phase 2a (Transporter system)
4. Deploy to staging environment
5. Beta test with 10-15 couriers
6. Iterate based on feedback
7. Launch Phase 2b (Inter-city logistics)

---

**Estimated Timeline**: 4-6 weeks  
**Team Size**: 2-3 developers  
**Priority**: High (enables next-day delivery)
