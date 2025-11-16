"""
ZimClassifieds - Zimbabwe Classifieds Platform
A comprehensive classifieds marketplace for product listings and relationship seeking.
Supports all major Zimbabwean cities and suburbs.
"""

from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import sqlite3
import uuid
import os
from pathlib import Path
import smtplib
import json
import urllib.request
import urllib.parse
import time
from email.message import EmailMessage
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
import stripe
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


app = Flask(__name__)
app.secret_key = 'zim-classifieds-secret-key-change-in-production'
DATABASE = 'zimclassifieds.db'

# Stripe Configuration
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY') or 'sk_test_placeholder'
STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY') or 'pk_test_placeholder'

# Load optional integrations from env
RECAPTCHA_SITE_KEY = os.environ.get('RECAPTCHA_SITE_KEY')
RECAPTCHA_SECRET_KEY = os.environ.get('RECAPTCHA_SECRET_KEY')
SMTP_SERVER = os.environ.get('SMTP_SERVER')
SMTP_PORT = int(os.environ.get('SMTP_PORT') or 0) if os.environ.get('SMTP_PORT') else None
SMTP_USER = os.environ.get('SMTP_USER')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')
EMAIL_FROM = os.environ.get('EMAIL_FROM') or 'no-reply@zimclassifieds.local'

serializer = URLSafeTimedSerializer(app.secret_key)

# Initialize database on app startup (for production/Render)
@app.before_request
def before_request():
    """Initialize database tables if they don't exist."""
    try:
        db = get_db()
        db.execute('SELECT 1 FROM users LIMIT 1')
        db.close()
    except Exception:
        # Tables don't exist; initialize them
        init_db()

# Image upload configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# Create upload folder if it doesn't exist
Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Zimbabwean cities and suburbs
ZIMBABWE_LOCATIONS = {
    'Harare': ['Harare CBD', 'Southerton', 'Northgate', 'Avondale', 'Borrowdale', 
               'Belgravia', 'Mount Pleasant', 'Waterfalls', 'Eastlea', 'Budiriro',
               'Highfield', 'Mbare', 'Glen Norah', 'Warren Park', 'Chitungwiza',
               'Kambuzuma', 'Mufakose', 'Dzivarasekwa', 'Sunningdale', 'Midlands'],
    'Bulawayo': ['Bulawayo CBD', 'Ascot', 'Hillside', 'Whitestone', 'Suburbs',
                 'Magwegwe', 'Nkulumane', 'Cowdray Park', 'Njube', 'Luveve',
                 'Entumbane', 'Mpilo', 'Kuwadzana'],
    'Mutare': ['Mutare CBD', 'Sakubva', 'Chikanga', 'Dangamvura', 'Westridge'],
    'Gweru': ['Gweru CBD', 'Mkoba', 'Southdowns', 'Vungu'],
    'Kwekwe': ['Kwekwe CBD', 'Redcliff', 'Amaveni'],
    'Chinhoyi': ['Chinhoyi CBD', 'Chinhoyi Suburbs'],
    'Victoria Falls': ['Victoria Falls CBD', 'Chinotimba'],
    'Kadoma': ['Kadoma CBD', 'Rimuka'],
}

LISTING_CATEGORIES = {
    'services': ['House Cleaning', 'Car Repair', 'Plumbing', 'Electrical', 'Gardening',
                 'Tutoring', 'Photography', 'Web Design', 'Pest Control', 'Painting'],
    'products': ['Electronics', 'Furniture', 'Clothing', 'Food & Drinks', 'Books',
                 'Sports Equipment', 'Toys', 'Tools', 'Home & Garden', 'Vehicles'],
    'jobs': ['Full-Time', 'Part-Time', 'Freelance', 'Internship'],
    'real_estate': ['Apartments', 'Houses', 'Land', 'Commercial Space', 'Office Space'],
    'relationships': ['Men Seeking Women', 'Women Seeking Men', 'Making Friends',
                      'Networking', 'Singles Events'],
}

LISTING_STATUSES = ['active', 'pending', 'sold', 'expired', 'archived']


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_file(file):
    """Save uploaded file and return filename."""
    if not file or file.filename == '':
        return None
    
    if not allowed_file(file.filename):
        return None
    
    # Generate unique filename
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    file.save(filepath)
    return f"uploads/{filename}"


def delete_image(image_path):
    """Delete image file if it exists."""
    if not image_path:
        return
    
    filepath = os.path.join('static', image_path)
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception as e:
        print(f"Error deleting image: {e}")


def get_db():
    """Get database connection."""
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db


