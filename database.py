"""
Database Configuration - Supports both SQLite and PostgreSQL
"""
import os
import sys

# Detect database type from environment
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL and DATABASE_URL.startswith('postgres'):
    # PostgreSQL configuration
    DB_TYPE = 'postgresql'
    
    # Fix Heroku postgres:// to postgresql://
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
    except ImportError:
        print("Error: psycopg2 not installed. Run: pip install psycopg2-binary")
        sys.exit(1)
    
    def get_db():
        """Get PostgreSQL database connection."""
        conn = psycopg2.connect(DATABASE_URL, sslmode='require' if 'amazonaws.com' in DATABASE_URL or 'heroku' in DATABASE_URL else 'prefer')
        conn.cursor_factory = RealDictCursor
        return conn
    
    def dict_factory(cursor, row):
        """Convert PostgreSQL row to dict."""
        return dict(row)
    
else:
    # SQLite configuration (default for development)
    DB_TYPE = 'sqlite'
    DATABASE_FILE = 'zimclassifieds.db'
    
    import sqlite3
    
    def get_db():
        """Get SQLite database connection."""
        db = sqlite3.connect(DATABASE_FILE)
        db.row_factory = sqlite3.Row
        return db
    
    def dict_factory(cursor, row):
        """Convert SQLite row to dict."""
        return {key: row[key] for key in row.keys()}


def execute_query(query, params=None):
    """
    Execute a query and return results.
    Handles differences between SQLite and PostgreSQL.
    """
    db = get_db()
    
    if DB_TYPE == 'postgresql':
        # PostgreSQL uses %s for placeholders
        query = query.replace('?', '%s')
        cursor = db.cursor()
        cursor.execute(query, params or ())
        
        if query.strip().upper().startswith('SELECT'):
            results = cursor.fetchall()
        else:
            db.commit()
            results = None
        
        cursor.close()
        db.close()
        return results
    else:
        # SQLite uses ?
        cursor = db.cursor()
        cursor.execute(query, params or ())
        
        if query.strip().upper().startswith('SELECT'):
            results = cursor.fetchall()
        else:
            db.commit()
            results = None
        
        cursor.close()
        db.close()
        return results


def get_placeholder():
    """Get the correct placeholder for the database type."""
    return '%s' if DB_TYPE == 'postgresql' else '?'


# Export configuration
__all__ = ['get_db', 'DB_TYPE', 'DATABASE_URL', 'execute_query', 'get_placeholder']
