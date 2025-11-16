"""
PostgreSQL Schema - Converted from SQLite
Run this to create tables in PostgreSQL database
"""

POSTGRESQL_SCHEMA = """
-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    location VARCHAR(255),
    email_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sellers table
CREATE TABLE IF NOT EXISTS sellers (
    id SERIAL PRIMARY KEY,
    seller_id VARCHAR(100) UNIQUE NOT NULL,
    user_id VARCHAR(100) NOT NULL,
    store_name VARCHAR(255) NOT NULL,
    store_slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    logo_image VARCHAR(255),
    banner_image VARCHAR(255),
    is_verified BOOLEAN DEFAULT FALSE,
    rating DECIMAL(3,2) DEFAULT 5.0,
    total_reviews INTEGER DEFAULT 0,
    total_sales INTEGER DEFAULT 0,
    return_policy TEXT,
    shipping_policy TEXT,
    response_time_hours INTEGER DEFAULT 24,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Products table
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    product_id VARCHAR(100) UNIQUE NOT NULL,
    seller_id INTEGER NOT NULL,
    category VARCHAR(100) NOT NULL,
    subcategory VARCHAR(100),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'ZWL',
    sku VARCHAR(100) UNIQUE,
    stock_quantity INTEGER DEFAULT 0,
    images TEXT,
    status VARCHAR(50) DEFAULT 'active',
    rating DECIMAL(3,2) DEFAULT 0,
    total_reviews INTEGER DEFAULT 0,
    total_sales INTEGER DEFAULT 0,
    views INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (seller_id) REFERENCES sellers(id)
);

-- Product Images table
CREATE TABLE IF NOT EXISTS product_images (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL,
    image_path VARCHAR(255) NOT NULL,
    display_order INTEGER DEFAULT 0,
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Inventory table
CREATE TABLE IF NOT EXISTS inventory (
    id SERIAL PRIMARY KEY,
    inventory_id VARCHAR(100) UNIQUE NOT NULL,
    product_id INTEGER NOT NULL,
    quantity_available INTEGER DEFAULT 0,
    quantity_reserved INTEGER DEFAULT 0,
    last_restocked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Cart table
CREATE TABLE IF NOT EXISTS cart (
    id SERIAL PRIMARY KEY,
    cart_id VARCHAR(100) UNIQUE NOT NULL,
    user_id VARCHAR(100) NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER DEFAULT 1,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Orders table
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR(100) UNIQUE NOT NULL,
    user_id VARCHAR(100) NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    payment_method VARCHAR(50),
    payment_status VARCHAR(50) DEFAULT 'pending',
    shipping_address TEXT,
    shipping_city VARCHAR(100),
    shipping_suburb VARCHAR(100),
    shipping_country VARCHAR(100) DEFAULT 'Zimbabwe',
    tracking_number VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Order Items table
CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    seller_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL,
    fulfillment_status VARCHAR(50) DEFAULT 'pending',
    tracking_number VARCHAR(100),
    shipped_at TIMESTAMP,
    delivered_at TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (seller_id) REFERENCES sellers(id)
);

-- Product Reviews table
CREATE TABLE IF NOT EXISTS product_reviews (
    id SERIAL PRIMARY KEY,
    review_id VARCHAR(100) UNIQUE NOT NULL,
    product_id INTEGER NOT NULL,
    user_id VARCHAR(100) NOT NULL,
    order_id INTEGER,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    title VARCHAR(255),
    review_text TEXT,
    images TEXT,
    status VARCHAR(50) DEFAULT 'active',
    helpful_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (order_id) REFERENCES orders(id)
);

-- Seller Ratings table
CREATE TABLE IF NOT EXISTS seller_ratings (
    id SERIAL PRIMARY KEY,
    rating_id VARCHAR(100) UNIQUE NOT NULL,
    seller_id INTEGER NOT NULL,
    user_id VARCHAR(100) NOT NULL,
    order_id INTEGER,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    review_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (seller_id) REFERENCES sellers(id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (order_id) REFERENCES orders(id)
);

-- Payment Transactions table
CREATE TABLE IF NOT EXISTS payment_transactions (
    id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(100) UNIQUE NOT NULL,
    order_id INTEGER NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'ZWL',
    payment_method VARCHAR(50),
    payment_gateway VARCHAR(50),
    gateway_transaction_id VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id)
);

-- Transporters table
CREATE TABLE IF NOT EXISTS transporters (
    id SERIAL PRIMARY KEY,
    transporter_id VARCHAR(100) UNIQUE NOT NULL,
    user_id VARCHAR(100) NOT NULL,
    transport_type VARCHAR(50) NOT NULL,
    vehicle_registration VARCHAR(50),
    vehicle_make_model VARCHAR(100),
    service_type VARCHAR(50) NOT NULL,
    primary_city VARCHAR(100) NOT NULL,
    coverage_areas TEXT,
    id_number VARCHAR(50),
    drivers_license VARCHAR(50),
    police_clearance VARCHAR(100),
    clearance_issue_date VARCHAR(20),
    clearance_expiry_date VARCHAR(20),
    rating DECIMAL(3,2) DEFAULT 5.0,
    total_deliveries INTEGER DEFAULT 0,
    completed_deliveries INTEGER DEFAULT 0,
    total_earnings DECIMAL(10,2) DEFAULT 0,
    status VARCHAR(50) DEFAULT 'pending',
    verified_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Deliveries table
CREATE TABLE IF NOT EXISTS deliveries (
    id SERIAL PRIMARY KEY,
    delivery_id VARCHAR(100) UNIQUE NOT NULL,
    order_id INTEGER NOT NULL,
    transporter_id INTEGER,
    delivery_type VARCHAR(50) NOT NULL,
    pickup_address TEXT,
    pickup_city VARCHAR(100),
    pickup_suburb VARCHAR(100),
    delivery_address TEXT,
    delivery_city VARCHAR(100),
    delivery_suburb VARCHAR(100),
    distance_km DECIMAL(10,2),
    delivery_fee DECIMAL(10,2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending_assignment',
    current_location VARCHAR(255),
    tracking_notes TEXT,
    assigned_at TIMESTAMP,
    picked_up_at TIMESTAMP,
    delivered_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (transporter_id) REFERENCES transporters(id)
);

-- Seller Commissions table
CREATE TABLE IF NOT EXISTS seller_commissions (
    id SERIAL PRIMARY KEY,
    commission_id VARCHAR(100) UNIQUE NOT NULL,
    seller_id INTEGER NOT NULL,
    order_id INTEGER NOT NULL,
    order_amount DECIMAL(10,2) NOT NULL,
    commission_rate DECIMAL(5,2) DEFAULT 10.00,
    commission_amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    paid_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (seller_id) REFERENCES sellers(id),
    FOREIGN KEY (order_id) REFERENCES orders(id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_products_seller ON products(seller_id);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_status ON products(status);
CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_product_images_product ON product_images(product_id);
CREATE INDEX IF NOT EXISTS idx_deliveries_transporter ON deliveries(transporter_id);
CREATE INDEX IF NOT EXISTS idx_deliveries_status ON deliveries(status);
"""

if __name__ == '__main__':
    import os
    import psycopg2
    
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    if not DATABASE_URL:
        print("Error: DATABASE_URL environment variable not set")
        print("Set it with: $env:DATABASE_URL=\"postgresql://username:password@host:5432/dbname\"")
        exit(1)
    
    # Fix Heroku postgres:// URL
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    print(f"Connecting to PostgreSQL database...")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        print("Creating tables...")
        cursor.execute(POSTGRESQL_SCHEMA)
        conn.commit()
        
        print("✅ PostgreSQL schema created successfully!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)