def init_db():
    """Initialize database with schema."""
    db = get_db()
    db.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            phone TEXT,
            location TEXT,
            bio TEXT,
            profile_image TEXT,
            account_type TEXT DEFAULT 'personal',
            verification_status TEXT DEFAULT 'unverified',
            email_verified INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            listing_id TEXT UNIQUE NOT NULL,
            user_id TEXT NOT NULL,
            category TEXT NOT NULL,
            subcategory TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            price REAL,
            currency TEXT DEFAULT 'ZWL',
            location_city TEXT NOT NULL,
            location_suburb TEXT NOT NULL,
            images TEXT,
            status TEXT DEFAULT 'active',
            views INTEGER DEFAULT 0,
            flags INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            bumped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id TEXT UNIQUE NOT NULL,
            sender_id TEXT NOT NULL,
            receiver_id TEXT NOT NULL,
            listing_id TEXT,
            subject TEXT,
            body TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sender_id) REFERENCES users(user_id),
            FOREIGN KEY (receiver_id) REFERENCES users(user_id),
            FOREIGN KEY (listing_id) REFERENCES listings(listing_id)
        );

        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            listing_id TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, listing_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (listing_id) REFERENCES listings(listing_id)
        );

        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            review_id TEXT UNIQUE NOT NULL,
            reviewer_id TEXT NOT NULL,
            reviewed_user_id TEXT NOT NULL,
            listing_id TEXT,
            rating INTEGER CHECK(rating >= 1 AND rating <= 5),
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (reviewer_id) REFERENCES users(user_id),
            FOREIGN KEY (reviewed_user_id) REFERENCES users(user_id),
            FOREIGN KEY (listing_id) REFERENCES listings(listing_id)
        );

        CREATE TABLE IF NOT EXISTS flags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            flag_id TEXT UNIQUE NOT NULL,
            listing_id TEXT NOT NULL,
            user_id TEXT,
            reason TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (listing_id) REFERENCES listings(listing_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS admin_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id TEXT UNIQUE NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT,
            role TEXT DEFAULT 'moderator',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_listings_user ON listings(user_id);
        CREATE INDEX IF NOT EXISTS idx_listings_category ON listings(category);
        CREATE INDEX IF NOT EXISTS idx_listings_location ON listings(location_city);
        CREATE INDEX IF NOT EXISTS idx_listings_status ON listings(status);
        CREATE INDEX IF NOT EXISTS idx_messages_receiver ON messages(receiver_id);
        CREATE INDEX IF NOT EXISTS idx_reviews_user ON reviews(reviewed_user_id);
        
        -- Landlord / Tenant (rentals) tables added during merge
        CREATE TABLE IF NOT EXISTS landlords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT,
            full_name TEXT,
            phone TEXT,
            company_name TEXT,
            verification_status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS tenants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT,
            full_name TEXT,
            phone TEXT,
            occupation TEXT,
            approval_status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS properties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            property_id TEXT UNIQUE NOT NULL,
            landlord_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            address TEXT,
            city TEXT,
            state TEXT,
            zipcode TEXT,
            price_per_month REAL,
            bedrooms INTEGER DEFAULT 0,
            bathrooms REAL DEFAULT 0,
            square_feet INTEGER DEFAULT 0,
            property_type TEXT,
            amenities TEXT,
            is_available INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (landlord_id) REFERENCES landlords(id)
        );

        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id TEXT UNIQUE NOT NULL,
            landlord_id INTEGER NOT NULL,
            property_id INTEGER,
            title TEXT,
            description TEXT,
            price_per_month REAL,
            city TEXT,
            is_available INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (landlord_id) REFERENCES landlords(id),
            FOREIGN KEY (property_id) REFERENCES properties(id)
        );

        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id TEXT UNIQUE NOT NULL,
            property_id INTEGER NOT NULL,
            tenant_id INTEGER NOT NULL,
            landlord_id INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            application_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (property_id) REFERENCES properties(id),
            FOREIGN KEY (tenant_id) REFERENCES tenants(id),
            FOREIGN KEY (landlord_id) REFERENCES landlords(id)
        );

        CREATE TABLE IF NOT EXISTS room_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ra_id TEXT UNIQUE NOT NULL,
            room_id INTEGER NOT NULL,
            tenant_id INTEGER NOT NULL,
            landlord_id INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            application_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (room_id) REFERENCES rooms(id),
            FOREIGN KEY (tenant_id) REFERENCES tenants(id),
            FOREIGN KEY (landlord_id) REFERENCES landlords(id)
        );

        CREATE TABLE IF NOT EXISTS lt_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id TEXT UNIQUE NOT NULL,
            sender_type TEXT,
            sender_id INTEGER,
            receiver_type TEXT,
            receiver_id INTEGER,
            body TEXT,
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS lt_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            review_id TEXT UNIQUE NOT NULL,
            property_id INTEGER,
            reviewer_type TEXT,
            reviewer_id INTEGER,
            rating INTEGER,
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (property_id) REFERENCES properties(id)
        );

        CREATE INDEX IF NOT EXISTS idx_properties_landlord ON properties(landlord_id);
        CREATE INDEX IF NOT EXISTS idx_rooms_landlord ON rooms(landlord_id);
        CREATE INDEX IF NOT EXISTS idx_applications_property ON applications(property_id);

        -- Phase 1: E-Commerce Marketplace Tables
        CREATE TABLE IF NOT EXISTS sellers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seller_id TEXT UNIQUE NOT NULL,
            user_id TEXT NOT NULL,
            store_name TEXT NOT NULL,
            store_slug TEXT UNIQUE NOT NULL,
            description TEXT,
            logo_image TEXT,
            banner_image TEXT,
            is_verified INTEGER DEFAULT 0,
            rating REAL DEFAULT 5.0,
            total_reviews INTEGER DEFAULT 0,
            total_sales INTEGER DEFAULT 0,
            return_policy TEXT,
            shipping_policy TEXT,
            response_time_hours INTEGER DEFAULT 24,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT UNIQUE NOT NULL,
            seller_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            subcategory TEXT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            currency TEXT DEFAULT 'ZWL',
            sku TEXT UNIQUE,
            stock_quantity INTEGER DEFAULT 0,
            images TEXT,
            status TEXT DEFAULT 'active',
            rating REAL DEFAULT 0,
            review_count INTEGER DEFAULT 0,
            views INTEGER DEFAULT 0,
            flags INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            bumped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            FOREIGN KEY (seller_id) REFERENCES sellers(id)
        );

        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inventory_id TEXT UNIQUE NOT NULL,
            product_id INTEGER NOT NULL,
            warehouse_location TEXT DEFAULT 'main',
            quantity_available INTEGER DEFAULT 0,
            quantity_reserved INTEGER DEFAULT 0,
            quantity_damaged INTEGER DEFAULT 0,
            last_restock TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id)
        );

        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cart_id TEXT UNIQUE NOT NULL,
            user_id TEXT NOT NULL,
            product_id INTEGER NOT NULL,
            seller_id INTEGER NOT NULL,
            quantity INTEGER DEFAULT 1,
            price_at_add REAL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, product_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (product_id) REFERENCES products(id),
            FOREIGN KEY (seller_id) REFERENCES sellers(id)
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT UNIQUE NOT NULL,
            user_id TEXT NOT NULL,
            order_number TEXT UNIQUE NOT NULL,
            total_amount REAL NOT NULL,
            currency TEXT DEFAULT 'ZWL',
            status TEXT DEFAULT 'pending',
            payment_method TEXT,
            payment_status TEXT DEFAULT 'pending',
            shipping_address TEXT,
            shipping_city TEXT,
            shipping_suburb TEXT,
            shipping_cost REAL DEFAULT 0,
            discount_applied REAL DEFAULT 0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_item_id TEXT UNIQUE NOT NULL,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            seller_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            subtotal REAL NOT NULL,
            fulfillment_status TEXT DEFAULT 'pending',
            tracking_number TEXT,
            shipped_at TIMESTAMP,
            delivered_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (product_id) REFERENCES products(id),
            FOREIGN KEY (seller_id) REFERENCES sellers(id)
        );

        CREATE TABLE IF NOT EXISTS product_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            review_id TEXT UNIQUE NOT NULL,
            product_id INTEGER NOT NULL,
            user_id TEXT NOT NULL,
            order_id INTEGER,
            rating INTEGER CHECK(rating >= 1 AND rating <= 5),
            title TEXT,
            comment TEXT,
            verified_purchase INTEGER DEFAULT 0,
            helpful_count INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id),
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (order_id) REFERENCES orders(id)
        );

        CREATE TABLE IF NOT EXISTS seller_ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rating_id TEXT UNIQUE NOT NULL,
            seller_id INTEGER NOT NULL,
            user_id TEXT NOT NULL,
            order_id INTEGER,
            rating INTEGER CHECK(rating >= 1 AND rating <= 5),
            comment TEXT,
            response_time_rating INTEGER,
            product_quality_rating INTEGER,
            shipping_rating INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (seller_id) REFERENCES sellers(id),
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (order_id) REFERENCES orders(id)
        );

        CREATE TABLE IF NOT EXISTS payment_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id TEXT UNIQUE NOT NULL,
            order_id INTEGER NOT NULL,
            user_id TEXT NOT NULL,
            amount REAL NOT NULL,
            currency TEXT DEFAULT 'ZWL',
            payment_method TEXT,
            provider TEXT,
            provider_reference TEXT,
            status TEXT DEFAULT 'pending',
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS seller_commissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            commission_id TEXT UNIQUE NOT NULL,
            seller_id INTEGER NOT NULL,
            order_id INTEGER,
            gross_amount REAL NOT NULL,
            commission_rate REAL DEFAULT 0.15,
            commission_amount REAL NOT NULL,
            net_amount REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            paid_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (seller_id) REFERENCES sellers(id),
            FOREIGN KEY (order_id) REFERENCES orders(id)
        );

        CREATE INDEX IF NOT EXISTS idx_products_seller ON products(seller_id);
        CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
        CREATE INDEX IF NOT EXISTS idx_products_status ON products(status);
        CREATE INDEX IF NOT EXISTS idx_inventory_product ON inventory(product_id);
        CREATE INDEX IF NOT EXISTS idx_cart_user ON cart(user_id);
        CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id);
        CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
        CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);
        CREATE INDEX IF NOT EXISTS idx_order_items_seller ON order_items(seller_id);
        CREATE INDEX IF NOT EXISTS idx_product_reviews_product ON product_reviews(product_id);
        CREATE INDEX IF NOT EXISTS idx_product_reviews_user ON product_reviews(user_id);
        CREATE INDEX IF NOT EXISTS idx_seller_ratings_seller ON seller_ratings(seller_id);
        CREATE INDEX IF NOT EXISTS idx_payment_transactions_order ON payment_transactions(order_id);
        CREATE INDEX IF NOT EXISTS idx_seller_commissions_seller ON seller_commissions(seller_id);
    ''')
    
    db.commit()
    db.close()


def generate_email_token(email):
    return serializer.dumps(email, salt='email-confirm-salt')


def confirm_email_token(token, expiration=3600*24):
    try:
        email = serializer.loads(token, salt='email-confirm-salt', max_age=expiration)
        return email
    except (SignatureExpired, BadSignature):
        return None


def send_email(to_address, subject, body):
    """Send an email using SMTP. If SMTP not configured, print the message to console (dev mode)."""
    if not SMTP_SERVER or not SMTP_PORT or not SMTP_USER or not SMTP_PASSWORD:
        print('SMTP not fully configured; email would be:')
        print('To:', to_address)
        print('Subject:', subject)
        print(body)
        return False

    try:
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = EMAIL_FROM
        msg['To'] = to_address
        msg.set_content(body)

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print('Error sending email:', e)
        return False


def verify_recaptcha(response_token, remote_ip=None):
    """Verify reCAPTCHA v2 token with Google's API. Returns True if verified or if recaptcha not configured."""
    if not RECAPTCHA_SECRET_KEY:
        # recaptcha not configured; allow by default (dev)
        print('RECAPTCHA not configured; skipping verification')
        return True

    url = 'https://www.google.com/recaptcha/api/siteverify'
    data = urllib.parse.urlencode({'secret': RECAPTCHA_SECRET_KEY, 'response': response_token}).encode()
    try:
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, timeout=5) as resp:
            result = json.loads(resp.read().decode())
            return result.get('success', False)
    except Exception as e:
        print('Error verifying recaptcha:', e)
        return False


def login_required(f):
    """Decorator to require login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def index():
    """Home page with featured listings."""
    db = get_db()
    
    # Get featured listings (most recently bumped, active)
    featured = db.execute('''
        SELECT * FROM listings
        WHERE status = 'active'
        ORDER BY bumped_at DESC
        LIMIT 12
    ''').fetchall()
    
    db.close()
    
    return render_template('index.html',
                         featured_listings=featured,
                         locations=ZIMBABWE_LOCATIONS,
                         categories=LISTING_CATEGORIES)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration."""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        recaptcha_response = request.form.get('g-recaptcha-response')
        
        db = get_db()
        error = None
        
        if not email or not password or not full_name:
            error = 'Email, password, and name are required.'
        elif password != confirm_password:
            error = 'Passwords do not match.'
        elif len(password) < 6:
            error = 'Password must be at least 6 characters.'
        
        if not error:
            # Check if email exists
            existing = db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
            if existing:
                error = 'Email already registered.'

        # Verify reCAPTCHA if configured
        if not error and RECAPTCHA_SECRET_KEY:
            if not recaptcha_response or not verify_recaptcha(recaptcha_response):
                error = 'reCAPTCHA verification failed. Please try again.'
        
        if error:
            db.close()
            return render_template('register.html', error=error, recaptcha_site_key=RECAPTCHA_SITE_KEY)
        
        # Create user
        user_id = str(uuid.uuid4())
        db.execute('''
            INSERT INTO users (user_id, email, password_hash, full_name, phone)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, email, generate_password_hash(password), full_name, phone))
        
        db.commit()
        db.close()

        # Send verification email (if configured)
        token = generate_email_token(email)
        verify_url = url_for('verify_email', token=token, _external=True)
        subject = 'Verify your ZimClassifieds account'
        body = f"Hello {full_name},\n\nPlease verify your email by clicking the link below:\n\n{verify_url}\n\nIf you didn't create an account, ignore this message."
        send_email(email, subject, body)

        return redirect(url_for('login', success='Registration successful! Check your email for a verification link.'))
    
    return render_template('register.html', recaptcha_site_key=RECAPTCHA_SITE_KEY)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login."""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        db.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['user_id']
            session['user_email'] = user['email']
            session['user_name'] = user['full_name']
            return redirect(url_for('dashboard'))
        
        return render_template('login.html', error='Invalid email or password')
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    """User logout."""
    session.clear()
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard."""
    db = get_db()
    user_id = session['user_id']
    
    # Get user info
    user = db.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
    
    # Get user's listings
    listings = db.execute('''
        SELECT * FROM listings
        WHERE user_id = ?
        ORDER BY created_at DESC
    ''', (user_id,)).fetchall()
    
    # Get unread messages
    messages = db.execute('''
        SELECT * FROM messages
        WHERE receiver_id = ? AND is_read = 0
        ORDER BY created_at DESC
        LIMIT 10
    ''', (user_id,)).fetchall()
    
    # Get favorites
    favorites = db.execute('''
        SELECT COUNT(*) as count FROM favorites WHERE user_id = ?
    ''', (user_id,)).fetchone()
    
    db.close()
    
    return render_template('dashboard.html',
                         user=user,
                         listings=listings,
                         messages=messages,
                         favorite_count=favorites['count'])


