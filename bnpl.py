"""
BNPL (Buy Now Pay Later) System for ZimClassifieds
Focus: Diaspora customers + Local flexible payments
Strategy: Massive penetration through installment plans
"""

from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
from functools import wraps
import sqlite3
import uuid
from datetime import datetime, timedelta
import json
import hashlib
import os

bnpl_bp = Blueprint('bnpl', __name__, url_prefix='/bnpl')

# Initialize Paynow
PAYNOW_AVAILABLE = False
paynow = None

try:
    from paynow import Paynow
    
    # Load config from config.json
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
            paynow_config = config.get('paynow', {})
            
            PAYNOW_INTEGRATION_ID = paynow_config.get('integration_id', '')
            PAYNOW_INTEGRATION_KEY = paynow_config.get('integration_key', '')
            PAYNOW_RETURN_URL = paynow_config.get('return_url', 'http://localhost:5001/bnpl/payment-return')
            PAYNOW_RESULT_URL = paynow_config.get('result_url', 'http://localhost:5001/bnpl/payment-webhook')
            
            if PAYNOW_INTEGRATION_ID and PAYNOW_INTEGRATION_KEY:
                paynow = Paynow(
                    PAYNOW_INTEGRATION_ID,
                    PAYNOW_INTEGRATION_KEY,
                    return_url=PAYNOW_RETURN_URL,
                    result_url=PAYNOW_RESULT_URL
                )
                PAYNOW_AVAILABLE = True
                print("✅ Paynow initialized successfully")
            else:
                print("⚠️ Paynow credentials not configured in config.json")
    else:
        print("⚠️ config.json not found - Paynow disabled")
        
except ImportError:
    print("⚠️ Paynow library not installed. Run: pip install paynow")
except Exception as e:
    print(f"⚠️ Error initializing Paynow: {e}")


def get_db():
    """Local DB helper to avoid circular import."""
    db = sqlite3.connect('zimclassifieds.db')
    db.row_factory = sqlite3.Row
    return db


