#!/usr/bin/env python3
"""
Database Reset Utility for BankNifty Dispersion Trade Monitor

This script helps resolve database schema issues by resetting the database.
Run this if you encounter "table has no column named" errors.

Usage:
    python reset_db.py
"""

import os
import sys
import logging
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from database import DatabaseManager
    from config import DATABASE_PATH
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running this script from the correct directory.")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main function to reset the database"""
    print("=" * 60)
    print("BankNifty Dispersion Trade Monitor - Database Reset Utility")
    print("=" * 60)
    
    # Check if database file exists
    db_path = Path(DATABASE_PATH)
    if db_path.exists():
        print(f"Found existing database: {DATABASE_PATH}")
        print(f"Database size: {db_path.stat().st_size} bytes")
    else:
        print(f"No existing database found at: {DATABASE_PATH}")
    
    # Confirm reset
    print("\nThis will:")
    print("1. Drop all existing tables (historical_data, alerts, settings)")
    print("2. Recreate tables with the correct schema")
    print("3. Initialize default settings")
    print("\nWARNING: All historical data and alerts will be lost!")
    
    response = input("\nDo you want to continue? (yes/no): ").lower().strip()
    
    if response not in ['yes', 'y']:
        print("Database reset cancelled.")
        return
    
    try:
        print("\nResetting database...")
        
        # Create database manager and reset
        db_manager = DatabaseManager()
        db_manager.reset_database()
        
        print("✅ Database reset completed successfully!")
        print(f"✅ New database created at: {DATABASE_PATH}")
        print("✅ All tables recreated with correct schema")
        print("✅ Default settings initialized")
        
        # Verify the reset
        print("\nVerifying database structure...")
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"✅ Tables created: {', '.join(tables)}")
        
        # Check historical_data columns
        cursor.execute("PRAGMA table_info(historical_data)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"✅ Historical data columns: {', '.join(columns)}")
        
        conn.close()
        
        print("\n" + "=" * 60)
        print("Database reset completed! You can now run the application:")
        print("python app.py")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"Error during database reset: {str(e)}")
        print(f"\n❌ Database reset failed: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Make sure no other instances of the app are running")
        print("2. Check file permissions")
        print("3. Try deleting the database file manually and restart the app")
        sys.exit(1)

if __name__ == "__main__":
    main()
