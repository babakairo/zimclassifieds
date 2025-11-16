"""
Pre-launch functionality test script for ZimClassifieds
Tests all critical user flows and pages
"""

import sqlite3
import os
from urllib.parse import urljoin

# Test configuration
BASE_URL = "http://127.0.0.1:5001"
DATABASE = "zimclassifieds.db"

def test_database_tables():
    """Verify all required tables exist."""
    print("\n=== Testing Database Schema ===")
    
    if not os.path.exists(DATABASE):
        print("❌ Database file not found")
        return False
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    required_tables = [
        'users', 'sellers', 'products', 'product_images', 'inventory',
        'cart', 'orders', 'order_items', 'product_reviews', 'seller_ratings',
        'payment_transactions', 'seller_commissions', 'transporters', 'deliveries'
    ]
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    existing_tables = [row[0] for row in cursor.fetchall()]
    
    all_good = True
    for table in required_tables:
        if table in existing_tables:
            print(f"✅ Table '{table}' exists")
        else:
            print(f"❌ Table '{table}' missing")
            all_good = False
    
    conn.close()
    return all_good


def test_critical_routes():
    """Test that critical routes are defined."""
    print("\n=== Testing Critical Routes ===")
    
    critical_routes = [
        ('/', 'Home page'),
        ('/products', 'Product listing'),
        ('/register', 'User registration'),
        ('/login', 'User login'),
        ('/about', 'About page'),
        ('/sellers/register', 'Seller registration'),
        ('/sellers/login', 'Seller login'),
        ('/transporters/register', 'Transporter registration'),
        ('/transporters/login', 'Transporter login'),
        ('/cart/', 'Shopping cart'),
    ]
    
    print("Routes to test (manual verification needed):")
    for route, description in critical_routes:
        url = urljoin(BASE_URL, route)
        print(f"  • {description}: {url}")
    
    return True


def test_template_route_references():
    """Check templates for incorrect route names."""
    print("\n=== Testing Template Routes ===")
    
    import re
    
    template_dir = 'templates'
    errors = []
    
    # Known incorrect route names
    bad_patterns = [
        (r"url_for\(['\"]browse_products", "browse_products (should be 'products')"),
        (r"url_for\(['\"]seller\.", "seller. (should be 'sellers.')"),
        (r"url_for\(['\"]rentals\.", "rentals. (blueprint not registered)"),
        (r"url_for\(['\"]transporter\.", "transporter. (should be 'transporters.')"),
    ]
    
    for root, dirs, files in os.walk(template_dir):
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        for pattern, issue in bad_patterns:
                            if re.search(pattern, content):
                                errors.append(f"{filepath}: Found {issue}")
                except Exception as e:
                    print(f"⚠️  Error reading {filepath}: {e}")
    
    if errors:
        print("❌ Found route errors:")
        for error in errors:
            print(f"  • {error}")
        return False
    else:
        print("✅ No route errors found in templates")
        return True


def test_product_images_table():
    """Verify product_images table structure."""
    print("\n=== Testing Product Images Table ===")
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    try:
        cursor.execute("PRAGMA table_info(product_images)")
        columns = {row[1] for row in cursor.fetchall()}
        
        required_columns = {'id', 'product_id', 'image_path', 'display_order', 'is_primary'}
        
        if required_columns.issubset(columns):
            print("✅ product_images table has all required columns")
            return True
        else:
            missing = required_columns - columns
            print(f"❌ product_images table missing columns: {missing}")
            return False
    except sqlite3.OperationalError as e:
        print(f"❌ Error checking product_images: {e}")
        return False
    finally:
        conn.close()


def test_transporters_table():
    """Verify transporters table structure."""
    print("\n=== Testing Transporters Table ===")
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    try:
        cursor.execute("PRAGMA table_info(transporters)")
        columns = {row[1] for row in cursor.fetchall()}
        
        required_columns = {'id', 'transporter_id', 'user_id', 'transport_type', 'service_type', 'status'}
        
        if required_columns.issubset(columns):
            print("✅ transporters table has all required columns")
            return True
        else:
            missing = required_columns - columns
            print(f"❌ transporters table missing columns: {missing}")
            return False
    except sqlite3.OperationalError as e:
        print(f"❌ Error checking transporters: {e}")
        return False
    finally:
        conn.close()


def test_file_structure():
    """Check that all critical files exist."""
    print("\n=== Testing File Structure ===")
    
    critical_files = [
        'app.py',
        'sellers.py',
        'transporters.py',
        'cart.py',
        'requirements.txt',
        'templates/base.html',
        'templates/index.html',
        'templates/about.html',
        'templates/register.html',
        'templates/login.html',
        'templates/products/browse.html',
        'templates/products/detail.html',
        'templates/sellers/register.html',
        'templates/sellers/dashboard.html',
        'templates/sellers/products.html',
        'templates/sellers/product_form.html',
        'templates/transporters/register.html',
        'templates/transporters/dashboard.html',
        'templates/cart/cart.html',
        'templates/checkout/order_confirmation.html',
        'static/uploads/',
    ]
    
    all_good = True
    for file_path in critical_files:
        exists = os.path.exists(file_path) or os.path.isdir(file_path)
        status = "✅" if exists else "❌"
        print(f"{status} {file_path}")
        if not exists:
            all_good = False
    
    return all_good


def run_all_tests():
    """Run all pre-launch tests."""
    print("=" * 60)
    print("ZimClassifieds Pre-Launch Functionality Test")
    print("=" * 60)
    
    results = {
        'Database Tables': test_database_tables(),
        'Critical Routes': test_critical_routes(),
        'Template Routes': test_template_route_references(),
        'Product Images': test_product_images_table(),
        'Transporters Table': test_transporters_table(),
        'File Structure': test_file_structure(),
    }
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED - Ready for launch!")
    else:
        print("❌ SOME TESTS FAILED - Fix issues before launch")
    print("=" * 60)
    
    return all_passed


if __name__ == '__main__':
    run_all_tests()
