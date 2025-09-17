# BankNifty Dispersion Trade Monitor - Optimized & Modular

A comprehensive real-time monitoring system for BankNifty dispersion trades with multi-level OTM support, now fully modularized and optimized.

## 🚀 Key Features

- **45-Day Expiry Monitoring**: Automatically starts monitoring 45 days before monthly expiry
- **Real ATM Straddle Premium Calculation**: Live data for BankNifty and all constituents
- **Multi-Level OTM Support**: ATM, OTM1, OTM2, and OTM3 levels
- **Normalized Lot Size Calculation**: Based on constituent weights
- **Net Premium Calculation**: Buy BankNifty straddle - Sell constituent straddles
- **Real-time Web Interface**: Modern, responsive UI with live data feeds
- **Historical Data & Charts**: Track premium changes over time
- **Alert System**: Configurable thresholds with notifications
- **Data Export**: CSV export for all OTM levels
- **Zerodha Integration**: Full API integration with TOTP support

## 📁 Optimized Project Structure

```
banknifty_dispersion/
├── app.py                 # Main Flask application (significantly reduced)
├── config.py              # Configuration and constants
├── database.py            # Database operations
├── auth.py                # Zerodha authentication
├── market_data.py         # Market data operations
├── websocket_handlers.py  # WebSocket event handlers
├── static/
│   └── js/
│       └── app.js         # Modular frontend JavaScript
├── templates/
│   └── index.html         # Optimized HTML template
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables
└── README.md             # This file
```

## 🔧 Code Optimization Results

### Before Optimization:
- **app.py**: ~900 lines
- **index.html**: ~1,250 lines with embedded JavaScript
- **Total**: Monolithic structure with duplicated code

### After Optimization:
- **app.py**: ~260 lines (71% reduction)
- **config.py**: 83 lines
- **database.py**: 266 lines
- **auth.py**: 116 lines
- **market_data.py**: 339 lines
- **websocket_handlers.py**: 218 lines
- **static/js/app.js**: 522 lines
- **index.html**: ~225 lines (82% reduction)

### Benefits:
- ✅ **Modular Architecture**: Separated concerns into logical modules
- ✅ **Maintainability**: Easier to debug and extend
- ✅ **Code Reusability**: Functions can be imported across modules
- ✅ **Performance**: Reduced HTML size and better caching
- ✅ **Scalability**: Easy to add new features without bloating main files

## 🛠 Installation & Setup

