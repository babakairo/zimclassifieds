# BNPL Checkout Integration - Implementation Guide

**Status:** Ready to Implement  
**Estimated Time:** 2-3 hours  
**Priority:** HIGH

---

## Overview

This guide implements BNPL option in the checkout page with:
1. Eligibility checker (shows if customer qualifies)
2. Payment plan calculator (shows installment breakdown)
3. Mobile money integration (Paynow for EcoCash/OneMoney)
4. First payment collection at checkout
5. Automatic weekly payment reminders

---

## Step 1: Install Required Libraries

```bash
# In your terminal (with venv activated):
pip install paynow africastalking

# Or add to requirements.txt:
echo "paynow==1.0.5" >> requirements.txt
echo "africastalking==1.2.8" >> requirements.txt
pip install -r requirements.txt
```

---

## Step 2: Update config.json

Add payment provider credentials:

```json
{
  "paynow": {
    "integration_id": "YOUR_PAYNOW_INTEGRATION_ID",
    "integration_key": "YOUR_PAYNOW_INTEGRATION_KEY",
    "return_url": "http://localhost:5001/bnpl/payment-return",
    "result_url": "http://localhost:5001/bnpl/payment-webhook"
  },
  "africastalking": {
    "username": "sandbox",
    "api_key": "YOUR_AFRICAS_TALKING_API_KEY",
    "sender_id": "ZimClass"
  }
}
```

**How to get credentials:**
1. **Paynow:** Register at https://www.paynow.co.zw (24-hour approval)
2. **Africa's Talking:** Register at https://africastalking.com (instant sandbox)

---

## Step 3: Update checkout.html

Replace the existing checkout template with BNPL option:

**File:** `templates/checkout/checkout.html`

Add BNPL option in the payment method section (around line 88):

```html
<!-- Add this AFTER the Cash on Delivery option -->

<!-- BNPL Option -->
<div class="form-check mb-3">
    <input class="form-check-input" type="radio" name="payment_method" 
           id="bnpl_payment" value="bnpl" onchange="checkBNPLEligibility()">
    <label class="form-check-label" for="bnpl_payment">
        <strong>💝 Buy Now, Pay Later (BNPL)</strong>
        <span class="badge bg-success ms-2">New!</span>
        <br>
        <small class="text-muted">Pay in weekly installments. Only 3% fee for diaspora!</small>
    </label>
</div>

<!-- BNPL Details Section (shown when BNPL selected) -->
<div id="bnplSection" class="card border-0 shadow-sm mb-3" style="display: none;">
    <div class="card-header bg-gradient text-white" style="background: linear-gradient(135deg, #10b981 0%, #059669 100%);">
        <h5 class="mb-0">💝 BNPL Payment Plan</h5>
    </div>
    <div class="card-body">
        <!-- Loading state -->
        <div id="bnplLoading" class="text-center py-3">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Checking eligibility...</span>
            </div>
            <p class="mt-2 mb-0">Checking your eligibility...</p>
        </div>
        
        <!-- Eligibility result -->
        <div id="bnplEligibility" style="display: none;">
            <!-- Approved -->
            <div id="bnplApproved" style="display: none;">
                <div class="alert alert-success mb-3">
                    <strong>✅ You're approved!</strong> 
                    <span id="isD diasporaMessage"></span>
                </div>
                
                <h6 class="mb-3">Your Payment Plan:</h6>
                <div class="table-responsive mb-3">
                    <table class="table table-sm">
                        <tr>
                            <td>Order Total:</td>
                            <td class="text-end"><strong>ZWL <span id="bnplOrderTotal">0.00</span></strong></td>
                        </tr>
                        <tr>
                            <td>BNPL Fee (<span id="bnplFeePercent">0</span>%):</td>
                            <td class="text-end">ZWL <span id="bnplFeeAmount">0.00</span></td>
                        </tr>
                        <tr class="table-light">
                            <td><strong>Total to Pay:</strong></td>
                            <td class="text-end"><strong>ZWL <span id="bnplTotalAmount">0.00</span></strong></td>
                        </tr>
                    </table>
                </div>
                
                <div class="alert alert-info">
                    <strong>📅 Payment Schedule:</strong><br>
                    <div id="bnplSchedule"></div>
                </div>
                
                <div class="alert alert-warning">
                    <small>
                        <strong>⚠️ Important:</strong>
                        <ul class="mb-0 mt-1">
                            <li>First payment due TODAY (via EcoCash/OneMoney)</li>
                            <li>Remaining payments: Every 7 days</li>
                            <li>We'll send SMS reminders before each payment</li>
                            <li>Late payments incur $5 penalty</li>
                        </ul>
                    </small>
                </div>
                
                <div class="form-check mb-3">
                    <input class="form-check-input" type="checkbox" id="bnplAgree" required>
                    <label class="form-check-label" for="bnplAgree">
                        <small>I agree to the <a href="/terms" target="_blank">BNPL Terms & Conditions</a></small>
                    </label>
                </div>
            </div>
            
            <!-- Declined -->
            <div id="bnplDeclined" style="display: none;">
                <div class="alert alert-danger">
                    <strong>❌ Not eligible for BNPL</strong><br>
                    <span id="bnplDeclineReason"></span>
                </div>
                <p class="mb-0">
                    <small>Please verify your account or choose another payment method.</small>
                </p>
            </div>
        </div>
    </div>
</div>
```

