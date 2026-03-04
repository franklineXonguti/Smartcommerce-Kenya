"""
M-Pesa Daraja API Integration.
"""
import requests
import base64
from datetime import datetime
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class MPesaAPI:
    """M-Pesa Daraja API client."""
    
    def __init__(self):
        self.environment = getattr(settings, 'MPESA_ENVIRONMENT', 'sandbox')
        self.consumer_key = getattr(settings, 'MPESA_CONSUMER_KEY', '')
        self.consumer_secret = getattr(settings, 'MPESA_CONSUMER_SECRET', '')
        self.shortcode = getattr(settings, 'MPESA_SHORTCODE', '174379')
        self.passkey = getattr(settings, 'MPESA_PASSKEY', '')
        self.callback_url = getattr(settings, 'MPESA_CALLBACK_URL', '')
        
        # Set base URL based on environment
        if self.environment == 'production':
            self.base_url = 'https://api.safaricom.co.ke'
        else:
            self.base_url = 'https://sandbox.safaricom.co.ke'
    
    def get_access_token(self):
        """
        Get OAuth access token from M-Pesa API.
        """
        url = f'{self.base_url}/oauth/v1/generate?grant_type=client_credentials'
        
        try:
            response = requests.get(
                url,
                auth=(self.consumer_key, self.consumer_secret),
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            return data.get('access_token')
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get M-Pesa access token: {str(e)}")
            raise Exception(f"Failed to authenticate with M-Pesa: {str(e)}")
    
    def generate_password(self, timestamp):
        """
        Generate password for STK Push.
        Password = Base64(Shortcode + Passkey + Timestamp)
        """
        data_to_encode = f"{self.shortcode}{self.passkey}{timestamp}"
        encoded = base64.b64encode(data_to_encode.encode())
        return encoded.decode('utf-8')
    
    def stk_push(self, phone_number, amount, account_reference, transaction_desc):
        """
        Initiate STK Push (Lipa Na M-Pesa Online).
        
        Args:
            phone_number: Customer phone number (format: 254XXXXXXXXX)
            amount: Amount to charge
            account_reference: Order number or reference
            transaction_desc: Description of transaction
        
        Returns:
            dict: Response from M-Pesa API
        """
        # Get access token
        access_token = self.get_access_token()
        
        # Generate timestamp and password
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password = self.generate_password(timestamp)
        
        # Prepare request
        url = f'{self.base_url}/mpesa/stkpush/v1/processrequest'
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'BusinessShortCode': self.shortcode,
            'Password': password,
            'Timestamp': timestamp,
            'TransactionType': 'CustomerPayBillOnline',
            'Amount': int(amount),  # Must be integer
            'PartyA': phone_number,
            'PartyB': self.shortcode,
            'PhoneNumber': phone_number,
            'CallBackURL': self.callback_url,
            'AccountReference': account_reference,
            'TransactionDesc': transaction_desc
        }
        
        try:
            logger.info(f"Initiating STK Push for {phone_number}, Amount: {amount}")
            
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            data = response.json()
            
            # Log response
            logger.info(f"STK Push Response: {data}")
            
            # Check if request was successful
            if data.get('ResponseCode') == '0':
                return {
                    'success': True,
                    'merchant_request_id': data.get('MerchantRequestID'),
                    'checkout_request_id': data.get('CheckoutRequestID'),
                    'response_code': data.get('ResponseCode'),
                    'response_description': data.get('ResponseDescription'),
                    'customer_message': data.get('CustomerMessage')
                }
            else:
                return {
                    'success': False,
                    'error_code': data.get('errorCode'),
                    'error_message': data.get('errorMessage', 'STK Push failed'),
                    'response_code': data.get('ResponseCode'),
                    'response_description': data.get('ResponseDescription')
                }
        
        except requests.exceptions.RequestException as e:
            logger.error(f"STK Push request failed: {str(e)}")
            return {
                'success': False,
                'error_message': f"Network error: {str(e)}"
            }
        except Exception as e:
            logger.error(f"STK Push error: {str(e)}")
            return {
                'success': False,
                'error_message': f"Error: {str(e)}"
            }
    
    def query_transaction_status(self, checkout_request_id):
        """
        Query the status of an STK Push transaction.
        
        Args:
            checkout_request_id: CheckoutRequestID from STK Push response
        
        Returns:
            dict: Transaction status
        """
        # Get access token
        access_token = self.get_access_token()
        
        # Generate timestamp and password
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password = self.generate_password(timestamp)
        
        # Prepare request
        url = f'{self.base_url}/mpesa/stkpushquery/v1/query'
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'BusinessShortCode': self.shortcode,
            'Password': password,
            'Timestamp': timestamp,
            'CheckoutRequestID': checkout_request_id
        }
        
        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            data = response.json()
            logger.info(f"Transaction Status Query Response: {data}")
            
            return {
                'success': True,
                'response_code': data.get('ResponseCode'),
                'response_description': data.get('ResponseDescription'),
                'result_code': data.get('ResultCode'),
                'result_desc': data.get('ResultDesc')
            }
        
        except Exception as e:
            logger.error(f"Transaction status query failed: {str(e)}")
            return {
                'success': False,
                'error_message': str(e)
            }
