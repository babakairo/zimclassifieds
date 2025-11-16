"""
Migrate data from SQLite to PostgreSQL
"""
import os
import sys
import sqlite3
import psycopg2
from psycopg2.extras import execute_values

# Tables to migrate in order (respecting foreign keys)
TABLES_ORDER = [
    'users',
    'sellers',
    'products',
    'product_images',
    'inventory',
    'cart',
    'orders',
    'order_items',
    'product_reviews',
    'seller_ratings',
    'payment_transactions',
    'transporters',
    'deliveries',
    'seller_commissions'
]

# Column type conversions
TYPE_CONVERSIONS = {
    'INTEGER': 'INT',
    'REAL': 'DECIMAL',
    'TEXT': 'TEXT',
    'TIMESTAMP': 'TIMESTAMP',
    'BOOLEAN': 'BOOLEAN'
}


def connect_sqlite(db_file='zimclassifieds.db'):
    """Connect to SQLite database."""
    if not os.path.exists(db_file):
        print(f"❌ Error: SQLite database '{db_file}' not found")
        return None
    
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    return conn


def connect_postgres():
    """Connect to PostgreSQL database."""
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    if not DATABASE_URL:
        print("❌ Error: DATABASE_URL environment variable not set")
        print("Set it with: $env:DATABASE_URL=\"postgresql://username:password@host:5432/dbname\"")
        return None
    
    # Fix Heroku postgres:// URL
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"❌ Error connecting to PostgreSQL: {e}")
        return None


def get_table_columns(sqlite_cursor, table_name):
    """Get column names for a table."""
    sqlite_cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in sqlite_cursor.fetchall()]
    return columns


def migrate_table(sqlite_conn, pg_conn, table_name):
    """Migrate a single table from SQLite to PostgreSQL."""
    print(f"\n📋 Migrating table: {table_name}")
    
    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()
    
    try:
        # Get column names
        columns = get_table_columns(sqlite_cursor, table_name)
        
        # Fetch all data from SQLite
        sqlite_cursor.execute(f"SELECT * FROM {table_name}")
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            print(f"   ⚠️  Table '{table_name}' is empty, skipping...")
            return 0
        
        # Convert SQLite rows to list of tuples
        data = []
        for row in rows:
            row_data = []
            for col in columns:
                value = row[col]
                # Convert SQLite boolean (0/1) to PostgreSQL boolean
                if isinstance(value, int) and col.endswith('_verified') or col.startswith('is_') or col == 'email_verified':
                    value = bool(value)
                row_data.append(value)
            data.append(tuple(row_data))
        
        # Prepare insert query
        columns_str = ', '.join(columns)
        placeholders = ', '.join(['%s'] * len(columns))
        
        # Clear existing data (optional - comment out if you want to append)
        pg_cursor.execute(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE")
        
        # Insert data in batches
        insert_query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
        execute_values(pg_cursor, insert_query, data, page_size=100)
        
        pg_conn.commit()
        
        print(f"   ✅ Migrated {len(data)} rows")
        return len(data)
        
    except Exception as e:
        print(f"   ❌ Error migrating {table_name}: {e}")
        pg_conn.rollback()
        return 0
    finally:
        sqlite_cursor.close()
        pg_cursor.close()


def reset_sequences(pg_conn):
    """Reset PostgreSQL sequences after data migration."""
    print("\n🔄 Resetting PostgreSQL sequences...")
    
    cursor = pg_conn.cursor()
    
    for table in TABLES_ORDER:
        try:
            cursor.execute(f"""
                SELECT setval(pg_get_serial_sequence('{table}', 'id'), 
                              COALESCE(MAX(id), 1), 
                              MAX(id) IS NOT NULL)
                FROM {table};
            """)
            result = cursor.fetchone()
            if result:
                print(f"   ✅ Reset sequence for {table}: {result[0]}")
        except Exception as e:
            print(f"   ⚠️  Could not reset sequence for {table}: {e}")
    
    pg_conn.commit()
    cursor.close()


def verify_migration(sqlite_conn, pg_conn):
    """Verify that migration was successful."""
    print("\n🔍 Verifying migration...")
    
    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()
    
    all_match = True
    
    for table in TABLES_ORDER:
        try:
            # Count rows in SQLite
            sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
            sqlite_count = sqlite_cursor.fetchone()[0]
            
            # Count rows in PostgreSQL
            pg_cursor.execute(f"SELECT COUNT(*) FROM {table}")
            pg_count = pg_cursor.fetchone()[0]
            
            if sqlite_count == pg_count:
                print(f"   ✅ {table}: {sqlite_count} rows (matched)")
            else:
                print(f"   ❌ {table}: SQLite={sqlite_count}, PostgreSQL={pg_count} (MISMATCH)")
                all_match = False
        except Exception as e:
            print(f"   ⚠️  Could not verify {table}: {e}")
    
    sqlite_cursor.close()
    pg_cursor.close()
    
    return all_match


def main():
    """Main migration function."""
    print("=" * 60)
    print("SQLite to PostgreSQL Migration Tool")
    print("=" * 60)
    
    # Connect to databases
    print("\n📡 Connecting to databases...")
    
    sqlite_conn = connect_sqlite()
    if not sqlite_conn:
        return
    print("   ✅ Connected to SQLite")
    
    pg_conn = connect_postgres()
    if not pg_conn:
        sqlite_conn.close()
        return
    print("   ✅ Connected to PostgreSQL")
    
    # Confirm migration
    print("\n⚠️  WARNING: This will TRUNCATE all PostgreSQL tables and migrate data from SQLite.")
    confirm = input("   Do you want to continue? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("\n❌ Migration cancelled.")
        sqlite_conn.close()
        pg_conn.close()
        return
    
    # Migrate tables
    print("\n🚀 Starting migration...")
    total_rows = 0
    
    for table in TABLES_ORDER:
        try:
            rows = migrate_table(sqlite_conn, pg_conn, table)
            total_rows += rows
        except Exception as e:
            print(f"   ❌ Failed to migrate {table}: {e}")
            continue
    
    # Reset sequences
    reset_sequences(pg_conn)
    
    # Verify migration
    all_match = verify_migration(sqlite_conn, pg_conn)
    
    # Close connections
    sqlite_conn.close()
    pg_conn.close()
    
    # Summary
    print("\n" + "=" * 60)
    if all_match:
        print("✅ Migration completed successfully!")
        print(f"📊 Total rows migrated: {total_rows}")
    else:
        print("⚠️  Migration completed with warnings")
        print("   Please check the mismatched tables above")
    print("=" * 60)


if __name__ == '__main__':
    main()
