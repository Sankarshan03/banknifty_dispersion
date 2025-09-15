# BankNifty Dispersion Trade Monitor

A comprehensive web application for monitoring BankNifty dispersion trades with real-time data integration from Zerodha API.

## Overview

The BankNifty Dispersion Trade Monitor is a Flask-based web application that helps traders analyze and monitor dispersion trades between BankNifty index options and its constituent stock options. The application calculates net premiums in real-time, provides historical data visualization, and sends alerts when premium thresholds are reached.

## Features

- **Real-time Data Integration**: Connects to Zerodha API for live market data
- **Net Premium Calculation**: Computes dispersion trade premiums between BankNifty and constituent stocks
- **Historical Data Visualization**: Charts showing premium trends over time
- **Configurable Alerts**: Set custom thresholds for trade signals
- **Export Functionality**: Download data in CSV format for further analysis
- **Responsive Design**: Works on desktop and mobile devices
- **User Authentication**: Secure login with Zerodha credentials
- **OTM Level Selection**: Analyze ATM and OTM options up to 3 levels

## Prerequisites

Before running this application, ensure you have:

- Python 3.7 or higher
- Zerodha trading account with API access
- API key and secret from Zerodha

## Installation

1. Clone or download the project files
2. Install required Python packages:
   ```bash
   pip install flask flask-cors kiteconnect
   ```
3. Update the Zerodha API credentials in `app.py`:
   ```python
   API_KEY = "your_api_key_here"
   API_SECRET = "your_api_secret_here"
   REDIRECT_URL = "http://127.0.0.1:5000/"
   ```

## Project Structure

```
banknifty_dispersion/
├── app.py                 # Flask backend application
├── templates/
│   └── index.html         # Main frontend HTML file
└── README.md              # This file
```

## Configuration

### Zerodha API Setup

1. Log in to your Zerodha Kite account
2. Go to API section and generate API key and secret
3. Set the redirect URL to `http://127.0.0.1:5000/`
4. Update the credentials in the application

### Application Settings

The application provides several configurable settings:

- **Refresh Interval**: How often to update data (default: 5 seconds)
- **Alert Threshold**: Net premium value that triggers alerts
- **OTM Level**: Select from ATM, OTM1, OTM2, or OTM3 options

## Usage

1. Start the application:
   ```bash
   python app.py
   ```

2. Open your browser and navigate to `http://127.0.0.1:5000`

3. Log in with your Zerodha credentials or use demo mode with mock data

4. Configure your settings in the settings panel

5. Monitor the net premium value and historical chart

6. Set alert thresholds to get notified when premium values are favorable

7. Export data using the export button when needed

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

## API Integration

The application integrates with Zerodha's Kite Connect API to:
- Authenticate users via OAuth
- Fetch real-time market data
- Retrieve option chain information
- Stream live quotes (WebSocket)

## Troubleshooting

### Common Issues

1. **TemplateNotFound Error**: Ensure the templates folder exists with index.html
2. **Authentication Errors**: Verify Zerodha API credentials and redirect URL
3. **Data Not Loading**: Check internet connection and Zerodha API status

### Debug Mode

The application runs in debug mode by default. For production use:
- Set `debug=False` in `app.run()`
- Use a production WSGI server like Gunicorn

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

For technical support or questions about the application, please create an issue in the project repository.

---

**Note**: This application is designed for monitoring purposes only and should not be considered as financial advice. Always conduct your own research and consult with a qualified financial advisor before making investment decisions.