Add JavaScript for BNPL functionality (at the end of the file, before `{% endblock %}`):

```html
<script>
// BNPL Global variables
let bnplPlan = null;

function updatePaymentUI() {
    const stripeSection = document.getElementById('stripeSection');
    const bnplSection = document.getElementById('bnplSection');
    const paymentMethod = document.querySelector('input[name="payment_method"]:checked').value;
    
    // Hide all payment-specific sections
    stripeSection.style.display = 'none';
    bnplSection.style.display = 'none';
    
    // Show relevant section
    if (paymentMethod === 'stripe_card') {
        stripeSection.style.display = '';
    } else if (paymentMethod === 'bnpl') {
        bnplSection.style.display = '';
    }
}

function checkBNPLEligibility() {
    updatePaymentUI();
    
    const loading = document.getElementById('bnplLoading');
    const eligibility = document.getElementById('bnplEligibility');
    const approved = document.getElementById('bnplApproved');
    const declined = document.getElementById('bnplDeclined');
    
    // Show loading
    loading.style.display = '';
    eligibility.style.display = 'none';
    
    // Get order total
    const orderTotal = {{ total }};
    
    // Check eligibility via API
    fetch('/bnpl/check-eligibility', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            amount: orderTotal
        })
    })
    .then(r => r.json())
    .then(data => {
        loading.style.display = 'none';
        eligibility.style.display = '';
        
        if (data.eligible) {
            // Show approval
            approved.style.display = '';
            declined.style.display = 'none';
            
            // Store plan
            bnplPlan = data.plan;
            
            // Update UI
            document.getElementById('bnplOrderTotal').textContent = orderTotal.toFixed(2);
            document.getElementById('bnplFeePercent').textContent = data.plan.fee_percent;
            document.getElementById('bnplFeeAmount').textContent = data.plan.fee_amount.toFixed(2);
            document.getElementById('bnplTotalAmount').textContent = data.plan.total_amount.toFixed(2);
            
            // Show diaspora message if applicable
            if (data.is_diaspora) {
                document.getElementById('isDiasporaMessage').innerHTML = 
                    '<br>🌍 <strong>Diaspora Special:</strong> You got the 3% rate!';
            }
            
            // Build payment schedule
            let scheduleHTML = '';
            data.plan.schedule.forEach((payment, index) => {
                const paymentDate = new Date(payment.due_date);
                const dateStr = paymentDate.toLocaleDateString('en-GB');
                const status = index === 0 ? '<span class="badge bg-warning">Due Today</span>' : 
                              '<span class="badge bg-secondary">Upcoming</span>';
                scheduleHTML += `
                    <div class="d-flex justify-content-between align-items-center mb-1">
                        <span>Payment ${index + 1}: ${dateStr}</span>
                        <span><strong>ZWL ${payment.amount.toFixed(2)}</strong> ${status}</span>
                    </div>
                `;
            });
            document.getElementById('bnplSchedule').innerHTML = scheduleHTML;
            
        } else {
            // Show decline
            approved.style.display = 'none';
            declined.style.display = '';
            document.getElementById('bnplDeclineReason').textContent = data.reason;
        }
    })
    .catch(err => {
        console.error('BNPL check error:', err);
        loading.style.display = 'none';
        eligibility.style.display = '';
        declined.style.display = '';
        approved.style.display = 'none';
        alert('Error checking BNPL eligibility. Please try again.');
    });
}

// Modify the existing processCheckout function to handle BNPL
function processCheckout(event) {
    event.preventDefault();
    
    const paymentMethod = document.querySelector('input[name="payment_method"]:checked').value;
    
    if (paymentMethod === 'stripe_card') {
        processStripePayment();
    } else if (paymentMethod === 'bnpl') {
        processBNPLPayment();
    } else {
        processOtherPayment();
    }
}

function processBNPLPayment() {
    // Check if terms agreed
    const agreed = document.getElementById('bnplAgree');
    if (!agreed.checked) {
        alert('Please agree to the BNPL terms and conditions');
        return;
    }
    
    const submitBtn = document.getElementById('submitBtn');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Creating BNPL Agreement...';
    
    const formData = {
        shipping_address: document.getElementById('shipping_address').value,
        shipping_city: document.getElementById('shipping_city').value,
        shipping_suburb: document.getElementById('shipping_suburb').value,
        payment_method: 'bnpl',
        bnpl_plan: bnplPlan
    };
    
    fetch('/bnpl/create-agreement', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            // Redirect to first payment page
            window.location.href = '/bnpl/first-payment/' + data.agreement_id;
        } else {
            alert('Error: ' + data.error);
            submitBtn.disabled = false;
            submitBtn.textContent = 'Place Order';
        }
    })
    .catch(err => {
        console.error('Error:', err);
        alert('An error occurred. Please try again.');
        submitBtn.disabled = false;
        submitBtn.textContent = 'Place Order';
    });
}
</script>
```

