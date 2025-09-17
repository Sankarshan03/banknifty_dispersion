# config.py - Configuration and Constants for BankNifty Dispersion Trade Monitor
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Zerodha API Configuration
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
REQUEST_TOKEN = os.getenv("REQUEST_TOKEN")
TOTP_SECRET = os.getenv("TOTP_SECRET")

if not all([API_KEY, API_SECRET]):
    raise ValueError("API_KEY and API_SECRET must be set in environment variables")

# Database Configuration
DATABASE_PATH = 'dispersion_trade.db'

# WebSocket Configuration
MAX_RECONNECT_ATTEMPTS = 5
RECONNECT_DELAY = 5
CONNECTION_TIMEOUT = 60  # seconds

# Data Update Configuration
DATA_UPDATE_INTERVAL = 30  # seconds
MONITORING_DAYS_BEFORE_EXPIRY = 45

# Enhanced BankNifty constituents with accurate weights and lot sizes
BANKNIFTY_CONSTITUENTS = [
    {'symbol': 'HDFCBANK', 'weight': 0.2861, 'lot_size': 550, 'instrument_token': 341249},
    {'symbol': 'ICICIBANK', 'weight': 0.2605, 'lot_size': 1375, 'instrument_token': 1270529},
    {'symbol': 'SBIN', 'weight': 0.0911, 'lot_size': 1500, 'instrument_token': 779521},
    {'symbol': 'KOTAKBANK', 'weight': 0.0810, 'lot_size': 400, 'instrument_token': 492033},
    {'symbol': 'AXISBANK', 'weight': 0.0782, 'lot_size': 1200, 'instrument_token': 1510401},
    {'symbol': 'INDUSINDBK', 'weight': 0.0337, 'lot_size': 900, 'instrument_token': 1346049},
    {'symbol': 'FEDERALBNK', 'weight': 0.0325, 'lot_size': 10000, 'instrument_token': 1023745},
    {'symbol': 'IDFCFIRSTB', 'weight': 0.0311, 'lot_size': 6250, 'instrument_token': 2863105},
    {'symbol': 'BANKBARODA', 'weight': 0.0298, 'lot_size': 2700, 'instrument_token': 1195009},
    {'symbol': 'AUBANK', 'weight': 0.0279, 'lot_size': 1800, 'instrument_token': 108033}
]

# BankNifty index details
BANKNIFTY_TOKEN = 260105
BANKNIFTY_LOT_SIZE = 15

# OTM Levels
OTM_LEVELS = ['ATM', 'OTM1', 'OTM2', 'OTM3']

# Default Settings
DEFAULT_SETTINGS = {
    'alert_threshold': 10000,
    'monitoring_days': MONITORING_DAYS_BEFORE_EXPIRY,
    'selected_otm_level': 'ATM',
    'auto_alerts_enabled': True
}

# Flask Configuration
FLASK_SECRET_KEY = 'banknifty_dispersion_secret_key_2025'
FLASK_DEBUG = False
FLASK_HOST = '127.0.0.1'
FLASK_PORTS = [5000, 5001, 5002, 8000, 8080]

# Logging Configuration
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Data Structure Template
INITIAL_DATA_STRUCTURE = {
    'banknifty': {
        'spot': 0,
        'atm_strike': 0,
        'otm_levels': {level: {'call_premium': 0, 'put_premium': 0, 'straddle_premium': 0} for level in OTM_LEVELS}
    },
    'constituents': {},
    'net_premium': {level: 0 for level in OTM_LEVELS},
    'last_updated': None,
    'normalized_lots': {},
    'expiry_date': None,
    'days_to_expiry': 0,
    'monitoring_active': False
}