### 1. Clone and Navigate
```bash
git clone <repository-url>
cd banknifty_dispersion
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file with your Zerodha credentials:
```env
API_KEY=your_zerodha_api_key
API_SECRET=your_zerodha_api_secret
REQUEST_TOKEN=your_request_token
TOTP_SECRET=your_totp_secret
```

### 4. Run the Application
```bash
python app.py
```

The application will automatically:
- Initialize the SQLite database
- Check if monitoring should start (45 days before expiry)
- Start the Flask server on available ports (5000, 5001, 5002, 8000, 8080)

## 📊 Module Descriptions

### `config.py`
- Centralizes all configuration settings
- Environment variable loading
- Constants for constituents, lot sizes, OTM levels
- Flask and database configuration

### `database.py`
- `DatabaseManager` class for all SQLite operations
- Historical data storage and retrieval
- Settings management
- Alert logging
- CSV export functionality

### `auth.py`
- `ZerodhaAuth` class for authentication
- TOTP generation and management
- Access token handling
- Login flow management

### `market_data.py`
- `MarketDataManager` class for market operations
- Option chain data fetching
- Net premium calculations
- Monitoring logic
- Alert checking

### `websocket_handlers.py`
- `WebSocketManager` class for real-time communication
- Socket.IO event handlers
- Connection monitoring
- Real-time data broadcasting

### `static/js/app.js`
- `DispersionTradeApp` class for frontend logic
- Modular JavaScript with proper separation
- Real-time UI updates
- Chart management
- User interaction handling

## 🎯 Usage

### Starting Monitoring
1. **Automatic**: Monitoring starts automatically 45 days before expiry
2. **Manual**: Use the "Start Monitoring" button in the web interface

### Authentication
1. Click "Get Zerodha Login URL" to get the login link
2. Use the displayed TOTP for two-factor authentication
3. Complete the Zerodha login flow

### Data Export
- Export data for any OTM level (ATM, OTM1, OTM2, OTM3)
- CSV format with historical data
- Accessible via export buttons in the interface

### Settings Configuration
- Alert thresholds
- OTM level selection
- Auto-alerts toggle
- Real-time settings sync

## 🔄 Real-time Features

- **WebSocket Connection**: Live data updates
- **Connection Monitoring**: Automatic reconnection
- **Heartbeat System**: Connection health tracking
- **Alert System**: Real-time notifications
- **Historical Charts**: Live premium tracking

## 📈 BankNifty Constituents

The system monitors the following constituents with accurate weights:
- HDFCBANK (28.91%)
- ICICIBANK (22.34%)
- KOTAKBANK (11.56%)
- AXISBANK (10.89%)
- SBIN (8.89%)
- INDUSINDBK (4.56%)
- BANKBARODA (2.34%)
- AUBANK (1.78%)
- PNB (1.56%)
- IDFCFIRSTB (1.34%)

## 🚨 Alert System

- Configurable threshold-based alerts
- Multi-level OTM monitoring
- Real-time notifications
- Historical alert logging
- Email/SMS integration ready

## 📱 Web Interface

- **Responsive Design**: Works on desktop and mobile
- **Real-time Updates**: Live data via WebSocket
- **Interactive Charts**: Historical premium visualization
- **Modern UI**: Bootstrap 5 with custom styling
- **Toast Notifications**: User-friendly feedback

## 🔧 Development

### Adding New Features
1. **Backend**: Add routes to `app.py` or create new modules
2. **Database**: Extend `DatabaseManager` in `database.py`
3. **Frontend**: Extend `DispersionTradeApp` in `app.js`
4. **Configuration**: Add constants to `config.py`

### Testing
- Use the built-in demo mode for testing without live data
- Mock data simulation available
- Connection diagnostics for troubleshooting

## 📝 API Endpoints

- `GET /` - Main web interface
- `GET /api/data` - Current market data
- `GET /api/status` - System status
- `GET /api/historical` - Historical data
- `GET /api/alerts` - Recent alerts
- `GET /api/settings` - Application settings
- `POST /api/settings` - Update settings
- `POST /api/start-monitoring` - Start monitoring
- `POST /api/stop-monitoring` - Stop monitoring
- `GET /api/export/<otm_level>` - Export data
- `GET /api/totp` - Current TOTP
- `GET /api/login-url` - Zerodha login URL
- `GET /api/connection-health` - Connection diagnostics

## 🔒 Security

- Environment variables for sensitive data
- TOTP-based authentication
- Secure token handling
- No hardcoded credentials

## 📊 Performance

- Optimized database queries
- Efficient WebSocket communication
- Minimal frontend JavaScript
- Responsive UI with lazy loading
- Connection pooling and caching

## 🐛 Troubleshooting

### Common Issues
1. **Connection Failed**: Check API credentials and TOTP
2. **No Data**: Ensure monitoring is active and within 45-day window
3. **WebSocket Issues**: Use the diagnostics button for connection info
4. **Database Errors**: Check file permissions and disk space

### Debug Mode
- Enable debug logging in `config.py`
- Use browser developer tools for frontend issues
- Check Flask logs for backend errors

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Follow the modular structure
4. Add appropriate tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Zerodha for the KiteConnect API
- Bootstrap for the UI framework
- Chart.js for data visualization
- Socket.IO for real-time communication

---

**Note**: This is a trading tool for educational and analysis purposes. Always verify calculations and use proper risk management when trading.