---

## Step 4: Update bnpl.py

Add the new routes and payment processing logic:

**File:** `classifieds/bnpl.py`

Add these new routes (insert after the existing routes):

```python
# Add these imports at the top
import json
from datetime import datetime, timedelta

# Initialize Paynow (add after Blueprint definition)
PAYNOW_INTEGRATION_ID = 'YOUR_INTEGRATION_ID'  # From config.json
PAYNOW_INTEGRATION_KEY = 'YOUR_INTEGRATION_KEY'
PAYNOW_RETURN_URL = 'http://localhost:5001/bnpl/payment-return'
PAYNOW_RESULT_URL = 'http://localhost:5001/bnpl/payment-webhook'

try:
    from paynow import Paynow
    paynow = Paynow(
        PAYNOW_INTEGRATION_ID,
        PAYNOW_INTEGRATION_KEY,
        return_url=PAYNOW_RETURN_URL,
        result_url=PAYNOW_RESULT_URL
    )
    PAYNOW_AVAILABLE = True
except ImportError:
    PAYNOW_AVAILABLE = False
    print("Warning: Paynow library not installed. BNPL payments disabled.")


@bnpl_bp.route('/create-agreement', methods=['POST'])
@login_required
def create_agreement_checkout():
    """Create BNPL agreement from checkout"""
    data = request.json
    
    # Get cart items
    db = get_db()
    cart_items = db.execute('''
        SELECT c.*, p.name, p.price, p.seller_id, s.store_name
        FROM cart c
        JOIN products p ON c.product_id = p.id
        JOIN sellers s ON p.seller_id = s.id
        WHERE c.user_id = ?
    ''', (session['user_id'],)).fetchall()
    
    if not cart_items:
        return jsonify({'success': False, 'error': 'Cart is empty'}), 400
    
    # Calculate totals
    subtotal = sum(item['price'] * item['quantity'] for item in cart_items)
    shipping = 10.00  # Base shipping
    tax = subtotal * 0.10  # 10% tax
    total = subtotal + shipping + tax
    
    # Get BNPL plan
    plan = data.get('bnpl_plan')
    if not plan:
        return jsonify({'success': False, 'error': 'Invalid BNPL plan'}), 400
    
    # Create order first
    order_id = str(uuid.uuid4())
    db.execute('''
        INSERT INTO orders 
        (order_id, user_id, total_amount, shipping_address, shipping_city, 
         payment_method, payment_status, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (order_id, session['user_id'], total, 
          data['shipping_address'], data['shipping_city'],
          'bnpl', 'pending', 'pending'))
    
    # Add order items
    for item in cart_items:
        db.execute('''
            INSERT INTO order_items
            (order_id, product_id, seller_id, quantity, price_at_purchase)
            VALUES (?, ?, ?, ?, ?)
        ''', (order_id, item['product_id'], item['seller_id'], 
              item['quantity'], item['price']))
    
    # Create BNPL agreement
    agreement_id = str(uuid.uuid4())
    
    # Detect if diaspora
    user = db.execute('SELECT phone, location FROM users WHERE user_id = ?',
                     (session['user_id'],)).fetchone()
    is_diaspora = detect_diaspora(user['phone'], user['location'])
    
    # Get user tier
    tier = get_user_tier(session['user_id'])
    
    # Create agreement
    db.execute('''
        INSERT INTO bnpl_agreements
        (agreement_id, user_id, order_id, principal_amount, fee_amount, 
         total_amount, installment_amount, installments, duration_weeks,
         fee_percent, is_diaspora, user_tier, payment_schedule, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (agreement_id, session['user_id'], order_id, 
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
    """Page for collecting first BNPL payment"""
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
    """Process first BNPL payment via mobile money"""
    if not PAYNOW_AVAILABLE:
        return jsonify({'success': False, 'error': 'Payment system unavailable'}), 503
    
    data = request.json
    agreement_id = data.get('agreement_id')
    payment_method_type = data.get('payment_method')  # 'ecocash', 'onemoney', 'telecash'
    
    db = get_db()
    
    agreement = db.execute('''
        SELECT * FROM bnpl_agreements WHERE agreement_id = ? AND user_id = ?
    ''', (agreement_id, session['user_id'])).fetchone()
    
    if not agreement:
        db.close()
        return jsonify({'success': False, 'error': 'Agreement not found'}), 404
    
    user = db.execute('SELECT * FROM users WHERE user_id = ?',
                     (session['user_id'],)).fetchone()
    
    # Create Paynow payment
    try:
        payment = paynow.create_payment(
            f"BNPL-{agreement_id}-1",  # Reference
            user['email']
        )
        
        payment.add(
            f"BNPL First Payment (1 of {agreement['installments']})",
            float(agreement['installment_amount'])
        )
        
        # Send mobile payment request
        response = paynow.send_mobile(
            payment,
            user['phone'],
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
                'message': 'Check your phone to approve payment'
            })
        else:
            db.close()
            return jsonify({'success': False, 'error': response.error}), 400
            
    except Exception as e:
        db.close()
        return jsonify({'success': False, 'error': str(e)}), 500


@bnpl_bp.route('/payment-webhook', methods=['POST'])
def payment_webhook():
    """Handle Paynow payment status updates"""
    data = request.form
    
    # Extract details from reference
    reference = data.get('reference', '')  # Format: BNPL-{agreement_id}-{installment}
    
    if not reference.startswith('BNPL-'):
        return 'Invalid reference', 400
    
    parts = reference.split('-')
    agreement_id = parts[1]
    installment_number = int(parts[2])
    
    # Check payment status with Paynow
    try:
        status = paynow.check_transaction_status(data['pollurl'])
        
        if status.paid:
            db = get_db()
            
            # Update payment status
            db.execute('''
                UPDATE bnpl_payments
                SET status = 'completed', payment_date = CURRENT_TIMESTAMP
                WHERE agreement_id = (SELECT id FROM bnpl_agreements WHERE agreement_id = ?)
                AND installment_number = ?
            ''', (agreement_id, installment_number))
            
            # If first payment, activate agreement and order
            if installment_number == 1:
                db.execute('''
                    UPDATE bnpl_agreements
                    SET status = 'active'
                    WHERE agreement_id = ?
                ''', (agreement_id,))
                
                # Get order_id and update order status
                order_id = db.execute('''
                    SELECT order_id FROM bnpl_agreements WHERE agreement_id = ?
                ''', (agreement_id,)).fetchone()['order_id']
                
                db.execute('''
                    UPDATE orders
                    SET status = 'confirmed', payment_status = 'partial'
                    WHERE order_id = ?
                ''', (order_id,))
            
            # Check if all payments complete
            total_paid = db.execute('''
                SELECT COUNT(*) as count FROM bnpl_payments
                WHERE agreement_id = (SELECT id FROM bnpl_agreements WHERE agreement_id = ?)
                AND status = 'completed'
            ''', (agreement_id,)).fetchone()['count']
            
            total_installments = db.execute('''
                SELECT installments FROM bnpl_agreements WHERE agreement_id = ?
            ''', (agreement_id,)).fetchone()['installments']
            
            if total_paid >= total_installments:
                db.execute('''
                    UPDATE bnpl_agreements
                    SET status = 'completed', completed_at = CURRENT_TIMESTAMP
                    WHERE agreement_id = ?
                ''', (agreement_id,))
                
                # Update order to fully paid
                order_id = db.execute('''
                    SELECT order_id FROM bnpl_agreements WHERE agreement_id = ?
                ''', (agreement_id,)).fetchone()['order_id']
                
                db.execute('''
                    UPDATE orders
                    SET payment_status = 'paid'
                    WHERE order_id = ?
                ''', (order_id,))
            
            db.commit()
            db.close()
            
            return 'OK', 200
        else:
            return 'Payment pending', 200
            
    except Exception as e:
        print(f"Webhook error: {e}")
        return 'Error', 500


@bnpl_bp.route('/payment-return')
def payment_return():
    """Handle return from Paynow"""
    agreement_id = request.args.get('agreement_id', '')
    
    return render_template('bnpl/payment_return.html',
                         agreement_id=agreement_id)


# Helper function
def detect_diaspora(phone, location):
    """Detect if user is diaspora based on phone and location"""
    if not phone and not location:
        return False
    
    # Check phone prefix
    diaspora_prefixes = ['+44', '+1', '+27', '+61', '+971']  # UK, USA, SA, AU, UAE
    if phone:
        for prefix in diaspora_prefixes:
            if phone.startswith(prefix):
                return True
    
    # Check location keywords
    diaspora_keywords = ['uk', 'usa', 'america', 'south africa', 'canada', 
                        'australia', 'london', 'johannesburg']
    if location:
        location_lower = location.lower()
        for keyword in diaspora_keywords:
            if keyword in location_lower:
                return True
    
    return False


def get_user_tier(user_id):
    """Get user's credit tier based on history"""
    db = get_db()
    
    # Check completed agreements
    completed = db.execute('''
        SELECT COUNT(*) as count FROM bnpl_agreements
        WHERE user_id = ? AND status = 'completed'
    ''', (user_id,)).fetchone()['count']
    
    # Check verification status
    user = db.execute('SELECT verification_status FROM users WHERE user_id = ?',
                     (user_id,)).fetchone()
    
    db.close()
    
    if completed >= 5 or user['verification_status'] == 'verified':
        return 'premium'
    elif completed >= 2:
        return 'verified'
    else:
        return 'basic'
```

