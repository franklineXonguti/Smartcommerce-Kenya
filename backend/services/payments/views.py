"""
Views for payments service.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction as db_transaction
import logging

from .models import Payment, MPesaPayment
from .serializers import (
    PaymentSerializer, MPesaPaymentSerializer,
    InitiateMPesaPaymentSerializer, MPesaCallbackSerializer
)
from .mpesa import MPesaAPI
from services.orders.models import Order

logger = logging.getLogger(__name__)


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for payment management.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentSerializer
    
    def get_queryset(self):
        """Return payments for the authenticated user."""
        return Payment.objects.filter(user=self.request.user).select_related('order')
    
    @action(detail=False, methods=['post'])
    def initiate_mpesa(self, request):
        """
        Initiate M-Pesa STK Push payment.
        """
        serializer = InitiateMPesaPaymentSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        order_id = serializer.validated_data['order_id']
        phone_number = serializer.validated_data['phone_number']
        
        # Get order
        order = get_object_or_404(Order, id=order_id, user=request.user)
        
        # Create payment record
        payment = Payment.objects.create(
            order=order,
            user=request.user,
            payment_method='mpesa',
            amount=order.total,
            currency='KES',
            status='pending'
        )
        
        # Initiate STK Push
        mpesa_api = MPesaAPI()
        result = mpesa_api.stk_push(
            phone_number=phone_number,
            amount=order.total,
            account_reference=order.order_number,
            transaction_desc=f'Payment for order {order.order_number}'
        )
        
        if result.get('success'):
            # Create M-Pesa payment record
            mpesa_payment = MPesaPayment.objects.create(
                payment=payment,
                merchant_request_id=result['merchant_request_id'],
                checkout_request_id=result['checkout_request_id'],
                phone_number=phone_number
            )
            
            # Update payment with transaction ID
            payment.transaction_id = result['checkout_request_id']
            payment.status = 'processing'
            payment.response_data = result
            payment.save()
            
            return Response({
                'success': True,
                'message': result.get('customer_message', 'STK Push sent to your phone'),
                'payment_id': payment.id,
                'checkout_request_id': result['checkout_request_id'],
                'merchant_request_id': result['merchant_request_id']
            }, status=status.HTTP_200_OK)
        else:
            # Update payment status to failed
            payment.status = 'failed'
            payment.error_message = result.get('error_message', 'STK Push failed')
            payment.response_data = result
            payment.save()
            
            return Response({
                'success': False,
                'message': result.get('error_message', 'Failed to initiate payment'),
                'payment_id': payment.id
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """
        Check payment status.
        """
        payment = self.get_object()
        
        # If payment has M-Pesa details, query status
        if hasattr(payment, 'mpesa_details'):
            mpesa_payment = payment.mpesa_details
            
            # If callback not received, query status
            if not mpesa_payment.callback_received:
                mpesa_api = MPesaAPI()
                result = mpesa_api.query_transaction_status(
                    mpesa_payment.checkout_request_id
                )
                
                return Response({
                    'payment_id': payment.id,
                    'status': payment.status,
                    'query_result': result
                })
        
        return Response({
            'payment_id': payment.id,
            'status': payment.status,
            'completed_at': payment.completed_at
        })


@api_view(['POST'])
@permission_classes([AllowAny])
def mpesa_callback(request):
    """
    M-Pesa callback endpoint for STK Push results.
    This endpoint receives payment confirmation from Safaricom.
    """
    logger.info(f"M-Pesa Callback received: {request.data}")
    
    try:
        serializer = MPesaCallbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        callback_data = serializer.validated_data['Body']
        stk_callback = callback_data.get('stkCallback', {})
        
        merchant_request_id = stk_callback.get('MerchantRequestID')
        checkout_request_id = stk_callback.get('CheckoutRequestID')
        result_code = stk_callback.get('ResultCode')
        result_desc = stk_callback.get('ResultDesc')
        
        # Find M-Pesa payment record
        try:
            mpesa_payment = MPesaPayment.objects.select_related('payment', 'payment__order').get(
                checkout_request_id=checkout_request_id
            )
        except MPesaPayment.DoesNotExist:
            logger.error(f"M-Pesa payment not found for CheckoutRequestID: {checkout_request_id}")
            return Response({'ResultCode': 0, 'ResultDesc': 'Accepted'})
        
        payment = mpesa_payment.payment
        order = payment.order
        
        # Update M-Pesa payment record
        with db_transaction.atomic():
            mpesa_payment.callback_received = True
            mpesa_payment.callback_received_at = timezone.now()
            mpesa_payment.callback_data = callback_data
            mpesa_payment.result_code = result_code
            mpesa_payment.result_desc = result_desc
            
            # Check if payment was successful
            if result_code == 0:
                # Extract callback metadata
                callback_metadata = stk_callback.get('CallbackMetadata', {})
                items = callback_metadata.get('Item', [])
                
                # Extract transaction details
                for item in items:
                    name = item.get('Name')
                    value = item.get('Value')
                    
                    if name == 'MpesaReceiptNumber':
                        mpesa_payment.mpesa_receipt_number = value
                        payment.external_reference = value
                    elif name == 'TransactionDate':
                        # Convert timestamp to datetime
                        # Format: 20240304143022 (YYYYMMDDHHmmss)
                        try:
                            mpesa_payment.transaction_date = timezone.datetime.strptime(
                                str(value), '%Y%m%d%H%M%S'
                            )
                        except:
                            pass
                
                # Update payment status
                payment.status = 'completed'
                payment.completed_at = timezone.now()
                
                # Update order status
                order.status = 'paid'
                order.paid_at = timezone.now()
                order.save()
                
                logger.info(f"Payment completed for order {order.order_number}")
            else:
                # Payment failed
                payment.status = 'failed'
                payment.error_message = result_desc
                
                logger.warning(f"Payment failed for order {order.order_number}: {result_desc}")
            
            mpesa_payment.save()
            payment.save()
        
        # Return success response to M-Pesa
        return Response({
            'ResultCode': 0,
            'ResultDesc': 'Accepted'
        })
    
    except Exception as e:
        logger.error(f"Error processing M-Pesa callback: {str(e)}", exc_info=True)
        
        # Still return success to M-Pesa to avoid retries
        return Response({
            'ResultCode': 0,
            'ResultDesc': 'Accepted'
        })
