# websocket_handlers.py - WebSocket Event Handlers for BankNifty Dispersion Trade Monitor
import logging
import threading
import time
from datetime import datetime
from flask import request
from market_data import market_data_manager
from config import CONNECTION_TIMEOUT, DATA_UPDATE_INTERVAL

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Manages WebSocket connections and real-time data updates"""
    
    def __init__(self, socketio):
        self.socketio = socketio
        self.is_connected = False
        self.last_heartbeat = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.connection_monitor_thread = None
        self.data_update_thread = None
        
        # Register event handlers
        self._register_handlers()
    
    def _register_handlers(self):
        """Register Socket.IO event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection"""
            logger.info(f"Client connected: {request.sid}")
            # Send current connection status to the newly connected client
            self.socketio.emit('connection_status', {
                'status': 'connected' if self.is_connected else 'disconnected',
                'message': 'Real-time data connection active' if self.is_connected else 'No real-time data connection',
                'timestamp': datetime.now().isoformat()
            }, room=request.sid)
            
            # Send current data if available
            current_data = market_data_manager.get_current_data()
            if current_data['last_updated']:
                self.socketio.emit('data_update', current_data, room=request.sid)
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            logger.info(f"Client disconnected: {request.sid}")
        
        @self.socketio.on('request_status')
        def handle_status_request():
            """Handle status request from client"""
            status = {
                'zerodha_connected': self.is_connected,
                'last_update': market_data_manager.current_data['last_updated'],
                'net_premium': market_data_manager.current_data['net_premium'],
                'reconnect_attempts': self.reconnect_attempts,
                'timestamp': datetime.now().isoformat(),
                'monitoring_active': market_data_manager.current_data['monitoring_active'],
                'days_to_expiry': market_data_manager.current_data['days_to_expiry']
            }
            
            if self.last_heartbeat:
                time_since_last = datetime.now() - self.last_heartbeat
                status['seconds_since_last_data'] = time_since_last.total_seconds()
            
            self.socketio.emit('status_response', status, room=request.sid)
        
        @self.socketio.on('force_reconnect')
        def handle_force_reconnect():
            """Handle force reconnect request from client"""
            try:
                logger.info("Force reconnect requested by client")
                self.is_connected = False
                self.init_websocket()
                self.socketio.emit('reconnect_response', {'status': 'success', 'message': 'Reconnection initiated'}, room=request.sid)
            except Exception as e:
                self.socketio.emit('reconnect_response', {'status': 'error', 'message': str(e)}, room=request.sid)
    
    def init_websocket(self):
        """Initialize WebSocket connection (demo mode)"""
        try:
            # For demo purposes, we'll simulate a connection
            self.is_connected = True
            self.last_heartbeat = datetime.now()
            logger.info("WebSocket connection simulated (demo mode)")
            
            # Start connection monitor
            if not self.connection_monitor_thread or not self.connection_monitor_thread.is_alive():
                self.start_connection_monitor()
            
            # Start periodic data updates if monitoring is active
            if market_data_manager.current_data['monitoring_active']:
                self.start_data_updates()
                
        except Exception as e:
            logger.error(f"Error initializing WebSocket: {str(e)}")
            self.is_connected = False
    
    def start_connection_monitor(self):
        """Start connection monitoring in a separate thread"""
        def monitor_connection():
            while True:
                try:
                    if self.last_heartbeat and self.is_connected:
                        time_since_last_tick = datetime.now() - self.last_heartbeat
                        # If no data received for more than CONNECTION_TIMEOUT seconds, consider connection stale
                        if time_since_last_tick.total_seconds() > CONNECTION_TIMEOUT:
                            logger.warning("Connection appears stale, attempting to reconnect...")
                            self.is_connected = False
                            self.init_websocket()
                    
                    time.sleep(30)  # Check every 30 seconds
                except Exception as e:
                    logger.error(f"Error in connection monitor: {str(e)}")
                    time.sleep(30)
        
        self.connection_monitor_thread = threading.Thread(target=monitor_connection, daemon=True)
        self.connection_monitor_thread.start()
        logger.info("Connection monitor started")
    
    def start_data_updates(self):
        """Start periodic data updates in a separate thread"""
        def periodic_update():
            while market_data_manager.current_data['monitoring_active'] and self.is_connected:
                try:
                    # Update market data
                    market_data_manager.update_market_data()
                    
                    # Emit update to all connected clients
                    current_data = market_data_manager.get_current_data()
                    self.socketio.emit('data_update', current_data)
                    
                    # Update heartbeat
                    self.last_heartbeat = datetime.now()
                    
                    # Emit any new alerts
                    if market_data_manager.alerts_data:
                        latest_alert = market_data_manager.alerts_data[-1]
                        self.socketio.emit('alert', latest_alert)
                    
                    time.sleep(DATA_UPDATE_INTERVAL)
                    
                except Exception as e:
                    logger.error(f"Error in periodic data update: {str(e)}")
                    time.sleep(DATA_UPDATE_INTERVAL)
        
        if not self.data_update_thread or not self.data_update_thread.is_alive():
            self.data_update_thread = threading.Thread(target=periodic_update, daemon=True)
            self.data_update_thread.start()
            logger.info("Data update thread started")
    
    def stop_data_updates(self):
        """Stop periodic data updates"""
        if self.data_update_thread and self.data_update_thread.is_alive():
            logger.info("Stopping data updates...")
            # The thread will stop when monitoring_active becomes False
    
    def emit_connection_status(self, status, message):
        """Emit connection status to all clients"""
        self.socketio.emit('connection_status', {
            'status': status,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
    
    def emit_data_update(self, data):
        """Emit data update to all clients"""
        self.socketio.emit('data_update', data)
    
    def emit_alert(self, alert_data):
        """Emit alert to all clients"""
        self.socketio.emit('alert', alert_data)
    
    def get_connection_status(self):
        """Get current connection status"""
        status_data = {
            'is_connected': self.is_connected,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'reconnect_attempts': self.reconnect_attempts,
            'max_reconnect_attempts': self.max_reconnect_attempts,
            'time_since_last_data': None
        }
        
        if self.last_heartbeat:
            time_since_last = datetime.now() - self.last_heartbeat
            status_data['time_since_last_data'] = time_since_last.total_seconds()
        
        return status_data
    
    def cleanup(self):
        """Clean up WebSocket connections on app shutdown"""
        try:
            logger.info("Cleaning up WebSocket connections...")
            self.is_connected = False
            
            # Stop threads
            if self.connection_monitor_thread and self.connection_monitor_thread.is_alive():
                logger.info("Stopping connection monitor...")
            
            if self.data_update_thread and self.data_update_thread.is_alive():
                logger.info("Stopping data update thread...")
            
            logger.info("WebSocket cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during WebSocket cleanup: {str(e)}")

# Global WebSocket manager instance (will be initialized with socketio in main app)
websocket_manager = None

def init_websocket_manager(socketio):
    """Initialize the global WebSocket manager"""
    global websocket_manager
    websocket_manager = WebSocketManager(socketio)
    return websocket_manager