@app.route('/verify_email/<token>')
def verify_email(token):
    email = confirm_email_token(token)
    if not email:
        return render_template('error.html', message='Verification link is invalid or has expired.'), 400

    db = get_db()
    user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    if not user:
        db.close()
        return render_template('error.html', message='User not found'), 404

    db.execute('UPDATE users SET email_verified = 1, verification_status = ? WHERE email = ?'
              , ('verified', email))
    db.commit()
    db.close()

    return redirect(url_for('login', success='Email verified! You can now post listings.'))


@app.route('/profile/<user_id>')
def view_profile(user_id):
    """View user profile."""
    db = get_db()
    
    user = db.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
    
    if not user:
        db.close()
        return render_template('error.html', message='User not found'), 404
    
    # Get user's active listings
    listings = db.execute('''
        SELECT * FROM listings
        WHERE user_id = ? AND status = 'active'
        ORDER BY created_at DESC
    ''', (user_id,)).fetchall()
    
    # Get user reviews
    reviews = db.execute('''
        SELECT r.*, u.full_name as reviewer_name
        FROM reviews r
        JOIN users u ON r.reviewer_id = u.user_id
        WHERE r.reviewed_user_id = ?
        ORDER BY r.created_at DESC
    ''', (user_id,)).fetchall()
    
    db.close()
    
    return render_template('profile.html',
                         user=user,
                         listings=listings,
                         reviews=reviews)


