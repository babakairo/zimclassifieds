# ZimClassifieds Marketplace

A modern, multi-seller ecommerce marketplace platform built with Flask, designed for Zimbabwe. Features include seller management, product catalog, shopping cart, **Buy Now Pay Later (BNPL)**, Paynow mobile money integration, Stripe payment processing, and courier logistics.

## ✨ Key Features

### Customer Features
- **Browse Products**: Search, filter, and discover products across categories
- **Smart Cart**: Add/remove items, manage quantities with real-time updates
- **Secure Checkout**: Stripe payment integration with test mode support
- **Order History**: Track all your purchases and deliveries
- **Product Reviews**: Rate and review products you've purchased
- **Seller Ratings**: View seller feedback and reliability metrics

### Seller Features
- **Store Management**: Create and customize your seller store
- **Product Management**: Add, edit, and manage product listings
- **Inventory Tracking**: Monitor stock levels across warehouses
- **Order Management**: View orders, manage fulfillment status
- **Sales Analytics**: Dashboard with sales metrics and earnings
- **Commission Tracking**: View platform commission calculations

### Payment Integration
- **Buy Now Pay Later (BNPL)**: Weekly installment payments with 3% diaspora rate
- **Paynow Mobile Money**: EcoCash, OneMoney, Telecash integration
- **Stripe Payments**: Secure international card payments
- **Multiple Payment Methods**: Bank transfer, cash on delivery
- **Automated Payments**: Webhook verification and status tracking
- **Diaspora Special**: Auto-detect diaspora customers for preferential rates

### Logistics (Phase 2 Ready)
- **Courier Network**: Individual courier operators register and operate by city
- **Warehouse Hubs**: Multi-city warehouse consolidation for efficient delivery
- **Delivery Tracking**: Real-time tracking with GPS coordinates
- **Same-City Delivery**: Next-day delivery targeting for local orders
- **Cross-City Delivery**: 2-3 day delivery via warehouse hubs
- **Transporter Earnings**: Per-delivery model with tips and bonuses

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip
- Virtual environment (venv)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/babakairo/zimclassifieds.git
   cd classifieds
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your:
   # - STRIPE_PUBLIC_KEY
   # - STRIPE_SECRET_KEY
   # - Any other API keys
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

   Visit `http://localhost:5000` in your browser.

## 📁 Project Structure

```
classifieds/
├── app.py                    # Main Flask application with core routes
├── bnpl.py                  # Buy Now Pay Later module (1000+ lines)
├── sellers.py               # Seller blueprint (store, products, orders, analytics)
├── cart.py                  # Shopping cart blueprint (AJAX operations)
├── transporters.py          # Courier/logistics management
├── database.py              # Database abstraction (SQLite/PostgreSQL)
├── config.json              # Application configuration
├── requirements.txt         # Python dependencies
├── runtime.txt              # Python version for deployment
├── Procfile                 # Heroku deployment config
├── .gitignore               # Git ignore rules
├── README.md                # This file
│
├── static/                  # Static assets
│   ├── css/                 # Stylesheets
│   ├── js/                  # JavaScript
│   └── uploads/             # User-uploaded images
│       ├── products/        # Product images
│       ├── ids/             # ID verification documents
│       └── police_clearance/ # Driver police clearance
│
├── templates/               # HTML templates (Jinja2)
│   ├── base.html           # Base template with navigation
│   ├── index.html          # Home page with BNPL banner
│   ├── about.html          # About page
│   ├── login.html          # User login
│   ├── register.html       # User registration
│   ├── dashboard.html      # Customer dashboard
│   ├── error.html          # Error pages
│   ├── products/           # Product browsing
│   ├── sellers/            # Seller management
│   ├── cart/               # Shopping cart
│   ├── checkout/           # Checkout with BNPL option
│   ├── bnpl/               # BNPL specific templates
│   │   ├── diaspora_landing.html
│   │   ├── first_payment.html
│   │   └── payment_return.html
│   └── transporters/       # Courier/driver portal
│
├── scripts/                 # Utility scripts
│   ├── seed_marketplace.py  # Generate test data
│   ├── migrate_to_postgres.py # PostgreSQL migration
│   ├── check_db.py          # Database viewer
│   └── test_functionality.py # Integration tests
│
└── docs/                    # Documentation
    ├── bnpl/                # BNPL documentation
    │   ├── BNPL_IMPLEMENTATION.md
    │   ├── BNPL_CASH_COLLECTION_GUIDE.md
    │   ├── BNPL_CHECKOUT_INTEGRATION.md
    │   ├── BNPL_NAVIGATION_UPDATE.md
    │   └── BNPL_QUICK_START.md
    ├── deployment/          # Deployment guides
    │   ├── DEPLOYMENT.md
    │   ├── POSTGRES_MIGRATION_GUIDE.md
    │   ├── PRODUCTION_DATABASE_SETUP.md
    │   └── MIGRATION_COMPLETE.md
    ├── guides/              # User guides
    │   ├── QUICK_START.md
    │   ├── STRIPE_SETUP.md
    │   └── COMPETITIVE_STRATEGY.md
    └── *.md                 # Project status documents
```

