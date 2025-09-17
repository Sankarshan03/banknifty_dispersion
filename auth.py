# auth.py - Authentication Module for Zerodha API
import pyotp
import logging
from kiteconnect import KiteConnect
from config import API_KEY, API_SECRET, REQUEST_TOKEN, TOTP_SECRET

logger = logging.getLogger(__name__)

class ZerodhaAuth:
    """Handles Zerodha authentication and TOTP operations"""
    
    def __init__(self):
        self.kite = KiteConnect(api_key=API_KEY)
        self.access_token = None
        self._request_token = REQUEST_TOKEN
    
    def get_current_totp(self):
        """Get current TOTP for manual use"""
        try:
            if TOTP_SECRET:
                totp = pyotp.TOTP(TOTP_SECRET)
                return totp.now()
            return None
        except Exception as e:
            logger.error(f"Error generating TOTP: {str(e)}")
            return None
    
    def obtain_access_token(self):
        """Obtain access token using API_KEY, API_SECRET and REQUEST_TOKEN"""
        try:
            if not self._request_token:
                # If no request token, try to get it via login flow with TOTP
                return self._obtain_access_token_with_totp()
            
            data = self.kite.generate_session(self._request_token, api_secret=API_SECRET)
            self.access_token = data['access_token']
            self.kite.set_access_token(self.access_token)
            logger.info(f"Access token obtained successfully: {self.access_token[:20]}...")
            return self.access_token
        except Exception as e:
            logger.error(f"Error obtaining access token with request token: {str(e)}")
            # Fallback to TOTP login
            return self._obtain_access_token_with_totp()
    
    def _obtain_access_token_with_totp(self):
        """Obtain access token using TOTP authentication"""
        try:
            if not TOTP_SECRET:
                raise Exception("TOTP_SECRET not set. Please set TOTP_SECRET in .env file.")
            
            # Generate TOTP
            current_totp = self.get_current_totp()
            logger.info(f"Generated TOTP: {current_totp}")
            
            # If we still have a request token, try to use it
            if self._request_token:
                data = self.kite.generate_session(self._request_token, api_secret=API_SECRET)
                self.access_token = data['access_token']
                self.kite.set_access_token(self.access_token)
                logger.info(f"Access token obtained with TOTP validation: {self.access_token[:20]}...")
                return self.access_token
            else:
                raise Exception("No request token available. Please complete Zerodha login flow.")
                
        except Exception as e:
            logger.error(f"Error with TOTP authentication: {str(e)}")
            raise e
    
    def get_login_url(self):
        """Get Zerodha login URL"""
        try:
            return self.kite.login_url()
        except Exception as e:
            logger.error(f"Error getting login URL: {str(e)}")
            raise e
    
    def process_login_callback(self, request_token):
        """Process login callback with request token"""
        try:
            # Update the request token
            self._request_token = request_token
            
            # Generate session with the new request token
            data = self.kite.generate_session(request_token, api_secret=API_SECRET)
            self.access_token = data['access_token']
            self.kite.set_access_token(self.access_token)
            
            logger.info(f"Login successful! Access token: {self.access_token[:20]}...")
            return True
            
        except Exception as e:
            logger.error(f"Error processing login callback: {str(e)}")
            return False
    
    def is_authenticated(self):
        """Check if user is authenticated"""
        return self.access_token is not None
    
    def get_kite_instance(self):
        """Get authenticated KiteConnect instance"""
        if not self.is_authenticated():
            raise Exception("Not authenticated. Please login first.")
        return self.kite
    
    def get_auth_status(self):
        """Get authentication status information"""
        return {
            'authenticated': self.is_authenticated(),
            'access_token_available': self.access_token is not None,
            'current_totp': self.get_current_totp(),
            'login_url': self.get_login_url() if not self.is_authenticated() else None
        }

# Global authentication instance
zerodha_auth = ZerodhaAuth()
