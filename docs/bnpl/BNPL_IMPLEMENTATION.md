# BNPL (Buy Now Pay Later) Implementation Guide

## 🎯 Strategic Vision

**Target**: Diaspora customers sending gifts home + Local flexible payments
**Penetration Strategy**: Massive adoption through installment plans
**Unique Advantage**: 3% fee for diaspora (competitors: 8-10%)

---

## ✅ What's Been Built

### 1. Core BNPL System (`bnpl.py`)

**Features**:
- ✅ Flexible payment plans (2/4/6 week installments)
- ✅ Diaspora detection (location/phone based)
- ✅ Credit scoring system
- ✅ User tier management (basic/verified/premium)
- ✅ Automatic fee calculation
- ✅ Payment schedule generation
- ✅ Agreement management

**Payment Plans**:
```python
Small ($20-$100):   2 payments, 2 weeks, 5% fee (3% diaspora)
Medium ($100-$500): 4 payments, 4 weeks, 8% fee (3% diaspora)
Large ($500-$2000): 6 payments, 6 weeks, 10% fee (3% diaspora)
```

### 2. Database Tables (Added to `app.py`)

**`bnpl_agreements`**:
- Stores BNPL contracts
- Tracks: principal, fees, installments, status
- Links to users and orders
- Stores payment schedule as JSON

**`bnpl_payments`**:
- Records individual installment payments
- Tracks: payment method, status, dates
- Links to agreements

**Indexes**: Optimized for user queries, status filters

### 3. Diaspora Landing Page ✅

**Location**: `/bnpl/diaspora-landing`
**Template**: `templates/bnpl/diaspora_landing.html`

**Content**:
- Hero with BNPL calculator
- Police-verified driver trust messaging
- Special 3% diaspora rate highlighted
- Video delivery confirmation feature
- Multiple recipient support
- Scheduled delivery option
- Testimonials from UK/SA/Canada customers
- Payment plan comparisons
- FAQ section
- Strong CTA for registration

### 4. API Endpoints

**User-Facing**:
- `POST /bnpl/check-eligibility` - Check if user can use BNPL for amount
- `POST /bnpl/create-agreement` - Create BNPL contract
- `GET /bnpl/my-agreements` - View user's agreements
- `GET /bnpl/agreement/<id>` - View specific agreement
- `POST /bnpl/pay-installment/<id>` - Pay an installment
- `GET /bnpl/diaspora-landing` - Marketing landing page

**Admin**:
- `GET /bnpl/admin/agreements` - View all agreements (TODO: Add auth)

---

## 🚀 Integration Points

### Checkout Flow (Next Step)

**Add BNPL option to checkout**:

1. **Check eligibility** on cart total
2. **Show BNPL widget** if eligible
3. **Calculate payment plan** dynamically
4. **Create agreement** on selection
5. **Process first payment** via Stripe
6. **Set up auto-pay** for remaining installments

**Example Checkout Widget**:
```html
<!-- Add to templates/checkout/checkout.html -->
<div class="card mb-3" id="bnpl-option" style="display:none;">
    <div class="card-header bg-success text-white">
        <strong>💳 Pay Over Time - Special Diaspora Rate!</strong>
    </div>
    <div class="card-body">
        <div class="row">
            <div class="col-md-6">
                <h5>Only $<span id="bnpl-installment">0</span> per week</h5>
                <p><span id="bnpl-installments">0</span> payments • <span id="bnpl-weeks">0</span> weeks</p>
            </div>
            <div class="col-md-6 text-end">
                <button class="btn btn-success" id="select-bnpl">Choose BNPL</button>
            </div>
        </div>
        <small class="text-muted">
            <span id="bnpl-fee-note">Only 3% fee for diaspora customers</span>
        </small>
    </div>
</div>

<script>
// Check BNPL eligibility
fetch('/bnpl/check-eligibility', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({amount: cartTotal})
})
.then(r => r.json())
.then(data => {
    if (data.success) {
        document.getElementById('bnpl-option').style.display = 'block';
        document.getElementById('bnpl-installment').textContent = data.plan.installment_amount;
        document.getElementById('bnpl-installments').textContent = data.plan.installments;
        document.getElementById('bnpl-weeks').textContent = data.plan.duration_weeks;
        
        if (data.plan.is_diaspora) {
            document.getElementById('bnpl-fee-note').innerHTML = 
                '<strong>Special Diaspora Rate: Only 3% fee! 🎉</strong>';
        }
    }
});
</script>
```

