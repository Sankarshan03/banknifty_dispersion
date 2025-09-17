#!/usr/bin/env python3
"""
Quick Database Fix for BankNifty Dispersion Trade Monitor

This script immediately fixes the "no such column" errors by resetting the database.
Run this now to fix the current issue.

Usage:
    python fix_db_now.py
"""

import os
import sys
import sqlite3
from pathlib import Path

# Database path
DATABASE_PATH = 'dispersion_trade.db'

def fix_database():
    """Fix the database by dropping and recreating the historical_data table"""
    try:
        print("🔧 Fixing database schema issues...")
        
        # Check if database exists
        db_path = Path(DATABASE_PATH)
        if not db_path.exists():
            print(f"❌ Database not found at: {DATABASE_PATH}")
            return False
            
        # Connect to database
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        print("📋 Current table structure:")
        cursor.execute("PRAGMA table_info(historical_data)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        print("\n🗑️ Dropping old historical_data table...")
        cursor.execute('DROP TABLE IF EXISTS historical_data')
        
        print("🏗️ Creating new historical_data table with correct schema...")
        cursor.execute('''
            CREATE TABLE historical_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                banknifty_spot REAL,
                expiry_date TEXT,
                days_to_expiry INTEGER,
                otm_level TEXT,
                net_premium REAL,
                banknifty_straddle_premium REAL,
                total_constituent_premium REAL
            )
        ''')
        
        # Verify the new structure
        print("\n✅ New table structure:")
        cursor.execute("PRAGMA table_info(historical_data)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        conn.commit()
        conn.close()
        
        print("\n🎉 Database fixed successfully!")
        print("✅ historical_data table recreated with all required columns")
        print("✅ You can now restart your application")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing database: {str(e)}")
        return False

def main():
    print("=" * 60)
    print("BankNifty Dispersion Trade Monitor - Quick Database Fix")
    print("=" * 60)
    
    if fix_database():
        print("\n" + "=" * 60)
        print("✅ FIXED! Restart your application now:")
        print("python app.py")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ Fix failed. Try manual steps:")
        print("1. Stop the application")
        print("2. Delete dispersion_trade.db file")
        print("3. Restart the application")
        print("=" * 60)

if __name__ == "__main__":
    main()
