"""
ZimClassifieds Ecommerce Platform
A multi-seller marketplace with Stripe payments and courier logistics.
Focus: Pure ecommerce - product browsing, seller stores, shopping cart, orders, and delivery.
"""

from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import sqlite3
import uuid
import os
from pathlib import Path
from email.message import EmailMessage
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
import stripe
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = 'zim-ecommerce-secret-key-change-in-production'
DATABASE = 'zimclassifieds.db'

# Stripe Configuration
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY') or 'sk_test_placeholder'
STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY') or 'pk_test_placeholder'

serializer = URLSafeTimedSerializer(app.secret_key)

# Initialize database on app startup
@app.before_request
def before_request():
    """Initialize database tables if they don't exist."""
    try:
        db = get_db()
        db.execute('SELECT 1 FROM users LIMIT 1')
        db.close()
    except Exception:
        init_db()

# Image upload configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Zimbabwe locations (for delivery)
ZIMBABWE_CITIES = {
    'Harare': ['Harare CBD', 'Southerton', 'Northgate', 'Avondale', 'Borrowdale', 
               'Belgravia', 'Mount Pleasant', 'Waterfalls', 'Eastlea', 'Budiriro',
               'Highfield', 'Mbare', 'Glen Norah', 'Warren Park', 'Chitungwiza',
               'Kambuzuma', 'Mufakose', 'Dzivarasekwa', 'Sunningdale', 'Midlands'],
    'Bulawayo': ['Bulawayo CBD', 'Ascot', 'Hillside', 'Whitestone', 'Magwegwe', 
                 'Nkulumane', 'Cowdray Park', 'Njube', 'Luveve'],
    'Mutare': ['Mutare CBD', 'Sakubva', 'Chikanga', 'Dangamvura', 'Westridge'],
    'Gweru': ['Gweru CBD', 'Mkoba', 'Southdowns', 'Vungu'],
    'Kwekwe': ['Kwekwe CBD', 'Redcliff', 'Amaveni'],
    'Chinhoyi': ['Chinhoyi CBD', 'Chinhoyi Suburbs'],
    'Victoria Falls': ['Victoria Falls CBD', 'Chinotimba'],
    'Kadoma': ['Kadoma CBD', 'Rimuka'],
}

# Product categories (ecommerce only)
PRODUCT_CATEGORIES = [
    'Electronics', 'Fashion', 'Home & Garden', 'Sports & Outdoors',
    'Toys & Games', 'Books & Media', 'Health & Beauty', 'Food & Groceries',
    'Furniture', 'Tools & Hardware', 'Automotive', 'Pet Supplies'
]


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_file(file):
    """Save uploaded file and return relative path."""
    if not file or file.filename == '':
        return None
    
    if not allowed_file(file.filename):
        return None
    
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
            email_verified INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (seller_id) REFERENCES sellers(id)
        );

        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inventory_id TEXT UNIQUE NOT NULL,
            product_id INTEGER NOT NULL,
            warehouse_location TEXT DEFAULT 'main',
            quantity_available INTEGER DEFAULT 0,
            quantity_reserved INTEGER DEFAULT 0,
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

        -- Indices for performance
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
    """Generate email verification token."""
    return serializer.dumps(email, salt='email-confirm-salt')


def confirm_email_token(token, expiration=3600*24):
    """Verify email token."""
    try:
        email = serializer.loads(token, salt='email-confirm-salt', max_age=expiration)
        return email
    except (SignatureExpired, BadSignature):
        return None