---

## Step 5: Create First Payment Template

Create new template for first payment collection:

**File:** `templates/bnpl/first_payment.html`

```html
{% extends "base.html" %}

{% block title %}First Payment - BNPL{% endblock %}

{% block content %}
<div class="container py-5">
    <div class="row justify-content-center">
        <div class="col-lg-6">
            <div class="text-center mb-4">
                <h1 class="h3">Complete Your First Payment</h1>
                <p class="text-muted">Pay the first installment to activate your BNPL agreement</p>
            </div>
            
            <div class="card border-0 shadow-sm mb-4">
                <div class="card-header bg-gradient text-white" 
                     style="background: linear-gradient(135deg, #10b981 0%, #059669 100%);">
                    <h5 class="mb-0">💝 Payment Details</h5>
                </div>
                <div class="card-body">
                    <dl class="row mb-0">
                        <dt class="col-6">First Payment:</dt>
                        <dd class="col-6 text-end">
                            <strong class="h5 text-primary">ZWL {{ "%.2f"|format(agreement.installment_amount) }}</strong>
                        </dd>
                        
                        <dt class="col-6">Total Installments:</dt>
                        <dd class="col-6 text-end">{{ agreement.installments }} payments</dd>
                        
                        <dt class="col-6">Payment Frequency:</dt>
                        <dd class="col-6 text-end">Weekly</dd>
                        
                        <dt class="col-6">Total Amount:</dt>
                        <dd class="col-6 text-end">ZWL {{ "%.2f"|format(agreement.total_amount) }}</dd>
                    </dl>
                </div>
            </div>
            
            {% if paynow_available %}
            <div class="card border-0 shadow-sm">
                <div class="card-header bg-white border-bottom">
                    <h5 class="mb-0">Select Payment Method</h5>
                </div>
                <div class="card-body">
                    <div class="d-grid gap-2">
                        <button class="btn btn-lg btn-success" onclick="payWithMobile('ecocash')">
                            📱 Pay with EcoCash
                        </button>
                        <button class="btn btn-lg btn-outline-success" onclick="payWithMobile('onemoney')">
                            📱 Pay with OneMoney
                        </button>
                        <button class="btn btn-lg btn-outline-success" onclick="payWithMobile('telecash')">
                            📱 Pay with Telecash
                        </button>
                    </div>
                    
                    <div id="paymentStatus" class="mt-4" style="display: none;">
                        <div class="alert alert-info">
                            <div class="d-flex align-items-center">
                                <div class="spinner-border spinner-border-sm me-3" role="status"></div>
                                <div>
                                    <strong>Payment request sent!</strong><br>
                                    <small>Check your phone and enter your PIN to approve</small>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            {% else %}
            <div class="alert alert-warning">
                Payment system is currently unavailable. Please try again later or contact support.
            </div>
            {% endif %}
            
            <div class="alert alert-light mt-4">
                <small>
                    <strong>What happens next:</strong>
                    <ol class="mb-0 mt-2">
                        <li>You'll receive a payment prompt on your phone</li>
                        <li>Enter your mobile money PIN to approve</li>
                        <li>Once confirmed, your order will be processed</li>
                        <li>We'll send SMS reminders for future payments</li>
                    </ol>
                </small>
            </div>
        </div>
    </div>
</div>

<script>
function payWithMobile(method) {
    const statusDiv = document.getElementById('paymentStatus');
    statusDiv.style.display = 'block';
    
    fetch('/bnpl/process-first-payment', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            agreement_id: '{{ agreement.agreement_id }}',
            payment_method: method
        })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            // Poll for payment status
            checkPaymentStatus(data.poll_url);
        } else {
            alert('Error: ' + data.error);
            statusDiv.style.display = 'none';
        }
    })
    .catch(err => {
        console.error('Error:', err);
        alert('An error occurred. Please try again.');
        statusDiv.style.display = 'none';
    });
}

function checkPaymentStatus(pollUrl) {
    // Poll every 5 seconds for payment confirmation
    const interval = setInterval(() => {
        fetch(pollUrl)
            .then(r => r.json())
            .then(data => {
                if (data.status === 'Paid') {
                    clearInterval(interval);
                    // Redirect to success page
                    window.location.href = '/bnpl/my-agreements?success=First payment completed!';
                } else if (data.status === 'Failed') {
                    clearInterval(interval);
                    alert('Payment failed. Please try again.');
                    document.getElementById('paymentStatus').style.display = 'none';
                }
            })
            .catch(err => {
                console.error('Poll error:', err);
            });
    }, 5000);
    
    // Stop polling after 5 minutes
    setTimeout(() => {
        clearInterval(interval);
    }, 300000);
}
</script>
{% endblock %}
```

