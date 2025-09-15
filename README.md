# BankNifty Dispersion Trade Monitor

A comprehensive web application for real-time monitoring of BankNifty dispersion trades with complete Zerodha API integration.

## Overview

The BankNifty Dispersion Trade Monitor is a Flask-based web application that helps traders analyze and monitor dispersion trades between BankNifty index options and its constituent stock options in real-time. The application calculates net premiums using live market data from Zerodha, provides historical data visualization, and sends alerts when premium thresholds are reached.

## Features

- **Real-time Data Integration**: Complete Zerodha API integration with WebSocket connection for live market data
- **Net Premium Calculation**: Real-time computation of dispersion trade premiums between BankNifty and constituent stocks
- **Historical Data Visualization**: Interactive charts showing premium trends over time with SQLite database storage
- **Configurable Alerts**: Set custom thresholds for trade signals with real-time notifications
- **Export Functionality**: Download current data in CSV format for further analysis
- **Responsive Design**: Works on desktop and mobile devices with Bootstrap UI
- **User Authentication**: Secure OAuth login with Zerodha credentials
- **OTM Level Selection**: Analyze ATM and OTM options up to 3 levels
- **Live Connection Status**: Real-time monitoring of WebSocket connection status

## Prerequisites

Before running this application, ensure you have:

- Python 3.7 or higher
- Zerodha trading account with API access
- API key and secret from Zerodha (already configured with your credentials)
- Modern web browser with JavaScript support

## Installation

1. Clone or download the project files
2. Install required Python packages:
   ```bash
   pip install flask flask-cors flask-socketio kiteconnect
   ```
3. The application is already configured with your Zerodha API credentials:
   ```python
   API_KEY = "your-api-key"
   API_SECRET = "your-api-secret"
   REDIRECT_URL = "your-redirect-url"
   ```

## Project Structure

```
banknifty_dispersion/
├── app.py                 # Flask backend application with Zerodha integration
├── templates/
│   └── index.html         # Main frontend HTML file
├── dispersion_trade.db    # SQLite database (created automatically)
└── README.md              # This file
```

## Configuration

### Zerodha API Setup

The application uses your provided Zerodha API credentials:
- API_KEY = "your-api-key"
- API_SECRET = "your-api-secret"
- REDIRECT_URL = "your-redirect-url"

### Application Settings

The application provides several configurable settings:
- **Alert Threshold**: Net premium value that triggers alerts (default: ₹10,000)
- **OTM Level**: Select from ATM, OTM1, OTM2, or OTM3 options
- **Real-time Updates**: Data refreshes automatically via WebSocket connection

## Usage

1. Start the application:
   ```bash
   python app.py
   ```

2. Open your browser and navigate to `http://127.0.0.1:5000`

3. Click "Connect to Zerodha" to authenticate with your Zerodha credentials

4. Once authenticated, the application will:
   - Establish a WebSocket connection to Zerodha for real-time data
   - Start displaying live BankNifty and constituent stock data
   - Calculate and update net premium values in real-time
   - Store historical data in the local database

5. Configure your settings in the settings panel:
   - Set alert thresholds for trade signals
   - Select OTM levels for analysis
   - Enable/disable alert notifications

6. Monitor the net premium value and historical chart

7. Set alert thresholds to get notified when premium values reach favorable levels

8. Export data using the export button when needed

## How Dispersion Trading Works

Dispersion trading involves:
1. Buying ATM straddles on BankNifty index options
2. Selling ATM straddles on constituent bank stocks
3. Weighting the positions according to index composition
4. Profiting from differences in implied volatility between index and components

The application calculates the net premium as:
```
Net Premium = (BankNifty Straddle Premium × Lot Size) - Σ(Constituent Straddle Premium × Normalized Lots × Lot Size)
```

## Real-Time Data Integration

The application uses Zerodha's Kite Connect API with WebSocket integration for:
- Real-time market data streaming
- Live option chain information
- Instant price updates for BankNifty and constituent stocks
- Automatic recalculation of net premiums on price changes

### WebSocket Implementation

The application establishes a persistent WebSocket connection to Zerodha's servers for:
- Real-time tick-by-tick data updates
- Efficient data transfer without polling
- Instant notification of price changes
- Live connection status monitoring

## Database Schema

The application uses SQLite with two main tables:

### Historical Data Table
- Stores timestamp, net premium, and BankNifty spot price
- Used for historical chart visualization
- Maintains last 100 data points in memory for performance

### Alerts Table
- Stores triggered alerts with timestamps and messages
- Used for alert history and notification tracking

## API Endpoints

- `/` - Main application page
- `/login` - Zerodha OAuth authentication
- `/api/data` - Current dispersion trade data
- `/api/historical` - Historical premium data
- `/api/alerts` - Alert history
- `/api/export` - Data export to CSV
- `/api/settings` - Application settings management
- `/api/status` - Connection status information

## Troubleshooting

### Common Issues

1. **Authentication Errors**:
   - Verify Zerodha API credentials are correct
   - Ensure redirect URL is properly configured in Zerodha developer console

2. **WebSocket Connection Issues**:
   - Check internet connection stability
   - Verify Zerodha API services are operational

3. **Data Not Loading**:
   - Check browser console for JavaScript errors
   - Verify Flask server is running correctly

4. **TemplateNotFound Error**:
   - Ensure the templates folder exists with index.html

### Debug Mode

The application runs in debug mode by default. For production use:
- Set `debug=False` in `app.run()`
- Use a production WSGI server like Gunicorn

## Performance Considerations

- The application maintains only the last 100 data points in memory for performance
- Historical data is stored in SQLite for persistence
- WebSocket connection efficiently handles real-time data updates
- UI updates are optimized to prevent browser lag

## Security Considerations

- API credentials are stored in the application code (consider environment variables for production)
- OAuth authentication flow ensures secure login
- SQLite database is local and doesn't contain sensitive information
- All client-server communication happens over HTTP (consider HTTPS for production)

## Browser Compatibility

The application works with:
- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+

## Contributing

Contributions to improve the application are welcome. Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is for educational and informational purposes only. Use at your own risk. Trading in financial markets involves risk, and past performance is not indicative of future results.

## Disclaimer

This application is not affiliated with Zerodha or NSE. It is provided as-is without any warranty. Users are responsible for their own trading decisions and should understand the risks involved in options trading.

## Support

For technical support or questions about the application:
1. Check the troubleshooting section above
2. Ensure all prerequisites are met
3. Verify Zerodha API credentials are correct
4. Check that the Flask server is running without errors

---

**Note**: This application is designed for monitoring purposes only and should not be considered as financial advice. Always conduct your own research and consult with a qualified financial advisor before making investment decisions.