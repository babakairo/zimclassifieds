"""
Shopping Cart Blueprint - E-Commerce Cart Management
Handles adding/removing products from cart and checkout flow.
"""

from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
from functools import wraps
import sqlite3
import uuid

cart_bp = Blueprint('cart', __name__, url_prefix='/cart')


def get_db():
    """Local DB helper to avoid circular import."""
    db = sqlite3.connect('zimclassifieds.db')
    db.row_factory = sqlite3.Row
    return db


def login_required(f):
    """Decorator to require login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@cart_bp.route('/')
@login_required
def view_cart():
    """View shopping cart."""
    db = get_db()
    user_id = session['user_id']
    
    # Get cart items with product info
    cart_items = db.execute('''
        SELECT c.*, p.name, p.price, s.store_name
        FROM cart c
        JOIN products p ON c.product_id = p.id
        JOIN sellers s ON c.seller_id = s.id
        WHERE c.user_id = ?
        ORDER BY c.added_at DESC
    ''', (user_id,)).fetchall()
    
    # Calculate totals
    subtotal = 0
    for item in cart_items:
        subtotal += item['price'] * item['quantity']
    
    shipping = 0  # Placeholder
    tax = subtotal * 0.10  # 10% tax
    total = subtotal + shipping + tax
    
    db.close()
    
    return render_template('cart/cart.html',
                         cart_items=cart_items,
                         subtotal=subtotal,
                         shipping=shipping,
                         tax=tax,
                         total=total)


@cart_bp.route('/api/add', methods=['POST'])
@login_required
def add_to_cart():
    """Add product to cart (AJAX)."""
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = int(data.get('quantity', 1))
    
    if quantity < 1:
        return jsonify({'success': False, 'message': 'Invalid quantity'}), 400
    
    db = get_db()
    user_id = session['user_id']
    
    # Get product
    product = db.execute('SELECT * FROM products WHERE product_id = ?', (product_id,)).fetchone()
    
    if not product:
        db.close()
        return jsonify({'success': False, 'message': 'Product not found'}), 404
    
    if product['stock_quantity'] < quantity:
        db.close()
        return jsonify({'success': False, 'message': 'Insufficient stock'}), 400
    
    # Check if already in cart
    existing = db.execute('''
        SELECT * FROM cart WHERE user_id = ? AND product_id = ?
    ''', (user_id, product['id'])).fetchone()
    
    if existing:
        # Update quantity
        new_qty = existing['quantity'] + quantity
        if product['stock_quantity'] < new_qty:
            db.close()
            return jsonify({'success': False, 'message': 'Insufficient stock'}), 400
        
        db.execute('''
            UPDATE cart SET quantity = ? WHERE user_id = ? AND product_id = ?
        ''', (new_qty, user_id, product['id']))
    else:
        # Add to cart
        cart_id = str(uuid.uuid4())
        db.execute('''
            INSERT INTO cart (cart_id, user_id, product_id, seller_id, quantity, price_at_add)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (cart_id, user_id, product['id'], product['seller_id'], quantity, product['price']))
    
    db.commit()
    db.close()
    
    return jsonify({'success': True, 'message': 'Product added to cart'})


@cart_bp.route('/api/remove', methods=['POST'])
@login_required
def remove_from_cart():
    """Remove product from cart (AJAX)."""
    data = request.get_json()
    product_id = data.get('product_id')
    
    db = get_db()
    user_id = session['user_id']
    
    # Get product
    product = db.execute('SELECT * FROM products WHERE product_id = ?', (product_id,)).fetchone()
    
    if not product:
        db.close()
        return jsonify({'success': False, 'message': 'Product not found'}), 404
    
    db.execute('''
        DELETE FROM cart WHERE user_id = ? AND product_id = ?
    ''', (user_id, product['id']))
    
    db.commit()
    db.close()
    
    return jsonify({'success': True, 'message': 'Product removed from cart'})


@cart_bp.route('/api/update', methods=['POST'])
@login_required
def update_cart():
    """Update cart item quantity (AJAX)."""
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = int(data.get('quantity', 1))
    
    if quantity < 1:
        return jsonify({'success': False, 'message': 'Invalid quantity'}), 400
    
    db = get_db()
    user_id = session['user_id']
    
    # Get product
    product = db.execute('SELECT * FROM products WHERE product_id = ?', (product_id,)).fetchone()
    
    if not product:
        db.close()
        return jsonify({'success': False, 'message': 'Product not found'}), 404
    
    if product['stock_quantity'] < quantity:
        db.close()
        return jsonify({'success': False, 'message': 'Insufficient stock'}), 400
    
    if quantity == 0:
        # Delete from cart
        db.execute('DELETE FROM cart WHERE user_id = ? AND product_id = ?', (user_id, product['id']))
    else:
        # Update quantity
        db.execute('''
            UPDATE cart SET quantity = ? WHERE user_id = ? AND product_id = ?
        ''', (quantity, user_id, product['id']))
    
    db.commit()
    db.close()
    
    return jsonify({'success': True, 'message': 'Cart updated'})


@cart_bp.route('/api/summary', methods=['GET'])
@login_required
def cart_summary():
    """Get cart summary (AJAX)."""
    db = get_db()
    user_id = session['user_id']
    
    # Get cart items
    cart_items = db.execute('''
        SELECT c.*, p.price
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = ?
    ''', (user_id,)).fetchall()
    
    item_count = len(cart_items)
    subtotal = sum(item['price'] * item['quantity'] for item in cart_items)
    
    db.close()
    
    return jsonify({
        'item_count': item_count,
        'subtotal': subtotal
    })


@cart_bp.route('/clear', methods=['POST'])
@login_required
def clear_cart():
    """Clear entire cart."""
    db = get_db()
    user_id = session['user_id']
    
    db.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))
    db.commit()
    db.close()
    
    return redirect(url_for('cart.view_cart'))