## 🗄️ Database Schema

### Core Tables
- **users**: Customer accounts (email, password, profile)
- **sellers**: Seller stores (store name, logo, ratings)
- **products**: Product listings (name, price, description, images)
- **inventory**: Stock levels per warehouse location

### Order Management
- **cart**: Shopping cart items (user, product, quantity)
- **orders**: Order headers (total, status, payment method)
- **order_items**: Individual items in orders with fulfillment status
- **payment_transactions**: Payment records (Stripe reference, status)

### Reviews & Ratings
- **product_reviews**: Customer reviews for products (5-star, text, verified purchase)
- **seller_ratings**: Seller performance ratings (response time, quality, shipping)

### Commission Management
- **seller_commissions**: Platform commission calculations (15% default)

All tables include indices for optimal query performance.

## 💳 Payment Processing

### Stripe Integration
- **Test Mode**: Use test card `4242 4242 4242 4242`
  - Expiry: 12/25 (any future date)
  - CVC: 123 (any 3 digits)

- **Test Webhook Handling**: Use Stripe CLI for local testing
  ```bash
  stripe listen --forward-to localhost:5000/webhook
  ```

- **Production Setup**: Set real API keys in environment variables

### Payment Flow
1. Customer adds items to cart
2. Proceeds to checkout
3. Stripe Checkout handles payment
4. On success: Order created, inventory reserved, cart cleared
5. Order confirmation page shows details

## 👥 User Workflows

### Customer Flow
1. **Register** → Create account
2. **Browse** → Search products by category or keyword
3. **View Seller Stores** → Browse all products from a seller
4. **Add to Cart** → AJAX cart operations
5. **Checkout** → Enter shipping address
6. **Payment** → Stripe card payment
7. **Order Confirmation** → View order details
8. **Track Order** → See fulfillment status
9. **Review Products** → Submit ratings and comments

### Seller Flow
1. **Register as Seller** → Create store with name and policy
2. **Create Products** → Add product name, price, images, stock
3. **Edit Products** → Update price, description, images
4. **View Orders** → See incoming customer orders
5. **Fulfill Orders** → Mark items as shipped with tracking
6. **Check Analytics** → View sales, revenue, commission earned
7. **View Store** → Public store page showing all products

## 🚚 Phase 2: Courier & Logistics (Coming Soon)

### Planned Features
- **Transporter Registration**: Individual couriers register by city
- **Delivery Assignment**: Automatic routing to available couriers
- **Multi-City Delivery**: Warehouse hub consolidation for cross-city orders
- **Real-Time Tracking**: GPS tracking with customer notifications
- **Earnings Dashboard**: Per-delivery payments with tips and bonuses
- **Quality Metrics**: Rating system, on-time delivery tracking

See `PHASE2_LOGISTICS_DESIGN.md` and `PHASE2_IMPLEMENTATION.md` for detailed specifications.

## 📊 Analytics & Metrics

### Seller Metrics
- Total sales (order count)
- Revenue by product/category
- Average order value
- Commission earned
- Customer response ratings
- Product review averages

