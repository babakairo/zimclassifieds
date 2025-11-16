# BNPL Cash Collection & User Verification Guide

**Last Updated:** November 16, 2025  
**Status:** Implementation Guide  
**Purpose:** Complete guide for collecting BNPL payments and verifying users in Zimbabwe

---

## Table of Contents
1. [Cash Collection Methods](#cash-collection-methods)
2. [User Verification Options](#user-verification-options)
3. [Implementation Strategy](#implementation-strategy)
4. [Payment Flow](#payment-flow)
5. [Security & Risk Management](#security--risk-management)

---

## 1. Cash Collection Methods

### Option A: Mobile Money (RECOMMENDED for Zimbabwe) ✅

**Why Mobile Money is Best:**
- 90%+ Zimbabwe population uses EcoCash, OneMoney, or Telecash
- Instant payment confirmation
- Lower fees than cards (2-3% vs 5-7%)
- No need for bank accounts
- Perfect for weekly installments

#### **Integration Options:**

##### 1. **EcoCash API** (Most Popular - 70% market share)
```
Provider: Econet Wireless Zimbabwe
API: EcoCash Merchant Integration
Fees: 2% transaction fee
Settlement: T+1 (next business day)
Documentation: https://developer.econet.co.zw/

Features:
- Push payment requests to customer's phone
- Automatic payment confirmations
- Instant balance checks
- Recurring payment support (perfect for BNPL)
```

**Implementation Steps:**
1. Register as EcoCash Merchant: merchants@econet.co.zw
2. Get Merchant Code and API credentials
3. Integrate API endpoints:
   - `/api/v1/push-payment` - Request payment from customer
   - `/api/v1/check-status` - Verify payment status
   - `/api/v1/webhooks` - Receive payment notifications

**Code Integration:**
```python
# In bnpl.py - Add EcoCash payment
def process_ecocash_payment(phone_number, amount, reference):
    """Process EcoCash payment for BNPL installment"""
    import requests
    
    payload = {
        'merchant_code': ECOCASH_MERCHANT_CODE,
        'phone_number': phone_number,  # Format: 263771234567
        'amount': amount,
        'reference': reference,  # BNPL agreement ID
        'description': f'ZimClassifieds BNPL Payment - Installment'
    }
    
    response = requests.post(
        'https://api.econet.co.zw/ecocash/push-payment',
        json=payload,
        headers={
            'Authorization': f'Bearer {ECOCASH_API_KEY}',
            'Content-Type': 'application/json'
        }
    )
    
    if response.json()['status'] == 'success':
        return {
            'success': True,
            'transaction_id': response.json()['transaction_id'],
            'message': 'Payment request sent. Check your phone.'
        }
    else:
        return {'success': False, 'error': response.json()['message']}
```

##### 2. **OneMoney API** (NetOne - 20% market share)
```
Provider: NetOne Zimbabwe
API: OneMoney Business API
Fees: 2.5% transaction fee
Documentation: https://www.onemoney.co.zw/business

Similar integration to EcoCash
Contact: business@onemoney.co.zw
```

##### 3. **Telecash API** (Telecel - 10% market share)
```
Provider: Telecel Zimbabwe
API: Telecash Merchant Services
Fees: 3% transaction fee
Contact: merchants@telecel.co.zw
```

##### 4. **Paynow (Aggregator)** ✅ EASIEST OPTION
```
Provider: Paynow (WebDev)
Website: https://www.paynow.co.zw
Fees: 3.5% (all mobile money networks)

WHY PAYNOW IS BEST FOR BNPL:
- Single integration for EcoCash, OneMoney, Telecash
- No need for multiple merchant accounts
- Instant setup (24 hours)
- Built-in fraud detection
- Automatic reconciliation
- Support for recurring payments
- Developer-friendly API
- Free test environment

Integration Steps:
1. Register at paynow.co.zw
2. Get Integration ID and Key
3. Install Python library: pip install paynow
```

**Paynow Implementation (RECOMMENDED):**
```python
# requirements.txt - Add this
paynow==1.0.5

# config.json - Add credentials
{
  "paynow": {
    "integration_id": "YOUR_INTEGRATION_ID",
    "integration_key": "YOUR_INTEGRATION_KEY",
    "return_url": "https://zimclassifieds.com/bnpl/payment-return",
    "result_url": "https://zimclassifieds.com/bnpl/payment-webhook"
  }
}

# bnpl.py - Add Paynow integration
from paynow import Paynow

paynow = Paynow(
    PAYNOW_INTEGRATION_ID,
    PAYNOW_INTEGRATION_KEY,
    return_url=PAYNOW_RETURN_URL,
    result_url=PAYNOW_RESULT_URL
)

@bnpl_bp.route('/pay-installment-mobile', methods=['POST'])
@login_required
def pay_installment_mobile():
    """Process BNPL installment via mobile money"""
    data = request.json
    agreement_id = data.get('agreement_id')
    installment_number = data.get('installment_number')
    
    db = get_db()
    
    # Get agreement details
    agreement = db.execute('''
        SELECT * FROM bnpl_agreements 
        WHERE agreement_id = ? AND user_id = ?
    ''', (agreement_id, session['user_id'])).fetchone()
    
    if not agreement:
        return jsonify({'success': False, 'error': 'Agreement not found'}), 404
    
    # Get user details
    user = db.execute('SELECT * FROM users WHERE user_id = ?', 
                     (session['user_id'],)).fetchone()
    
    # Create Paynow payment
    payment = paynow.create_payment(
        f"BNPL-{agreement_id}-{installment_number}",
        user['email']
    )
    
    # Add payment item
    payment.add(
        f"BNPL Installment {installment_number}",
        agreement['installment_amount']
    )
    
    # Send payment request
    response = paynow.send_mobile(
        payment,
        user['phone'],  # Customer phone number
        'ecocash'  # or 'onemoney' or 'telecash'
    )
    
    if response.success:
        # Save payment record
        payment_id = str(uuid.uuid4())
        db.execute('''
            INSERT INTO bnpl_payments
            (payment_id, agreement_id, installment_number, amount, 
             payment_method, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (payment_id, agreement['id'], installment_number, 
              agreement['installment_amount'], 'mobile_money', 'pending'))
        
        db.commit()
        db.close()
        
        # Return poll URL for status checking
        return jsonify({
            'success': True,
            'poll_url': response.poll_url,
            'payment_id': payment_id,
            'message': 'Check your phone for payment prompt'
        })
    else:
        db.close()
        return jsonify({'success': False, 'error': response.error}), 400


@bnpl_bp.route('/payment-webhook', methods=['POST'])
def payment_webhook():
    """Handle Paynow payment notifications"""
    data = request.form
    
    # Verify payment status
    status = paynow.check_transaction_status(data['pollurl'])
    
    if status.paid:
        # Extract agreement and installment from reference
        reference = data['reference']  # Format: BNPL-{agreement_id}-{installment_number}
        parts = reference.split('-')
        agreement_id = parts[1]
        installment_number = int(parts[2])
        
        db = get_db()
        
        # Update payment status
        db.execute('''
            UPDATE bnpl_payments
            SET status = 'completed', 
                payment_date = CURRENT_TIMESTAMP,
                payment_method = 'mobile_money'
            WHERE agreement_id = (SELECT id FROM bnpl_agreements WHERE agreement_id = ?)
            AND installment_number = ?
        ''', (agreement_id, installment_number))
        
        # Check if all installments paid
        total_installments = db.execute('''
            SELECT installments FROM bnpl_agreements WHERE agreement_id = ?
        ''', (agreement_id,)).fetchone()['installments']
        
        paid_installments = db.execute('''
            SELECT COUNT(*) as count FROM bnpl_payments
            WHERE agreement_id = (SELECT id FROM bnpl_agreements WHERE agreement_id = ?)
            AND status = 'completed'
        ''', (agreement_id,)).fetchone()['count']
        
        if paid_installments >= total_installments:
            # Mark agreement as completed
            db.execute('''
                UPDATE bnpl_agreements
                SET status = 'completed', completed_at = CURRENT_TIMESTAMP
                WHERE agreement_id = ?
            ''', (agreement_id,))
        
        db.commit()
        db.close()
        
        return 'OK', 200
    else:
        return 'Payment not completed', 200
```

---

### Option B: Bank Transfers & Cards

#### 1. **Stripe** (For Diaspora Payments)
```
Current Setup: Already integrated
Use Case: International card payments (UK, USA, SA)
Fees: 3.4% + $0.30 per transaction
Recurring: Setup Stripe Subscriptions for auto-pay
```

#### 2. **Bank Transfer (Zimbabwe Banks)**
```
Banks: CBZ, Stanbic, FBC, Steward Bank
Process: Manual verification
Use Case: Large purchases, corporate buyers
Fees: 0% (customer pays bank fees)
Settlement: 1-3 business days
```

---

## 2. User Verification Options

### Tier 1: Basic Verification (Free - Instant) ✅
**What You Already Have:**
- Email verification (via registration)
- Phone number (SMS OTP)

**Additional Basic Checks:**
```python
# Add to registration/verification
def verify_basic_user(user_id):
    """Basic user verification"""
    checks = {
        'email_verified': False,
        'phone_verified': False,
        'id_uploaded': False
    }
    
    # Send email verification
    send_verification_email(user['email'])
    
    # Send SMS OTP
    send_sms_otp(user['phone'])
    
    return checks
```

**SMS OTP Integration Options:**
1. **Africa's Talking** ✅ RECOMMENDED
   - Website: https://africastalking.com
   - Coverage: Zimbabwe, all Africa
   - Cost: $0.01 per SMS
   - API: Simple REST API
   - Signup: Free sandbox, pay as you go
   
```python
# pip install africastalking

import africastalking

# Initialize
africastalking.initialize(
    username='YOUR_USERNAME',
    api_key='YOUR_API_KEY'
)

sms = africastalking.SMS

def send_verification_sms(phone, otp):
    """Send OTP via SMS"""
    try:
        response = sms.send(
            f"Your ZimClassifieds verification code is: {otp}",
            [phone]  # Format: +263771234567
        )
        return {'success': True, 'message_id': response['SMSMessageData']['Recipients'][0]['messageId']}
    except Exception as e:
        return {'success': False, 'error': str(e)}
```

2. **Twilio** (More expensive, global)
   - Cost: $0.05 per SMS to Zimbabwe
   - Better for diaspora SMS

---

### Tier 2: Identity Verification (Paid - 24 hours)

#### Option A: National ID Verification ✅ BEST FOR ZIMBABWE

**Service: Zimra ID Verification API** (Unofficial)
```
What it does: Verify ID number against national registry
Cost: Unofficial services charge $0.50-$1 per check
Alternative: Manual verification via seller submission
```

**Manual ID Verification Process:**
```python
# Add to user profile
def upload_national_id():
    """User uploads photo of National ID"""
    # Customer uploads:
    # - Front of ID
    # - Back of ID
    # - Selfie holding ID
    
    # Store in:
    # users table: id_document_front, id_document_back, id_selfie
    
    # Admin reviews within 24 hours
    # Set: verification_status = 'verified'
```

**Database Update:**
```sql
ALTER TABLE users ADD COLUMN id_document_front TEXT;
ALTER TABLE users ADD COLUMN id_document_back TEXT;
ALTER TABLE users ADD COLUMN id_selfie TEXT;
ALTER TABLE users ADD COLUMN id_verified_at TIMESTAMP;
ALTER TABLE users ADD COLUMN id_verified_by TEXT;
```

#### Option B: Employment/Payslip Verification
```
For higher credit limits ($500+):
- Request recent payslip
- Employer verification letter
- Proof of income

Process:
1. User uploads documents
2. Admin verifies employment
3. Increases credit limit based on income
4. 3x monthly salary = max credit
```

---

### Tier 3: Advanced Verification (Premium Users)

#### Option A: Credit Bureau Check (Zimbabwe)
**TransUnion Zimbabwe**
- Website: https://www.transunion.co.zw
- Cost: $2-5 per check
- Returns: Credit score, loan history, defaults
- Integration: API available for businesses

```python
# Pseudocode for credit check
def check_credit_bureau(id_number):
    """Check credit score with TransUnion"""
    response = requests.post(
        'https://api.transunion.co.zw/credit-check',
        json={'id_number': id_number, 'consent': True},
        headers={'Authorization': f'Bearer {TRANSUNION_API_KEY}'}
    )
    
    return {
        'credit_score': response.json()['score'],  # 300-850
        'risk_level': response.json()['risk_level'],  # low/medium/high
        'defaults': response.json()['defaults'],
        'recommendations': 'approve' if score > 600 else 'decline'
    }
```

#### Option B: Social Verification
```
Quick & Free verification methods:
- LinkedIn profile verification
- Facebook/WhatsApp confirmation
- Google account verification
- Reference contacts (2-3 people)
```

---

## 3. Implementation Strategy

### Phase 1: Launch (Week 1) ✅ READY TO IMPLEMENT

**Payment Method:**
- Paynow integration (EcoCash, OneMoney, Telecash)
- Stripe for diaspora

**Verification:**
- Email + Phone OTP (Africa's Talking)
- Manual ID document upload & review
- Start with conservative limits: $20-$100

**Credit Scoring:**
- Use existing simple scoring system
- Start: Basic tier ($100), verified tier ($200)
- Increase limits after 2 successful payments

---

### Phase 2: Optimize (Month 1-2)

**Enhancements:**
- Automatic ID verification (if API available)
- Payment reminder SMS (3 days before due)
- Auto-retry failed payments
- WhatsApp payment reminders (free via WhatsApp Business API)

**Credit Improvements:**
- Track payment history
- Reward good payers with limit increases
- Implement soft credit checks for $500+ purchases

---

### Phase 3: Scale (Month 3+)

**Advanced Features:**
- TransUnion credit bureau integration
- Employer verification for large purchases
- Direct salary deduction (for employed users)
- Partnership with employers for guaranteed payments

---

## 4. Payment Flow (User Journey)

### Customer Checkout Experience:

```
1. Customer adds $240 worth of items to cart
2. At checkout, sees 3 payment options:
   ☑ Pay in Full (Stripe/Bank Transfer)
   ☑ BNPL - 6 weeks (EcoCash/OneMoney) ✨
   ☑ Cash on Delivery

3. Selects BNPL:
   → System checks eligibility
   → Shows plan: 6 × $40/week = $240 + $7.20 (3% fee)
   → Total: $247.20
   
4. Customer agrees to terms:
   → First payment: $40 (via EcoCash immediately)
   → Remaining: 5 × $40 (weekly auto-debit)
   
5. First payment processed:
   → Customer receives EcoCash prompt on phone
   → Enters PIN to approve
   → Payment confirmed
   → Order released to seller
   → Seller ships product
   
6. Weekly payments (automatic):
   → Day 7: SMS reminder sent
   → Day 8: Auto-payment request via EcoCash
   → Customer approves on phone
   → Payment recorded
   → Customer gets confirmation SMS
   
7. After 6 payments:
   → Agreement marked complete
   → Credit limit increased for next purchase
```

---

## 5. Security & Risk Management

### Fraud Prevention:

#### 1. **Device Fingerprinting**
```python
# Track device information
def track_device(request):
    return {
        'ip_address': request.remote_addr,
        'user_agent': request.user_agent.string,
        'device_fingerprint': hash(request.user_agent.string + request.remote_addr)
    }

# Flag suspicious:
# - Multiple accounts from same device
# - VPN/proxy usage
# - Rapid account creation
```

#### 2. **Payment Limits**
```python
BNPL_LIMITS = {
    'basic': {'max_amount': 100, 'max_active': 1},
    'verified': {'max_amount': 500, 'max_active': 2},
    'premium': {'max_amount': 2000, 'max_active': 3}
}

# Don't allow new BNPL if:
# - User has active defaults
# - More than 2 late payments
# - Total exposure > limit
```

#### 3. **Delivery Confirmation**
```
CRITICAL: Don't release product without payment!

Process:
1. First installment MUST be paid before shipping
2. Seller gets paid only after first installment clears
3. For regional deliveries: Cash on delivery backup
4. Video confirmation for high-value items (diaspora)
```

#### 4. **Default Management**
```python
# Automatic actions on missed payment:
def handle_missed_payment(agreement_id):
    # Day 1: SMS reminder
    # Day 3: Phone call
    # Day 7: Suspend account, add late fee ($5)
    # Day 14: Report to credit bureau
    # Day 30: Collection agency / legal action
    
    # Also:
    # - Block new purchases
    # - Reduce credit score
    # - Flag for manual review
```

---

## 6. Quick Start Checklist

### To Go Live with BNPL Cash Collection:

#### Week 1 Setup:
- [ ] Register for Paynow merchant account (https://paynow.co.zw)
- [ ] Install Paynow library: `pip install paynow`
- [ ] Add Paynow credentials to config.json
- [ ] Register for Africa's Talking SMS (https://africastalking.com)
- [ ] Add SMS verification to registration
- [ ] Create ID upload feature in user profile
- [ ] Test payment flow end-to-end
- [ ] Set up payment webhooks
- [ ] Add payment reminder system
- [ ] Create admin verification dashboard

#### Week 2 Launch:
- [ ] Start with basic verification only (email + phone + ID)
- [ ] Conservative limits: $20-$100 max
- [ ] Manual ID verification (24-hour turnaround)
- [ ] Monitor first 50 transactions closely
- [ ] Collect feedback and adjust

#### Month 2 Improvements:
- [ ] Add automatic payment reminders
- [ ] Implement soft credit checks
- [ ] Increase limits for good payers
- [ ] Add TransUnion integration (optional)

---

## 7. Cost Breakdown

### Transaction Costs:
```
Payment Processing:
- Paynow (mobile money): 3.5% per transaction
- EcoCash direct: 2% (if you get merchant account)
- Stripe (diaspora): 3.4% + $0.30

SMS Notifications:
- Africa's Talking: $0.01 per SMS
- Expected: 3 SMS per customer (verification + 2 reminders)
- Cost per customer: $0.03

ID Verification:
- Manual: Free (your time)
- Automatic API: $0.50-1 per check (optional)

Credit Bureau:
- TransUnion: $2-5 per check (for premium users only)

Total Cost per $100 BNPL Transaction:
- Payment fee: $3.50 (3.5%)
- SMS costs: $0.03
- Total: $3.53 (3.53%)

Your Revenue:
- BNPL fee: 3% ($3.00)
- Net margin: -$0.53 per transaction

HOWEVER:
- Increased sales volume offsets costs
- Reduced cart abandonment
- Higher average order values
- Customer lifetime value increases
```

---

## 8. Legal & Compliance

### Required Documents:

1. **BNPL Terms & Conditions**
   - Interest rate disclosure (3% is NOT interest, it's a service fee)
   - Payment schedule
   - Late payment penalties
   - Default consequences

2. **Privacy Policy**
   - How you collect/store data
   - Mobile money integration
   - ID document storage
   - Credit bureau reporting

3. **Customer Agreement**
   - Signed digitally
   - Stored in database
   - Customer acknowledges terms

### Zimbabwe Regulations:
- Reserve Bank of Zimbabwe: Register if processing >$10,000/month
- Consumer Protection: Clear disclosure of all fees
- Data Protection: Secure storage of ID documents (encrypted)

---

## 9. Next Steps

### Immediate Actions:
1. **Register for Paynow** (takes 24 hours)
2. **Register for Africa's Talking** (instant setup)
3. **Implement code changes** (see next section)
4. **Test with friends/family** (10 test transactions)
5. **Launch to limited group** (first 50 customers)
6. **Collect feedback**
7. **Scale up**

### Success Metrics to Track:
- BNPL adoption rate (target: 20% of checkouts)
- Default rate (target: <5%)
- Average order value with BNPL (should be 2-3x higher)
- Customer satisfaction (NPS score)
- Repeat purchase rate (should be higher for BNPL users)

---

## 10. Support & Resources

### Zimbabwe Payment Providers:
- Paynow: support@paynow.co.zw | +263 719 386 600
- EcoCash Merchant: merchants@econet.co.zw | +263 86 7732 2274
- Africa's Talking: help@africastalking.com

### Development Resources:
- Paynow Docs: https://developers.paynow.co.zw
- Africa's Talking Docs: https://developers.africastalking.com
- Stripe Docs: https://stripe.com/docs

### Getting Help:
- Zimbabwe Fintech WhatsApp Groups
- Developer Zimbabwe Forum
- Paynow Support (very responsive!)

---

**Ready to implement? See BNPL_CHECKOUT_INTEGRATION.md for code implementation!**
