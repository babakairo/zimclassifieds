"""
Quick PostgreSQL Setup Script
Run this after setting DATABASE_URL environment variable
"""
import os
import sys

def check_database_url():
    """Check if DATABASE_URL is set."""
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("❌ DATABASE_URL environment variable not set")
        print("\nSet it with:")
        print('  PowerShell: $env:DATABASE_URL="postgresql://username:password@host:5432/dbname"')
        print('  Or for Heroku: heroku config:get DATABASE_URL')
        return False
    
    if db_url.startswith('postgres://'):
        print("⚠️  Fixing Heroku DATABASE_URL format...")
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
        os.environ['DATABASE_URL'] = db_url
    
    print(f"✅ DATABASE_URL: {db_url[:30]}...")
    return True


def check_dependencies():
    """Check if required packages are installed."""
    try:
        import psycopg2
        print("✅ psycopg2 installed")
        return True
    except ImportError:
        print("❌ psycopg2 not installed")
        print("\nInstall with: pip install psycopg2-binary")
        return False


def test_connection():
    """Test PostgreSQL connection."""
    try:
        from database import get_db, DB_TYPE
        
        if DB_TYPE != 'postgresql':
            print(f"⚠️  Warning: Using {DB_TYPE} instead of PostgreSQL")
            return False
        
        db = get_db()
        print("✅ PostgreSQL connection successful")
        db.close()
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


def create_schema():
    """Create database tables."""
    print("\n📋 Creating database tables...")
    try:
        from create_postgres_schema import POSTGRESQL_SCHEMA
        import psycopg2
        
        db_url = os.environ.get('DATABASE_URL')
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        cursor.execute(POSTGRESQL_SCHEMA)
        conn.commit()
        
        cursor.close()
        conn.close()
        
        print("✅ Tables created successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        return False


def main():
    """Run setup wizard."""
    print("=" * 60)
    print("PostgreSQL Setup Wizard")
    print("=" * 60)
    
    print("\n1️⃣ Checking DATABASE_URL...")
    if not check_database_url():
        return
    
    print("\n2️⃣ Checking dependencies...")
    if not check_dependencies():
        return
    
    print("\n3️⃣ Testing connection...")
    if not test_connection():
        return
    
    print("\n4️⃣ Create database tables?")
    choice = input("   (yes/no): ").strip().lower()
    
    if choice == 'yes':
        if create_schema():
            print("\n" + "=" * 60)
            print("✅ PostgreSQL setup complete!")
            print("\nYou can now:")
            print("  1. Run the app: python app.py")
            print("  2. Migrate data: python migrate_to_postgres.py")
            print("  3. View database: python view_database.py")
            print("=" * 60)
        else:
            print("\n❌ Setup incomplete - please fix errors and try again")
    else:
        print("\n✅ Connection verified - you can create tables later with:")
        print("   python create_postgres_schema.py")


if __name__ == '__main__':
    main()