def login_required(f):
    """Decorator to require user login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# BNPL Configuration
BNPL_CONFIG = {
    'min_amount': 20,  # Minimum order for BNPL (USD)
    'max_amount_unverified': 100,  # Max for new users
    'max_amount_verified': 500,  # Max for verified users
    'max_amount_premium': 2000,  # Max for premium users with good history
    
    'plans': {
        'small': {
            'min': 20,
            'max': 100,
            'installments': 2,
            'duration_weeks': 2,
            'fee_percent': 5,
            'description': '2 payments over 2 weeks'
        },
        'medium': {
            'min': 100,
            'max': 500,
            'installments': 4,
            'duration_weeks': 4,
            'fee_percent': 8,
            'description': '4 payments over 4 weeks'
        },
        'large': {
            'min': 500,
            'max': 5000,
            'installments': 6,
            'duration_weeks': 6,
            'fee_percent': 10,
            'description': '6 payments over 6 weeks'
        }
    },
    
    'diaspora_bonus': {
        'enabled': True,
        'reduced_fee': 3,  # Only 3% fee for diaspora customers
        'instant_approval_limit': 500,  # Auto-approve up to $500 for diaspora
        'message': 'Special diaspora rate: Only 3% fee!'
    }
}


def calculate_bnpl_plan(amount, is_diaspora=False, user_tier='basic'):
    """
    Calculate BNPL installment plan based on amount and user profile.
    
    Args:
        amount: Order total in USD
        is_diaspora: Whether user is diaspora customer
        user_tier: 'basic', 'verified', or 'premium'
    
    Returns:
        dict with plan details or None if not eligible
    """
    if amount < BNPL_CONFIG['min_amount']:
        return None
    
    # Determine user's limit
    limits = {
        'basic': BNPL_CONFIG['max_amount_unverified'],
        'verified': BNPL_CONFIG['max_amount_verified'],
        'premium': BNPL_CONFIG['max_amount_premium']
    }
    
    # Diaspora gets higher limits
    if is_diaspora:
        limits = {k: v * 2 for k, v in limits.items()}
    
    max_limit = limits.get(user_tier, limits['basic'])
    
    if amount > max_limit:
        return {
            'eligible': False,
            'reason': f'Amount exceeds your limit of ${max_limit}',
            'upgrade_message': 'Verify your account to increase your limit'
        }
    
    # Select plan based on amount
    plan = None
    for plan_key, plan_config in BNPL_CONFIG['plans'].items():
        if plan_config['min'] <= amount <= plan_config['max']:
            plan = plan_config
            plan_name = plan_key
            break
    
    if not plan:
        return None
    
    # Calculate fees (diaspora discount)
    fee_percent = BNPL_CONFIG['diaspora_bonus']['reduced_fee'] if is_diaspora else plan['fee_percent']
    fee_amount = round(amount * (fee_percent / 100), 2)
    total_amount = amount + fee_amount
    installment_amount = round(total_amount / plan['installments'], 2)
    
    # Calculate payment schedule
    today = datetime.now()
    payment_schedule = []
    for i in range(plan['installments']):
        due_date = today + timedelta(weeks=i * (plan['duration_weeks'] / plan['installments']))
        payment_schedule.append({
            'installment_number': i + 1,
            'amount': installment_amount,
            'due_date': due_date.strftime('%Y-%m-%d'),
            'status': 'pending'
        })
    
    return {
        'eligible': True,
        'plan_name': plan_name,
        'order_amount': amount,
        'fee_percent': fee_percent,
        'fee_amount': fee_amount,
        'total_amount': total_amount,
        'installment_amount': installment_amount,
        'installments': plan['installments'],
        'duration_weeks': plan['duration_weeks'],
        'description': plan['description'],
        'payment_schedule': payment_schedule,
        'is_diaspora': is_diaspora,
        'diaspora_bonus': BNPL_CONFIG['diaspora_bonus'] if is_diaspora else None,
        'first_payment_due': payment_schedule[0]['due_date']
    }


def get_user_bnpl_eligibility(user_id):
    """
    Determine user's BNPL eligibility and tier.
    
    Checks:
    - Account age
    - Purchase history
    - Payment history
    - Verification status
    """
    db = get_db()
    
    # Get user info
    user = db.execute('''
        SELECT created_at, location, phone, email
        FROM users WHERE user_id = ?
    ''', (user_id,)).fetchone()
    
    if not user:
        db.close()
        return None
    
    # Check if diaspora (simple heuristic: non-Zimbabwean phone or location)
    is_diaspora = False
    location = (user['location'] or '').lower()
    phone = (user['phone'] or '')
    
    diaspora_indicators = ['uk', 'united kingdom', 'usa', 'south africa', 'sa', 'canada', 'australia']
    if any(indicator in location for indicator in diaspora_indicators):
        is_diaspora = True
    elif phone.startswith('+44') or phone.startswith('+1') or phone.startswith('+27'):
        is_diaspora = True
    
    # Get purchase history
    orders = db.execute('''
        SELECT COUNT(*) as order_count, 
               SUM(CASE WHEN payment_status = 'paid' THEN 1 ELSE 0 END) as paid_count,
               MAX(created_at) as last_order
        FROM orders
        WHERE user_id = ?
    ''', (user_id,)).fetchone()
    
    # Get BNPL history
    bnpl_history = db.execute('''
        SELECT COUNT(*) as bnpl_count,
               SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_count,
               SUM(CASE WHEN status = 'defaulted' THEN 1 ELSE 0 END) as defaulted_count
        FROM bnpl_agreements
        WHERE user_id = ?
    ''', (user_id,)).fetchone()
    
    db.close()
    
    # Determine tier
    tier = 'basic'
    order_count = orders['order_count'] or 0
    paid_count = orders['paid_count'] or 0
    bnpl_completed = bnpl_history['completed_count'] or 0
    bnpl_defaulted = bnpl_history['defaulted_count'] or 0
    
    # Calculate credit score (simple version)
    credit_score = 50  # Base score
    
    # Positive factors
    credit_score += min(paid_count * 5, 25)  # +5 per successful order, max +25
    credit_score += min(bnpl_completed * 10, 30)  # +10 per completed BNPL, max +30
    
    # Diaspora bonus
    if is_diaspora:
        credit_score += 20
    
    # Negative factors
    credit_score -= bnpl_defaulted * 30  # -30 per defaulted BNPL
    
    # Determine tier based on score
    if credit_score >= 85:
        tier = 'premium'
    elif credit_score >= 65:
        tier = 'verified'
    else:
        tier = 'basic'
    
    # If has defaults, downgrade
    if bnpl_defaulted > 0:
        tier = 'basic'
    
    return {
        'user_id': user_id,
        'tier': tier,
        'credit_score': credit_score,
        'is_diaspora': is_diaspora,
        'order_count': order_count,
        'paid_count': paid_count,
        'bnpl_completed': bnpl_completed,
        'bnpl_defaulted': bnpl_defaulted,
        'eligible': bnpl_defaulted == 0,  # Not eligible if has defaults
        'reason': 'Outstanding defaulted payment' if bnpl_defaulted > 0 else None
    }


@bnpl_bp.route('/check-eligibility', methods=['POST'])
@login_required
def check_eligibility():
    """Check if user is eligible for BNPL on a specific order amount."""
    data = request.get_json()
    amount = float(data.get('amount', 0))
    
    user_id = session['user_id']
    eligibility = get_user_bnpl_eligibility(user_id)
    
    if not eligibility['eligible']:
        return jsonify({
            'success': False,
            'message': eligibility['reason']
        })
    
    plan = calculate_bnpl_plan(
        amount,
        is_diaspora=eligibility['is_diaspora'],
        user_tier=eligibility['tier']
    )
    
    if not plan or not plan.get('eligible'):
        return jsonify({
            'success': False,
            'message': plan.get('reason') if plan else 'Amount not eligible for BNPL'
        })
    
    return jsonify({
        'success': True,
        'plan': plan,
        'user_tier': eligibility['tier'],
        'credit_score': eligibility['credit_score']
    })


@bnpl_bp.route('/create-agreement', methods=['POST'])
@login_required
def create_agreement():
    """Create a BNPL agreement for an order."""
    data = request.get_json()
    order_id = data.get('order_id')
    amount = float(data.get('amount'))
    
    user_id = session['user_id']
    
    # Verify eligibility
    eligibility = get_user_bnpl_eligibility(user_id)
    if not eligibility['eligible']:
        return jsonify({
            'success': False,
            'error': eligibility['reason']
        }), 403
    
    # Calculate plan
    plan = calculate_bnpl_plan(
        amount,
        is_diaspora=eligibility['is_diaspora'],
        user_tier=eligibility['tier']
    )
    
    if not plan or not plan.get('eligible'):
        return jsonify({
            'success': False,
            'error': plan.get('reason') if plan else 'Not eligible'
        }), 403
    
    # Create agreement
    db = get_db()
    agreement_id = str(uuid.uuid4())
    
    db.execute('''
        INSERT INTO bnpl_agreements (
            agreement_id, user_id, order_id, 
            principal_amount, fee_amount, total_amount,
            installment_amount, installments, duration_weeks,
            fee_percent, is_diaspora, user_tier,
            payment_schedule, status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', CURRENT_TIMESTAMP)
    ''', (
        agreement_id, user_id, order_id,
        plan['order_amount'], plan['fee_amount'], plan['total_amount'],
        plan['installment_amount'], plan['installments'], plan['duration_weeks'],
        plan['fee_percent'], 1 if plan['is_diaspora'] else 0, eligibility['tier'],
        json.dumps(plan['payment_schedule'])
    ))
    
    db.commit()
    db.close()
    
    return jsonify({
        'success': True,
        'agreement_id': agreement_id,
        'plan': plan
    })


@bnpl_bp.route('/my-agreements')
@login_required
def my_agreements():
    """View user's BNPL agreements."""
    db = get_db()
    user_id = session['user_id']
    
    agreements = db.execute('''
        SELECT ba.*, o.order_number
        FROM bnpl_agreements ba
        LEFT JOIN orders o ON ba.order_id = o.id
        WHERE ba.user_id = ?
        ORDER BY ba.created_at DESC
    ''', (user_id,)).fetchall()
    
    # Parse payment schedules
    agreements_data = []
    for agreement in agreements:
        agreement_dict = dict(agreement)
        agreement_dict['payment_schedule'] = json.loads(agreement['payment_schedule'])
        agreements_data.append(agreement_dict)
    
    db.close()
    
    return render_template('bnpl/my_agreements.html', agreements=agreements_data)