@app.route('/listing/new', methods=['GET', 'POST'])
@login_required
def create_listing():
    """Create new listing."""
    if request.method == 'POST':
        user_id = session['user_id']
        category = request.form.get('category')
        subcategory = request.form.get('subcategory')
        title = request.form.get('title')
        description = request.form.get('description')
        price = request.form.get('price')
        location_city = request.form.get('location_city')
        location_suburb = request.form.get('location_suburb')
        recaptcha_response = request.form.get('g-recaptcha-response')
        
        db = get_db()
        error = None
        
        if not all([category, title, description, location_city, location_suburb]):
            error = 'Missing required fields.'
        
        if error:
            db.close()
            return render_template('create_listing.html',
                                 error=error,
                                 categories=LISTING_CATEGORIES,
                                 locations=ZIMBABWE_LOCATIONS,
                                 recaptcha_site_key=RECAPTCHA_SITE_KEY)
        
        # Handle image uploads
        images = []
        if 'images' in request.files:
            files = request.files.getlist('images')
            for file in files:
                if file and file.filename != '':
                    image_path = save_uploaded_file(file)
                    if image_path:
                        images.append(image_path)
        
        # Determine listing status: if user's email not verified, set to 'pending'
        user = db.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
        # sqlite3.Row doesn't have .get(); use indexing with a safe fallback
        email_verified = user['email_verified'] if user and 'email_verified' in user.keys() else 0
        status = 'active' if email_verified == 1 else 'pending'

        # Verify reCAPTCHA if enabled
        if RECAPTCHA_SECRET_KEY and not verify_recaptcha(recaptcha_response):
            db.close()
            return render_template('create_listing.html', error='reCAPTCHA failed. Please try again.', categories=LISTING_CATEGORIES, locations=ZIMBABWE_LOCATIONS, recaptcha_site_key=RECAPTCHA_SITE_KEY)

        listing_id = str(uuid.uuid4())
        images_json = ','.join(images) if images else None

        db.execute('''
            INSERT INTO listings
            (listing_id, user_id, category, subcategory, title, description,
             price, location_city, location_suburb, status, images)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (listing_id, user_id, category, subcategory, title, description,
              price, location_city, location_suburb, status, images_json))
        
        db.commit()
        db.close()
        
        return redirect(url_for('view_listing', listing_id=listing_id))
    
    return render_template('create_listing.html',
                         categories=LISTING_CATEGORIES,
                         locations=ZIMBABWE_LOCATIONS)


@app.route('/listing/<listing_id>')
def view_listing(listing_id):
    """View listing details."""
    db = get_db()
    
    listing = db.execute('SELECT * FROM listings WHERE listing_id = ?', (listing_id,)).fetchone()
    
    if not listing:
        db.close()
        return render_template('error.html', message='Listing not found'), 404
    
    # Get seller info
    seller = db.execute('SELECT * FROM users WHERE user_id = ?', (listing['user_id'],)).fetchone()
    
    # Increment views
    db.execute('UPDATE listings SET views = views + 1 WHERE listing_id = ?', (listing_id,))
    db.commit()
    
    # Check if favorited
    is_favorite = False
    if 'user_id' in session:
        fav = db.execute('''
            SELECT id FROM favorites
            WHERE user_id = ? AND listing_id = ?
        ''', (session['user_id'], listing_id)).fetchone()
        is_favorite = fav is not None
    
    db.close()
    
    return render_template('listing_detail.html',
                         listing=listing,
                         seller=seller,
                         is_favorite=is_favorite)


@app.route('/listing/<listing_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_listing(listing_id):
    """Edit listing."""
    db = get_db()
    listing = db.execute('SELECT * FROM listings WHERE listing_id = ?', (listing_id,)).fetchone()
    
    if not listing or listing['user_id'] != session['user_id']:
        db.close()
        return render_template('error.html', message='Unauthorized'), 403
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        price = request.form.get('price')
        location_suburb = request.form.get('location_suburb')
        status = request.form.get('status')
        
        # Handle new image uploads
        images = listing['images'].split(',') if listing['images'] else []
        
        if 'images' in request.files:
            files = request.files.getlist('images')
            for file in files:
                if file and file.filename != '':
                    image_path = save_uploaded_file(file)
                    if image_path:
                        images.append(image_path)
        
        # Handle image deletions
        delete_images = request.form.getlist('delete_images')
        for image_path in delete_images:
            delete_image(image_path)
            if image_path in images:
                images.remove(image_path)
        
        images_json = ','.join(images) if images else None
        
        db.execute('''
            UPDATE listings
            SET title = ?, description = ?, price = ?,
                location_suburb = ?, status = ?, images = ?, updated_at = CURRENT_TIMESTAMP
            WHERE listing_id = ?
        ''', (title, description, price, location_suburb, status, images_json, listing_id))
        
        db.commit()
        db.close()
        
        return redirect(url_for('view_listing', listing_id=listing_id))
    
    db.close()
    
    listing_images = listing['images'].split(',') if listing['images'] else []
    
    return render_template('edit_listing.html',
                         listing=listing,
                         listing_images=listing_images,
                         locations=ZIMBABWE_LOCATIONS,
                         categories=LISTING_CATEGORIES)


@app.route('/listing/<listing_id>/delete', methods=['POST'])
@login_required
def delete_listing(listing_id):
    """Delete listing."""
    db = get_db()
    listing = db.execute('SELECT * FROM listings WHERE listing_id = ?', (listing_id,)).fetchone()
    
    if not listing or listing['user_id'] != session['user_id']:
        db.close()
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    # Delete associated images
    if listing['images']:
        for image_path in listing['images'].split(','):
            delete_image(image_path)
    
    db.execute('DELETE FROM listings WHERE listing_id = ?', (listing_id,))
    db.commit()
    db.close()
    
    return jsonify({'success': True, 'message': 'Listing deleted'})


@app.route('/search')
def search():
    """Search listings."""
    query = request.args.get('q', '')
    category = request.args.get('category', '')
    location_city = request.args.get('city', '')
    price_min = request.args.get('price_min', type=float)
    price_max = request.args.get('price_max', type=float)
    
    db = get_db()
    
    sql = 'SELECT * FROM listings WHERE status = "active"'
    params = []
    
    if query:
        sql += ' AND (title LIKE ? OR description LIKE ?)'
        params.extend([f'%{query}%', f'%{query}%'])
    
    if category:
        sql += ' AND category = ?'
        params.append(category)
    
    if location_city:
        sql += ' AND location_city = ?'
        params.append(location_city)
    
    if price_min:
        sql += ' AND price >= ?'
        params.append(price_min)
    
    if price_max:
        sql += ' AND price <= ?'
        params.append(price_max)
    
    sql += ' ORDER BY bumped_at DESC'
    
    listings = db.execute(sql, params).fetchall()
    db.close()
    
    return render_template('search_results.html',
                         listings=listings,
                         query=query,
                         category=category,
                         location_city=location_city,
                         locations=ZIMBABWE_LOCATIONS,
                         categories=LISTING_CATEGORIES)


@app.route('/messages')
@login_required
def messages():
    """User messages."""
    db = get_db()
    user_id = session['user_id']
    
    # Get conversations
    conversations = db.execute('''
        SELECT DISTINCT
            CASE WHEN sender_id = ? THEN receiver_id ELSE sender_id END as other_user_id,
            MAX(created_at) as last_message_time
        FROM messages
        WHERE sender_id = ? OR receiver_id = ?
        GROUP BY other_user_id
        ORDER BY last_message_time DESC
    ''', (user_id, user_id, user_id)).fetchall()
    
    db.close()
    
    return render_template('messages.html', conversations=conversations)


@app.route('/message/<other_user_id>')
@login_required
def view_conversation(other_user_id):
    """View conversation with user."""
    db = get_db()
    user_id = session['user_id']
    
    # Get other user
    other_user = db.execute('SELECT * FROM users WHERE user_id = ?', (other_user_id,)).fetchone()
    
    if not other_user:
        db.close()
        return render_template('error.html', message='User not found'), 404
    
    # Get messages
    conversation = db.execute('''
        SELECT * FROM messages
        WHERE (sender_id = ? AND receiver_id = ?)
           OR (sender_id = ? AND receiver_id = ?)
        ORDER BY created_at ASC
    ''', (user_id, other_user_id, other_user_id, user_id)).fetchall()
    
    # Mark as read
    db.execute('''
        UPDATE messages
        SET is_read = 1
        WHERE receiver_id = ? AND sender_id = ?
    ''', (user_id, other_user_id))
    
    db.commit()
    db.close()
    
    return render_template('conversation.html',
                         other_user=other_user,
                         messages=conversation)


@app.route('/api/send-message', methods=['POST'])
@login_required
def send_message():
    """Send message."""
    data = request.get_json()
    receiver_id = data.get('receiver_id')
    body = data.get('body')
    listing_id = data.get('listing_id')
    
    if not receiver_id or not body:
        return jsonify({'success': False, 'message': 'Missing fields'}), 400
    
    db = get_db()
    message_id = str(uuid.uuid4())
    
    db.execute('''
        INSERT INTO messages (message_id, sender_id, receiver_id, body, listing_id)
        VALUES (?, ?, ?, ?, ?)
    ''', (message_id, session['user_id'], receiver_id, body, listing_id))
    
    db.commit()
    db.close()
    
    return jsonify({'success': True, 'message': 'Message sent'})


@app.route('/api/favorite/<listing_id>', methods=['POST'])
@login_required
def toggle_favorite(listing_id):
    """Toggle favorite listing."""
    db = get_db()
    user_id = session['user_id']
    
    existing = db.execute('''
        SELECT id FROM favorites
        WHERE user_id = ? AND listing_id = ?
    ''', (user_id, listing_id)).fetchone()
    
    if existing:
        db.execute('DELETE FROM favorites WHERE user_id = ? AND listing_id = ?',
                  (user_id, listing_id))
        action = 'removed'
    else:
        db.execute('''
            INSERT INTO favorites (user_id, listing_id)
            VALUES (?, ?)
        ''', (user_id, listing_id))
        action = 'added'
    
    db.commit()
    db.close()
    
    return jsonify({'success': True, 'action': action})


@app.route('/api/bump-listing/<listing_id>', methods=['POST'])
@login_required
def bump_listing(listing_id):
    """Bump listing to top (refresh bump timestamp)."""
    db = get_db()
    
    # Check if user owns the listing
    listing = db.execute('SELECT * FROM listings WHERE listing_id = ?', (listing_id,)).fetchone()
    
    if not listing:
        db.close()
        return jsonify({'success': False, 'message': 'Listing not found'}), 404
    
    if listing['user_id'] != session['user_id']:
        db.close()
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    # Update bumped_at timestamp
    db.execute('UPDATE listings SET bumped_at = CURRENT_TIMESTAMP WHERE listing_id = ?', (listing_id,))
    db.commit()
    db.close()
    
    return jsonify({'success': True, 'message': 'Listing bumped to top!'})


@app.route('/api/flag-listing/<listing_id>', methods=['POST'])
def flag_listing(listing_id):
    """Flag listing as inappropriate."""
    data = request.get_json()
    reason = data.get('reason')
    description = data.get('description')
    
    if not reason:
        return jsonify({'success': False, 'message': 'Reason required'}), 400
    
    db = get_db()
    flag_id = str(uuid.uuid4())
    user_id = session.get('user_id')
    
    db.execute('''
        INSERT INTO flags (flag_id, listing_id, user_id, reason, description)
        VALUES (?, ?, ?, ?, ?)
    ''', (flag_id, listing_id, user_id, reason, description))
    
    db.execute('UPDATE listings SET flags = flags + 1 WHERE listing_id = ?', (listing_id,))
    db.commit()
    db.close()
    
    return jsonify({'success': True, 'message': 'Listing flagged for review'})


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        db = get_db()
        admin = db.execute('SELECT * FROM admin_users WHERE username = ?', (username,)).fetchone()
        db.close()
        
        if admin and check_password_hash(admin['password_hash'], password):
            session['admin_id'] = admin['admin_id']
            session['admin_username'] = admin['username']
            return redirect(url_for('admin_dashboard'))
        
        return render_template('admin_login.html', error='Invalid credentials')
    
    return render_template('admin_login.html')


@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Admin dashboard."""
    db = get_db()
    
    stats = {
        'total_users': db.execute('SELECT COUNT(*) as count FROM users').fetchone()['count'],
        'total_listings': db.execute('SELECT COUNT(*) as count FROM listings').fetchone()['count'],
        'active_listings': db.execute('SELECT COUNT(*) as count FROM listings WHERE status = "active"').fetchone()['count'],
        'pending_flags': db.execute('SELECT COUNT(*) as count FROM flags WHERE status = "pending"').fetchone()['count'],
        'total_flags': db.execute('SELECT COUNT(*) as count FROM flags').fetchone()['count'],
        'pending_listings': db.execute('SELECT COUNT(*) as count FROM listings WHERE status = "pending"').fetchone()['count'],
    }

    # Get recent flags
    flags = db.execute('''
        SELECT f.*, l.title, u.full_name
        FROM flags f
        LEFT JOIN listings l ON f.listing_id = l.listing_id
        LEFT JOIN users u ON f.user_id = u.user_id
        WHERE f.status = 'pending'
        ORDER BY f.created_at DESC
        LIMIT 20
    ''').fetchall()

    # Get recent pending listings
    pending_listings = db.execute('''
        SELECT l.*, u.full_name as owner_name
        FROM listings l
        LEFT JOIN users u ON l.user_id = u.user_id
        WHERE l.status = 'pending'
        ORDER BY l.created_at DESC
        LIMIT 50
    ''').fetchall()

    # Get all listings for listings tab
    all_listings = db.execute('''
        SELECT l.*, u.full_name as owner_name
        FROM listings l
        LEFT JOIN users u ON l.user_id = u.user_id
        ORDER BY l.created_at DESC
        LIMIT 200
    ''').fetchall()

    # Get users list
    users = db.execute('SELECT * FROM users ORDER BY created_at DESC LIMIT 200').fetchall()

    db.close()

    return render_template('admin_dashboard.html', stats=stats, flags=flags, pending_listings=pending_listings, all_listings=all_listings, users=users)



@app.route('/admin/listing/<listing_id>/<action>', methods=['POST'])
@admin_required
def admin_listing_action(listing_id, action):
    if action not in ['approve', 'reject']:
        return jsonify({'success': False, 'message': 'Invalid action'}), 400

    db = get_db()
    listing = db.execute('SELECT * FROM listings WHERE listing_id = ?', (listing_id,)).fetchone()
    if not listing:
        db.close()
        return jsonify({'success': False, 'message': 'Listing not found'}), 404

    if action == 'approve':
        db.execute('UPDATE listings SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE listing_id = ?', ('active', listing_id))
    else:
        db.execute('UPDATE listings SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE listing_id = ?', ('removed', listing_id))

    db.commit()
    db.close()

    return jsonify({'success': True, 'message': f'Listing {action}d'})


@app.route('/terms')
def terms():
    return render_template('terms.html')


@app.route('/privacy')
def privacy():
    return render_template('privacy.html')


@app.context_processor
def inject_globals():
    return dict(recaptcha_site_key=RECAPTCHA_SITE_KEY, ga_id=os.environ.get('GA_MEASUREMENT_ID'))


@app.route('/admin/flag/<flag_id>/<action>', methods=['POST'])
@admin_required
def review_flag(flag_id, action):
    """Review flagged listing."""
    if action not in ['approve', 'reject']:
        return jsonify({'success': False, 'message': 'Invalid action'}), 400
    
    db = get_db()
    
    flag = db.execute('SELECT * FROM flags WHERE flag_id = ?', (flag_id,)).fetchone()
    if not flag:
        db.close()
        return jsonify({'success': False, 'message': 'Flag not found'}), 404
    
    if action == 'approve':
        # Remove the listing
        db.execute('UPDATE listings SET status = ? WHERE listing_id = ?',
                  ('removed', flag['listing_id']))
    
    # Update flag status
    db.execute('UPDATE flags SET status = ? WHERE flag_id = ?', (action, flag_id))
    
    db.commit()
    db.close()
    
    return jsonify({'success': True, 'message': f'Flag {action}ed'})


@app.route('/admin/logout')
def admin_logout():
    """Admin logout."""
    session.clear()
    return redirect(url_for('admin_login'))


# ============= PHASE 1: E-COMMERCE ROUTES =============

@app.route('/products')
def browse_products():
    """Browse all products (marketplace)."""
    db = get_db()
    
    category = request.args.get('category', '')
    search_q = request.args.get('q', '')
    price_min = request.args.get('price_min', type=float)
    price_max = request.args.get('price_max', type=float)
    sort = request.args.get('sort', 'newest')
    
    sql = 'SELECT p.*, s.store_name FROM products p JOIN sellers s ON p.seller_id = s.id WHERE p.status = "active"'
    params = []
    
    if search_q:
        sql += ' AND (p.name LIKE ? OR p.description LIKE ?)'
        params.extend([f'%{search_q}%', f'%{search_q}%'])
    
    if category:
        sql += ' AND p.category = ?'
        params.append(category)
    
    if price_min:
        sql += ' AND p.price >= ?'
        params.append(price_min)
    
    if price_max:
        sql += ' AND p.price <= ?'
        params.append(price_max)
    
    # Sorting
    if sort == 'price_low':
        sql += ' ORDER BY p.price ASC'
    elif sort == 'price_high':
        sql += ' ORDER BY p.price DESC'
    elif sort == 'rating':
        sql += ' ORDER BY p.rating DESC'
    else:  # newest
        sql += ' ORDER BY p.bumped_at DESC'
    
    products = db.execute(sql, params).fetchall()
    db.close()
    
    return render_template('products/browse.html',
                         products=products,
                         search_q=search_q,
                         category=category,
                         sort=sort)


@app.route('/product/<product_id>')
def product_detail(product_id):
    """Product detail page."""
    db = get_db()
    
    product = db.execute('''
        SELECT p.*, s.store_name, s.seller_id as seller_slug, s.id as seller_id
        FROM products p
        JOIN sellers s ON p.seller_id = s.id
        WHERE p.product_id = ?
    ''', (product_id,)).fetchone()
    
    if not product:
        db.close()
        return render_template('error.html', message='Product not found'), 404
    
    # Increment views
    db.execute('UPDATE products SET views = views + 1 WHERE product_id = ?', (product_id,))
    
    # Get reviews
    reviews = db.execute('''
        SELECT pr.*, u.full_name as reviewer_name
        FROM product_reviews pr
        JOIN users u ON pr.user_id = u.user_id
        WHERE pr.product_id = ? AND pr.status = 'active'
        ORDER BY pr.created_at DESC
    ''', (product['id'],)).fetchall()
    
    # Get seller rating
    seller_rating = db.execute('''
        SELECT AVG(rating) as avg_rating FROM seller_ratings WHERE seller_id = ?
    ''', (product['seller_id'],)).fetchone()
    
    db.commit()
    db.close()
    
    return render_template('products/detail.html',
                         product=product,
                         reviews=reviews,
                         seller_rating=seller_rating['avg_rating'] if seller_rating else 5.0)


@app.route('/checkout')
@login_required
def checkout():
    """Checkout page."""
    db = get_db()
    user_id = session['user_id']
    
    # Get user info
    user = db.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
    
    # Get cart items
    cart_items = db.execute('''
        SELECT c.*, p.name, p.price, s.store_name
        FROM cart c
        JOIN products p ON c.product_id = p.id
        JOIN sellers s ON c.seller_id = s.id
        WHERE c.user_id = ?
    ''', (user_id,)).fetchall()
    
    if not cart_items:
        db.close()
        return redirect(url_for('cart.view_cart'))
    
    # Calculate totals
    subtotal = sum(item['price'] * item['quantity'] for item in cart_items)
    shipping = 0
    tax = subtotal * 0.10
    total = subtotal + shipping + tax
    
    db.close()
    
    return render_template('checkout/checkout.html',
                         user=user,
                         cart_items=cart_items,
                         subtotal=subtotal,
                         shipping=shipping,
                         tax=tax,
                         total=total,
                         stripe_public_key=STRIPE_PUBLIC_KEY)


@app.route('/api/stripe-checkout', methods=['POST'])
@login_required
def create_stripe_checkout():
    """Create Stripe checkout session for Stripe payment."""
    try:
        data = request.get_json()
        user_id = session['user_id']
        
        db = get_db()
        
        # Get user details
        user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        
        # Get cart items
        cart_items = db.execute('''
            SELECT c.*, p.name, p.price, s.store_name FROM cart c
            JOIN products p ON c.product_id = p.id
            JOIN sellers s ON c.seller_id = s.id
            WHERE c.user_id = ?
        ''', (user_id,)).fetchall()
        
        if not cart_items:
            db.close()
            return jsonify({'success': False, 'message': 'Cart is empty'}), 400
        
        # Build line items for Stripe
        line_items = []
        for item in cart_items:
            line_items.append({
                'price_data': {
                    'currency': 'usd',  # Change to ZWL when Stripe supports it
                    'product_data': {
                        'name': f"{item['name'][:50]} (from {item['store_name']})",
                    },
                    'unit_amount': int(item['price'] * 100),  # Convert to cents
                },
                'quantity': item['quantity'],
            })
        
        # Create Stripe checkout session
        session_obj = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=request.host_url.rstrip('/') + url_for('stripe_success', _external=False),
            cancel_url=request.host_url.rstrip('/') + url_for('checkout', _external=False),
            customer_email=user['email'],
            metadata={
                'user_id': user_id,
                'shipping_address': data.get('shipping_address'),
                'shipping_city': data.get('shipping_city'),
                'shipping_suburb': data.get('shipping_suburb'),
            }
        )
        
        db.close()
        
        return jsonify({
            'success': True,
            'sessionId': session_obj.id,
            'publishableKey': STRIPE_PUBLIC_KEY
        })
    
    except stripe.error.CardError as e:
        return jsonify({'success': False, 'message': f'Card error: {e.user_message}'}), 400
    except stripe.error.StripeException as e:
        return jsonify({'success': False, 'message': f'Stripe error: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/stripe-success')
@login_required
def stripe_success():
    """Handle successful Stripe payment."""
    session_id = request.args.get('session_id')
    
    if not session_id:
        return redirect(url_for('checkout'))
    
    try:
        # Retrieve session from Stripe
        checkout_session = stripe.checkout.Session.retrieve(session_id)
        
        if checkout_session.payment_status == 'paid':
            # Create order from Stripe session
            user_id = session['user_id']
            
            db = get_db()
            
            # Get cart items
            cart_items = db.execute('''
                SELECT c.*, p.price FROM cart c
                JOIN products p ON c.product_id = p.id
                WHERE c.user_id = ?
            ''', (user_id,)).fetchall()
            
            if cart_items:
                # Calculate totals
                subtotal = sum(item['price'] * item['quantity'] for item in cart_items)
                shipping = 0
                tax = subtotal * 0.10
                total = subtotal + shipping + tax
                
                # Create order
                order_id = str(uuid.uuid4())
                order_number = f"ORD-{int(time.time())}"
                
                # Get metadata from Stripe session
                metadata = checkout_session.metadata or {}
                shipping_address = metadata.get('shipping_address', '')
                shipping_city = metadata.get('shipping_city', '')
                shipping_suburb = metadata.get('shipping_suburb', '')
                
                db.execute('''
                    INSERT INTO orders
                    (order_id, user_id, order_number, total_amount, shipping_address, shipping_city,
                     shipping_suburb, shipping_cost, payment_method, payment_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (order_id, user_id, order_number, total, shipping_address, shipping_city,
                      shipping_suburb, shipping, 'stripe_card', 'paid'))
                
                # Get order internal ID
                order_data = db.execute('SELECT id FROM orders WHERE order_id = ?', (order_id,)).fetchone()
                order_internal_id = order_data['id']
                
                # Create order items
                for item in cart_items:
                    order_item_id = str(uuid.uuid4())
                    item_subtotal = item['price'] * item['quantity']
                    
                    db.execute('''
                        INSERT INTO order_items
                        (order_item_id, order_id, product_id, seller_id, quantity, unit_price, subtotal)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (order_item_id, order_internal_id, item['product_id'], item['seller_id'],
                          item['quantity'], item['price'], item_subtotal))
                    
                    # Update product stock
                    db.execute('''
                        UPDATE products SET stock_quantity = stock_quantity - ? WHERE id = ?
                    ''', (item['quantity'], item['product_id']))
                
                # Create payment transaction
                transaction_id = checkout_session.payment_intent
                db.execute('''
                    INSERT INTO payment_transactions 
                    (transaction_id, order_id, user_id, amount, payment_method, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (transaction_id, order_internal_id, user_id, total, 'stripe_card', 'completed'))
                
                # Clear cart
                db.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))
                
                db.commit()
                db.close()
                
                return redirect(url_for('order_confirmation', order_id=order_id))
        
        return redirect(url_for('checkout'))
    
    except stripe.error.StripeException as e:
        return redirect(url_for('checkout'))


