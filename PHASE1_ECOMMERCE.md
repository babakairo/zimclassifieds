# Phase 1: E-Commerce Marketplace Transformation

## Overview
Convert ZimClassifieds from a classifieds platform to a Takealot-style e-commerce marketplace with seller stores, shopping carts, orders, and payment processing.

---

## Phase 1 Database Schema

### New Tables & Changes

#### 1. **sellers** (Seller Profiles/Stores)
```sql
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
```

#### 2. **products** (Replaces listings for marketplace)
```sql
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
```

#### 3. **inventory** (Stock management per location)
```sql
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
```

#### 4. **cart** (Shopping cart items)
```sql
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
```

#### 5. **orders** (Customer orders)
```sql
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
```

#### 6. **order_items** (Items in each order)
```sql
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
```

#### 7. **product_reviews** (Product ratings & reviews)
```sql
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
```

#### 8. **seller_ratings** (Seller/Store ratings)
```sql
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
```

#### 9. **payment_transactions** (Payment tracking)
```sql
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
```

#### 10. **seller_commissions** (Platform revenue tracking)
```sql
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
```

### Indices for Performance
```sql
CREATE INDEX idx_products_seller ON products(seller_id);
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_status ON products(status);
CREATE INDEX idx_inventory_product ON inventory(product_id);
CREATE INDEX idx_cart_user ON cart(user_id);
CREATE INDEX idx_orders_user ON orders(user_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_order_items_seller ON order_items(seller_id);
CREATE INDEX idx_product_reviews_product ON product_reviews(product_id);
CREATE INDEX idx_product_reviews_user ON product_reviews(user_id);
CREATE INDEX idx_seller_ratings_seller ON seller_ratings(seller_id);
CREATE INDEX idx_payment_transactions_order ON payment_transactions(order_id);
CREATE INDEX idx_seller_commissions_seller ON seller_commissions(seller_id);
```

---

## Phase 1 Features & Routes

### A. Seller Management (`/sellers` blueprint)
- `GET /sellers/register` - Register as seller
- `POST /sellers/register` - Create seller account
- `GET /sellers/<seller_id>` - View seller store
- `GET /sellers/dashboard` - Seller dashboard (products, orders, analytics)
- `GET /sellers/products` - Manage seller's products
- `POST /sellers/product/new` - Add new product
- `POST /sellers/product/<product_id>/edit` - Edit product
- `POST /sellers/product/<product_id>/delete` - Delete product
- `GET /sellers/orders` - View seller's orders
- `POST /sellers/order/<order_id>/fulfill` - Mark order as shipped
- `GET /sellers/analytics` - Sales analytics

### B. Product Browsing (`/products` routes in main app.py)
- `GET /products` - Browse all products with filters
- `GET /products/<product_id>` - Product detail page
- `GET /products/category/<category>` - Browse by category
- `GET /api/product-search` - Search API with filters

### C. Shopping Cart (`/cart` blueprint)
- `GET /cart` - View cart
- `POST /api/add-to-cart` - Add product to cart
- `POST /api/remove-from-cart` - Remove from cart
- `POST /api/update-cart` - Update quantities
- `GET /api/cart/summary` - Get cart totals

### D. Checkout & Orders (`/orders` routes in main app.py)
- `GET /checkout` - Checkout page
- `POST /orders` - Create order from cart
- `GET /orders/<order_id>` - View order details
- `GET /orders/history` - Customer order history
- `POST /api/payment/process` - Process payment (Stripe/PayPal stub)

### E. Reviews & Ratings
- `POST /api/product-review` - Submit product review
- `POST /api/seller-rating` - Submit seller rating
- `GET /api/product-reviews/<product_id>` - Get product reviews

---

## Implementation Steps

### Step 1: Update Database Schema (app.py)
- Add all 10 new tables to `init_db()`
- Create indices
- Ensure backward compatibility with existing users/listings

### Step 2: Create Seller Blueprint (sellers.py)
- Seller registration and store setup
- Seller dashboard with product management
- Order fulfillment interface
- Analytics/reporting

### Step 3: Create Cart Blueprint (cart.py)
- Shopping cart management
- Cart API endpoints
- Cart persistence

### Step 4: Create Product Routes (app.py)
- Product browsing and filtering
- Product detail pages
- Product search

### Step 5: Create Order Routes (app.py)
- Checkout flow
- Order creation
- Order history
- Payment processing (stub)

### Step 6: Create Templates
- Seller dashboard
- Product pages
- Cart and checkout
- Order history
- Reviews and ratings

### Step 7: Testing & Deployment
- End-to-end flow testing
- Performance testing
- Deploy to Render/Railway

---

## Takealot-Style Features Included

✅ **Marketplace**: Multiple sellers on one platform
✅ **Seller Stores**: Branded seller pages with ratings
✅ **Shopping Cart**: Add/remove products
✅ **Checkout**: Address and payment
✅ **Orders**: Order tracking and fulfillment
✅ **Reviews**: Product and seller ratings
✅ **Inventory**: Stock management
✅ **Commission**: Platform takes % of sales
✅ **Search & Filters**: Category, price, ratings
✅ **Analytics**: Seller sales dashboard

---

## Next Phase (Phase 2): Logistics Integration
- Shipping partner APIs (DHL, FedEx, etc.)
- Real-time tracking
- Warehouse management
- Return/refund management
- Shipping cost calculator
- Own delivery fleet (future)

