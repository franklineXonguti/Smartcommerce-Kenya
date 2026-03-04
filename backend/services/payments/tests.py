"""
Tests for payments service (M-Pesa).
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from unittest.mock import patch, MagicMock

from services.products.models import Product, ProductVariant, Category
from services.users.models import Address
from services.orders.models import Order, OrderItem
from .models import Payment, MPesaPayment

User = get_user_model()


class MPesaPaymentTestCase(TestCase):
    """Test cases for M-Pesa payment integration."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            phone_number='+254712345678',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Create test category
        self.category = Category.objects.create(
            name='Electronics',
            slug='electronics'
        )
        
        # Create test product
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            description='Test description',
            category=self.category,
            base_price=Decimal('1000.00'),
            is_active=True
        )
        
        # Create product variant
        self.variant = ProductVariant.objects.create(
            product=self.product,
            sku='TEST-001',
            price=Decimal('1000.00'),
            stock=10,
            is_active=True
        )
        
        # Create address
        self.address = Address.objects.create(
            user=self.user,
            full_name='Test User',
            phone_number='+254712345678',
            county='Nairobi',
            town='Nairobi',
            street='Test Street',
            is_default=True
        )
        
        # Create order
        self.order = Order.objects.create(
            user=self.user,
            shipping_address=self.address,
            shipping_full_name=self.address.full_name,
            shipping_phone=self.address.phone_number,
            shipping_county=self.address.county,
            shipping_town=self.address.town,
            shipping_street=self.address.street,
            subtotal=Decimal('2000.00'),
            shipping_cost=Decimal('200.00'),
            discount_amount=Decimal('0.00'),
            total=Decimal('2200.00'),
            status='pending'
        )
        
        # Create order item
        self.order_item = OrderItem.objects.create(
            order=self.order,
            variant=self.variant,
            quantity=2,
            price=Decimal('1000.00')
        )
        
        # Authenticate client
        self.client.force_authenticate(user=self.user)
    
    @patch('services.payments.views.MPesaAPI')
    def test_initiate_mpesa_payment_success(self, mock_mpesa_api):
        """Test successful M-Pesa payment initiation."""
        # Mock M-Pesa API response
        mock_instance = mock_mpesa_api.return_value
        mock_instance.stk_push.return_value = {
            'success': True,
            'merchant_request_id': 'TEST-MERCHANT-123',
            'checkout_request_id': 'TEST-CHECKOUT-456',
            'response_code': '0',
            'response_description': 'Success',
            'customer_message': 'STK Push sent to your phone'
        }
        
        data = {
            'order_id': self.order.id,
            'phone_number': '0712345678'
        }
        
        response = self.client.post('/api/payments/payments/initiate_mpesa/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('checkout_request_id', response.data)
        
        # Verify payment was created
        payment = Payment.objects.get(order=self.order)
        self.assertEqual(payment.payment_method, 'mpesa')
        self.assertEqual(payment.status, 'processing')
        self.assertEqual(payment.amount, self.order.total)
        
        # Verify M-Pesa payment record was created
        mpesa_payment = MPesaPayment.objects.get(payment=payment)
        self.assertEqual(mpesa_payment.checkout_request_id, 'TEST-CHECKOUT-456')
        self.assertEqual(mpesa_payment.phone_number, '254712345678')
    
    @patch('services.payments.views.MPesaAPI')
    def test_initiate_mpesa_payment_failure(self, mock_mpesa_api):
        """Test failed M-Pesa payment initiation."""
        # Mock M-Pesa API response
        mock_instance = mock_mpesa_api.return_value
        mock_instance.stk_push.return_value = {
            'success': False,
            'error_message': 'Invalid phone number'
        }
        
        data = {
            'order_id': self.order.id,
            'phone_number': '0712345678'
        }
        
        response = self.client.post('/api/payments/payments/initiate_mpesa/', data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        
        # Verify payment was created with failed status
        payment = Payment.objects.get(order=self.order)
        self.assertEqual(payment.status, 'failed')
    
    def test_initiate_mpesa_invalid_order(self):
        """Test M-Pesa payment with invalid order."""
        data = {
            'order_id': 9999,
            'phone_number': '0712345678'
        }
        
        response = self.client.post('/api/payments/payments/initiate_mpesa/', data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_initiate_mpesa_already_paid_order(self):
        """Test M-Pesa payment for already paid order."""
        # Create a completed payment
        Payment.objects.create(
            order=self.order,
            user=self.user,
            payment_method='mpesa',
            amount=self.order.total,
            status='completed'
        )
        
        data = {
            'order_id': self.order.id,
            'phone_number': '0712345678'
        }
        
        response = self.client.post('/api/payments/payments/initiate_mpesa/', data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_phone_number_normalization(self):
        """Test phone number normalization."""
        test_cases = [
            ('0712345678', '254712345678'),
            ('254712345678', '254712345678'),
            ('+254712345678', '254712345678'),
            ('0712 345 678', '254712345678'),
        ]
        
        for input_phone, expected_phone in test_cases:
            from services.payments.serializers import InitiateMPesaPaymentSerializer
            serializer = InitiateMPesaPaymentSerializer()
            normalized = serializer.validate_phone_number(input_phone)
            self.assertEqual(normalized, expected_phone)
    
    def test_mpesa_callback_success(self):
        """Test successful M-Pesa callback processing."""
        # Create payment and M-Pesa payment records
        payment = Payment.objects.create(
            order=self.order,
            user=self.user,
            payment_method='mpesa',
            amount=self.order.total,
            status='processing',
            transaction_id='TEST-CHECKOUT-456'
        )
        
        mpesa_payment = MPesaPayment.objects.create(
            payment=payment,
            merchant_request_id='TEST-MERCHANT-123',
            checkout_request_id='TEST-CHECKOUT-456',
            phone_number='254712345678'
        )
        
        # Simulate M-Pesa callback
        callback_data = {
            'Body': {
                'stkCallback': {
                    'MerchantRequestID': 'TEST-MERCHANT-123',
                    'CheckoutRequestID': 'TEST-CHECKOUT-456',
                    'ResultCode': 0,
                    'ResultDesc': 'The service request is processed successfully.',
                    'CallbackMetadata': {
                        'Item': [
                            {'Name': 'Amount', 'Value': 2200},
                            {'Name': 'MpesaReceiptNumber', 'Value': 'TEST-RECEIPT-789'},
                            {'Name': 'TransactionDate', 'Value': 20240304143022},
                            {'Name': 'PhoneNumber', 'Value': 254712345678}
                        ]
                    }
                }
            }
        }
        
        response = self.client.post('/api/payments/mpesa/callback/', callback_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['ResultCode'], 0)
        
        # Verify payment was updated
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'completed')
        self.assertIsNotNone(payment.completed_at)
        
        # Verify M-Pesa payment was updated
        mpesa_payment.refresh_from_db()
        self.assertTrue(mpesa_payment.callback_received)
        self.assertEqual(mpesa_payment.mpesa_receipt_number, 'TEST-RECEIPT-789')
        self.assertEqual(mpesa_payment.result_code, 0)
        
        # Verify order was updated
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'paid')
        self.assertIsNotNone(self.order.paid_at)
    
    def test_mpesa_callback_failure(self):
        """Test failed M-Pesa callback processing."""
        # Create payment and M-Pesa payment records
        payment = Payment.objects.create(
            order=self.order,
            user=self.user,
            payment_method='mpesa',
            amount=self.order.total,
            status='processing',
            transaction_id='TEST-CHECKOUT-456'
        )
        
        mpesa_payment = MPesaPayment.objects.create(
            payment=payment,
            merchant_request_id='TEST-MERCHANT-123',
            checkout_request_id='TEST-CHECKOUT-456',
            phone_number='254712345678'
        )
        
        # Simulate M-Pesa callback with failure
        callback_data = {
            'Body': {
                'stkCallback': {
                    'MerchantRequestID': 'TEST-MERCHANT-123',
                    'CheckoutRequestID': 'TEST-CHECKOUT-456',
                    'ResultCode': 1032,
                    'ResultDesc': 'Request cancelled by user'
                }
            }
        }
        
        response = self.client.post('/api/payments/mpesa/callback/', callback_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify payment was updated to failed
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'failed')
        self.assertIn('cancelled', payment.error_message.lower())
        
        # Verify M-Pesa payment was updated
        mpesa_payment.refresh_from_db()
        self.assertTrue(mpesa_payment.callback_received)
        self.assertEqual(mpesa_payment.result_code, 1032)
    
    def test_list_user_payments(self):
        """Test listing user's payments."""
        # Create some payments
        Payment.objects.create(
            order=self.order,
            user=self.user,
            payment_method='mpesa',
            amount=self.order.total,
            status='completed'
        )
        
        response = self.client.get('/api/payments/payments/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_payments_require_authentication(self):
        """Test payments endpoints require authentication."""
        self.client.force_authenticate(user=None)
        
        response = self.client.get('/api/payments/payments/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
