from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import uuid

# Import helper from main app
import sqlite3


def get_db():
    """Local DB helper to avoid circular import with app module when registering blueprint."""
    db = sqlite3.connect('zimclassifieds.db')
    db.row_factory = sqlite3.Row
    return db

rentals_bp = Blueprint('rentals', __name__, url_prefix='/rentals')


def landlord_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('user_type') != 'landlord' or 'landlord_id' not in session:
            return redirect(url_for('rentals.login'))
        return f(*args, **kwargs)
    return decorated


def tenant_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('user_type') != 'tenant' or 'tenant_id' not in session:
            return redirect(url_for('rentals.login'))
        return f(*args, **kwargs)
    return decorated


@rentals_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_type = request.form.get('user_type')  # 'landlord' or 'tenant'
        username = request.form.get('username')
        password = request.form.get('password')

        db = get_db()

        if user_type == 'landlord':
            user = db.execute(
                'SELECT id, user_id, password_hash, verification_status FROM landlords WHERE username = ?',
                (username,)
            ).fetchone()

            if user and check_password_hash(user['password_hash'], password):
                if user['verification_status'] != 'approved':
                    return render_template('rentals/login.html', error=f'Your landlord account is {user["verification_status"]}. Please wait for admin verification.')

                session['user_id'] = user['user_id']
                session['user_type'] = 'landlord'
                session['landlord_id'] = user['id']
                session['username'] = username
                db.close()
                return redirect(url_for('rentals.landlord_dashboard'))

        elif user_type == 'tenant':
            user = db.execute(
                'SELECT id, user_id, password_hash, approval_status FROM tenants WHERE username = ?',
                (username,)
            ).fetchone()

            if user and check_password_hash(user['password_hash'], password):
                if user['approval_status'] != 'approved':
                    return render_template('rentals/login.html', error=f'Your tenant account is {user["approval_status"]}. Please wait for admin approval.')

                session['user_id'] = user['user_id']
                session['user_type'] = 'tenant'
                session['tenant_id'] = user['id']
                session['username'] = username
                db.close()
                return redirect(url_for('rentals.tenant_dashboard'))

        db.close()
        return render_template('rentals/login.html', error='Invalid username or password')

    return render_template('rentals/login.html')


@rentals_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_type = request.form.get('user_type')
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')

        if password != confirm_password:
            return render_template('rentals/register.html', error='Passwords do not match')

        db = get_db()
        try:
            user_id = str(uuid.uuid4())
            password_hash = generate_password_hash(password)

            if user_type == 'landlord':
                company_name = request.form.get('company_name')
                db.execute('''
                    INSERT INTO landlords (user_id, username, password_hash, email, full_name, phone, company_name)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, username, password_hash, email, full_name, phone, company_name))

            elif user_type == 'tenant':
                occupation = request.form.get('occupation')
                db.execute('''
                    INSERT INTO tenants (user_id, username, password_hash, email, full_name, phone, occupation)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, username, password_hash, email, full_name, phone, occupation))

            db.commit()
            db.close()
            return render_template('rentals/register.html', success=f'Account created! Your account is pending {user_type} verification. Please log in and wait for admin approval.')
        except Exception:
            db.close()
            return render_template('rentals/register.html', error='Username or email may already exist')

    return render_template('rentals/register.html')


# Landlord dashboard and property routes (adapted)
@rentals_bp.route('/landlord/dashboard')
def landlord_dashboard():
    if 'landlord_id' not in session:
        return redirect(url_for('rentals.login'))

    db = get_db()
    landlord_id = session['landlord_id']

    landlord = db.execute('SELECT * FROM landlords WHERE id = ?', (landlord_id,)).fetchone()

    properties_count = db.execute('SELECT COUNT(*) as count FROM properties WHERE landlord_id = ?', (landlord_id,)).fetchone()['count']
    rooms_count = db.execute('SELECT COUNT(*) as count FROM rooms WHERE landlord_id = ?', (landlord_id,)).fetchone()['count']

    applications = db.execute('''
        SELECT a.*, p.title, t.full_name
        FROM applications a
        JOIN properties p ON a.property_id = p.id
        JOIN tenants t ON a.tenant_id = t.id
        WHERE a.landlord_id = ?
        ORDER BY a.application_date DESC
    ''', (landlord_id,)).fetchall()

    room_applications = db.execute('''
        SELECT ra.*, r.title, t.full_name
        FROM room_applications ra
        JOIN rooms r ON ra.room_id = r.id
        JOIN tenants t ON ra.tenant_id = t.id
        WHERE ra.landlord_id = ?
        ORDER BY ra.application_date DESC
    ''', (landlord_id,)).fetchall()

    unread_messages = db.execute('''
        SELECT COUNT(*) as count FROM lt_messages
        WHERE receiver_type = 'landlord' AND receiver_id = ? AND is_read = 0
    ''', (landlord_id,)).fetchone()['count']

    db.close()

    return render_template('rentals/landlord_dashboard.html', landlord=landlord, properties_count=properties_count, rooms_count=rooms_count, applications=applications, room_applications=room_applications, unread_messages=unread_messages)