def login_required(f):
    """Decorator for routes requiring login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# ============================================================================
# CORE ECOMMERCE ROUTES
# ============================================================================

@app.route('/')
def index():
    """Home page with featured products and sellers."""
    db = get_db()
    
    # Get featured products (random, recently added)
    featured_products = db.execute('''
        SELECT p.*, s.store_name, s.store_slug
        FROM products p
        JOIN sellers s ON p.seller_id = s.id
        WHERE p.status = 'active' AND p.stock_quantity > 0
        ORDER BY p.created_at DESC
        LIMIT 12
    ''').fetchall()
    
    # Get top sellers (by sales)
    top_sellers = db.execute('''
        SELECT seller_id, store_name, store_slug, rating, total_sales
        FROM sellers
        WHERE is_verified = 1
        ORDER BY total_sales DESC
        LIMIT 8
    ''').fetchall()
    
    db.close()
    
    return render_template('index.html',
                         featured_products=featured_products,
                         top_sellers=top_sellers,
                         categories=PRODUCT_CATEGORIES)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration."""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        
        db = get_db()
        error = None
        
        if not email or not password or not full_name:
            error = 'Email, password, and name are required.'
        elif password != confirm_password:
            error = 'Passwords do not match.'
        elif len(password) < 6:
            error = 'Password must be at least 6 characters.'
        
        if not error:
            existing = db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
            if existing:
                error = 'Email already registered.'
        
        if error:
            db.close()
            return render_template('register.html', error=error)
        
        # Create user
        user_id = str(uuid.uuid4())
        db.execute('''
            INSERT INTO users (user_id, email, password_hash, full_name, phone)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, email, generate_password_hash(password), full_name, phone))
        
        db.commit()
        db.close()
        
        return redirect(url_for('login', success='Registration successful! Please log in.'))
    
    return render_template('register.html')


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
    """Customer dashboard - orders and account."""
    db = get_db()
    user_id = session['user_id']
    
    # Get user info
    user = db.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
    
    # Get recent orders
    orders = db.execute('''
        SELECT o.*, COUNT(oi.id) as item_count
        FROM orders o
        LEFT JOIN order_items oi ON o.id = oi.order_id
        WHERE o.user_id = ?
        GROUP BY o.id
        ORDER BY o.created_at DESC
        LIMIT 10
    ''', (user_id,)).fetchall()
    
    db.close()
    
    return render_template('dashboard.html',
                         user=user,
                         orders=orders)


# ============================================================================
# PRODUCT BROWSING & SEARCH
# ============================================================================

@app.route('/products')
def products():
    """Browse products with filtering."""
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    sort = request.args.get('sort', 'newest')
    
    db = get_db()
    
    query = '''
        SELECT p.*, s.store_name, s.store_slug
        FROM products p
        JOIN sellers s ON p.seller_id = s.id
        WHERE p.status = 'active' AND p.stock_quantity > 0
    '''
    params = []
    
    if category:
        query += ' AND p.category = ?'
        params.append(category)
    
    if search:
        query += ' AND (p.name LIKE ? OR p.description LIKE ?)'
        search_term = f'%{search}%'
        params.extend([search_term, search_term])
    
    # Sorting
    if sort == 'price_asc':
        query += ' ORDER BY p.price ASC'
    elif sort == 'price_desc':
        query += ' ORDER BY p.price DESC'
    elif sort == 'rating':
        query += ' ORDER BY p.rating DESC'
    else:  # newest
        query += ' ORDER BY p.created_at DESC'
    
    products = db.execute(query, params).fetchall()
    db.close()
    
    return render_template('products/browse.html',
                         products=products,
                         categories=PRODUCT_CATEGORIES,
                         current_category=category,
                         search_term=search,
                         sort=sort)


@app.route('/product/<product_id>')
def product_detail(product_id):
    """Product detail page."""
    db = get_db()
    
    product = db.execute('''
        SELECT p.*, s.store_name, s.store_slug, s.rating as seller_rating
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
        SELECT r.*, u.full_name
        FROM product_reviews r
        JOIN users u ON r.user_id = u.user_id
        WHERE r.product_id = ? AND r.status = 'active'
        ORDER BY r.created_at DESC
    ''', (db.execute('SELECT id FROM products WHERE product_id = ?', (product_id,)).fetchone()[0],)).fetchall()
    
    db.commit()
    db.close()
    
    return render_template('products/detail.html',
                         product=product,
                         reviews=reviews)


# ============================================================================
# SELLER STORES
# ============================================================================

@app.route('/seller/<store_slug>')
def seller_store(store_slug):
    """View seller store."""
    db = get_db()
    
    seller = db.execute('''
        SELECT s.*, u.full_name
        FROM sellers s
        JOIN users u ON s.user_id = u.user_id
        WHERE s.store_slug = ?
    ''', (store_slug,)).fetchone()
    
    if not seller:
        db.close()
        return render_template('error.html', message='Store not found'), 404
    
    # Get seller products
    products = db.execute('''
        SELECT * FROM products
        WHERE seller_id = ? AND status = 'active'
        ORDER BY created_at DESC
    ''', (seller['id'],)).fetchall()
    
    # Get seller ratings
    ratings = db.execute('''
        SELECT * FROM seller_ratings
        WHERE seller_id = ?
        ORDER BY created_at DESC
        LIMIT 5
    ''', (seller['id'],)).fetchall()
    
    db.close()
    
    return render_template('sellers/store.html',
                         seller=seller,
                         products=products,
                         ratings=ratings)


# ============================================================================
# CART MANAGEMENT (using cart blueprint)
# ============================================================================

# Cart routes are in cart.py blueprint - imported and registered below


# ============================================================================
# CHECKOUT & ORDERS
# ============================================================================

@app.route('/checkout')
@login_required
def checkout():
    """Checkout page."""
    db = get_db()
    user_id = session['user_id']
    
    # Get cart items
    cart_items = db.execute('''
        SELECT c.*, p.name, p.price, s.store_name, s.store_slug
        FROM cart c
        JOIN products p ON c.product_id = p.id
        JOIN sellers s ON c.seller_id = s.id
        WHERE c.user_id = ?
    ''', (user_id,)).fetchall()
    
    if not cart_items:
        db.close()
        return redirect(url_for('products'))
    
    # Calculate totals
    subtotal = sum(item['price'] * item['quantity'] for item in cart_items)
    shipping_cost = 50  # Base shipping
    total = subtotal + shipping_cost
    
    # Get user address
    user = db.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
    
    db.close()
    
    return render_template('checkout/checkout.html',
                         cart_items=cart_items,
                         subtotal=subtotal,
                         shipping_cost=shipping_cost,
                         total=total,
                         user=user,
                         cities=ZIMBABWE_CITIES,
                         stripe_public_key=STRIPE_PUBLIC_KEY)


@app.route('/api/stripe-checkout', methods=['POST'])
@login_required
def stripe_checkout():
    """Create Stripe checkout session."""
    user_id = session['user_id']
    db = get_db()
    
    # Get cart items
    cart_items = db.execute('''
        SELECT c.*, p.name, p.price, p.product_id
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = ?
    ''', (user_id,)).fetchall()
    
    if not cart_items:
        db.close()
        return jsonify({'error': 'Cart is empty'}), 400
    
    # Build line items for Stripe
    line_items = []
    for item in cart_items:
        line_items.append({
            'price_data': {
                'currency': 'zwd',  # Zimbabwe Dollar
                'unit_amount': int(item['price'] * 100),
                'product_data': {
                    'name': item['name'],
                    'metadata': {'product_id': item['product_id']}
                },
            },
            'quantity': item['quantity'],
        })
    
    # Add shipping
    line_items.append({
        'price_data': {
            'currency': 'zwd',
            'unit_amount': 5000,  # 50 ZWL
            'product_data': {'name': 'Shipping'}
        },
        'quantity': 1,
    })
    
    try:
        session_obj = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=url_for('stripe_success', _external=True),
            cancel_url=url_for('checkout', _external=True),
            metadata={'user_id': user_id}
        )
        
        db.close()
        return jsonify({
            'sessionId': session_obj.id,
            'publishableKey': STRIPE_PUBLIC_KEY
        })
    
    except Exception as e:
        db.close()
        return jsonify({'error': str(e)}), 400


@app.route('/stripe-success')
@login_required
def stripe_success():
    """Handle successful Stripe payment."""
    user_id = session['user_id']
    db = get_db()
    
    # Get cart items
    cart_items = db.execute('''
        SELECT c.*, p.product_id as pid
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = ?
    ''', (user_id,)).fetchall()
    
    if not cart_items:
        db.close()
        return redirect(url_for('products'))
    
    # Create order
    order_id = str(uuid.uuid4())
    order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
    subtotal = sum(item['price'] * item['quantity'] for item in cart_items)
    total = subtotal + 50  # +50 ZWL shipping
    
    db.execute('''
        INSERT INTO orders (order_id, user_id, order_number, total_amount, 
                           payment_method, payment_status, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (order_id, user_id, order_number, total, 'stripe', 'paid', 'confirmed'))
    
    order = db.execute('SELECT id FROM orders WHERE order_id = ?', (order_id,)).fetchone()
    
    # Create order items
    for item in cart_items:
        order_item_id = str(uuid.uuid4())
        db.execute('''
            INSERT INTO order_items (order_item_id, order_id, product_id, 
                                    seller_id, quantity, unit_price, subtotal)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (order_item_id, order[0], item['product_id'], item['seller_id'],
              item['quantity'], item['price'], item['price'] * item['quantity']))
        
        # Reserve inventory
        db.execute('''
            UPDATE inventory 
            SET quantity_reserved = quantity_reserved + ?
            WHERE product_id = ?
        ''', (item['quantity'], item['product_id']))
    
    # Clear cart
    db.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))
    
    db.commit()
    db.close()
    
    return redirect(url_for('order_confirmation', order_id=order_id))


@app.route('/order-confirmation/<order_id>')
@login_required
def order_confirmation(order_id):
    """Order confirmation page."""
    db = get_db()
    user_id = session['user_id']
    
    order = db.execute('''
        SELECT * FROM orders 
        WHERE order_id = ? AND user_id = ?
    ''', (order_id, user_id)).fetchone()
    
    if not order:
        db.close()
        return render_template('error.html', message='Order not found'), 404
    
    # Get order items
    items = db.execute('''
        SELECT oi.*, p.name, s.store_name
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        JOIN sellers s ON oi.seller_id = s.id
        WHERE oi.order_id = ?
    ''', (order[0],)).fetchall()
    
    db.close()
    
    return render_template('checkout/order_confirmation.html',
                         order=order,
                         items=items)


@app.route('/order/<order_id>')
@login_required
def order_detail(order_id):
    """Order detail page."""
    db = get_db()
    user_id = session['user_id']
    
    order = db.execute('''
        SELECT * FROM orders 
        WHERE order_id = ? AND user_id = ?
    ''', (order_id, user_id)).fetchone()
    
    if not order:
        db.close()
        return render_template('error.html', message='Order not found'), 404
    
    # Get order items
    items = db.execute('''
        SELECT oi.*, p.name, p.product_id, s.store_name
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        JOIN sellers s ON oi.seller_id = s.id
        WHERE oi.order_id = ?
    ''', (order[0],)).fetchall()
    
    db.close()
    
    return render_template('checkout/order_detail.html',
                         order=order,
                         items=items)


@app.route('/orders/history')
@login_required
def order_history():
    """Order history page."""
    db = get_db()
    user_id = session['user_id']
    
    orders = db.execute('''
        SELECT o.*, COUNT(oi.id) as item_count
        FROM orders o
        LEFT JOIN order_items oi ON o.id = oi.order_id
        WHERE o.user_id = ?
        GROUP BY o.id
        ORDER BY o.created_at DESC
    ''', (user_id,)).fetchall()
    
    db.close()
    
    return render_template('checkout/order_history.html', orders=orders)


@app.route('/api/product-review', methods=['POST'])
@login_required
def product_review():
    """Submit product review."""
    user_id = session['user_id']
    data = request.get_json()
    
    product_id = data.get('product_id')
    rating = data.get('rating')
    title = data.get('title')
    comment = data.get('comment')
    
    if not all([product_id, rating, title, comment]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    if not (1 <= rating <= 5):
        return jsonify({'error': 'Invalid rating'}), 400
    
    db = get_db()
    
    # Check if user purchased this product
    product = db.execute('SELECT id FROM products WHERE product_id = ?', (product_id,)).fetchone()
    purchase = db.execute('''
        SELECT oi.id FROM order_items oi
        JOIN orders o ON oi.order_id = o.id
        WHERE o.user_id = ? AND oi.product_id = ?
    ''', (user_id, product[0])).fetchone()
    
    if not purchase:
        db.close()
        return jsonify({'error': 'You must purchase this product to review it'}), 403
    
    # Create review
    review_id = str(uuid.uuid4())
    db.execute('''
        INSERT INTO product_reviews 
        (review_id, product_id, user_id, rating, title, comment, verified_purchase)
        VALUES (?, ?, ?, ?, ?, ?, 1)
    ''', (review_id, product[0], user_id, rating, title, comment))
    
    # Update product rating
    reviews = db.execute('''
        SELECT AVG(rating) as avg_rating, COUNT(*) as count
        FROM product_reviews
        WHERE product_id = ?
    ''', (product[0],)).fetchone()
    
    db.execute('''
        UPDATE products 
        SET rating = ?, review_count = ?
        WHERE id = ?
    ''', (reviews['avg_rating'], reviews['count'], product[0]))
    
    db.commit()
    db.close()
    
    return jsonify({'success': True, 'message': 'Review submitted successfully'})


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return render_template('error.html', message='Page not found'), 404


@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors."""
    return render_template('error.html', message='Server error'), 500


# ============================================================================
# REGISTER BLUEPRINTS
# ============================================================================

# Register cart blueprint
try:
    from cart import cart_bp
    app.register_blueprint(cart_bp, url_prefix='/cart')
except Exception as e:
    print(f"Warning: Could not load cart blueprint: {e}")

# Register sellers blueprint
try:
    from sellers import sellers_bp
    app.register_blueprint(sellers_bp, url_prefix='/sellers')
except Exception as e:
    print(f"Warning: Could not load sellers blueprint: {e}")


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
