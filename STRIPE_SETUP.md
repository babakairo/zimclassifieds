# Stripe Payment Integration Guide

## Overview
ZimClassifieds now supports secure Stripe card payments. This guide covers setup, testing, and deployment.

## Setup Instructions

### 1. Create Stripe Account
- Sign up for free at [stripe.com](https://stripe.com)
- Navigate to the [API Keys page](https://dashboard.stripe.com/apikeys)
- Copy your **Publishable Key** (starts with `pk_`) and **Secret Key** (starts with `sk_`)

### 2. Configure Environment Variables

Create a `.env` file in the project root (copy from `.env.example`):

```bash
# Stripe Payment Keys
STRIPE_PUBLIC_KEY=pk_test_your_public_key_here
STRIPE_SECRET_KEY=sk_test_your_secret_key_here
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `stripe==7.0.0` - Stripe Python library
- `python-dotenv==1.0.0` - Environment variable management

### 4. Test the Integration

#### Test Card Numbers

Use these cards in **test mode** (requires expiry 12/25 or later, any CVC):

| Use Case | Card Number | Status |
|----------|------------|--------|
| Success | `4242 4242 4242 4242` | ✅ Payment succeeds |
| Decline | `4000 0000 0000 0002` | ❌ Payment declined |
| Auth Required | `4000 0025 0000 3155` | 🔐 Requires 3D Secure |
| Authentication | `4000 0025 0000 3055` | 🔐 Requires authentication |

**Always use:**
- **Expiry**: 12/25 (or any future date: MM/YY)
- **CVC**: 123 (or any 3 digits)

#### Testing Steps

1. Go to `/checkout`
2. Fill in shipping address
3. Select "Credit/Debit Card (Stripe)"
4. Use test card from above (e.g., `4242 4242 4242 4242`)
5. Fill in expiry `12/25` and CVC `123`
6. Click "Place Order"
7. You should be redirected to Stripe Checkout
8. Complete the payment
9. See order confirmation page

#### Viewing Test Transactions

In Stripe Dashboard:
1. Go to [Developers > Events](https://dashboard.stripe.com/logs/events)
2. Filter by `charge.succeeded` or `charge.failed`
3. Click transaction to see details

## Flow Diagram

```
Customer Checkout
    ↓
Select "Stripe" payment
    ↓
Fill shipping address
    ↓
POST /api/stripe-checkout
    ↓
Create Stripe Session (backend)
    ↓
Redirect to Stripe Checkout (hosted payment form)
    ↓
Customer enters card details
    ↓
Stripe processes payment
    ↓
Success → Redirect to /stripe-success
    ↓
Create order in database
    ↓
Display order confirmation
```

## Implementation Details

### Routes

#### POST `/api/stripe-checkout`
- **Purpose**: Create Stripe checkout session
- **Auth**: Login required
- **Payload**:
  ```json
  {
    "shipping_address": "123 Main St",
    "shipping_city": "Harare",
    "shipping_suburb": "Avondale",
    "payment_method": "stripe_card"
  }
  ```
- **Response**:
  ```json
  {
    "success": true,
    "sessionId": "cs_test_...",
    "publishableKey": "pk_test_..."
  }
  ```

#### GET `/stripe-success`
- **Purpose**: Handle Stripe payment success
- **Auth**: Login required
- **Query Params**: `session_id` (from Stripe)
- **Action**: Creates order, redirects to confirmation

#### POST `/api/orders`
- **Purpose**: Create order for non-Stripe payments
- **Auth**: Login required
- **Supported methods**: `bank_transfer`, `cod` (cash on delivery)

### Database Changes

**payment_transactions table** now tracks:
- `transaction_id` - Stripe Payment Intent ID (or custom UUID)
- `payment_method` - 'stripe_card', 'bank_transfer', 'cod'
- `status` - 'pending', 'completed', 'failed'

**orders table** now has:
- `payment_status` - 'pending', 'paid', 'failed'
- `payment_method` - Selected payment method

## Moving to Production

### 1. Switch to Live Keys

When ready for production:
1. Go to [Stripe Dashboard](https://dashboard.stripe.com)
2. Switch from **Test** to **Live** mode (toggle in top left)
3. Copy your **live** Publishable and Secret keys
4. Update `.env`:
   ```bash
   STRIPE_PUBLIC_KEY=pk_live_your_live_public_key
   STRIPE_SECRET_KEY=sk_live_your_live_secret_key
   ```

### 2. Setup Webhooks (Optional but Recommended)

For production, add webhooks to handle:
- `charge.succeeded` - Confirm payment
- `charge.failed` - Handle failures
- `charge.dispute.created` - Handle chargebacks

1. Go to [Webhooks page](https://dashboard.stripe.com/webhooks)
2. Add endpoint: `https://yourdomain.com/stripe-webhook`
3. Select events: `charge.succeeded`, `charge.failed`
4. Copy Signing Secret
5. Add to `.env`: `STRIPE_WEBHOOK_SECRET=whsec_...`

### 3. Enable 3D Secure (PCI Compliance)

In Stripe Dashboard:
1. Go to Settings > Payments
2. Enable 3D Secure requirement
3. This protects against fraud and chargebacks

### 4. Security Checklist

- [ ] Never commit `.env` file with live keys
- [ ] Use environment variables for all secrets
- [ ] Enable HTTPS only in production
- [ ] Regularly rotate API keys
- [ ] Monitor webhook logs for failures
- [ ] Set up email notifications for failed payments
- [ ] Implement rate limiting on checkout endpoint

## Troubleshooting

### "Stripe module not found"
```bash
pip install stripe python-dotenv
```

### Payment redirects to Stripe but doesn't work
1. Check that STRIPE_PUBLIC_KEY starts with `pk_test_` or `pk_live_`
2. Verify STRIPE_SECRET_KEY starts with `sk_test_` or `sk_live_`
3. Ensure keys are in `.env` file (not hardcoded)
4. Check browser console for JavaScript errors

### Test cards not working
- Ensure you're using cards from the test card list above
- Use expiry `12/25` (or any future date)
- Use any 3-digit CVC
- Make sure you're in **test mode** (not live)

### Order not created after payment
1. Check Stripe Dashboard > Events for `charge.succeeded`
2. Check application logs for errors
3. Verify `stripe_success` route is being hit
4. Ensure cart has items (cart must not be empty)

## Fee Structure

**Stripe Charges:**
- 2.9% + $0.30 USD per successful transaction
- Example: $100 order = $2.90 + $0.30 = $3.20 fee

**ZimClassifieds Commission:**
- 15% of seller's revenue (in addition to Stripe fees)
- Example: $100 order = $15 platform fee + $3.20 Stripe fee

## Support

- Stripe Documentation: https://stripe.com/docs
- Python Library: https://github.com/stripe/stripe-python
- Support Email: support@stripe.com

## References

- [Stripe Checkout API](https://stripe.com/docs/payments/checkout)
- [Test Card Numbers](https://stripe.com/docs/testing)
- [Payment Methods](https://stripe.com/docs/payments/payment-methods)
- [Webhooks Guide](https://stripe.com/docs/webhooks)