### Platform Metrics
- Total GMV (Gross Merchandise Value)
- Commission revenue
- Active sellers
- Product inventory status
- Payment success rate

## 🔒 Security Features

- Password hashing with Werkzeug
- CSRF protection on forms
- SQL injection prevention via parameterized queries
- Email verification (optional, configurable)
- Secure file upload with extension validation
- Environment variables for sensitive keys

## 📝 API Endpoints

### Products
- `GET /products` - Browse products with filtering
- `GET /product/<product_id>` - Product details
- `GET /seller/<store_slug>` - Seller store page

### Cart
- `GET /cart/` - View cart
- `POST /cart/api/add` - Add item to cart
- `POST /cart/api/remove` - Remove item
- `POST /cart/api/update` - Update quantity
- `GET /cart/api/summary` - Get cart totals

### Orders
- `POST /api/stripe-checkout` - Create Stripe session
- `GET /stripe-success` - Stripe success callback
- `GET /checkout` - Checkout page
- `POST /api/orders` - Create order (non-Stripe)
- `GET /order/<order_id>` - Order details
- `GET /orders/history` - Order history

### Sellers
- `POST /sellers/register` - Register seller
- `GET /sellers/dashboard` - Seller dashboard
- `POST /sellers/product/new` - Create product
- `POST /sellers/product/<id>/edit` - Edit product
- `GET /sellers/analytics` - Sales analytics
- `GET /sellers/<store_slug>` - Public store

### Reviews
- `POST /api/product-review` - Submit product review

## 🧪 Testing

### Test Data
Run the seed script to populate test data:
```bash
python seed_marketplace.py
```

This creates:
- 6 seller stores
- 60 products across 6 categories
- 5 customer accounts
- 10+ sample orders
- Reviews and ratings

### End-to-End Test
1. Register as seller → `/sellers/register`
2. Create product → `/sellers/product/new`
3. Register as customer → `/register`
4. Browse products → `/products`
5. Add to cart → Cart page
6. Checkout → `/checkout`
7. Pay with test card
8. View order → Order confirmation page

## 📦 Dependencies

Key libraries:
- **Flask** (2.3.3): Web framework
- **Stripe** (7.0.0): Payment processing
- **SQLite3**: Database
- **Werkzeug**: Security utilities
- **python-dotenv**: Environment configuration

See `requirements.txt` for full list.

## 🌍 Deployment

### Heroku / Render
1. Set environment variables (Stripe keys)
2. Ensure `Procfile` includes: `web: python app.py`
3. Push to Git
4. Platform automatically detects requirements.txt

### Docker
```bash
docker build -t zimclassifieds .
docker run -p 5000:5000 zimclassifieds
```

See `DEPLOYMENT.md` for detailed deployment guide.

## 🐛 Troubleshooting

### Stripe Tests Failing
- Verify API keys in `.env` file
- Ensure `stripe` library is installed: `pip install stripe==7.0.0`
- Test mode works with test API keys only

### Database Errors
- Delete `zimclassifieds.db` to reset (dev only)
- Check database permissions
- Run `python app.py` to auto-initialize on first request

### Cart Not Updating
- Check browser console for JavaScript errors
- Verify cart.py blueprint is loaded in app.py
- Clear browser cache and cookies

## 📞 Support

For issues and feature requests:
- GitHub Issues: https://github.com/babakairo/zimclassifieds/issues
- Documentation: See PHASE1_COMPLETE.md for detailed implementation

## 📄 License

MIT License - See LICENSE file for details

## 🎯 Next Steps

1. **Test Phase 1**: Run end-to-end seller → customer → order flow
2. **Customize**: Update store name, logo, colors in templates
3. **Production Setup**: Configure real Stripe keys for live payments
4. **Phase 2**: Implement courier registration and logistics system
5. **Scaling**: Add caching, optimize queries, increase server capacity

---

**Current Status**: ✅ Phase 1 Complete - Fully functional ecommerce marketplace  
**Phase 2 Status**: 🟡 Design Complete - Ready for implementation  
**Last Updated**: November 16, 2025