@bnpl_bp.route('/agreement/<agreement_id>')
@login_required
def agreement_detail(agreement_id):
    """View specific BNPL agreement details."""
    db = get_db()
    user_id = session['user_id']
    
    agreement = db.execute('''
        SELECT ba.*, o.order_number, o.total_amount as order_total
        FROM bnpl_agreements ba
        LEFT JOIN orders o ON ba.order_id = o.id
        WHERE ba.agreement_id = ? AND ba.user_id = ?
    ''', (agreement_id, user_id)).fetchone()
    
    if not agreement:
        db.close()
        return 'Agreement not found', 404
    
    agreement_dict = dict(agreement)
    agreement_dict['payment_schedule'] = json.loads(agreement['payment_schedule'])
    
    # Get payments made
    payments = db.execute('''
        SELECT * FROM bnpl_payments
        WHERE agreement_id = ?
        ORDER BY payment_date ASC
    ''', (agreement_id,)).fetchall()
    
    db.close()
    
    return render_template('bnpl/agreement_detail.html', 
                         agreement=agreement_dict,
                         payments=payments)


@bnpl_bp.route('/pay-installment/<agreement_id>', methods=['POST'])
@login_required
def pay_installment(agreement_id):
    """Process an installment payment."""
    # This would integrate with Stripe/payment gateway
    # For now, just mark as paid
    
    data = request.get_json()
    installment_number = data.get('installment_number')
    payment_method = data.get('payment_method', 'card')
    
    db = get_db()
    user_id = session['user_id']
    
    # Get agreement
    agreement = db.execute('''
        SELECT * FROM bnpl_agreements
        WHERE agreement_id = ? AND user_id = ?
    ''', (agreement_id, user_id)).fetchone()
    
    if not agreement:
        db.close()
        return jsonify({'success': False, 'error': 'Agreement not found'}), 404
    
    # Create payment record
    payment_id = str(uuid.uuid4())
    
    db.execute('''
        INSERT INTO bnpl_payments (
            payment_id, agreement_id, installment_number,
            amount, payment_method, status, payment_date
        ) VALUES (?, ?, ?, ?, ?, 'completed', CURRENT_TIMESTAMP)
    ''', (payment_id, agreement_id, installment_number, 
          agreement['installment_amount'], payment_method))
    
    # Check if all installments paid
    payments_made = db.execute('''
        SELECT COUNT(*) as count FROM bnpl_payments
        WHERE agreement_id = ? AND status = 'completed'
    ''', (agreement_id,)).fetchone()['count']
    
    if payments_made >= agreement['installments']:
        # Mark agreement as completed
        db.execute('''
            UPDATE bnpl_agreements
            SET status = 'completed', completed_at = CURRENT_TIMESTAMP
            WHERE agreement_id = ?
        ''', (agreement_id,))
    
    db.commit()
    db.close()
    
    return jsonify({
        'success': True,
        'payment_id': payment_id,
        'remaining': agreement['installments'] - payments_made
    })


