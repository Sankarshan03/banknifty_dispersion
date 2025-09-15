from flask import Flask, jsonify, request, render_template, session, redirect
from flask_cors import CORS
from kiteconnect import KiteConnect, KiteTicker
import logging
import threading
import time
from datetime import datetime, timedelta
import json
from random import random
import os

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'banknifty_dispersion_secret_key'
CORS(app)

# Zerodha API Configuration
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
REDIRECT_URL = os.getenv("REDIRECT_URL")

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

@app.route('/')
def index():
    # Always render the main template which includes the login form
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
            return redirect('/')
        except Exception as e:
            return f"Error generating session: {str(e)}"
    return redirect(kite.login_url())

@app.route('/api/data')
def get_data():
    # This would fetch real data from Zerodha API
    # For now, we'll return mock data
    
    # Simulate fetching live data
    bn_spot = 45000 + random() * 200 - 100
    atm_strike = round(bn_spot / 100) * 100
    call_premium = 100 + random() * 200
    put_premium = 100 + random() * 200
    
    current_data['banknifty'] = {
        'spot': bn_spot,
        'atm_strike': atm_strike,
        'call_premium': call_premium,
        'put_premium': put_premium,
        'straddle_premium': call_premium + put_premium
    }
    
    # Constituents data
    min_weight = min([stock['weight'] for stock in BANKNIFTY_CONSTITUENTS])
    total_constituent_premium = 0
    
    for stock in BANKNIFTY_CONSTITUENTS:
        spot = 1000 + random() * 1000
        strike = round(spot / 10) * 10
        call_premium = 10 + random() * 40
        put_premium = 10 + random() * 40
        straddle_premium = call_premium + put_premium
        
        # Calculate normalized lots based on weight
        normalized_lot = max(1, round(stock['weight'] / min_weight))
        current_data['normalized_lots'][stock['symbol']] = normalized_lot
        
        # Add to constituent premium
        total_constituent_premium += normalized_lot * stock['lot_size'] * straddle_premium
        
        current_data['constituents'][stock['symbol']] = {
            'spot': spot,
            'atm_strike': strike,
            'call_premium': call_premium,
            'put_premium': put_premium,
            'straddle_premium': straddle_premium,
            'weight': stock['weight'],
            'lot_size': stock['lot_size']
        }
    
    # BankNifty premium
    banknifty_premium = 25 * current_data['banknifty']['straddle_premium']
    
    # Net premium (buy BankNifty straddle, sell constituent straddles)
    net_premium = banknifty_premium - total_constituent_premium
    
    current_data['net_premium'] = net_premium
    current_data['last_updated'] = datetime.now().isoformat()
    
    return jsonify(current_data)

@app.route('/api/historical')
def get_historical():
    # This would return historical data from database
    # For now, return mock data
    historical = []
    now = datetime.now()
    
    for i in range(24):
        time = (now - timedelta(hours=i)).isoformat()
        premium = 10000 + (random() * 20000 - 10000)
        historical.append({'time': time, 'premium': premium})
    
    return jsonify(historical)

@app.route('/api/export')
def export_data():
    # This would generate a CSV file for export
    # For now, return mock CSV
    import csv
    from io import StringIO
    
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Symbol', 'Weight', 'Spot', 'Straddle Premium', 'Lot Size'])
    
    for symbol, data in current_data['constituents'].items():
        cw.writerow([
            symbol,
            data['weight'],
            data['spot'],
            data['straddle_premium'],
            data['lot_size']
        ])
    
    output = si.getvalue()
    return output, 200, {'Content-Type': 'text/csv', 'Content-Disposition': 'attachment; filename=dispersion_data.csv'}

@app.route('/api/is_authenticated')
def is_authenticated():
    # Check if user is authenticated with Zerodha
    if 'access_token' in session:
        return jsonify({'authenticated': True})
    else:
        return jsonify({'authenticated': False})

if __name__ == '__main__':
    app.run(debug=True)