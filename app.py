# app.py - Refactored BankNifty Dispersion Trade Monitor (Main Application)
from flask import Flask, jsonify, request, render_template, redirect, send_file
from flask_cors import CORS
from flask_socketio import SocketIO
import logging
import signal
import atexit
import csv
import io
from datetime import datetime

# Import custom modules
from config import FLASK_SECRET_KEY, FLASK_HOST, FLASK_PORTS, LOG_LEVEL
from database import db_manager
from auth import zerodha_auth
from market_data import market_data_manager
from websocket_handlers import init_websocket_manager

# Configure logging
logging.basicConfig(level=getattr(logging, LOG_LEVEL))
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize WebSocket manager
websocket_manager = init_websocket_manager(socketio)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data')
def get_data():
    """Get current dispersion trade data"""
    return jsonify(market_data_manager.get_current_data())

@app.route('/api/historical')
def get_historical():
    """Get historical data from database"""
    try:
        historical_data = db_manager.get_historical_data()
        return jsonify(historical_data)
    except Exception as e:
        logger.error(f"Error fetching historical data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts')
def get_alerts():
    """Get recent alerts"""
    try:
        alerts = db_manager.get_alerts()
        return jsonify(alerts)
    except Exception as e:
        logger.error(f"Error fetching alerts: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings', methods=['GET', 'POST'])
def manage_settings():
    """Get or update application settings"""
    try:
        if request.method == 'GET':
            settings = db_manager.get_settings()
            return jsonify(settings)
        elif request.method == 'POST':
            data = request.json
            db_manager.update_settings(data)
            return jsonify({'status': 'success', 'message': 'Settings updated'})
    except Exception as e:
        logger.error(f"Error managing settings: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/export/<otm_level>')
def export_data(otm_level):
    """Export data to CSV"""
    try:
        rows = db_manager.export_data_to_csv(otm_level)
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Timestamp', 'BankNifty Spot', 'Net Premium', 'BankNifty Straddle Premium'])
        
        # Write data
        for row in rows:
            writer.writerow(row)
        
        # Create response
        output.seek(0)
        
        return send_file(
            io.BytesIO(output.getvalue().encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'banknifty_dispersion_{otm_level}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
        
    except Exception as e:
        logger.error(f"Error exporting data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/start-monitoring', methods=['POST'])
def start_monitoring():
    """Start dispersion trade monitoring"""
    try:
        success, message = market_data_manager.start_monitoring()
        if success:
            # Start WebSocket data updates
            websocket_manager.start_data_updates()
            return jsonify({
                'status': 'success',
                'message': message,
                'expiry_date': market_data_manager.current_data['expiry_date'],
                'days_to_expiry': market_data_manager.current_data['days_to_expiry']
            })
        else:
            return jsonify({'status': 'error', 'message': message})
    except Exception as e:
        logger.error(f"Error starting monitoring: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stop-monitoring', methods=['POST'])
def stop_monitoring():
    """Stop dispersion trade monitoring"""
    try:
        success, message = market_data_manager.stop_monitoring()
        if success:
            # Stop WebSocket data updates
            websocket_manager.stop_data_updates()
            return jsonify({'status': 'success', 'message': message})
        else:
            return jsonify({'status': 'error', 'message': message})
    except Exception as e:
        logger.error(f"Error stopping monitoring: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/status')
def get_status():
    """Get system status"""
    try:
        connection_status = websocket_manager.get_connection_status()
        current_data = market_data_manager.get_current_data()
        
        status_data = {
            'zerodha_connected': connection_status['is_connected'],
            'last_update': current_data['last_updated'],
            'net_premium': current_data['net_premium'],
            'reconnect_attempts': connection_status['reconnect_attempts'],
            'last_heartbeat': connection_status['last_heartbeat'],
            'monitoring_active': current_data['monitoring_active'],
            'days_to_expiry': current_data['days_to_expiry'],
            'expiry_date': current_data['expiry_date'],
            'seconds_since_last_data': connection_status['time_since_last_data']
        }
        
        return jsonify(status_data)
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/totp')
def get_totp():
    """Get current TOTP for Zerodha authentication"""
    try:
        current_totp = zerodha_auth.get_current_totp()
        if current_totp:
            return jsonify({
                'totp': current_totp,
                'timestamp': datetime.now().isoformat(),
                'message': 'Current TOTP for Zerodha login'
            })
        else:
            return jsonify({'error': 'TOTP secret not configured'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/login-url')
def get_login_url():
    """Get Zerodha login URL"""
    try:
        login_url = zerodha_auth.get_login_url()
        return jsonify({
            'login_url': login_url,
            'message': 'Use this URL to login to Zerodha',
            'current_totp': zerodha_auth.get_current_totp()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/connection-health')
def connection_health():
    """Get detailed connection health information"""
    try:
        health_data = websocket_manager.get_connection_status()
        return jsonify(health_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/login')
def login():
    """Handle Zerodha login callback"""
    request_token = request.args.get('request_token')
    if request_token:
        try:
            success = zerodha_auth.process_login_callback(request_token)
            if success:
                return redirect('/')
            else:
                return f"Login failed<br><a href='/'>Go back to main page</a>"
        except Exception as e:
            error_msg = f"Error processing login: {str(e)}"
            logger.error(error_msg)
            return f"{error_msg}<br><a href='/'>Go back to main page</a>"
    
    # If no request token, show login page
    try:
        auth_status = zerodha_auth.get_auth_status()
        return f"""
        <h2>Zerodha Login Required</h2>
        <p>Please use the following TOTP when logging in: <strong>{auth_status['current_totp']}</strong></p>
        <p><a href="{auth_status['login_url']}" target="_blank">Click here to login to Zerodha</a></p>
        <p>After login, you will be redirected back to the application.</p>
        <p><a href="/">Go back to main page</a></p>
        """
    except Exception as e:
        return f"Error: {str(e)}<br><a href='/'>Go back to main page</a>"

# Cleanup handlers
def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    market_data_manager.stop_monitoring()
    websocket_manager.cleanup()
    exit(0)

def cleanup_on_exit():
    """Cleanup on application exit"""
    logger.info("Application shutting down...")
    market_data_manager.stop_monitoring()
    websocket_manager.cleanup()

# Register cleanup handlers
atexit.register(cleanup_on_exit)
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == '__main__':
    logger.info("Starting BankNifty Dispersion Trading App...")
    
    # Check if monitoring should start automatically
    if market_data_manager.should_start_monitoring():
        logger.info(f"Monitoring period active. Days to expiry: {market_data_manager.current_data['days_to_expiry']}")
        market_data_manager.start_monitoring()
    else:
        logger.info(f"Monitoring will start 45 days before expiry. Current days to expiry: {market_data_manager.current_data['days_to_expiry']}")
    
    # Initialize WebSocket connection
    try:
        logger.info("Initializing WebSocket connection...")
        websocket_manager.init_websocket()
        logger.info("Setup complete. Starting Flask app...")
    except Exception as e:
        logger.error(f"Error initializing connections: {str(e)}")
        logger.info("App will start but real-time data may not be available.")
    
    # Try to start server on different ports
    for port in FLASK_PORTS:
        try:
            logger.info(f"Attempting to start server on http://{FLASK_HOST}:{port}")
            socketio.run(app, debug=False, host=FLASK_HOST, port=port, use_reloader=False)
            break
        except OSError as e:
            if "Address already in use" in str(e) or "10048" in str(e):
                logger.info(f"Port {port} is busy, trying next port...")
                continue
            else:
                logger.error(f"Error starting server on port {port}: {e}")
                break
    else:
        logger.error("Could not start server on any available port!")