@bnpl_bp.route('/diaspora-landing')
def diaspora_landing():
    """Special landing page for diaspora customers promoting BNPL."""
    
    # Detect if user is likely diaspora based on IP/location (simple version)
    # In production, you'd use a proper IP geolocation service
    is_likely_diaspora = False
    user_country = "Zimbabwe"  # Default
    
    # Check if user is logged in and has diaspora indicators
    if 'user_id' in session:
        db = get_db()
        user = db.execute('''
            SELECT location, phone FROM users WHERE user_id = ?
        ''', (session['user_id'],)).fetchone()
        db.close()
        
        if user:
            location = (user['location'] or '').lower()
            phone = (user['phone'] or '')
            
            # Check diaspora indicators
            diaspora_countries = {
                'uk': 'United Kingdom',
                'united kingdom': 'United Kingdom',
                'london': 'United Kingdom',
                'manchester': 'United Kingdom',
                'birmingham': 'United Kingdom',
                'usa': 'United States',
                'united states': 'United States',
                'america': 'United States',
                'south africa': 'South Africa',
                'sa': 'South Africa',
                'johannesburg': 'South Africa',
                'cape town': 'South Africa',
                'pretoria': 'South Africa',
                'canada': 'Canada',
                'toronto': 'Canada',
                'australia': 'Australia',
                'sydney': 'Australia'
            }
            
            for indicator, country in diaspora_countries.items():
                if indicator in location:
                    is_likely_diaspora = True
                    user_country = country
                    break
            
            # Check phone prefixes
            if phone.startswith('+44'):
                is_likely_diaspora = True
                user_country = 'United Kingdom'
            elif phone.startswith('+1'):
                is_likely_diaspora = True
                user_country = 'United States'
            elif phone.startswith('+27'):
                is_likely_diaspora = True
                user_country = 'South Africa'
    
    return render_template('bnpl/diaspora_landing.html', 
                         bnpl_config=BNPL_CONFIG,
                         is_likely_diaspora=is_likely_diaspora,
                         user_country=user_country)