@app.route('/order-confirmation/<order_id>')
@login_required
def order_confirmation(order_id):
    """Display order confirmation page."""
    user_id = session['user_id']
    db = get_db()
    
    order = db.execute('''
        SELECT * FROM orders WHERE order_id = ? AND user_id = ?
    ''', (order_id, user_id)).fetchone()
    
    if not order:
        db.close()
        return redirect(url_for('order_history'))
    
    order_items = db.execute('''
        SELECT oi.*, p.name, s.store_name FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        JOIN sellers s ON oi.seller_id = s.id
        WHERE oi.order_id = ?
    ''', (order['id'],)).fetchall()
    
    db.close()
    
    return render_template('checkout/order_confirmation.html',
                          order=order,
                          order_items=order_items)


@app.route('/api/orders', methods=['POST'])
@login_required
def create_order():
    """Create order from cart (for non-Stripe payment methods)."""
    data = request.get_json()
    user_id = session['user_id']
    
    shipping_address = data.get('shipping_address')
    shipping_city = data.get('shipping_city')
    shipping_suburb = data.get('shipping_suburb')
    payment_method = data.get('payment_method')
    
    if not all([shipping_address, shipping_city, shipping_suburb, payment_method]):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    
    # Stripe payments should use /api/stripe-checkout instead
    if payment_method == 'stripe_card':
        return jsonify({'success': False, 'message': 'Use Stripe checkout'}), 400
    
    db = get_db()
    
    # Get cart items
    cart_items = db.execute('''
        SELECT c.*, p.price FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = ?
    ''', (user_id,)).fetchall()
    
    if not cart_items:
        db.close()
        return jsonify({'success': False, 'message': 'Cart is empty'}), 400
    
    # Calculate totals
    subtotal = sum(item['price'] * item['quantity'] for item in cart_items)
    shipping = 0
    tax = subtotal * 0.10
    total = subtotal + shipping + tax
    
    # Create order
    order_id = str(uuid.uuid4())
    order_number = f"ORD-{int(time.time())}"
    
    db.execute('''
        INSERT INTO orders
        (order_id, user_id, order_number, total_amount, shipping_address, shipping_city,
         shipping_suburb, shipping_cost, payment_method, payment_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (order_id, user_id, order_number, total, shipping_address, shipping_city,
          shipping_suburb, shipping, payment_method, 'pending'))

    
    # Get order internal ID
    order_data = db.execute('SELECT id FROM orders WHERE order_id = ?', (order_id,)).fetchone()
    order_internal_id = order_data['id']
    
    # Create order items
    for item in cart_items:
        order_item_id = str(uuid.uuid4())
        item_subtotal = item['price'] * item['quantity']
        
        db.execute('''
            INSERT INTO order_items
            (order_item_id, order_id, product_id, seller_id, quantity, unit_price, subtotal)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (order_item_id, order_internal_id, item['product_id'], item['seller_id'],
              item['quantity'], item['price'], item_subtotal))
        
        # Update product stock
        db.execute('''
            UPDATE products SET stock_quantity = stock_quantity - ? WHERE id = ?
        ''', (item['quantity'], item['product_id']))
    
    # Clear cart
    db.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))
    
    # Create payment transaction
    transaction_id = str(uuid.uuid4())
    db.execute('''
        INSERT INTO payment_transactions (transaction_id, order_id, user_id, amount, payment_method, status)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (transaction_id, order_internal_id, user_id, total, payment_method, 'pending'))
    
    db.commit()
    db.close()
    
    return jsonify({'success': True, 'order_id': order_id, 'order_number': order_number})


@app.route('/order/<order_id>')
@login_required
def view_order(order_id):
    """View order details."""
    db = get_db()
    user_id = session['user_id']
    
    order = db.execute('''
        SELECT * FROM orders WHERE order_id = ? AND user_id = ?
    ''', (order_id, user_id)).fetchone()
    
    if not order:
        db.close()
        return render_template('error.html', message='Order not found'), 404
    
    # Get order items
    order_items = db.execute('''
        SELECT oi.*, p.name, s.store_name
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        JOIN sellers s ON oi.seller_id = s.id
        WHERE oi.order_id = ?
    ''', (order['id'],)).fetchall()
    
    db.close()
    
    return render_template('checkout/order_detail.html',
                         order=order,
                         order_items=order_items)


@app.route('/orders/history')
@login_required
def order_history():
    """View order history."""
    db = get_db()
    user_id = session['user_id']
    
    orders = db.execute('''
        SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC
    ''', (user_id,)).fetchall()
    
    db.close()
    
    return render_template('checkout/order_history.html', orders=orders)


@app.route('/api/product-review', methods=['POST'])
@login_required
def submit_product_review():
    """Submit product review."""
    data = request.get_json()
    product_id = data.get('product_id')
    rating = int(data.get('rating', 0))
    title = data.get('title', '')
    comment = data.get('comment', '')
    
    if not (1 <= rating <= 5):
        return jsonify({'success': False, 'message': 'Invalid rating'}), 400
    
    db = get_db()
    user_id = session['user_id']
    
    # Get product
    product = db.execute('SELECT * FROM products WHERE product_id = ?', (product_id,)).fetchone()
    
    if not product:
        db.close()
        return jsonify({'success': False, 'message': 'Product not found'}), 404
    
    # Check if user already reviewed
    existing = db.execute('''
        SELECT id FROM product_reviews WHERE product_id = ? AND user_id = ?
    ''', (product['id'], user_id)).fetchone()
    
    if existing:
        db.close()
        return jsonify({'success': False, 'message': 'You already reviewed this product'}), 400
    
    # Create review
    review_id = str(uuid.uuid4())
    db.execute('''
        INSERT INTO product_reviews (review_id, product_id, user_id, rating, title, comment, verified_purchase)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (review_id, product['id'], user_id, rating, title, comment, 1))
    
    # Update product rating
    avg_rating = db.execute('''
        SELECT AVG(rating) as avg FROM product_reviews WHERE product_id = ? AND status = 'active'
    ''', (product['id'],)).fetchone()['avg']
    
    review_count = db.execute('''
        SELECT COUNT(*) as count FROM product_reviews WHERE product_id = ? AND status = 'active'
    ''', (product['id'],)).fetchone()['count']
    
    db.execute('''
        UPDATE products SET rating = ?, review_count = ? WHERE id = ?
    ''', (avg_rating, review_count, product['id']))
    
    db.commit()
    db.close()
    
    return jsonify({'success': True, 'message': 'Review submitted'})


# Register blueprints
try:
    from rentals import rentals_bp
    app.register_blueprint(rentals_bp)
except Exception as e:
    print('Could not register rentals blueprint:', e)

try:
    from sellers import sellers_bp
    app.register_blueprint(sellers_bp)
except Exception as e:
    print('Could not register sellers blueprint:', e)

try:
    from cart import cart_bp
    app.register_blueprint(cart_bp)
except Exception as e:
    print('Could not register cart blueprint:', e)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
