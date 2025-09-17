# market_data.py - Market Data Operations for BankNifty Dispersion Trade Monitor
import logging
from datetime import datetime, timedelta
from auth import zerodha_auth
from database import db_manager
from config import (
    BANKNIFTY_CONSTITUENTS, BANKNIFTY_LOT_SIZE, OTM_LEVELS, 
    MONITORING_DAYS_BEFORE_EXPIRY, INITIAL_DATA_STRUCTURE
)

logger = logging.getLogger(__name__)

class MarketDataManager:
    """Handles market data operations and calculations"""
    
    def __init__(self):
        self.current_data = INITIAL_DATA_STRUCTURE.copy()
        self.historical_data = []
        self.alerts_data = []
    
    def get_next_expiry_date(self):
        """Get the next monthly expiry date for BankNifty options"""
        try:
            now = datetime.now()
            current_month = now.month
            current_year = now.year
            
            # Try current month first
            last_thursday = self._get_last_thursday(current_year, current_month)
            
            # If current month's expiry has passed, get next month's
            if last_thursday < now.date():
                if current_month == 12:
                    current_month = 1
                    current_year += 1
                else:
                    current_month += 1
                last_thursday = self._get_last_thursday(current_year, current_month)
            
            return last_thursday
            
        except Exception as e:
            logger.error(f"Error calculating next expiry: {str(e)}")
            # Fallback to 30 days from now
            return (datetime.now() + timedelta(days=30)).date()
    
    def _get_last_thursday(self, year, month):
        """Get the last Thursday of a given month and year"""
        # Get the last day of the month
        if month == 12:
            last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = datetime(year, month + 1, 1) - timedelta(days=1)
        
        # Find the last Thursday
        days_back = (last_day.weekday() - 3) % 7
        last_thursday = last_day - timedelta(days=days_back)
        
        return last_thursday.date()
    
    def should_start_monitoring(self):
        """Check if monitoring should start (45 days before expiry)"""
        try:
            expiry_date = self.get_next_expiry_date()
            days_to_expiry = (expiry_date - datetime.now().date()).days
            
            self.current_data['expiry_date'] = expiry_date.isoformat()
            self.current_data['days_to_expiry'] = days_to_expiry
            
            # Start monitoring 45 days before expiry
            return days_to_expiry <= MONITORING_DAYS_BEFORE_EXPIRY
            
        except Exception as e:
            logger.error(f"Error checking monitoring status: {str(e)}")
            return False
    
    def calculate_normalized_lots(self):
        """Calculate normalized lot sizes based on constituent weights"""
        try:
            # Find the minimum weight to use as base
            min_weight = min([stock['weight'] for stock in BANKNIFTY_CONSTITUENTS])
            
            normalized_lots = {}
            
            for stock in BANKNIFTY_CONSTITUENTS:
                symbol = stock['symbol']
                weight = stock['weight']
                lot_size = stock['lot_size']
                
                # Calculate normalized lots (minimum 1 lot)
                normalized_lot_count = max(1, round(weight / min_weight))
                
                normalized_lots[symbol] = {
                    'lot_count': normalized_lot_count,
                    'lot_size': lot_size,
                    'total_quantity': normalized_lot_count * lot_size,
                    'weight': weight
                }
            
            self.current_data['normalized_lots'] = normalized_lots
            return normalized_lots
            
        except Exception as e:
            logger.error(f"Error calculating normalized lots: {str(e)}")
            return {}
    
    def get_option_chain_data(self, symbol, expiry_date):
        """Fetch real option chain data from Zerodha"""
        try:
            if not zerodha_auth.is_authenticated():
                logger.warning("No authentication available for option chain data")
                return None
            
            kite = zerodha_auth.get_kite_instance()
            
            # Get instruments for the symbol
            instruments = kite.instruments(exchange='NFO')
            
            # Filter for options of the given symbol and expiry
            option_instruments = [
                inst for inst in instruments 
                if inst['name'] == symbol and 
                inst['expiry'].date() == expiry_date and
                inst['instrument_type'] in ['CE', 'PE']
            ]
            
            if not option_instruments:
                logger.warning(f"No option instruments found for {symbol} with expiry {expiry_date}")
                return None
            
            # Get current spot price
            if symbol == 'BANKNIFTY':
                quote = kite.quote([f'NSE:{symbol}'])
                spot_price = quote[f'NSE:{symbol}']['last_price']
            else:
                quote = kite.quote([f'NSE:{symbol}'])
                spot_price = quote[f'NSE:{symbol}']['last_price']
            
            # Calculate ATM and OTM strikes
            if symbol == 'BANKNIFTY':
                strike_interval = 100
            else:
                strike_interval = 10 if spot_price < 1000 else 50
            
            atm_strike = round(spot_price / strike_interval) * strike_interval
            
            strikes = {
                'ATM': atm_strike,
                'OTM1': atm_strike + strike_interval,
                'OTM2': atm_strike + (2 * strike_interval),
                'OTM3': atm_strike + (3 * strike_interval)
            }
            
            option_data = {}
            
            for level, strike in strikes.items():
                # Find CE and PE instruments for this strike
                ce_inst = next((inst for inst in option_instruments 
                              if inst['strike'] == strike and inst['instrument_type'] == 'CE'), None)
                pe_inst = next((inst for inst in option_instruments 
                              if inst['strike'] == strike and inst['instrument_type'] == 'PE'), None)
                
                if ce_inst and pe_inst:
                    # Get quotes for both options
                    tokens = [f"NFO:{ce_inst['tradingsymbol']}", f"NFO:{pe_inst['tradingsymbol']}"]
                    quotes = kite.quote(tokens)
                    
                    ce_premium = quotes[f"NFO:{ce_inst['tradingsymbol']}"]['last_price']
                    pe_premium = quotes[f"NFO:{pe_inst['tradingsymbol']}"]['last_price']
                    
                    option_data[level] = {
                        'strike': strike,
                        'call_premium': ce_premium,
                        'put_premium': pe_premium,
                        'straddle_premium': ce_premium + pe_premium
                    }
            
            return {
                'spot': spot_price,
                'atm_strike': atm_strike,
                'otm_levels': option_data
            }
            
        except Exception as e:
            logger.error(f"Error fetching option chain for {symbol}: {str(e)}")
            return None
    
    def calculate_net_premiums(self):
        """Calculate net premiums for all OTM levels"""
        try:
            normalized_lots = self.current_data['normalized_lots']
            
            for otm_level in OTM_LEVELS:
                # BankNifty straddle premium
                bn_straddle = self.current_data['banknifty']['otm_levels'].get(otm_level, {}).get('straddle_premium', 0)
                bn_premium = BANKNIFTY_LOT_SIZE * bn_straddle
                
                # Constituent straddles premium
                total_constituent_premium = 0
                
                for stock in BANKNIFTY_CONSTITUENTS:
                    symbol = stock['symbol']
                    
                    if symbol in self.current_data['constituents'] and symbol in normalized_lots:
                        constituent_data = self.current_data['constituents'][symbol]
                        straddle_premium = constituent_data['otm_levels'].get(otm_level, {}).get('straddle_premium', 0)
                        
                        normalized_lot_data = normalized_lots[symbol]
                        total_quantity = normalized_lot_data['total_quantity']
                        
                        total_constituent_premium += total_quantity * straddle_premium
                
                # Net premium = Buy BankNifty straddle - Sell constituent straddles
                net_premium = bn_premium - total_constituent_premium
                self.current_data['net_premium'][otm_level] = net_premium
                
        except Exception as e:
            logger.error(f"Error calculating net premiums: {str(e)}")
    
    def update_market_data(self):
        """Update market data for BankNifty and constituents"""
        try:
            if not self.current_data['monitoring_active']:
                return
                
            expiry_date = datetime.fromisoformat(self.current_data['expiry_date']).date()
            
            # Update BankNifty data
            bn_data = self.get_option_chain_data('BANKNIFTY', expiry_date)
            if bn_data:
                self.current_data['banknifty'].update(bn_data)
            
            # Update constituent data
            for stock in BANKNIFTY_CONSTITUENTS:
                symbol = stock['symbol']
                stock_data = self.get_option_chain_data(symbol, expiry_date)
                
                if stock_data:
                    self.current_data['constituents'][symbol] = stock_data
                    self.current_data['constituents'][symbol]['weight'] = stock['weight']
                    self.current_data['constituents'][symbol]['lot_size'] = stock['lot_size']
            
            # Calculate net premiums for all OTM levels
            self.calculate_net_premiums()
            
            # Update timestamp
            self.current_data['last_updated'] = datetime.now().isoformat()
            
            # Store in database
            db_manager.store_historical_data(self.current_data)
            
            # Check for alerts
            self.check_alerts()
            
            # Maintain in-memory historical data for charts
            self.historical_data.append({
                'timestamp': datetime.now().isoformat(),
                'banknifty_spot': self.current_data['banknifty']['spot'],
                'net_premium_atm': self.current_data['net_premium']['ATM'],
                'net_premium_otm1': self.current_data['net_premium']['OTM1'],
                'net_premium_otm2': self.current_data['net_premium']['OTM2'],
                'net_premium_otm3': self.current_data['net_premium']['OTM3']
            })
            
            # Keep only last 100 records in memory
            if len(self.historical_data) > 100:
                self.historical_data.pop(0)
            
        except Exception as e:
            logger.error(f"Error updating market data: {str(e)}")
    
    def check_alerts(self):
        """Check for alert conditions and trigger notifications"""
        try:
            settings = db_manager.get_settings()
            
            if not settings.get('auto_alerts_enabled', True):
                return
                
            threshold = settings.get('alert_threshold', 10000)
            
            for otm_level in OTM_LEVELS:
                net_premium = self.current_data['net_premium'][otm_level]
                
                if abs(net_premium) >= threshold:
                    alert_message = f"{otm_level} Net Premium Alert: ₹{net_premium:.2f} (Threshold: ₹{threshold:.2f})"
                    
                    # Store alert in database
                    db_manager.store_alert(otm_level, net_premium, threshold, alert_message)
                    
                    # Add to in-memory alerts
                    alert_data = {
                        'timestamp': datetime.now().isoformat(),
                        'otm_level': otm_level,
                        'net_premium': net_premium,
                        'threshold': threshold,
                        'message': alert_message
                    }
                    self.alerts_data.append(alert_data)
                    
                    logger.info(f"Alert triggered: {alert_message}")
            
            # Keep only last 50 alerts in memory
            if len(self.alerts_data) > 50:
                self.alerts_data.pop(0)
                
        except Exception as e:
            logger.error(f"Error checking alerts: {str(e)}")
    
    def start_monitoring(self):
        """Start dispersion trade monitoring"""
        try:
            if self.should_start_monitoring():
                self.current_data['monitoring_active'] = True
                self.calculate_normalized_lots()
                return True, f"Monitoring started. Days to expiry: {self.current_data['days_to_expiry']}"
            else:
                return False, f"Monitoring will start {MONITORING_DAYS_BEFORE_EXPIRY} days before expiry. Current days to expiry: {self.current_data['days_to_expiry']}"
                
        except Exception as e:
            logger.error(f"Error starting monitoring: {str(e)}")
            return False, str(e)
    
    def stop_monitoring(self):
        """Stop dispersion trade monitoring"""
        try:
            self.current_data['monitoring_active'] = False
            return True, "Monitoring stopped"
        except Exception as e:
            logger.error(f"Error stopping monitoring: {str(e)}")
            return False, str(e)
    
    def get_current_data(self):
        """Get current market data"""
        return self.current_data.copy()

# Global market data manager instance
market_data_manager = MarketDataManager()