# ============================================================================
# PAYNOW PAYMENT INTEGRATION
# ============================================================================

@bnpl_bp.route('/create-agreement-checkout', methods=['POST'])
@login_required
def create_agreement_checkout():
    """Create BNPL agreement from checkout flow"""
    data = request.json
    
    db = get_db()
    
    # Get cart items
    cart_items = db.execute('''
        SELECT c.*, p.name, p.price, p.seller_id
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = ?
    ''', (session['user_id'],)).fetchall()
    
    if not cart_items:
        db.close()
        return jsonify({'success': False, 'error': 'Cart is empty'}), 400
    
    # Calculate totals
    subtotal = sum(item['price'] * item['quantity'] for item in cart_items)
    shipping = 10.00
    tax = subtotal * 0.10
    total = subtotal + shipping + tax
    
    # Get BNPL plan
    plan = data.get('bnpl_plan')
    if not plan:
        db.close()
        return jsonify({'success': False, 'error': 'Invalid BNPL plan'}), 400
    
    # Create order
    order_id = str(uuid.uuid4())
    db.execute('''
        INSERT INTO orders 
        (order_id, user_id, total_amount, shipping_address, shipping_city, 
         payment_method, payment_status, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (order_id, session['user_id'], total, 
          data.get('shipping_address', ''), data.get('shipping_city', ''),
          'bnpl', 'pending', 'pending'))
    
    # Get order internal ID
    order = db.execute('SELECT id FROM orders WHERE order_id = ?', (order_id,)).fetchone()
    
    # Add order items
    for item in cart_items:
        db.execute('''
            INSERT INTO order_items
            (order_id, product_id, seller_id, quantity, price_at_purchase)
            VALUES (?, ?, ?, ?, ?)
        ''', (order['id'], item['product_id'], item['seller_id'], 
              item['quantity'], item['price']))
    
    # Create BNPL agreement
    agreement_id = str(uuid.uuid4())
    
    # Detect diaspora
    user = db.execute('SELECT phone, location FROM users WHERE user_id = ?',
                     (session['user_id'],)).fetchone()
    is_diaspora = detect_diaspora_status(user['phone'], user['location'])
    
    # Get user tier
    tier = get_user_credit_tier(session['user_id'])
    
    # Create agreement
    db.execute('''
        INSERT INTO bnpl_agreements
        (agreement_id, user_id, order_id, principal_amount, fee_amount, 
         total_amount, installment_amount, installments, duration_weeks,
         fee_percent, is_diaspora, user_tier, payment_schedule, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (agreement_id, session['user_id'], order['id'], 
          plan['principal_amount'], plan['fee_amount'], plan['total_amount'],
          plan['installment_amount'], plan['installments'], plan['duration_weeks'],
          plan['fee_percent'], is_diaspora, tier, json.dumps(plan['schedule']), 'pending'))
    
    # Clear cart
    db.execute('DELETE FROM cart WHERE user_id = ?', (session['user_id'],))
    
    db.commit()
    db.close()
    
    return jsonify({
        'success': True,
        'agreement_id': agreement_id,
        'order_id': order_id
    })


@bnpl_bp.route('/first-payment/<agreement_id>')
@login_required
def first_payment_page(agreement_id):
    """Page for collecting first BNPL payment via Paynow"""
    db = get_db()
    
    agreement = db.execute('''
        SELECT * FROM bnpl_agreements WHERE agreement_id = ? AND user_id = ?
    ''', (agreement_id, session['user_id'])).fetchone()
    
    if not agreement:
        db.close()
        return 'Agreement not found', 404
    
    user = db.execute('SELECT * FROM users WHERE user_id = ?',
                     (session['user_id'],)).fetchone()
    
    db.close()
    
    return render_template('bnpl/first_payment.html',
                         agreement=agreement,
                         user=user,
                         paynow_available=PAYNOW_AVAILABLE)


@bnpl_bp.route('/process-first-payment', methods=['POST'])
@login_required
def process_first_payment():
    """Process first BNPL payment via Paynow mobile money"""
    if not PAYNOW_AVAILABLE:
        return jsonify({'success': False, 'error': 'Payment system unavailable. Please contact support.'}), 503
    
    data = request.json
    agreement_id = data.get('agreement_id')
    payment_method_type = data.get('payment_method', 'ecocash')  # ecocash, onemoney, telecash
    
    db = get_db()
    
    # Get agreement
    agreement = db.execute('''
        SELECT ba.*, u.phone, u.email 
        FROM bnpl_agreements ba
        JOIN users u ON ba.user_id = u.user_id
        WHERE ba.agreement_id = ? AND ba.user_id = ?
    ''', (agreement_id, session['user_id'])).fetchone()
    
    if not agreement:
        db.close()
        return jsonify({'success': False, 'error': 'Agreement not found'}), 404
    
    if agreement['status'] not in ['pending', 'active']:
        db.close()
        return jsonify({'success': False, 'error': 'Agreement is not in valid state'}), 400
    
    try:
        # Create Paynow payment
        reference = f"BNPL-{agreement_id}-1"
        
        payment = paynow.create_payment(reference, agreement['email'])
        payment.add(
            f"BNPL First Payment (1 of {agreement['installments']})",
            float(agreement['installment_amount'])
        )
        
        # Send mobile payment request
        response = paynow.send_mobile(
            payment,
            agreement['phone'],
            payment_method_type
        )
        
        if response.success:
            # Save payment record
            payment_id = str(uuid.uuid4())
            db.execute('''
                INSERT INTO bnpl_payments
                (payment_id, agreement_id, installment_number, amount,
                 payment_method, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (payment_id, agreement['id'], 1, agreement['installment_amount'],
                  payment_method_type, 'pending'))
            
            db.commit()
            db.close()
            
            return jsonify({
                'success': True,
                'poll_url': response.poll_url,
                'payment_id': payment_id,
                'reference': reference,
                'message': 'Check your phone to approve payment'
            })
        else:
            db.close()
            return jsonify({'success': False, 'error': response.error}), 400
            
    except Exception as e:
        db.close()
        print(f"Payment error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bnpl_bp.route('/check-payment-status', methods=['POST'])
@login_required
def check_payment_status():
    """Check payment status via Paynow polling"""
    if not PAYNOW_AVAILABLE:
        return jsonify({'success': False, 'error': 'Payment system unavailable'}), 503
    
    data = request.json
    poll_url = data.get('poll_url')
    
    if not poll_url:
        return jsonify({'success': False, 'error': 'Poll URL required'}), 400
    
    try:
        status = paynow.check_transaction_status(poll_url)
        
        return jsonify({
            'success': True,
            'paid': status.paid,
            'status': status.status,
            'amount': str(status.amount) if hasattr(status, 'amount') else None
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bnpl_bp.route('/payment-webhook', methods=['POST'])
def payment_webhook():
    """Handle Paynow payment status updates (webhook callback)"""
    print("📥 Webhook received from Paynow")
    print(f"Data: {request.form.to_dict()}")
    
    data = request.form.to_dict()
    
    # Extract reference
    reference = data.get('reference', '')
    
    if not reference or not reference.startswith('BNPL-'):
        print(f"⚠️ Invalid reference: {reference}")
        return 'Invalid reference', 400
    
    # Parse reference: BNPL-{agreement_id}-{installment}
    parts = reference.split('-')
    if len(parts) < 3:
        print(f"⚠️ Malformed reference: {reference}")
        return 'Malformed reference', 400
    
    agreement_id = parts[1]
    installment_number = int(parts[2])
    
    # Verify webhook authenticity (important for security!)
    if not verify_paynow_webhook(data):
        print("⚠️ Webhook verification failed!")
        return 'Unauthorized', 403
    
    status_text = data.get('status', '')
    
    try:
        db = get_db()
        
        if status_text == 'Paid':
            print(f"✅ Payment confirmed for {reference}")
            
            # Get agreement internal ID
            agreement = db.execute('''
                SELECT id, installments, order_id FROM bnpl_agreements 
                WHERE agreement_id = ?
            ''', (agreement_id,)).fetchone()
            
            if not agreement:
                db.close()
                return 'Agreement not found', 404
            
            # Update payment status
            db.execute('''
                UPDATE bnpl_payments
                SET status = 'completed', 
                    payment_date = CURRENT_TIMESTAMP
                WHERE agreement_id = ?
                AND installment_number = ?
            ''', (agreement['id'], installment_number))
            
            # If first payment, activate agreement and order
            if installment_number == 1:
                print(f"🎉 Activating agreement {agreement_id}")
                
                db.execute('''
                    UPDATE bnpl_agreements
                    SET status = 'active'
                    WHERE agreement_id = ?
                ''', (agreement_id,))
                
                # Update order status
                db.execute('''
                    UPDATE orders
                    SET status = 'confirmed', 
                        payment_status = 'partial'
                    WHERE id = ?
                ''', (agreement['order_id'],))
            
            # Check if all payments completed
            total_paid = db.execute('''
                SELECT COUNT(*) as count FROM bnpl_payments
                WHERE agreement_id = ? AND status = 'completed'
            ''', (agreement['id'],)).fetchone()['count']
            
            if total_paid >= agreement['installments']:
                print(f"🎊 All payments complete for {agreement_id}")
                
                db.execute('''
                    UPDATE bnpl_agreements
                    SET status = 'completed', completed_at = CURRENT_TIMESTAMP
                    WHERE agreement_id = ?
                ''', (agreement_id,))
                
                # Mark order as fully paid
                db.execute('''
                    UPDATE orders
                    SET payment_status = 'paid'
                    WHERE id = ?
                ''', (agreement['order_id'],))
            
            db.commit()
            db.close()
            
            print(f"✅ Webhook processed successfully for {reference}")
            return 'OK', 200
            
        elif status_text in ['Failed', 'Cancelled']:
            print(f"❌ Payment failed/cancelled for {reference}")
            
            # Update payment status
            agreement = db.execute('''
                SELECT id FROM bnpl_agreements WHERE agreement_id = ?
            ''', (agreement_id,)).fetchone()
            
            if agreement:
                db.execute('''
                    UPDATE bnpl_payments
                    SET status = 'failed'
                    WHERE agreement_id = ? AND installment_number = ?
                ''', (agreement['id'], installment_number))
                
                db.commit()
            
            db.close()
            return 'OK', 200
            
        else:
            print(f"ℹ️ Payment pending for {reference}")
            db.close()
            return 'OK', 200
            
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        return 'Error', 500


@bnpl_bp.route('/payment-return')
def payment_return():
    """Handle return from Paynow payment page"""
    reference = request.args.get('reference', '')
    
    # Extract agreement ID
    agreement_id = ''
    if reference and reference.startswith('BNPL-'):
        parts = reference.split('-')
        if len(parts) >= 2:
            agreement_id = parts[1]
    
    return render_template('bnpl/payment_return.html',
                         agreement_id=agreement_id,
                         reference=reference)


def verify_paynow_webhook(data):
    """Verify webhook is authentic from Paynow"""
    if not PAYNOW_AVAILABLE:
        return False
    
    try:
        # Get hash from webhook
        received_hash = data.get('hash', '').upper()
        
        # Build verification string
        verify_string = ""
        for key in sorted(data.keys()):
            if key != 'hash':
                verify_string += str(data[key])
        
        # Add integration key
        verify_string += PAYNOW_INTEGRATION_KEY
        
        # Calculate hash
        import hashlib
        calculated_hash = hashlib.sha512(verify_string.encode()).hexdigest().upper()
        
        # Compare
        is_valid = calculated_hash == received_hash
        
        if not is_valid:
            print(f"⚠️ Hash mismatch!")
            print(f"Expected: {calculated_hash}")
            print(f"Received: {received_hash}")
        
        return is_valid
        
    except Exception as e:
        print(f"Error verifying webhook: {e}")
        return False


def detect_diaspora_status(phone, location):
    """Detect if user is diaspora based on phone and location"""
    if not phone and not location:
        return False
    
    # Check phone prefix
    diaspora_prefixes = ['+44', '+1', '+27', '+61', '+971']
    if phone:
        for prefix in diaspora_prefixes:
            if phone.startswith(prefix):
                return True
    
    # Check location keywords
    if location:
        location_lower = location.lower()
        diaspora_keywords = ['uk', 'usa', 'america', 'south africa', 'canada', 
                            'australia', 'london', 'johannesburg']
        for keyword in diaspora_keywords:
            if keyword in location_lower:
                return True
    
    return False


def get_user_credit_tier(user_id):
    """Get user's credit tier based on history"""
    db = get_db()
    
    # Check completed agreements
    completed = db.execute('''
        SELECT COUNT(*) as count FROM bnpl_agreements
        WHERE user_id = ? AND status = 'completed'
    ''', (user_id,)).fetchone()['count']
    
    # Check verification
    user = db.execute('SELECT verification_status FROM users WHERE user_id = ?',
                     (user_id,)).fetchone()
    
    db.close()
    
    if completed >= 5 or (user and user['verification_status'] == 'verified'):
        return 'premium'
    elif completed >= 2:
        return 'verified'
    else:
        return 'basic'


# Admin routes (for managing BNPL)
@bnpl_bp.route('/admin/agreements')
def admin_agreements():
    """Admin view of all BNPL agreements."""
    # TODO: Add admin authentication
    db = get_db()
    
    agreements = db.execute('''
        SELECT ba.*, u.full_name, u.email, o.order_id
        FROM bnpl_agreements ba
        JOIN users u ON ba.user_id = u.user_id
        LEFT JOIN orders o ON ba.order_id = o.id
        ORDER BY ba.created_at DESC
        LIMIT 100
    ''').fetchall()
    
    db.close()
    
    return render_template('bnpl/admin_agreements.html', agreements=agreements)
