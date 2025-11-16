"""
Migration script to add police clearance columns to transporters table.
Run this to update existing databases with the new police clearance requirement.
"""

import sqlite3
import os

def migrate_sqlite():
    """Add police clearance columns to SQLite database."""
    db_file = 'zimclassifieds.db'
    
    if not os.path.exists(db_file):
        print(f"❌ Database file '{db_file}' not found")
        return False
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(transporters)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'police_clearance' in columns:
            print("✅ Police clearance columns already exist")
            conn.close()
            return True
        
        print("Adding police clearance columns to transporters table...")
        
        # Add new columns
        cursor.execute('''
            ALTER TABLE transporters 
            ADD COLUMN police_clearance TEXT
        ''')
        
        cursor.execute('''
            ALTER TABLE transporters 
            ADD COLUMN clearance_issue_date TEXT
        ''')
        
        cursor.execute('''
            ALTER TABLE transporters 
            ADD COLUMN clearance_expiry_date TEXT
        ''')
        
        conn.commit()
        conn.close()
        
        print("✅ Successfully added police clearance columns to SQLite database")
        return True
        
    except sqlite3.Error as e:
        print(f"❌ SQLite error: {e}")
        return False


def migrate_postgres():
    """Add police clearance columns to PostgreSQL database."""
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
    except ImportError:
        print("⚠️  psycopg2 not installed. Run: pip install psycopg2-binary")
        return False
    
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("⚠️  DATABASE_URL not set. Skipping PostgreSQL migration.")
        return False
    
    # Fix Heroku postgres:// to postgresql://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    try:
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='transporters' AND column_name='police_clearance'
        """)
        
        if cursor.fetchone():
            print("✅ Police clearance columns already exist in PostgreSQL")
            conn.close()
            return True
        
        print("Adding police clearance columns to transporters table...")
        
        # Add new columns
        cursor.execute('''
            ALTER TABLE transporters 
            ADD COLUMN police_clearance VARCHAR(100)
        ''')
        
        cursor.execute('''
            ALTER TABLE transporters 
            ADD COLUMN clearance_issue_date VARCHAR(20)
        ''')
        
        cursor.execute('''
            ALTER TABLE transporters 
            ADD COLUMN clearance_expiry_date VARCHAR(20)
        ''')
        
        conn.commit()
        conn.close()
        
        print("✅ Successfully added police clearance columns to PostgreSQL database")
        return True
        
    except psycopg2.Error as e:
        print(f"❌ PostgreSQL error: {e}")
        return False


if __name__ == '__main__':
    print("=" * 60)
    print("Police Clearance Migration Script")
    print("=" * 60)
    print()
    
    # Migrate SQLite
    print("Checking SQLite database...")
    migrate_sqlite()
    print()
    
    # Migrate PostgreSQL if DATABASE_URL is set
    print("Checking PostgreSQL database...")
    migrate_postgres()
    print()
    
    print("=" * 60)
    print("Migration complete!")
    print("=" * 60)