---

## 📊 Credit Scoring Logic

### Factors

**Positive** (increase limit):
- ✅ Completed orders (+5 points each, max +25)
- ✅ Completed BNPL agreements (+10 points each, max +30)
- ✅ Diaspora status (+20 points)

**Negative** (decrease limit):
- ❌ Defaulted BNPL payments (-30 points each)

### Tiers

```
Credit Score 85+:  Premium tier ($2000 limit diaspora, $1000 local)
Credit Score 65+:  Verified tier ($1000 limit diaspora, $500 local)
Credit Score <65:  Basic tier ($200 limit diaspora, $100 local)
```

### Auto-Approval

- **Diaspora**: Instant approval up to $500
- **Local**: Manual review above $100 (basic tier)

---

## 💰 Revenue Model

### Fee Structure

| User Type | Plan Size | Standard Fee | Diaspora Fee | Our Take |
|-----------|-----------|-------------|--------------|----------|
| All | Small ($20-$100) | 5% | **3%** | $1-$3 |
| All | Medium ($100-$500) | 8% | **3%** | $3-$15 |
| All | Large ($500-$2000) | 10% | **3%** | $15-$60 |

**Why 3% for Diaspora?**
- Lower default risk (stable income)
- Higher order values
- Marketing differentiation
- Competitive vs. remittance services (10-15%)

### Projected Revenue

**Conservative Estimate**:
```
100 diaspora orders/month
Average order: $300
Average fee (3%): $9
Monthly revenue: $900
Annual revenue: $10,800
```

**Growth Scenario** (6 months):
```
500 diaspora orders/month
Average order: $400
Average fee (3%): $12
Monthly revenue: $6,000
Annual revenue: $72,000
```

---

## 🎯 Marketing Strategy

### Diaspora Channels

**1. UK/SA Zimbabwe Facebook Groups**
- "Zimbabweans in UK"
- "Zimbabweans in South Africa"
- "Zim Diaspora Network"

**Post Strategy**:
```
"💝 Sending something home this month?

We've built something special for you:
✅ Buy now, pay over 2-6 weeks
✅ Only 3% fee (not 10% like others)
✅ Police-verified drivers
✅ Video proof of delivery

My mum's smile when the fridge arrived? Priceless.
And I paid $40/week instead of $240 upfront.

Try it: [link]"
```

**2. WhatsApp Groups**
- Partner with diaspora community admins
- Offer affiliate commission (5%)
- Share success stories weekly

**3. Influencer Partnerships**
- UK-based Zim YouTubers
- SA-based Zim Instagram influencers
- Gift products for review/unboxing

### Local Marketing

**For Local BNPL Users**:
- "Buy the phone you need, pay over 4 weeks"
- Target young professionals (25-35)
- Partner with employers for payroll deduction
- Radio ads emphasizing flexibility

---

## 🔧 Technical Integration Steps

### Step 1: Add BNPL to Checkout ⏳

**File**: `templates/checkout.html`
**Action**: Add BNPL widget with eligibility check

### Step 2: Stripe Integration ⏳

**File**: `bnpl.py` → `pay_installment()`
**Action**: Process first payment, set up auto-pay

```python
import stripe

def process_first_payment(agreement_id, card_token):
    # Charge first installment
    charge = stripe.Charge.create(
        amount=int(installment_amount * 100),  # cents
        currency="usd",
        source=card_token
    )
    
    # Set up subscription for remaining payments
    customer = stripe.Customer.create(source=card_token)
    
    stripe.Subscription.create(
        customer=customer.id,
        items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {'name': f'BNPL Agreement {agreement_id}'},
                'recurring': {'interval': 'week'},
                'unit_amount': int(installment_amount * 100)
            }
        }]
    )
```

### Step 3: SMS Reminders ⏳

**Integration**: Twilio or Africa's Talking
**Triggers**:
- 3 days before payment due
- Day of payment due
- 1 day after missed payment

### Step 4: Admin Dashboard ⏳

**Features**:
- View all agreements
- Filter by status (active/completed/defaulted)
- Manual payment marking
- Credit limit adjustments
- Diaspora verification

### Step 5: Email Notifications ⏳

**Triggers**:
- Agreement created
- Payment processed
- Payment failed
- Agreement completed

---

## 🎬 Launch Checklist