@rentals_bp.route('/landlord/properties', methods=['GET', 'POST'])
def landlord_properties():
    if 'landlord_id' not in session:
        return redirect(url_for('rentals.login'))

    db = get_db()
    landlord_id = session['landlord_id']

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        address = request.form.get('address')
        city = request.form.get('city')
        state = request.form.get('state')
        zipcode = request.form.get('zipcode')
        price = float(request.form.get('price_per_month') or 0)
        bedrooms = int(request.form.get('bedrooms') or 0)
        bathrooms = float(request.form.get('bathrooms') or 0)
        square_feet = int(request.form.get('square_feet') or 0)
        property_type = request.form.get('property_type')
        amenities = request.form.get('amenities')

        property_id = str(uuid.uuid4())

        db.execute('''
            INSERT INTO properties
            (property_id, landlord_id, title, description, address, city, state, zipcode,
             price_per_month, bedrooms, bathrooms, square_feet, property_type, amenities)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (property_id, landlord_id, title, description, address, city, state, zipcode,
              price, bedrooms, bathrooms, square_feet, property_type, amenities))

        db.commit()
        db.close()
        return jsonify({'success': True, 'message': 'Property listed successfully'})

    properties = db.execute('SELECT * FROM properties WHERE landlord_id = ? ORDER BY created_at DESC', (landlord_id,)).fetchall()
    db.close()

    return render_template('rentals/landlord_properties.html', properties=properties)


@rentals_bp.route('/listings')
def browse_listings():
    db = get_db()
    listing_type = request.args.get('type', 'properties')
    city_filter = request.args.get('city', '')
    price_min = request.args.get('price_min', type=float)
    price_max = request.args.get('price_max', type=float)
    bedrooms = request.args.get('bedrooms', type=int)

    properties = []
    rooms = []

    if listing_type == 'rooms':
        query = 'SELECT * FROM rooms WHERE is_available = 1'
        params = []
        if city_filter:
            query += ' AND city LIKE ?'
            params.append(f'%{city_filter}%')
        if price_min:
            query += ' AND price_per_month >= ?'
            params.append(price_min)
        if price_max:
            query += ' AND price_per_month <= ?'
            params.append(price_max)
        query += ' ORDER BY created_at DESC'
        rooms = db.execute(query, params).fetchall()
    else:
        query = 'SELECT * FROM properties WHERE is_available = 1'
        params = []
        if city_filter:
            query += ' AND city LIKE ?'
            params.append(f'%{city_filter}%')
        if price_min:
            query += ' AND price_per_month >= ?'
            params.append(price_min)
        if price_max:
            query += ' AND price_per_month <= ?'
            params.append(price_max)
        if bedrooms:
            query += ' AND bedrooms >= ?'
            params.append(bedrooms)
        query += ' ORDER BY created_at DESC'
        properties = db.execute(query, params).fetchall()

    db.close()
    return render_template('rentals/browse_listings.html', properties=properties, rooms=rooms, listing_type=listing_type)


@rentals_bp.route('/property/<property_id>')
def property_detail(property_id):
    db = get_db()
    property_data = db.execute('''
        SELECT p.*, l.full_name as landlord_name, l.phone as landlord_phone, l.email as landlord_email
        FROM properties p
        JOIN landlords l ON p.landlord_id = l.id
        WHERE p.property_id = ?
    ''', (property_id,)).fetchone()

    reviews = db.execute('''
        SELECT r.*, t.full_name as reviewer_name
        FROM lt_reviews r
        LEFT JOIN tenants t ON r.reviewer_type = 'tenant' AND r.reviewer_id = t.id
        WHERE r.property_id = ?
        ORDER BY r.created_at DESC
    ''', (property_data['id'],)).fetchall() if property_data else []

    db.close()

    if not property_data:
        return 'Property not found', 404

    return render_template('rentals/property_detail.html', property=property_data, reviews=reviews)


@rentals_bp.route('/api/apply-property', methods=['POST'])
def apply_property():
    data = request.get_json()
    property_id = data.get('property_id')

    if 'tenant_id' not in session:
        return jsonify({'success': False, 'message': 'Login as tenant to apply'}), 403

    db = get_db()
    tenant_id = session['tenant_id']

    property_data = db.execute('SELECT id, landlord_id FROM properties WHERE property_id = ?', (property_id,)).fetchone()
    if not property_data:
        db.close()
        return jsonify({'success': False, 'message': 'Property not found'}), 404

    existing = db.execute('SELECT id FROM applications WHERE property_id = ? AND tenant_id = ?', (property_data['id'], tenant_id)).fetchone()
    if existing:
        db.close()
        return jsonify({'success': False, 'message': 'You already applied for this property'}), 400

    application_id = str(uuid.uuid4())
    db.execute('INSERT INTO applications (application_id, property_id, tenant_id, landlord_id) VALUES (?, ?, ?, ?)', (application_id, property_data['id'], tenant_id, property_data['landlord_id']))
    db.commit()
    db.close()

    return jsonify({'success': True, 'message': 'Application submitted successfully'})
