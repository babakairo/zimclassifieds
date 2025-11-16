"""
Transporters Blueprint - Logistics & Delivery Management
Handles transporter registration, delivery assignments, and tracking for local and regional deliveries.
"""

from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import sqlite3
import uuid
import re

transporters_bp = Blueprint('transporters', __name__, url_prefix='/transporters')


def get_db():
    """Local DB helper to avoid circular import."""
    db = sqlite3.connect('zimclassifieds.db')
    db.row_factory = sqlite3.Row
    return db


def transporter_required(f):
    """Decorator to require transporter login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'transporter_id' not in session or 'user_id' not in session:
            return redirect(url_for('transporters.login'))
        return f(*args, **kwargs)
    return decorated_function


@transporters_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Transporter registration page."""
    if request.method == 'POST':
        # Personal Information
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        phone = request.form.get('phone')
        
        # Transport Details
        transport_type = request.form.get('transport_type')  # motorcycle, car, van, truck
        vehicle_registration = request.form.get('vehicle_registration')
        vehicle_make_model = request.form.get('vehicle_make_model')
        
        # Service Coverage
        service_type = request.form.get('service_type')  # local, regional, both
        primary_city = request.form.get('primary_city')
        coverage_areas = request.form.getlist('coverage_areas')  # Multiple areas
        
        # Documents
        id_number = request.form.get('id_number')
        drivers_license = request.form.get('drivers_license')
        police_clearance = request.form.get('police_clearance')
        clearance_issue_date = request.form.get('clearance_issue_date')
        clearance_expiry_date = request.form.get('clearance_expiry_date')
        
        db = get_db()
        error = None
        
        # Validation
        if not all([full_name, email, password, phone, transport_type, service_type, primary_city, police_clearance]):
            error = 'All required fields must be filled, including police clearance certificate.'
        elif password != confirm_password:
            error = 'Passwords do not match.'
        elif len(password) < 6:
            error = 'Password must be at least 6 characters.'
        elif db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone():
            error = 'Email already registered.'
        
        if error:
            db.close()
            return render_template('transporters/register.html', error=error)
        
        # Create user account
        user_id = str(uuid.uuid4())
        db.execute('''
            INSERT INTO users (user_id, email, password_hash, full_name, phone)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, email, generate_password_hash(password), full_name, phone))
        
        # Create transporter profile
        transporter_id = str(uuid.uuid4())
        db.execute('''
            INSERT INTO transporters 
            (transporter_id, user_id, transport_type, vehicle_registration, vehicle_make_model,
             service_type, primary_city, coverage_areas, id_number, drivers_license, 
             police_clearance, clearance_issue_date, clearance_expiry_date, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
        ''', (transporter_id, user_id, transport_type, vehicle_registration, vehicle_make_model,
              service_type, primary_city, ','.join(coverage_areas), id_number, drivers_license,
              police_clearance, clearance_issue_date, clearance_expiry_date))
        
        db.commit()
        db.close()
        
        return redirect(url_for('transporters.login', success='Registration successful! Your account will be verified within 24 hours.'))
    
    # Get cities for dropdown
    from app import ZIMBABWE_CITIES
    return render_template('transporters/register.html', cities=ZIMBABWE_CITIES)


@transporters_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Transporter login."""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        
        if user and check_password_hash(user['password_hash'], password):
            # Check if user is a transporter
            transporter = db.execute('''
                SELECT * FROM transporters WHERE user_id = ?
            ''', (user['user_id'],)).fetchone()
            
            if transporter:
                if transporter['status'] == 'suspended':
                    db.close()
                    return render_template('transporters/login.html', error='Your account has been suspended.')
                
                session['user_id'] = user['user_id']
                session['transporter_id'] = transporter['transporter_id']
                session['user_name'] = user['full_name']
                session['transporter_status'] = transporter['status']
                
                db.close()
                return redirect(url_for('transporters.dashboard'))
            else:
                db.close()
                return render_template('transporters/login.html', error='Not a transporter account.')
        
        db.close()
        return render_template('transporters/login.html', error='Invalid email or password')
    
    return render_template('transporters/login.html')


@transporters_bp.route('/logout')
def logout():
    """Transporter logout."""
    session.pop('transporter_id', None)
    session.pop('transporter_status', None)
    return redirect(url_for('index'))


@transporters_bp.route('/dashboard')
@transporter_required
def dashboard():
    """Transporter dashboard - overview of deliveries and earnings."""
    db = get_db()
    transporter_id = session['transporter_id']
    
    # Get transporter info
    transporter = db.execute('''
        SELECT t.*, u.full_name, u.email, u.phone
        FROM transporters t
        JOIN users u ON t.user_id = u.user_id
        WHERE t.transporter_id = ?
    ''', (transporter_id,)).fetchone()
    
    # Get statistics
    stats = db.execute('''
        SELECT 
            COUNT(*) as total_deliveries,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
            SUM(CASE WHEN status = 'in_transit' THEN 1 ELSE 0 END) as in_transit,
            SUM(CASE WHEN status = 'pending_pickup' THEN 1 ELSE 0 END) as pending_pickup,
            SUM(delivery_fee) as total_earnings
        FROM deliveries
        WHERE transporter_id = (SELECT id FROM transporters WHERE transporter_id = ?)
    ''', (transporter_id,)).fetchone()
    
    # Get recent deliveries
    recent_deliveries = db.execute('''
        SELECT d.*, o.order_id, u.full_name as customer_name
        FROM deliveries d
        JOIN orders o ON d.order_id = o.id
        JOIN users u ON o.user_id = u.user_id
        WHERE d.transporter_id = (SELECT id FROM transporters WHERE transporter_id = ?)
        ORDER BY d.created_at DESC
        LIMIT 10
    ''', (transporter_id,)).fetchall()
    
    db.close()
    
    return render_template('transporters/dashboard.html',
                         transporter=transporter,
                         stats=stats,
                         recent_deliveries=recent_deliveries)


@transporters_bp.route('/available-jobs')
@transporter_required
def available_jobs():
    """View available delivery jobs."""
    db = get_db()
    transporter_id = session['transporter_id']
    
    # Get transporter info for filtering
    transporter = db.execute('''
        SELECT * FROM transporters WHERE transporter_id = ?
    ''', (transporter_id,)).fetchone()
    
    # Get available deliveries matching transporter's coverage
    if transporter['service_type'] == 'local':
        # Local deliveries in primary city
        jobs = db.execute('''
            SELECT d.*, o.order_id, o.total_amount,
                   u.full_name as customer_name, u.phone as customer_phone,
                   s.store_name as seller_name
            FROM deliveries d
            JOIN orders o ON d.order_id = o.id
            JOIN users u ON o.user_id = u.user_id
            JOIN order_items oi ON o.id = oi.order_id
            JOIN products p ON oi.product_id = p.id
            JOIN sellers s ON p.seller_id = s.id
            WHERE d.transporter_id IS NULL
            AND d.delivery_type = 'local'
            AND d.pickup_city = ?
            AND d.status = 'pending_assignment'
            GROUP BY d.id
            ORDER BY d.created_at ASC
        ''', (transporter['primary_city'],)).fetchall()
    elif transporter['service_type'] == 'regional':
        # Regional/inter-city deliveries
        coverage = transporter['coverage_areas'].split(',')
        placeholders = ','.join(['?' for _ in coverage])
        jobs = db.execute(f'''
            SELECT d.*, o.order_id, o.total_amount,
                   u.full_name as customer_name, u.phone as customer_phone,
                   s.store_name as seller_name
            FROM deliveries d
            JOIN orders o ON d.order_id = o.id
            JOIN users u ON o.user_id = u.user_id
            JOIN order_items oi ON o.id = oi.order_id
            JOIN products p ON oi.product_id = p.id
            JOIN sellers s ON p.seller_id = s.id
            WHERE d.transporter_id IS NULL
            AND d.delivery_type = 'regional'
            AND (d.pickup_city IN ({placeholders}) OR d.delivery_city IN ({placeholders}))
            AND d.status = 'pending_assignment'
            GROUP BY d.id
            ORDER BY d.created_at ASC
        ''', (*coverage, *coverage)).fetchall()
    else:  # both
        coverage = transporter['coverage_areas'].split(',')
        placeholders = ','.join(['?' for _ in coverage])
        jobs = db.execute(f'''
            SELECT d.*, o.order_id, o.total_amount,
                   u.full_name as customer_name, u.phone as customer_phone,
                   s.store_name as seller_name
            FROM deliveries d
            JOIN orders o ON d.order_id = o.id
            JOIN users u ON o.user_id = u.user_id
            JOIN order_items oi ON o.id = oi.order_id
            JOIN products p ON oi.product_id = p.id
            JOIN sellers s ON p.seller_id = s.id
            WHERE d.transporter_id IS NULL
            AND d.status = 'pending_assignment'
            AND (d.pickup_city = ? OR d.pickup_city IN ({placeholders}) OR d.delivery_city IN ({placeholders}))
            GROUP BY d.id
            ORDER BY d.created_at ASC
        ''', (transporter['primary_city'], *coverage, *coverage)).fetchall()
    
    db.close()
    
    return render_template('transporters/available_jobs.html', jobs=jobs)


@transporters_bp.route('/accept-job/<delivery_id>', methods=['POST'])
@transporter_required
def accept_job(delivery_id):
    """Accept a delivery job."""
    db = get_db()
    transporter_id = session['transporter_id']
    
    # Get transporter's internal ID
    transporter = db.execute('''
        SELECT id, status FROM transporters WHERE transporter_id = ?
    ''', (transporter_id,)).fetchone()
    
    if transporter['status'] != 'active':
        db.close()
        return jsonify({'success': False, 'error': 'Account not active'}), 403
    
    # Check if delivery is still available
    delivery = db.execute('''
        SELECT * FROM deliveries WHERE id = ? AND transporter_id IS NULL
    ''', (delivery_id,)).fetchone()
    
    if not delivery:
        db.close()
        return jsonify({'success': False, 'error': 'Job no longer available'}), 404
    
    # Assign transporter to delivery
    db.execute('''
        UPDATE deliveries
        SET transporter_id = ?, status = 'assigned', assigned_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (transporter['id'], delivery_id))
    
    db.commit()
    db.close()
    
    return jsonify({'success': True, 'message': 'Job accepted successfully'})


@transporters_bp.route('/my-deliveries')
@transporter_required
def my_deliveries():
    """View assigned deliveries."""
    db = get_db()
    transporter_id = session['transporter_id']
    
    status_filter = request.args.get('status', 'all')
    
    query = '''
        SELECT d.*, o.order_id, o.total_amount,
               u.full_name as customer_name, u.phone as customer_phone, u.location as customer_location,
               s.store_name as seller_name, s.user_id as seller_user_id,
               su.phone as seller_phone
        FROM deliveries d
        JOIN orders o ON d.order_id = o.id
        JOIN users u ON o.user_id = u.user_id
        JOIN order_items oi ON o.id = oi.order_id
        JOIN products p ON oi.product_id = p.id
        JOIN sellers s ON p.seller_id = s.id
        JOIN users su ON s.user_id = su.user_id
        WHERE d.transporter_id = (SELECT id FROM transporters WHERE transporter_id = ?)
    '''
    
    params = [transporter_id]
    
    if status_filter != 'all':
        query += ' AND d.status = ?'
        params.append(status_filter)
    
    query += ' GROUP BY d.id ORDER BY d.created_at DESC'
    
    deliveries = db.execute(query, params).fetchall()
    db.close()
    
    return render_template('transporters/my_deliveries.html', 
                         deliveries=deliveries,
                         current_status=status_filter)


@transporters_bp.route('/delivery/<int:delivery_id>')
@transporter_required
def delivery_detail(delivery_id):
    """View delivery details."""
    db = get_db()
    transporter_id = session['transporter_id']
    
    delivery = db.execute('''
        SELECT d.*, o.order_id, o.total_amount,
               u.full_name as customer_name, u.phone as customer_phone, u.location as customer_location,
               s.store_name as seller_name, su.phone as seller_phone
        FROM deliveries d
        JOIN orders o ON d.order_id = o.id
        JOIN users u ON o.user_id = u.user_id
        JOIN order_items oi ON o.id = oi.order_id
        JOIN products p ON oi.product_id = p.id
        JOIN sellers s ON p.seller_id = s.id
        JOIN users su ON s.user_id = su.user_id
        WHERE d.id = ?
        AND d.transporter_id = (SELECT id FROM transporters WHERE transporter_id = ?)
        GROUP BY d.id
    ''', (delivery_id, transporter_id)).fetchone()
    
    if not delivery:
        db.close()
        return 'Delivery not found', 404
    
    # Get order items
    items = db.execute('''
        SELECT oi.*, p.name as product_name
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        WHERE oi.order_id = ?
    ''', (delivery['order_id'],)).fetchall()
    
    db.close()
    
    return render_template('transporters/delivery_detail.html', 
                         delivery=delivery,
                         items=items)


@transporters_bp.route('/update-status/<int:delivery_id>', methods=['POST'])
@transporter_required
def update_delivery_status(delivery_id):
    """Update delivery status."""
    db = get_db()
    transporter_id = session['transporter_id']
    
    new_status = request.json.get('status')
    notes = request.json.get('notes', '')
    location = request.json.get('location', '')  # GPS coordinates
    
    valid_statuses = ['assigned', 'picked_up', 'in_transit', 'arrived', 'completed', 'failed']
    
    if new_status not in valid_statuses:
        db.close()
        return jsonify({'success': False, 'error': 'Invalid status'}), 400
    
    # Verify ownership
    delivery = db.execute('''
        SELECT * FROM deliveries 
        WHERE id = ? AND transporter_id = (SELECT id FROM transporters WHERE transporter_id = ?)
    ''', (delivery_id, transporter_id)).fetchone()
    
    if not delivery:
        db.close()
        return jsonify({'success': False, 'error': 'Delivery not found'}), 404
    
    # Update delivery
    timestamp_field = None
    if new_status == 'picked_up':
        timestamp_field = 'picked_up_at'
    elif new_status == 'completed':
        timestamp_field = 'delivered_at'
    
    if timestamp_field:
        db.execute(f'''
            UPDATE deliveries
            SET status = ?, {timestamp_field} = CURRENT_TIMESTAMP, tracking_notes = ?, current_location = ?
            WHERE id = ?
        ''', (new_status, notes, location, delivery_id))
    else:
        db.execute('''
            UPDATE deliveries
            SET status = ?, tracking_notes = ?, current_location = ?
            WHERE id = ?
        ''', (new_status, notes, location, delivery_id))
    
    # If completed, update order status
    if new_status == 'completed':
        db.execute('''
            UPDATE orders
            SET status = 'completed', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (delivery['order_id'],))
    
    db.commit()
    db.close()
    
    return jsonify({'success': True, 'message': f'Status updated to {new_status}'})


@transporters_bp.route('/earnings')
@transporter_required
def earnings():
    """View earnings and payment history."""
    db = get_db()
    transporter_id = session['transporter_id']
    
    # Get earnings summary
    summary = db.execute('''
        SELECT 
            SUM(CASE WHEN status = 'completed' THEN delivery_fee ELSE 0 END) as total_earned,
            SUM(CASE WHEN status = 'completed' AND DATE(delivered_at) = DATE('now') THEN delivery_fee ELSE 0 END) as today_earnings,
            SUM(CASE WHEN status = 'completed' AND strftime('%Y-%W', delivered_at) = strftime('%Y-%W', 'now') THEN delivery_fee ELSE 0 END) as week_earnings,
            SUM(CASE WHEN status = 'completed' AND strftime('%Y-%m', delivered_at) = strftime('%Y-%m', 'now') THEN delivery_fee ELSE 0 END) as month_earnings,
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_deliveries
        FROM deliveries
        WHERE transporter_id = (SELECT id FROM transporters WHERE transporter_id = ?)
    ''', (transporter_id,)).fetchone()
    
    # Get delivery history
    deliveries = db.execute('''
        SELECT d.*, o.order_id
        FROM deliveries d
        JOIN orders o ON d.order_id = o.id
        WHERE d.transporter_id = (SELECT id FROM transporters WHERE transporter_id = ?)
        AND d.status = 'completed'
        ORDER BY d.delivered_at DESC
        LIMIT 50
    ''', (transporter_id,)).fetchall()
    
    db.close()
    
    return render_template('transporters/earnings.html', 
                         summary=summary,
                         deliveries=deliveries)


@transporters_bp.route('/profile', methods=['GET', 'POST'])
@transporter_required
def profile():
    """View and edit transporter profile."""
    db = get_db()
    transporter_id = session['transporter_id']
    
    if request.method == 'POST':
        # Update profile
        phone = request.form.get('phone')
        vehicle_registration = request.form.get('vehicle_registration')
        vehicle_make_model = request.form.get('vehicle_make_model')
        coverage_areas = request.form.getlist('coverage_areas')
        
        db.execute('''
            UPDATE users
            SET phone = ?
            WHERE user_id = ?
        ''', (phone, session['user_id']))
        
        db.execute('''
            UPDATE transporters
            SET vehicle_registration = ?, vehicle_make_model = ?, coverage_areas = ?
            WHERE transporter_id = ?
        ''', (vehicle_registration, vehicle_make_model, ','.join(coverage_areas), transporter_id))
        
        db.commit()
        db.close()
        
        return redirect(url_for('transporters.profile', success='Profile updated successfully'))
    
    # Get profile
    transporter = db.execute('''
        SELECT t.*, u.full_name, u.email, u.phone
        FROM transporters t
        JOIN users u ON t.user_id = u.user_id
        WHERE t.transporter_id = ?
    ''', (transporter_id,)).fetchone()
    
    db.close()
    
    from app import ZIMBABWE_CITIES
    return render_template('transporters/profile.html', 
                         transporter=transporter,
                         cities=ZIMBABWE_CITIES)
