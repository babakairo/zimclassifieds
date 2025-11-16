"""
Sellers Blueprint - E-Commerce Marketplace Seller Management
Handles seller registration, store management, product management, and order fulfillment.
"""

from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from pathlib import Path
import sqlite3
import uuid
import re
import os

sellers_bp = Blueprint('sellers', __name__, url_prefix='/sellers')


def get_db():
    """Local DB helper to avoid circular import."""
    db = sqlite3.connect('zimclassifieds.db')
    db.row_factory = sqlite3.Row
    return db


def seller_required(f):
    """Decorator to require seller login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'seller_id' not in session or 'user_id' not in session:
            return redirect(url_for('sellers.register'))
        return f(*args, **kwargs)
    return decorated_function


def slugify(text):
    """Convert text to URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    return text


def allowed_file(filename):
    """Check if file extension is allowed."""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_file(file):
    """Save uploaded file and return relative path."""
    if not file or file.filename == '':
        return None
    
    if not allowed_file(file.filename):
        return None
    
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4()}.{ext}"
    
    upload_folder = 'static/uploads'
    os.makedirs(upload_folder, exist_ok=True)
    
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)
    return f"uploads/{filename}"


@sellers_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Seller registration page."""
    if request.method == 'POST':
        store_name = request.form.get('store_name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        description = request.form.get('description')
        return_policy = request.form.get('return_policy')
        
        db = get_db()
        error = None
        
        # Validation
        if not all([store_name, email, password, full_name]):
            error = 'Store name, email, password, and name are required.'
        elif password != confirm_password:
            error = 'Passwords do not match.'
        elif len(password) < 6:
            error = 'Password must be at least 6 characters.'
        
        if not error:
            # Check if user already exists
            user_check = db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
            seller_check = db.execute('SELECT id FROM sellers WHERE store_slug = ?', (slugify(store_name),)).fetchone()
            
            if user_check:
                error = 'Email already registered as a regular user.'
            elif seller_check:
                error = 'Store name already taken. Please choose another.'
        
        if not error:
            # Create user account
            user_id = str(uuid.uuid4())
            db.execute('''
                INSERT INTO users (user_id, email, password_hash, full_name, phone)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, email, generate_password_hash(password), full_name, phone))
            
            # Create seller profile
            seller_id = str(uuid.uuid4())
            store_slug = slugify(store_name)
            
            db.execute('''
                INSERT INTO sellers (seller_id, user_id, store_name, store_slug, description, return_policy)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (seller_id, user_id, store_name, store_slug, description, return_policy))
            
            db.commit()
            db.close()
            
            # Auto-login
            session['user_id'] = user_id
            session['user_email'] = email
            session['user_name'] = full_name
            session['seller_id'] = seller_id
            session['store_name'] = store_name
            
            return redirect(url_for('sellers.dashboard'))
        
        db.close()
        return render_template('sellers/register.html', error=error)
    
    return render_template('sellers/register.html')


@sellers_bp.route('/dashboard')
@seller_required
def dashboard():
    """Seller dashboard - overview stats."""
    db = get_db()
    seller_id = session['seller_id']
    
    # Get seller info
    seller = db.execute('SELECT * FROM sellers WHERE seller_id = ?', (seller_id,)).fetchone()
    
    # Get stats
    products_count = db.execute('SELECT COUNT(*) as count FROM products WHERE seller_id = (SELECT id FROM sellers WHERE seller_id = ?)', (seller_id,)).fetchone()['count']
    
    total_orders = db.execute('''
        SELECT COUNT(*) as count FROM order_items
        WHERE seller_id = (SELECT id FROM sellers WHERE seller_id = ?)
    ''', (seller_id,)).fetchone()['count']
    
    pending_orders = db.execute('''
        SELECT COUNT(*) as count FROM order_items
        WHERE seller_id = (SELECT id FROM sellers WHERE seller_id = ?)
        AND fulfillment_status = 'pending'
    ''', (seller_id,)).fetchone()['count']
    
    total_sales = db.execute('''
        SELECT SUM(subtotal) as total FROM order_items
        WHERE seller_id = (SELECT id FROM sellers WHERE seller_id = ?)
    ''', (seller_id,)).fetchone()['total'] or 0
    
    # Recent orders
    recent_orders = db.execute('''
        SELECT oi.*, o.order_number, o.created_at as order_date, u.full_name as customer_name, p.name as product_name
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.id
        JOIN users u ON o.user_id = u.user_id
        JOIN products p ON oi.product_id = p.id
        WHERE oi.seller_id = (SELECT id FROM sellers WHERE seller_id = ?)
        ORDER BY o.created_at DESC
        LIMIT 10
    ''', (seller_id,)).fetchall()
    
    db.close()
    
    return render_template('sellers/dashboard.html',
                         seller=seller,
                         products_count=products_count,
                         total_orders=total_orders,
                         pending_orders=pending_orders,
                         total_sales=total_sales,
                         recent_orders=recent_orders)


@sellers_bp.route('/products')
@seller_required
def products():
    """List seller's products."""
    db = get_db()
    seller_id = session['seller_id']
    
    # Get seller's internal ID
    seller_data = db.execute('SELECT id FROM sellers WHERE seller_id = ?', (seller_id,)).fetchone()
    seller_internal_id = seller_data['id'] if seller_data else None
    
    # Get seller's products
    products = db.execute('''
        SELECT * FROM products
        WHERE seller_id = ?
        ORDER BY created_at DESC
    ''', (seller_internal_id,)).fetchall()
    
    db.close()
    
    return render_template('sellers/products.html', products=products)


