# app.py
from flask import Flask, jsonify, request, render_template, session, redirect
from flask_cors import CORS
from flask_socketio import SocketIO
from kiteconnect import KiteConnect, KiteTicker
import logging
import threading
import time
from datetime import datetime, timedelta
import json
import pandas as pd
import sqlite3
import os
from functools import wraps

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'banknifty_dispersion_secret_key_2025'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Zerodha API Configuration
API_KEY = "myh2vafxnb137700"
API_SECRET = "7ayjvayso5ma6y8dyp0ad64i8ybh06mc"
REDIRECT_URL = "http://127.0.0.1:5000/"

# Initialize KiteConnect
kite = KiteConnect(api_key=API_KEY)

# Global variables
access_token = None
kws = None
current_data = {
    'banknifty': {'spot': 0, 'atm_strike': 0, 'call_premium': 0, 'put_premium': 0, 'straddle_premium': 0},
    'constituents': {},
    'net_premium': 0,
    'last_updated': None,
    'normalized_lots': {}
}
historical_data = []
alerts = []
is_connected = False

# BankNifty constituents with weights and instrument tokens
BANKNIFTY_CONSTITUENTS = [
    {'symbol': 'HDFCBANK', 'weight': 0.25, 'lot_size': 15, 'instrument_token': 341249},
    {'symbol': 'ICICIBANK', 'weight': 0.20, 'lot_size': 25, 'instrument_token': 1270529},
    {'symbol': 'KOTAKBANK', 'weight': 0.15, 'lot_size': 15, 'instrument_token': 492033},
    {'symbol': 'AXISBANK', 'weight': 0.14, 'lot_size': 15, 'instrument_token': 1510401},
    {'symbol': 'SBIN', 'weight': 0.13, 'lot_size': 15, 'instrument_token': 779521},
    {'symbol': 'INDUSINDBK', 'weight': 0.06, 'lot_size': 20, 'instrument_token': 1346049},
    {'symbol': 'BANKOFBARODA', 'weight': 0.04, 'lot_size': 15, 'instrument_token': 1195009},
    {'symbol': 'AUBANK', 'weight': 0.03, 'lot_size': 10, 'instrument_token': 108033}
]

# BankNifty index instrument token
BANKNIFTY_TOKEN = 260105

# Database setup
def init_db():
    conn = sqlite3.connect('dispersion_trade.db')
    c = conn.cursor()
    
    # Create historical data table
    c.execute('''CREATE TABLE IF NOT EXISTS historical_data
                 (timestamp DATETIME, net_premium REAL, banknifty_spot REAL)''')
    
    # Create alerts table
    c.execute('''CREATE TABLE IF NOT EXISTS alerts
                 (timestamp DATETIME, message TEXT, triggered BOOLEAN)''')
    
    conn.commit()
    conn.close()

init_db()

# Authentication required decorator
def authentication_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'access_token' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    request_token = request.args.get('request_token')
    if request_token:
        try:
            data = kite.generate_session(request_token, api_secret=API_SECRET)
            session['access_token'] = data['access_token']
            global access_token
            access_token = data['access_token']
            kite.set_access_token(access_token)
            
            # Initialize WebSocket connection after successful login
            init_websocket()
            
            return redirect('/')
        except Exception as e:
            return f"Error generating session: {str(e)}"
    return redirect(kite.login_url())

def init_websocket():
    """Initialize Zerodha WebSocket connection"""
    global kws, is_connected
    
    try:
        kws = KiteTicker(API_KEY, access_token)
        
        # Define callback methods
        kws.on_ticks = on_ticks
        kws.on_connect = on_connect
        kws.on_close = on_close
        kws.on_error = on_error
        
        # Subscribe to BankNifty and constituent tokens
        tokens = [BANKNIFTY_TOKEN] + [stock['instrument_token'] for stock in BANKNIFTY_CONSTITUENTS]
        kws.subscribe(tokens)
        
        # Start WebSocket in a separate thread
        ws_thread = threading.Thread(target=kws.connect)
        ws_thread.daemon = True
        ws_thread.start()
        
        is_connected = True
        print("WebSocket connection initialized")
        
    except Exception as e:
        print(f"Error initializing WebSocket: {str(e)}")
        is_connected = False

