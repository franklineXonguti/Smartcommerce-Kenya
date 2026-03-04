"""
Serializers for payments service.
"""
from rest_framework import serializers
from .models import Payment, MPesaPayment
from services.orders.models import Order


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for payment details."""
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'order', 'order_number', 'payment_method', 'payment_method_display',
            'amount', 'currency', 'status', 'status_display', 'transaction_id',
            'external_reference', 'error_message', 'created_at', 'completed_at'
        ]
        read_only_fields = fields


class MPesaPaymentSerializer(serializers.ModelSerializer):
    """Serializer for M-Pesa payment details."""
    payment = PaymentSerializer(read_only=True)
    
    class Meta:
        model = MPesaPayment
        fields = [
            'id', 'payment', 'merchant_request_id', 'checkout_request_id',
            'mpesa_receipt_number', 'phone_number', 'transaction_date',
            'result_code', 'result_desc', 'callback_received', 'created_at'
        ]
        read_only_fields = fields


class InitiateMPesaPaymentSerializer(serializers.Serializer):
    """Serializer for initiating M-Pesa STK Push."""
    order_id = serializers.IntegerField()
    phone_number = serializers.CharField(max_length=15)
    
    def validate_order_id(self, value):
        """Validate order exists and belongs to user."""
        request = self.context.get('request')
        if not request or not request.user:
            raise serializers.ValidationError("Authentication required")
        
        try:
            order = Order.objects.get(id=value, user=request.user)
        except Order.DoesNotExist:
            raise serializers.ValidationError("Order not found")
        
        # Check if order is pending payment
        if order.status != 'pending':
            raise serializers.ValidationError("Order is not pending payment")
        
        # Check if there's already a successful payment
        if order.payments.filter(status='completed').exists():
            raise serializers.ValidationError("Order has already been paid")
        
        return value
    
    def validate_phone_number(self, value):
        """Validate and normalize phone number."""
        # Remove spaces and special characters
        phone = value.replace(' ', '').replace('-', '').replace('+', '')
        
        # Convert to international format
        if phone.startswith('0'):
            phone = '254' + phone[1:]
        elif phone.startswith('254'):
            pass
        else:
            raise serializers.ValidationError("Invalid phone number format. Use 07XX or +2547XX")
        
        # Validate length
        if len(phone) != 12:
            raise serializers.ValidationError("Invalid phone number length")
        
        return phone


class MPesaCallbackSerializer(serializers.Serializer):
    """Serializer for M-Pesa callback data."""
    Body = serializers.DictField()