@sellers_bp.route('/product/new', methods=['GET', 'POST'])
@seller_required
def new_product():
    """Create new product."""
    if request.method == 'POST':
        db = get_db()
        seller_id = session['seller_id']
        
        # Get seller's internal ID
        seller_data = db.execute('SELECT id FROM sellers WHERE seller_id = ?', (seller_id,)).fetchone()
        seller_internal_id = seller_data['id'] if seller_data else None
        
        name = request.form.get('name')
        description = request.form.get('description')
        category = request.form.get('category')
        subcategory = request.form.get('subcategory')
        price = float(request.form.get('price') or 0)
        sku = request.form.get('sku')
        stock_quantity = int(request.form.get('stock_quantity') or 0)
        
        error = None
        
        if not all([name, category, price, stock_quantity]):
            error = 'Product name, category, price, and stock are required.'
        elif price <= 0:
            error = 'Price must be greater than 0.'
        elif stock_quantity < 0:
            error = 'Stock cannot be negative.'
        
        # Check if SKU already exists (if provided)
        if sku:
            existing_sku = db.execute('SELECT id FROM products WHERE sku = ?', (sku,)).fetchone()
            if existing_sku:
                error = f'SKU "{sku}" is already in use. Please use a different SKU or leave it blank.'
        
        if error:
            db.close()
            return render_template('sellers/product_form.html', error=error)
        
        # Create product (SKU can be NULL if not provided)
        product_id = str(uuid.uuid4())
        
        db.execute('''
            INSERT INTO products
            (product_id, seller_id, name, description, category, subcategory, price, sku, stock_quantity)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (product_id, seller_internal_id, name, description, category, subcategory, price, sku if sku else None, stock_quantity))
        
        # Get the inserted product's internal ID
        product_internal_id = db.execute('SELECT id FROM products WHERE product_id = ?', (product_id,)).fetchone()['id']
        
        # Handle image uploads (max 10 images)
        uploaded_files = request.files.getlist('images')
        if uploaded_files:
            for idx, file in enumerate(uploaded_files[:10]):  # Limit to 10 images
                if file and file.filename and allowed_file(file.filename):
                    image_path = save_uploaded_file(file)
                    if image_path:
                        db.execute('''
                            INSERT INTO product_images (product_id, image_path, display_order, is_primary)
                            VALUES (?, ?, ?, ?)
                        ''', (product_internal_id, image_path, idx, 1 if idx == 0 else 0))
        
        # Create inventory record
        inventory_id = str(uuid.uuid4())
        db.execute('''
            INSERT INTO inventory (inventory_id, product_id, quantity_available)
            VALUES (?, ?, ?)
        ''', (inventory_id, product_internal_id, stock_quantity))
        
        db.commit()
        db.close()
        
        return redirect(url_for('sellers.products'))
    
    return render_template('sellers/product_form.html')


@sellers_bp.route('/product/<product_id>/edit', methods=['GET', 'POST'])
@seller_required
def edit_product(product_id):
    """Edit product."""
    db = get_db()
    seller_id = session['seller_id']
    
    # Get seller's internal ID
    seller_data = db.execute('SELECT id FROM sellers WHERE seller_id = ?', (seller_id,)).fetchone()
    seller_internal_id = seller_data['id'] if seller_data else None
    
    product = db.execute('SELECT * FROM products WHERE product_id = ? AND seller_id = ?', (product_id, seller_internal_id)).fetchone()
    
    if not product:
        db.close()
        return 'Product not found', 404
    
    # Get existing images
    product_images = db.execute('''
        SELECT * FROM product_images 
        WHERE product_id = ? 
        ORDER BY is_primary DESC, display_order ASC
    ''', (product['id'],)).fetchall()
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = float(request.form.get('price') or 0)
        stock_quantity = int(request.form.get('stock_quantity') or 0)
        status = request.form.get('status')
        
        error = None
        if not name or price <= 0:
            error = 'Invalid input.'
        
        if not error:
            db.execute('''
                UPDATE products
                SET name = ?, description = ?, price = ?, stock_quantity = ?, status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE product_id = ?
            ''', (name, description, price, stock_quantity, status, product_id))
            
            db.execute('''
                UPDATE inventory
                SET quantity_available = ?
                WHERE product_id = (SELECT id FROM products WHERE product_id = ?)
            ''', (stock_quantity, product_id))
            
            # Handle new image uploads
            uploaded_files = request.files.getlist('images')
            if uploaded_files:
                # Get current image count
                current_count = len(product_images)
                max_images = 10
                
                for idx, file in enumerate(uploaded_files):
                    if current_count + idx >= max_images:
                        break
                    
                    if file and file.filename and allowed_file(file.filename):
                        image_path = save_uploaded_file(file)
                        if image_path:
                            # If no images exist, make this the primary
                            is_primary = 1 if current_count == 0 and idx == 0 else 0
                            db.execute('''
                                INSERT INTO product_images (product_id, image_path, display_order, is_primary)
                                VALUES (?, ?, ?, ?)
                            ''', (product['id'], image_path, current_count + idx, is_primary))
            
            db.commit()
            db.close()
            
            return redirect(url_for('sellers.products'))
        
        db.close()
        return render_template('sellers/product_form.html', product=product, product_images=product_images, error=error)
    
    db.close()
    
    return render_template('sellers/product_form.html', product=product, product_images=product_images)


@sellers_bp.route('/product/<product_id>/delete', methods=['POST'])
@seller_required
def delete_product(product_id):
    """Delete product."""
    db = get_db()
    seller_id = session['seller_id']
    
    # Get seller's internal ID
    seller_data = db.execute('SELECT id FROM sellers WHERE seller_id = ?', (seller_id,)).fetchone()
    seller_internal_id = seller_data['id'] if seller_data else None
    
    product = db.execute('SELECT * FROM products WHERE product_id = ? AND seller_id = ?', (product_id, seller_internal_id)).fetchone()
    
    if not product:
        db.close()
        return jsonify({'success': False, 'message': 'Product not found'}), 404
    
    db.execute('DELETE FROM products WHERE product_id = ?', (product_id,))
    db.commit()
    db.close()
    
    return jsonify({'success': True, 'message': 'Product deleted'})


@sellers_bp.route('/product/<product_id>/image/<int:image_id>/delete', methods=['POST'])
@seller_required
def delete_product_image(product_id, image_id):
    """Delete a product image."""
    db = get_db()
    seller_id = session['seller_id']
    
    # Verify ownership
    seller_data = db.execute('SELECT id FROM sellers WHERE seller_id = ?', (seller_id,)).fetchone()
    product = db.execute('SELECT * FROM products WHERE product_id = ? AND seller_id = ?', 
                        (product_id, seller_data['id'])).fetchone()
    
    if not product:
        db.close()
        return jsonify({'success': False, 'error': 'Product not found'}), 404
    
    # Get image
    image = db.execute('SELECT * FROM product_images WHERE id = ? AND product_id = ?', 
                      (image_id, product['id'])).fetchone()
    
    if not image:
        db.close()
        return jsonify({'success': False, 'error': 'Image not found'}), 404
    
    # Delete file
    try:
        filepath = os.path.join('static', image['image_path'])
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception as e:
        print(f"Error deleting file: {e}")
    
    # Delete from database
    db.execute('DELETE FROM product_images WHERE id = ?', (image_id,))
    
    # If this was primary, make another image primary
    if image['is_primary']:
        next_image = db.execute('''
            SELECT id FROM product_images 
            WHERE product_id = ? 
            ORDER BY display_order ASC 
            LIMIT 1
        ''', (product['id'],)).fetchone()
        
        if next_image:
            db.execute('UPDATE product_images SET is_primary = 1 WHERE id = ?', (next_image['id'],))
    
    db.commit()
    db.close()
    
    return jsonify({'success': True})


@sellers_bp.route('/product/<product_id>/image/<int:image_id>/set-primary', methods=['POST'])
@seller_required
def set_primary_image(product_id, image_id):
    """Set an image as primary."""
    db = get_db()
    seller_id = session['seller_id']
    
    # Verify ownership
    seller_data = db.execute('SELECT id FROM sellers WHERE seller_id = ?', (seller_id,)).fetchone()
    product = db.execute('SELECT * FROM products WHERE product_id = ? AND seller_id = ?', 
                        (product_id, seller_data['id'])).fetchone()
    
    if not product:
        db.close()
        return jsonify({'success': False, 'error': 'Product not found'}), 404
    
    # Unset all primary flags for this product
    db.execute('UPDATE product_images SET is_primary = 0 WHERE product_id = ?', (product['id'],))
    
    # Set new primary
    db.execute('UPDATE product_images SET is_primary = 1 WHERE id = ? AND product_id = ?', 
              (image_id, product['id']))
    
    db.commit()
    db.close()
    
    return jsonify({'success': True})


@sellers_bp.route('/orders')
@seller_required
def orders():
    """View seller's orders."""
    db = get_db()
    seller_id = session['seller_id']
    
    # Get seller's internal ID
    seller_data = db.execute('SELECT id FROM sellers WHERE seller_id = ?', (seller_id,)).fetchone()
    seller_internal_id = seller_data['id'] if seller_data else None
    
    # Get seller's order items
    order_items = db.execute('''
        SELECT oi.*, o.order_number, o.created_at as order_date, u.full_name as customer_name, p.name as product_name
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.id
        JOIN users u ON o.user_id = u.user_id
        JOIN products p ON oi.product_id = p.id
        WHERE oi.seller_id = ?
        ORDER BY o.created_at DESC
    ''', (seller_internal_id,)).fetchall()
    
    db.close()
    
    return render_template('sellers/orders.html', orders=order_items)


@sellers_bp.route('/order/<int:order_item_id>/fulfill', methods=['POST'])
@seller_required
def fulfill_order(order_item_id):
    """Mark order item as shipped."""
    db = get_db()
    seller_id = session['seller_id']
    
    # Get seller's internal ID
    seller_data = db.execute('SELECT id FROM sellers WHERE seller_id = ?', (seller_id,)).fetchone()
    seller_internal_id = seller_data['id'] if seller_data else None
    
    tracking_number = request.form.get('tracking_number')
    
    order_item = db.execute('''
        SELECT * FROM order_items WHERE id = ? AND seller_id = ?
    ''', (order_item_id, seller_internal_id)).fetchone()
    
    if not order_item:
        db.close()
        return jsonify({'success': False, 'message': 'Order not found'}), 404
    
    db.execute('''
        UPDATE order_items
        SET fulfillment_status = 'shipped', tracking_number = ?, shipped_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (tracking_number, order_item_id))
    
    db.commit()
    db.close()
    
    return jsonify({'success': True, 'message': 'Order marked as shipped'})