# WebSocket callbacks
def on_ticks(ws, ticks):
    """Handle incoming ticks"""
    try:
        process_ticks(ticks)
        
        # Emit update to all connected clients
        socketio.emit('data_update', current_data)
        
        # Check for alerts
        check_alerts()
        
    except Exception as e:
        print(f"Error processing ticks: {str(e)}")

def on_connect(ws, response):
    """Handle WebSocket connection"""
    print("WebSocket connected")
    global is_connected
    is_connected = True

def on_close(ws, code, reason):
    """Handle WebSocket close"""
    print(f"WebSocket closed: {code} - {reason}")
    global is_connected
    is_connected = False

def on_error(ws, code, reason):
    """Handle WebSocket error"""
    print(f"WebSocket error: {code} - {reason}")
    global is_connected
    is_connected = False

def process_ticks(ticks):
    """Process incoming ticks and update current data"""
    for tick in ticks:
        # Update BankNifty data
        if tick['instrument_token'] == BANKNIFTY_TOKEN:
            current_data['banknifty']['spot'] = tick['last_price']
            current_data['banknifty']['atm_strike'] = round(tick['last_price'] / 100) * 100
            
            # In a real implementation, you would fetch option premiums for ATM strikes
            # For demo, we'll simulate these values
            current_data['banknifty']['call_premium'] = tick['last_price'] * 0.005  # 0.5% of spot
            current_data['banknifty']['put_premium'] = tick['last_price'] * 0.0045  # 0.45% of spot
            current_data['banknifty']['straddle_premium'] = (
                current_data['banknifty']['call_premium'] + 
                current_data['banknifty']['put_premium']
            )
        
        # Update constituent data
        for stock in BANKNIFTY_CONSTITUENTS:
            if tick['instrument_token'] == stock['instrument_token']:
                symbol = stock['symbol']
                current_data['constituents'][symbol] = {
                    'spot': tick['last_price'],
                    'atm_strike': round(tick['last_price'] / 10) * 10,
                    'call_premium': tick['last_price'] * 0.01,  # 1% of spot
                    'put_premium': tick['last_price'] * 0.009,  # 0.9% of spot
                    'straddle_premium': tick['last_price'] * 0.019,  # 1.9% of spot
                    'weight': stock['weight'],
                    'lot_size': stock['lot_size']
                }
    
    # Calculate net premium
    calculate_net_premium()
    current_data['last_updated'] = datetime.now().isoformat()
    
    # Store historical data
    store_historical_data()

def calculate_net_premium():
    """Calculate net premium for the dispersion trade"""
    # Get BankNifty straddle premium
    bn_straddle = current_data['banknifty']['straddle_premium']
    bn_lot_size = 25  # Standard BankNifty lot size
    
    # Calculate weighted constituent straddles
    total_constituent_premium = 0
    min_weight = min([stock['weight'] for stock in BANKNIFTY_CONSTITUENTS])
    
    for stock in BANKNIFTY_CONSTITUENTS:
        symbol = stock['symbol']
        if symbol in current_data['constituents']:
            straddle_premium = current_data['constituents'][symbol]['straddle_premium']
            lot_size = stock['lot_size']
            
            # Calculate normalized lots based on weight
            normalized_lot = max(1, round(stock['weight'] / min_weight))
            current_data['normalized_lots'][symbol] = normalized_lot
            
            # Add to constituent premium
            total_constituent_premium += normalized_lot * lot_size * straddle_premium
    
    # BankNifty premium
    banknifty_premium = bn_lot_size * bn_straddle
    
    # Net premium (buy BankNifty straddle, sell constituent straddles)
    net_premium = banknifty_premium - total_constituent_premium
    
    current_data['net_premium'] = net_premium

