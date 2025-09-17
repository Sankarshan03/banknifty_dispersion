# database.py - Database Operations for BankNifty Dispersion Trade Monitor
import sqlite3
import logging
from datetime import datetime
from collections import defaultdict
from config import DATABASE_PATH, OTM_LEVELS, DEFAULT_SETTINGS

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Handles all database operations for the dispersion trade monitor"""
    
    def __init__(self, db_path=DATABASE_PATH):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Initialize SQLite database with required tables"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Historical data table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS historical_data (
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
            
            # Check and add missing columns to existing table
            self._migrate_historical_data_table(cursor)
            
            # Alerts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    otm_level TEXT,
                    net_premium REAL,
                    threshold REAL,
                    message TEXT
                )
            ''')
            
            # Settings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY,
                    alert_threshold REAL DEFAULT 10000,
                    monitoring_days INTEGER DEFAULT 45,
                    selected_otm_level TEXT DEFAULT 'ATM',
                    auto_alerts_enabled BOOLEAN DEFAULT 1
                )
            ''')
            
            # Insert default settings if not exists
            cursor.execute('INSERT OR IGNORE INTO settings (id) VALUES (1)')
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            raise
    
    def _migrate_historical_data_table(self, cursor):
        """Migrate historical_data table to add missing columns"""
        try:
            # Get current table schema
            cursor.execute("PRAGMA table_info(historical_data)")
            columns = [row[1] for row in cursor.fetchall()]
            
            # Add missing columns - COMPLETE LIST
            required_columns = [
                ('expiry_date', 'TEXT'),
                ('days_to_expiry', 'INTEGER'),
                ('otm_level', 'TEXT'),
                ('net_premium', 'REAL'),
                ('banknifty_straddle_premium', 'REAL'),
                ('total_constituent_premium', 'REAL')
            ]
            
            for column_name, column_type in required_columns:
                if column_name not in columns:
                    cursor.execute(f'ALTER TABLE historical_data ADD COLUMN {column_name} {column_type}')
                    logger.info(f"Added missing column: {column_name}")
                    
        except Exception as e:
            logger.warning(f"Error during table migration: {str(e)}")
            # If migration fails, suggest reset
            logger.warning("Consider running 'python reset_db.py' to fix database schema issues")
    
    def store_historical_data(self, current_data):
        """Store current data in database with error handling"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Check if required data exists
            if not current_data or 'banknifty' not in current_data:
                logger.warning("No valid data to store")
                conn.close()
                return
            
            for otm_level in OTM_LEVELS:
                try:
                    # Use safer data extraction with defaults
                    banknifty_spot = current_data.get('banknifty', {}).get('spot', 0)
                    expiry_date = current_data.get('expiry_date', '')
                    days_to_expiry = current_data.get('days_to_expiry', 0)
                    net_premium = current_data.get('net_premium', {}).get(otm_level, 0)
                    straddle_premium = current_data.get('banknifty', {}).get('otm_levels', {}).get(otm_level, {}).get('straddle_premium', 0)
                    
                    cursor.execute('''
                        INSERT INTO historical_data 
                        (banknifty_spot, expiry_date, days_to_expiry, otm_level, net_premium, 
                         banknifty_straddle_premium, total_constituent_premium)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        banknifty_spot,
                        expiry_date,
                        days_to_expiry,
                        otm_level,
                        net_premium,
                        straddle_premium,
                        0  # Will calculate this properly if needed
                    ))
                except Exception as level_error:
                    logger.warning(f"Error storing data for {otm_level}: {str(level_error)}")
                    continue
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error storing historical data: {str(e)}")
            # Don't raise the exception to prevent app crash
            logger.info("Continuing without storing historical data")
    
    def get_historical_data(self, limit=1000):
        """Get historical data from database"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT timestamp, banknifty_spot, otm_level, net_premium
                FROM historical_data
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            # Convert to structured format
            historical = defaultdict(list)
            for row in rows:
                timestamp, spot, otm_level, net_premium = row
                historical[otm_level].append({
                    'timestamp': timestamp,
                    'banknifty_spot': spot,
                    'net_premium': net_premium
                })
            
            return dict(historical)
            
        except Exception as e:
            logger.error(f"Error fetching historical data: {str(e)}")
            return {}
    
    def store_alert(self, otm_level, net_premium, threshold, message):
        """Store alert in database"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO alerts (otm_level, net_premium, threshold, message)
                VALUES (?, ?, ?, ?)
            ''', (otm_level, net_premium, threshold, message))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error storing alert: {str(e)}")
    
    def get_alerts(self, limit=50):
        """Get recent alerts"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT timestamp, otm_level, net_premium, threshold, message
                FROM alerts
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            alerts = [
                {
                    'timestamp': row[0],
                    'otm_level': row[1],
                    'net_premium': row[2],
                    'threshold': row[3],
                    'message': row[4]
                }
                for row in rows
            ]
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error fetching alerts: {str(e)}")
            return []
    
    def get_settings(self):
        """Get application settings"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM settings WHERE id = 1')
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'alert_threshold': row[1],
                    'monitoring_days': row[2],
                    'selected_otm_level': row[3],
                    'auto_alerts_enabled': bool(row[4])
                }
            else:
                return DEFAULT_SETTINGS
                
        except Exception as e:
            logger.error(f"Error fetching settings: {str(e)}")
            return DEFAULT_SETTINGS
    
    def update_settings(self, settings):
        """Update application settings"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE settings SET
                alert_threshold = ?,
                monitoring_days = ?,
                selected_otm_level = ?,
                auto_alerts_enabled = ?
                WHERE id = 1
            ''', (
                settings.get('alert_threshold', DEFAULT_SETTINGS['alert_threshold']),
                settings.get('monitoring_days', DEFAULT_SETTINGS['monitoring_days']),
                settings.get('selected_otm_level', DEFAULT_SETTINGS['selected_otm_level']),
                settings.get('auto_alerts_enabled', DEFAULT_SETTINGS['auto_alerts_enabled'])
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error updating settings: {str(e)}")
            raise
    
    def export_data_to_csv(self, otm_level):
        """Export historical data for specific OTM level"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT timestamp, banknifty_spot, net_premium, banknifty_straddle_premium
                FROM historical_data
                WHERE otm_level = ?
                ORDER BY timestamp DESC
            ''', (otm_level,))
            
            rows = cursor.fetchall()
            conn.close()
            
            return rows
            
        except Exception as e:
            logger.error(f"Error exporting data: {str(e)}")
            return []

# Global database manager instance
db_manager = DatabaseManager()
