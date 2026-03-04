from django.db import models
from django.core.validators import MinValueValidator
from services.users.models import User
from services.orders.models import Order


class Payment(models.Model):
    """
    Payment transactions for orders.
    """
    PAYMENT_METHODS = [
        ('mpesa', 'M-Pesa'),
        ('stripe', 'Stripe (Card)'),
        ('cash', 'Cash on Delivery'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    
    # Payment details
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    currency = models.CharField(max_length=3, default='KES')
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # External references
    transaction_id = models.CharField(max_length=255, unique=True, blank=True)
    external_reference = models.CharField(max_length=255, blank=True)
    
    # Response data
    response_data = models.JSONField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'payments'
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['transaction_id']),
            models.Index(fields=['status']),
            models.Index(fields=['payment_method', 'status']),
        ]

    def __str__(self):
        return f"Payment {self.transaction_id} - {self.order.order_number}"


class StripePayment(models.Model):
    """
    Stripe-specific payment details.
    """
    payment = models.OneToOneField(
        Payment,
        on_delete=models.CASCADE,
        related_name='stripe_details'
    )
    
    # Stripe IDs
    payment_intent_id = models.CharField(max_length=255, unique=True)
    checkout_session_id = models.CharField(max_length=255, blank=True)
    charge_id = models.CharField(max_length=255, blank=True)
    
    # Card details (last 4 digits only)
    card_brand = models.CharField(max_length=50, blank=True)
    card_last4 = models.CharField(max_length=4, blank=True)
    card_exp_month = models.IntegerField(null=True, blank=True)
    card_exp_year = models.IntegerField(null=True, blank=True)
    
    # Receipt
    receipt_url = models.URLField(blank=True)
    
    # Refund
    refund_id = models.CharField(max_length=255, blank=True)
    refund_reason = models.TextField(blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'stripe_payments'
        verbose_name = 'Stripe Payment'
        verbose_name_plural = 'Stripe Payments'
        ordering = ['-created_at']

    def __str__(self):
        return f"Stripe Payment {self.payment_intent_id}"


class MPesaPayment(models.Model):
    """
    M-Pesa-specific payment details.
    """
    payment = models.OneToOneField(
        Payment,
        on_delete=models.CASCADE,
        related_name='mpesa_details'
    )
    
    # M-Pesa transaction details
    merchant_request_id = models.CharField(max_length=255)
    checkout_request_id = models.CharField(max_length=255, unique=True)
    mpesa_receipt_number = models.CharField(max_length=255, blank=True)
    
    # Customer details
    phone_number = models.CharField(max_length=15)
    
    # Transaction details
    transaction_date = models.DateTimeField(null=True, blank=True)
    result_code = models.IntegerField(null=True, blank=True)
    result_desc = models.TextField(blank=True)
    
    # Callback data
    callback_received = models.BooleanField(default=False)
    callback_data = models.JSONField(null=True, blank=True)
    callback_received_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'mpesa_payments'
        verbose_name = 'M-Pesa Payment'
        verbose_name_plural = 'M-Pesa Payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['checkout_request_id']),
            models.Index(fields=['mpesa_receipt_number']),
        ]

    def __str__(self):
        return f"M-Pesa Payment {self.checkout_request_id}"


class Refund(models.Model):
    """
    Refund requests and processing.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    REASON_CHOICES = [
        ('customer_request', 'Customer Request'),
        ('damaged_product', 'Damaged Product'),
        ('wrong_item', 'Wrong Item Sent'),
        ('not_received', 'Not Received'),
        ('fraud', 'Fraudulent Order'),
        ('other', 'Other'),
    ]

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='refunds'
    )
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='refunds'
    )
    
    # Refund details
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    reason = models.CharField(max_length=50, choices=REASON_CHOICES)
    description = models.TextField()
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Processing
    requested_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='refund_requests'
    )
    processed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_refunds'
    )
    
    # External reference
    refund_transaction_id = models.CharField(max_length=255, blank=True)
    
    # Notes
    admin_notes = models.TextField(blank=True)
    
    # Timestamps
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'refunds'
        verbose_name = 'Refund'
        verbose_name_plural = 'Refunds'
        ordering = ['-requested_at']
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Refund for {self.order.order_number} - KES {self.amount}"