def store_historical_data():
    """Store current data in historical database"""
    conn = sqlite3.connect('dispersion_trade.db')
    c = conn.cursor()
    
    c.execute('''INSERT INTO historical_data (timestamp, net_premium, banknifty_spot)
                 VALUES (?, ?, ?)''', 
              (datetime.now(), current_data['net_premium'], current_data['banknifty']['spot']))
    
    conn.commit()
    conn.close()
    
    # Keep in-memory history (last 100 data points)
    historical_data.append({
        'time': datetime.now().isoformat(),
        'premium': current_data['net_premium'],
        'banknifty_spot': current_data['banknifty']['spot']
    })
    
    if len(historical_data) > 100:
        historical_data.pop(0)

def check_alerts():
    """Check if any alerts should be triggered"""
    threshold = float(request.args.get('threshold', 10000))
    net_premium = current_data['net_premium']
    
    if abs(net_premium) >= threshold:
        alert_message = f"Net premium alert: ₹{net_premium:.2f} (Threshold: ₹{threshold:.2f})"
        
        # Store alert in database
        conn = sqlite3.connect('dispersion_trade.db')
        c = conn.cursor()
        c.execute('''INSERT INTO alerts (timestamp, message, triggered)
                     VALUES (?, ?, ?)''', 
                  (datetime.now(), alert_message, True))
        conn.commit()
        conn.close()
        
        # Emit alert to all connected clients
        socketio.emit('alert', {'message': alert_message, 'timestamp': datetime.now().isoformat()})

# API Routes
@app.route('/api/data')
@authentication_required
def get_data():
    return jsonify(current_data)

@app.route('/api/historical')
@authentication_required
def get_historical():
    # Get historical data from database
    conn = sqlite3.connect('dispersion_trade.db')
    c = conn.cursor()
    
    c.execute('''SELECT timestamp, net_premium, banknifty_spot 
                 FROM historical_data 
                 ORDER BY timestamp DESC LIMIT 100''')
    
    data = [{'time': row[0], 'premium': row[1], 'banknifty_spot': row[2]} for row in c.fetchall()]
    conn.close()
    
    return jsonify(data)

@app.route('/api/alerts')
@authentication_required
def get_alerts():
    # Get alerts from database
    conn = sqlite3.connect('dispersion_trade.db')
    c = conn.cursor()
    
    c.execute('''SELECT timestamp, message 
                 FROM alerts 
                 ORDER BY timestamp DESC LIMIT 20''')
    
    alerts = [{'time': row[0], 'message': row[1]} for row in c.fetchall()]
    conn.close()
    
    return jsonify(alerts)

@app.route('/api/export')
@authentication_required
def export_data():
    # Export data to CSV
    import csv
    from io import StringIO
    
    si = StringIO()
    cw = csv.writer(si)
    
    # Write header
    cw.writerow(['Timestamp', 'Symbol', 'Spot', 'Straddle Premium', 'Lot Size', 'Weight'])
    
    # Write BankNifty data
    cw.writerow([
        current_data['last_updated'],
        'BANKNIFTY',
        current_data['banknifty']['spot'],
        current_data['banknifty']['straddle_premium'],
        25,
        'N/A'
    ])
    
    # Write constituents data
    for symbol, data in current_data['constituents'].items():
        cw.writerow([
            current_data['last_updated'],
            symbol,
            data['spot'],
            data['straddle_premium'],
            data['lot_size'],
            data['weight']
        ])
    
    output = si.getvalue()
    return output, 200, {
        'Content-Type': 'text/csv',
        'Content-Disposition': 'attachment; filename=dispersion_data.csv'
    }

@app.route('/api/settings', methods=['POST'])
@authentication_required
def update_settings():
    """Update application settings"""
    data = request.json
    threshold = data.get('alert_threshold', 10000)
    
    # In a real implementation, you would save these settings to a database
    return jsonify({'status': 'success', 'alert_threshold': threshold})

@app.route('/api/status')
@authentication_required
def get_status():
    """Get application and connection status"""
    return jsonify({
        'zerodha_connected': is_connected,
        'last_update': current_data['last_updated'],
        'net_premium': current_data['net_premium']
    })

if __name__ == '__main__':
    socketio.run(app, debug=True)