---

## Step 6: Test the Integration

### Testing Checklist:

1. **[ ] Test BNPL Eligibility Check**
   - Add items to cart ($50-$150)
   - Go to checkout
   - Select BNPL option
   - Verify eligibility check shows correct plan

2. **[ ] Test Payment Plan Display**
   - Verify installment amounts correct
   - Check fee percentage (3% diaspora, 5-10% local)
   - Confirm payment schedule shows correct dates

3. **[ ] Test Agreement Creation**
   - Complete checkout with BNPL
   - Verify agreement created in database
   - Check order created correctly

4. **[ ] Test First Payment (Sandbox)**
   - Use Paynow sandbox credentials
   - Test with sandbox mobile number
   - Verify webhook receives payment confirmation

5. **[ ] Test Payment Status Updates**
   - Confirm payment marked as completed
   - Verify order status updated
   - Check agreement activated

---

## Next Steps

After basic integration working:

1. **Add Payment Reminders**
   - SMS reminders 2 days before due date
   - Email reminders

2. **Add Auto-Retry**
   - Retry failed payments automatically
   - SMS notification on retry

3. **Add Admin Dashboard**
   - View all BNPL agreements
   - Track payment status
   - Manage defaults

4. **Add Credit Scoring**
   - Track payment history
   - Auto-increase limits for good payers
   - Flag high-risk users

---

**Ready to implement? Start with Step 1!**
