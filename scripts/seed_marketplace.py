"""
Seed script to populate marketplace with sample sellers, products, and orders.
Generates realistic test data for Phase 1 e-commerce platform testing.

Run: python seed_marketplace.py
"""

import sqlite3
import uuid
from datetime import datetime, timedelta
import random

DB = 'zimclassifieds.db'

# Sample seller data
SELLERS = [
    {
        'full_name': 'TechHub Zimbabwe',
        'email': 'shop@techhub.zim',
        'phone': '+263771234567',
        'store_name': 'TechHub Zimbabwe',
        'description': 'Premium electronics and gadgets from trusted brands. Fast shipping across Zimbabwe.',
        'return_policy': '30-day money-back guarantee on all products.',
    },
    {
        'full_name': 'Fashion Forward',
        'email': 'info@fashionforward.zim',
        'phone': '+263772345678',
        'store_name': 'Fashion Forward',
        'description': 'Latest fashion trends, clothing, and accessories for men, women, and kids.',
        'return_policy': '14-day returns accepted on unused items.',
    },
    {
        'full_name': 'Home Comfort Store',
        'email': 'sales@homecomfort.zim',
        'phone': '+263773456789',
        'store_name': 'Home Comfort',
        'description': 'Quality home furnishings, bedding, kitchen, and garden supplies.',
        'return_policy': '30-day returns with proof of purchase.',
    },
    {
        'full_name': 'BookWorm Zimbabwe',
        'email': 'orders@bookworm.zim',
        'phone': '+263774567890',
        'store_name': 'BookWorm',
        'description': 'Wide selection of books, novels, textbooks, and educational materials.',
        'return_policy': '7-day returns on unopened books only.',
    },
    {
        'full_name': 'Sports Pro Equipment',
        'email': 'support@sportspro.zim',
        'phone': '+263775678901',
        'store_name': 'Sports Pro',
        'description': 'Premium sports equipment, fitness gear, and outdoor equipment.',
        'return_policy': 'Full refund within 30 days of purchase.',
    },
    {
        'full_name': 'Toy Kingdom',
        'email': 'info@toykingdom.zim',
        'phone': '+263776789012',
        'store_name': 'Toy Kingdom',
        'description': 'Safe, educational, and fun toys for children of all ages.',
        'return_policy': '30-day returns on all toy products.',
    },
]

# Sample products (category, name, price, stock)
PRODUCTS = {
    'electronics': [
        ('Samsung Galaxy A51 Phone', 350.00, 15),
        ('Wireless Earbuds Pro', 85.00, 30),
        ('USB-C Fast Charger', 25.00, 50),
        ('Power Bank 20000mAh', 45.00, 25),
        ('LED Smart Bulbs (4-pack)', 60.00, 20),
        ('Portable Bluetooth Speaker', 120.00, 18),
        ('Desktop Computer Monitor 24\"', 280.00, 8),
        ('Gaming Keyboard RGB', 95.00, 12),
        ('Wireless Mouse Combo', 35.00, 40),
        ('Laptop Stand Adjustable', 55.00, 22),
    ],
    'clothing': [
        ('Cotton T-Shirt Premium', 25.00, 60),
        ('Denim Jeans Classic Fit', 65.00, 35),
        ('Casual Sneakers Unisex', 120.00, 28),
        ('Winter Jacket Waterproof', 150.00, 12),
        ('Dress Shirt Professional', 55.00, 20),
        ('Sports Leggings High Waist', 45.00, 35),
        ('Summer Sundress Floral', 48.00, 25),
        ('Formal Business Shoes', 110.00, 15),
        ('Cotton Socks Pack (6)', 15.00, 50),
        ('Casual Hoodie Sweatshirt', 70.00, 30),
    ],
    'home': [
        ('Pillow Memory Foam Set', 85.00, 20),
        ('Bed Sheet Set Cotton', 95.00, 25),
        ('Kitchen Knife Set (6pc)', 75.00, 18),
        ('Non-Stick Cookware Set', 120.00, 15),
        ('Ceramic Dinnerware Set', 110.00, 12),
        ('Stainless Steel Cutlery', 65.00, 20),
        ('Table Lamp Modern Design', 55.00, 25),
        ('Curtain Rod Extendable', 35.00, 30),
        ('Door Mat Indoor Outdoor', 28.00, 40),
        ('Storage Shelving Unit', 145.00, 10),
    ],
    'books': [
        ('The Psychology of Money', 35.00, 20),
        ('Thinking Fast and Slow', 40.00, 15),
        ('Atomic Habits', 38.00, 25),
        ('The Lean Startup', 32.00, 12),
        ('How to Win Friends', 30.00, 18),
        ('Python Programming Guide', 55.00, 10),
        ('Business Strategy Essentials', 45.00, 14),
        ('Nutrition Science Textbook', 65.00, 8),
        ('Travel Guide Africa', 28.00, 16),
        ('Technology Innovation', 50.00, 11),
    ],
    'sports': [
        ('Yoga Mat Premium Non-Slip', 45.00, 30),
        ('Dumbbell Set 20kg', 85.00, 15),
        ('Resistance Bands Set', 28.00, 35),
        ('Running Shoes Professional', 135.00, 20),
        ('Bicycle Helmet Safety', 65.00, 25),
        ('Swimming Goggles Pro', 35.00, 20),
        ('Football Official Size', 55.00, 18),
        ('Cricket Bat Premium', 120.00, 10),
        ('Tennis Racket Beginner', 95.00, 12),
        ('Fitness Jump Rope', 25.00, 40),
    ],
    'toys': [
        ('Building Blocks Set 500pc', 42.00, 25),
        ('Remote Control Car Racing', 65.00, 18),
        ('Puzzle 1000 Pieces Scenic', 22.00, 30),
        ('Action Figures Pack (6)', 38.00, 20),
        ('Board Game Family Fun', 45.00, 22),
        ('Doll House Miniature Kit', 75.00, 12),
        ('Toy Robot Interactive', 85.00, 15),
        ('Bicycle Kids 20\" Blue', 145.00, 10),
        ('Scooter Trick Stunt', 95.00, 14),
        ('Art Supplies Set Deluxe', 55.00, 25),
    ],
}

