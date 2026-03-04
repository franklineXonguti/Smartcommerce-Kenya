from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from services.users.models import User


class VendorProfile(models.Model):
    """
    Vendor profile for multi-vendor marketplace.
    """
    APPROVAL_STATUS = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='vendor_profile'
    )
    
    # Business information
    business_name = models.CharField(max_length=255)
    business_description = models.TextField()
    business_email = models.EmailField()
    business_phone = models.CharField(max_length=15)
    
    # Business registration
    registration_number = models.CharField(max_length=100, blank=True)
    tax_id = models.CharField(max_length=100, blank=True)
    
    # Address
    county = models.CharField(max_length=100)
    town = models.CharField(max_length=100)
    street_address = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=20, blank=True)
    
    # Warehouse location for delivery calculations
    warehouse_latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    warehouse_longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    
    # Financial
    commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=15.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Platform commission percentage"
    )
    payout_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00
    )
    
    # Payout details
    bank_name = models.CharField(max_length=100, blank=True)
    bank_account_number = models.CharField(max_length=50, blank=True)
    bank_account_name = models.CharField(max_length=255, blank=True)
    mpesa_number = models.CharField(max_length=15, blank=True)
    
    # Approval
    approval_status = models.CharField(
        max_length=20,
        choices=APPROVAL_STATUS,
        default='pending'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_vendors'
    )
    rejection_reason = models.TextField(blank=True)
    
    # Logo and branding
    logo = models.ImageField(upload_to='vendors/logos/', null=True, blank=True)
    banner = models.ImageField(upload_to='vendors/banners/', null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'vendor_profiles'
        verbose_name = 'Vendor Profile'
        verbose_name_plural = 'Vendor Profiles'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['approval_status']),
            models.Index(fields=['business_name']),
        ]

    def __str__(self):
        return self.business_name

    @property
    def is_approved(self):
        return self.approval_status == 'approved'

    @property
    def total_products(self):
        return self.products.filter(is_active=True).count()

    @property
    def total_sales(self):
        """Calculate total sales amount."""
        from services.orders.models import OrderItem
        return OrderItem.objects.filter(
            product__vendor=self,
            order__status='completed'
        ).aggregate(
            total=models.Sum(models.F('quantity') * models.F('price'))
        )['total'] or 0


class VendorPayout(models.Model):
    """
    Track vendor payout requests and transactions.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    PAYOUT_METHODS = [
        ('bank', 'Bank Transfer'),
        ('mpesa', 'M-Pesa'),
    ]

    vendor = models.ForeignKey(
        VendorProfile,
        on_delete=models.CASCADE,
        related_name='payouts'
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    payout_method = models.CharField(max_length=20, choices=PAYOUT_METHODS)
    
    # Payout details
    account_details = models.JSONField(help_text="Bank or M-Pesa details")
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Transaction reference
    transaction_reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    
    # Processing
    processed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_payouts'
    )

    class Meta:
        db_table = 'vendor_payouts'
        verbose_name = 'Vendor Payout'
        verbose_name_plural = 'Vendor Payouts'
        ordering = ['-requested_at']
        indexes = [
            models.Index(fields=['vendor', 'status']),
            models.Index(fields=['status', '-requested_at']),
        ]

    def __str__(self):
        return f"{self.vendor.business_name} - KES {self.amount} ({self.status})"


class VendorEarning(models.Model):
    """
    Track individual earnings from orders.
    """
    vendor = models.ForeignKey(
        VendorProfile,
        on_delete=models.CASCADE,
        related_name='earnings'
    )
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='vendor_earnings'
    )
    
    # Amounts
    gross_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Total order amount for vendor's products"
    )
    commission_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Platform commission"
    )
    net_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Amount vendor receives"
    )
    commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Commission rate at time of order"
    )
    
    # Payout tracking
    is_paid_out = models.BooleanField(default=False)
    payout = models.ForeignKey(
        VendorPayout,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='earnings'
    )
    paid_out_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'vendor_earnings'
        verbose_name = 'Vendor Earning'
        verbose_name_plural = 'Vendor Earnings'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['vendor', 'is_paid_out']),
            models.Index(fields=['order']),
        ]

    def __str__(self):
        return f"{self.vendor.business_name} - Order {self.order.order_number}"