### Pre-Launch
- [ ] Add BNPL to checkout flow
- [ ] Integrate Stripe for payments
- [ ] Set up auto-pay subscriptions
- [ ] Create SMS reminder system
- [ ] Build admin dashboard
- [ ] Test with dummy orders
- [ ] Legal: T&C, privacy policy updates

### Soft Launch (Week 1)
- [ ] Enable for 50 beta users
- [ ] Diaspora-only initially
- [ ] Monitor default rates
- [ ] Gather feedback
- [ ] Fix bugs

### Full Launch (Week 2-4)
- [ ] Open to all diaspora customers
- [ ] Start diaspora marketing campaign
- [ ] Partner with influencers
- [ ] Track conversion rates
- [ ] Optimize messaging

### Scale (Month 2+)
- [ ] Enable for local customers
- [ ] Increase credit limits for good payers
- [ ] Add employer partnerships
- [ ] Expand to other African countries (SA, Botswana)

---

## 📈 Success Metrics

### Week 1
- [ ] 20+ diaspora users sign up
- [ ] 10+ BNPL agreements created
- [ ] 0% default rate
- [ ] Average order value: $250+

### Month 1
- [ ] 100+ diaspora users
- [ ] 50+ active agreements
- [ ] $15,000 GMV through BNPL
- [ ] <2% default rate
- [ ] 4.5+ star reviews

### Month 3
- [ ] 500+ total BNPL users
- [ ] 200+ active agreements
- [ ] $60,000 GMV through BNPL
- [ ] <3% default rate
- [ ] Featured in diaspora media

---

## 🚨 Risk Management

### Default Prevention

**1. Progressive Limits**
- Start small ($100)
- Increase with good payment history
- Cap at $2000 (diaspora), $1000 (local)

**2. Early Warning System**
- SMS 3 days before due
- Email reminders
- Phone call if missed
- Grace period (3 days)

**3. Collections Process**
- Week 1: Friendly reminder
- Week 2: Payment plan offer
- Week 3: Reduce future limits
- Week 4: Collections agency

### Fraud Prevention

**1. Verification Required**
- Email verification
- Phone verification
- First order must be paid fully (no BNPL)
- Diaspora: Credit card AVS check

**2. Red Flags**
- New account + high value order
- Mismatched shipping/billing
- Multiple failed cards
- Suspicious location changes

---

## 🎯 Competitive Advantage

### vs. Ownai, Tillpoint, Others

| Feature | Competitors | **ZimClassifieds** |
|---------|------------|-------------------|
| BNPL Available | ❌ | ✅ **UNIQUE** |
| Diaspora Focus | Partial | ✅ **PRIMARY** |
| Special Diaspora Rate | N/A | ✅ **3% only** |
| Police-Verified Drivers | ❌ | ✅ |
| Video Delivery Proof | ❌ | ✅ |
| Flexible Plans | N/A | ✅ 2/4/6 weeks |

**Why This Wins**:
1. **First mover**: No local competitor has BNPL
2. **Diaspora-focused**: Untapped market with higher purchasing power
3. **Trust layer**: Police clearance + video = unbeatable safety
4. **Low friction**: Instant approval, no paperwork
5. **Network effects**: More users → better data → better credit scoring → lower risk → lower fees

---

## 📞 Next Actions

### Immediate (This Week)
1. ✅ BNPL system built
2. ✅ Database tables added
3. ✅ Diaspora landing page created
4. ⏳ Add BNPL to checkout
5. ⏳ Stripe integration

### Short Term (Weeks 2-4)
1. SMS reminders setup
2. Email templates
3. Admin dashboard
4. Beta testing with 20 users
5. Marketing content creation

### Medium Term (Months 2-3)
1. Launch to all diaspora
2. Influencer partnerships
3. WhatsApp group outreach
4. Facebook ads campaign
5. Monitor and optimize

---

## 🏆 The Vision

**6 Months from Now**:
- 1,000+ diaspora customers using BNPL
- $200k+ monthly GMV through installment plans
- Featured in "How Zimbabwe is Revolutionizing Diaspora Commerce"
- Copycats emerge (but we have the trust layer they can't replicate)

**12 Months from Now**:
- Expand to SA, Botswana, Mozambique diaspora
- Partner with employers for payroll deduction
- Launch "BNPL for Business" (B2B working capital)
- $1M+ annual GMV through BNPL

**The Moat**: Police-verified delivery + diaspora-first BNPL + community trust = impossible to replicate quickly

---

Ready to make this happen! 🚀🇿🇼