@sellers_bp.route('/analytics')
@seller_required
def analytics():
    """Seller sales analytics."""
    db = get_db()
    seller_id = session['seller_id']
    
    # Get seller's internal ID
    seller_data = db.execute('SELECT id FROM sellers WHERE seller_id = ?', (seller_id,)).fetchone()
    seller_internal_id = seller_data['id'] if seller_data else None
    
    # Total sales
    total_sales = db.execute('''
        SELECT SUM(subtotal) as total FROM order_items
        WHERE seller_id = ?
    ''', (seller_internal_id,)).fetchone()['total'] or 0
    
    # Total orders
    total_orders = db.execute('''
        SELECT COUNT(*) as count FROM order_items WHERE seller_id = ?
    ''', (seller_internal_id,)).fetchone()['count']
    
    # Top products
    top_products = db.execute('''
        SELECT p.name, COUNT(oi.id) as qty_sold, SUM(oi.subtotal) as sales
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        WHERE oi.seller_id = ?
        GROUP BY p.id
        ORDER BY qty_sold DESC
        LIMIT 10
    ''', (seller_internal_id,)).fetchall()
    
    # Monthly sales (last 6 months)
    monthly_sales = db.execute('''
        SELECT DATE(oi.created_at) as sale_date, SUM(oi.subtotal) as daily_total
        FROM order_items oi
        WHERE oi.seller_id = ? AND oi.created_at >= date('now', '-6 months')
        GROUP BY DATE(oi.created_at)
        ORDER BY oi.created_at DESC
    ''', (seller_internal_id,)).fetchall()
    
    db.close()
    
    return render_template('sellers/analytics.html',
                         total_sales=total_sales,
                         total_orders=total_orders,
                         top_products=top_products,
                         monthly_sales=monthly_sales)


@sellers_bp.route('/<store_slug>')
def view_store(store_slug):
    """Public seller store page."""
    db = get_db()
    
    seller = db.execute('SELECT * FROM sellers WHERE store_slug = ?', (store_slug,)).fetchone()
    
    if not seller:
        db.close()
        return 'Store not found', 404
    
    # Get seller's products
    products = db.execute('''
        SELECT * FROM products WHERE seller_id = ? AND status = 'active'
        ORDER BY created_at DESC
    ''', (seller['id'],)).fetchall()
    
    # Get seller's ratings
    ratings = db.execute('''
        SELECT AVG(rating) as avg_rating, COUNT(*) as review_count
        FROM seller_ratings WHERE seller_id = ?
    ''', (seller['id'],)).fetchone()
    
    db.close()
    
    return render_template('sellers/store.html',
                         seller=seller,
                         products=products,
                         avg_rating=ratings['avg_rating'] if ratings else 0,
                         review_count=ratings['review_count'] if ratings else 0)
