"""
Quick database viewer for ZimClassifieds
Run: python view_database.py
"""

import sqlite3
import sys

DATABASE = 'zimclassifieds.db'

def show_tables():
    """List all tables in database."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    
    print("\n=== TABLES IN DATABASE ===")
    for idx, (table,) in enumerate(tables, 1):
        print(f"{idx}. {table}")
    
    conn.close()
    return [t[0] for t in tables]


def show_table_data(table_name, limit=10):
    """Show data from a specific table."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Get column names
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        total_rows = cursor.fetchone()[0]
        
        # Get data
        cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
        rows = cursor.fetchall()
        
        print(f"\n=== TABLE: {table_name} ===")
        print(f"Total rows: {total_rows}")
        print(f"Columns: {', '.join(columns)}")
        print(f"\nShowing first {min(limit, len(rows))} rows:\n")
        
        if rows:
            # Print header
            print(" | ".join(f"{col:15}" for col in columns))
            print("-" * (len(columns) * 17))
            
            # Print rows
            for row in rows:
                print(" | ".join(f"{str(row[col])[:15]:15}" for col in columns))
        else:
            print("(Table is empty)")
        
    except sqlite3.Error as e:
        print(f"Error: {e}")
    finally:
        conn.close()


def run_custom_query(query):
    """Run a custom SQL query."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        cursor.execute(query)
        
        if query.strip().upper().startswith('SELECT'):
            rows = cursor.fetchall()
            if rows:
                columns = rows[0].keys()
                
                print("\n=== QUERY RESULTS ===")
                print(" | ".join(f"{col:15}" for col in columns))
                print("-" * (len(columns) * 17))
                
                for row in rows:
                    print(" | ".join(f"{str(row[col])[:15]:15}" for col in columns))
                
                print(f"\nTotal rows: {len(rows)}")
            else:
                print("\nNo results found.")
        else:
            conn.commit()
            print(f"\nQuery executed successfully. Rows affected: {cursor.rowcount}")
    
    except sqlite3.Error as e:
        print(f"Error: {e}")
    finally:
        conn.close()


def interactive_mode():
    """Interactive database viewer."""
    print("=" * 60)
    print("ZimClassifieds Database Viewer")
    print("=" * 60)
    
    while True:
        print("\n\nOptions:")
        print("1. List all tables")
        print("2. View table data")
        print("3. Run custom SQL query")
        print("4. Quick stats")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            show_tables()
        
        elif choice == '2':
            tables = show_tables()
            table_choice = input("\nEnter table name or number: ").strip()
            
            if table_choice.isdigit():
                idx = int(table_choice) - 1
                if 0 <= idx < len(tables):
                    table_name = tables[idx]
                else:
                    print("Invalid table number!")
                    continue
            else:
                table_name = table_choice
            
            limit = input("How many rows to show? (default 10): ").strip()
            limit = int(limit) if limit.isdigit() else 10
            
            show_table_data(table_name, limit)
        
        elif choice == '3':
            print("\nEnter your SQL query (or 'back' to return):")
            query = input("> ").strip()
            
            if query.lower() != 'back':
                run_custom_query(query)
        
        elif choice == '4':
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            
            print("\n=== QUICK STATS ===")
            
            stats_queries = [
                ("Total Users", "SELECT COUNT(*) FROM users"),
                ("Total Sellers", "SELECT COUNT(*) FROM sellers"),
                ("Total Products", "SELECT COUNT(*) FROM products"),
                ("Total Orders", "SELECT COUNT(*) FROM orders"),
                ("Total Transporters", "SELECT COUNT(*) FROM transporters"),
                ("Total Deliveries", "SELECT COUNT(*) FROM deliveries"),
            ]
            
            for label, query in stats_queries:
                try:
                    cursor.execute(query)
                    count = cursor.fetchone()[0]
                    print(f"{label}: {count}")
                except:
                    print(f"{label}: N/A")
            
            conn.close()
        
        elif choice == '5':
            print("\nGoodbye!")
            break
        
        else:
            print("Invalid choice!")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        # Command line mode
        if sys.argv[1] == 'tables':
            show_tables()
        elif sys.argv[1] == 'view' and len(sys.argv) > 2:
            table_name = sys.argv[2]
            limit = int(sys.argv[3]) if len(sys.argv) > 3 else 10
            show_table_data(table_name, limit)
        elif sys.argv[1] == 'query' and len(sys.argv) > 2:
            query = ' '.join(sys.argv[2:])
            run_custom_query(query)
        else:
            print("Usage:")
            print("  python view_database.py                    # Interactive mode")
            print("  python view_database.py tables             # List all tables")
            print("  python view_database.py view <table> [n]   # View table data")
            print("  python view_database.py query <SQL>        # Run SQL query")
    else:
        # Interactive mode
        interactive_mode()