# Sample customer data
CUSTOMERS = [
    {'full_name': 'John Mwangi', 'email': 'john@example.com', 'address': '123 Main Street', 'location': 'Harare'},
    {'full_name': 'Sarah Nyoni', 'email': 'sarah@example.com', 'address': '456 Oak Avenue', 'location': 'Bulawayo'},
    {'full_name': 'David Mutendi', 'email': 'david@example.com', 'address': '789 Pine Road', 'location': 'Mutare'},
    {'full_name': 'Grace Chiparwa', 'email': 'grace@example.com', 'address': '321 Elm Street', 'location': 'Gweru'},
    {'full_name': 'James Muchenje', 'email': 'james@example.com', 'address': '654 Maple Drive', 'location': 'Kwekwe'},
]


def seed_marketplace():
    """Create marketplace sample data."""
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("🌱 Seeding marketplace data...")
    
    # 1. Create sellers
    seller_ids = []
    for seller_data in SELLERS:
        seller_id = str(uuid.uuid4())
        seller_ids.append(seller_id)
        
        cursor.execute('''
            INSERT INTO sellers (id, full_name, email, phone, store_name, description, 
                                return_policy, slug, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            seller_id,
            seller_data['full_name'],
            seller_data['email'],
            seller_data['phone'],
            seller_data['store_name'],
            seller_data['description'],
            seller_data['return_policy'],
            seller_data['store_name'].lower().replace(' ', '-'),
            datetime.now().isoformat()
        ))
        print(f"✓ Created seller: {seller_data['store_name']}")
    
    # 2. Create products
    product_ids_by_seller = {seller_id: [] for seller_id in seller_ids}
    
    for category, products in PRODUCTS.items():
        for i, (name, price, stock) in enumerate(products):
            seller_id = seller_ids[i % len(seller_ids)]  # Distribute products across sellers
            product_id = str(uuid.uuid4())
            product_ids_by_seller[seller_id].append(product_id)
            
            cursor.execute('''
                INSERT INTO products (id, name, description, category, price, stock_quantity, 
                                     seller_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                product_id,
                name,
                f"High-quality {category} product. Fast shipping available.",
                category,
                price,
                stock,
                seller_id,
                datetime.now().isoformat()
            ))
            
            # Create inventory record
            inventory_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO inventory (id, product_id, seller_id, quantity_on_hand, 
                                      quantity_reserved, reorder_level, last_restocked)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                inventory_id,
                product_id,
                seller_id,
                stock,
                0,
                10,
                datetime.now().isoformat()
            ))
    
    print(f"✓ Created {sum(len(p) for p in PRODUCTS.values())} products across {len(seller_ids)} sellers")
    
    # 3. Create sample customers
    customer_user_ids = []
    for customer_data in CUSTOMERS:
        user_id = str(uuid.uuid4())
        customer_user_ids.append(user_id)
        
        cursor.execute('''
            INSERT INTO users (user_id, full_name, email, phone, address, location, 
                              created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            customer_data['full_name'],
            customer_data['email'],
            '+263777' + str(random.randint(1000000, 9999999)),
            customer_data['address'],
            customer_data['location'],
            datetime.now().isoformat()
        ))
        print(f"✓ Created customer: {customer_data['full_name']}")
    
    # 4. Create sample orders
    for customer_idx, customer_user_id in enumerate(customer_user_ids):
        num_orders = random.randint(1, 3)
        
        for order_num in range(num_orders):
            order_id = str(uuid.uuid4())
            order_number = f"ORD-{int(datetime.now().timestamp())}{order_num:02d}"
            
            # Select 1-3 random products
            selected_sellers = random.sample(seller_ids, min(2, len(seller_ids)))
            total_amount = 0
            
            created_ago = timedelta(days=random.randint(0, 30))
            order_created = datetime.now() - created_ago
            
            cursor.execute('''
                INSERT INTO orders (order_id, user_id, order_number, total_amount, 
                                   shipping_address, shipping_city, shipping_suburb, 
                                   shipping_cost, payment_method, payment_status, status, 
                                   created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                order_id,
                customer_user_id,
                order_number,
                500,  # Will update after adding items
                '123 Test Street',
                CUSTOMERS[customer_idx]['location'],
                CUSTOMERS[customer_idx]['location'],
                0,
                random.choice(['stripe_card', 'bank_transfer', 'cod']),
                'paid',
                random.choice(['pending', 'processing', 'shipped', 'completed']),
                order_created.isoformat()
            ))
            
            # Get order internal ID
            order_data = cursor.execute(
                'SELECT id FROM orders WHERE order_id = ?', (order_id,)
            ).fetchone()
            order_internal_id = order_data['id']
            
            # Add 1-3 items to order
            for _ in range(random.randint(1, 3)):
                seller_id = random.choice(selected_sellers)
                if product_ids_by_seller[seller_id]:
                    product_id = random.choice(product_ids_by_seller[seller_id])
                    
                    # Get product details
                    product = cursor.execute(
                        'SELECT price FROM products WHERE id = ?', (product_id,)
                    ).fetchone()
                    
                    quantity = random.randint(1, 3)
                    unit_price = product['price']
                    subtotal = unit_price * quantity
                    total_amount += subtotal
                    
                    order_item_id = str(uuid.uuid4())
                    cursor.execute('''
                        INSERT INTO order_items (order_item_id, order_id, product_id, 
                                                seller_id, quantity, unit_price, subtotal, 
                                                fulfillment_status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        order_item_id,
                        order_internal_id,
                        product_id,
                        seller_id,
                        quantity,
                        unit_price,
                        subtotal,
                        random.choice(['pending', 'processing', 'shipped', 'delivered'])
                    ))
            
            # Update order total and create payment transaction
            cursor.execute(
                'UPDATE orders SET total_amount = ? WHERE id = ?',
                (total_amount, order_internal_id)
            )
            
            transaction_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO payment_transactions (transaction_id, order_id, user_id, amount, 
                                                 payment_method, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                transaction_id,
                order_internal_id,
                customer_user_id,
                total_amount,
                random.choice(['stripe_card', 'bank_transfer', 'cod']),
                'completed',
                order_created.isoformat()
            ))
    
    print(f"✓ Created {len(customer_user_ids) * 2} sample orders")
    
    # 5. Add sample reviews
    for customer_idx, customer_user_id in enumerate(customer_user_ids):
        # Product reviews
        for _ in range(random.randint(2, 5)):
            product_id = random.choice([p for products in product_ids_by_seller.values() for p in products])
            
            cursor.execute('''
                INSERT INTO product_reviews (id, product_id, user_id, rating, title, comment, 
                                            helpful_count, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                str(uuid.uuid4()),
                product_id,
                customer_user_id,
                random.randint(3, 5),
                random.choice(['Great product!', 'Excellent quality', 'Highly recommended', 'Good value']),
                'Quick delivery and great packaging. Very satisfied with this purchase.',
                random.randint(0, 10),
                (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat()
            ))
        
        # Seller reviews
        for _ in range(random.randint(1, 3)):
            seller_id = random.choice(seller_ids)
            
            cursor.execute('''
                INSERT INTO seller_ratings (id, seller_id, user_id, rating, comment, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                str(uuid.uuid4()),
                seller_id,
                customer_user_id,
                random.randint(4, 5),
                'Excellent seller, fast shipping.',
                (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat()
            ))
    
    print("✓ Created product and seller reviews")
    
    # Commit all changes
    conn.commit()
    conn.close()
    
    print("\n✅ Marketplace seeding complete!")
    print(f"   - {len(SELLERS)} sellers")
    print(f"   - {sum(len(p) for p in PRODUCTS.values())} products")
    print(f"   - {len(CUSTOMERS)} customers")
    print(f"   - {len(CUSTOMERS) * 2} sample orders")
    print("\n📝 Sample login credentials:")
    print("   Email: john@example.com")
    print("   (No password required - set up as needed)\n")


if __name__ == '__main__':
    try:
        seed_marketplace()
    except Exception as e:
        print(f"\n❌ Error seeding marketplace: {e}")
        import traceback
        traceback.print_exc()
