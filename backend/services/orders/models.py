from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from services.users.models import User, Address
from services.products.models import Product, ProductVariant, Coupon


class Order(models.Model):
    """
    Customer orders.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('paid', 'Paid'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]

    # Order identification
    order_number = models.CharField(max_length=50, unique=True, editable=False)
    
    # Customer
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    
    # Shipping address
    shipping_address = models.ForeignKey(
        Address,
        on_delete=models.SET_NULL,
        null=True,
        related_name='orders'
    )
    
    # Snapshot of address at time of order (in case address is deleted/changed)
    shipping_full_name = models.CharField(max_length=255)
    shipping_phone = models.CharField(max_length=15)
    shipping_county = models.CharField(max_length=100)
    shipping_town = models.CharField(max_length=100)
    shipping_ward = models.CharField(max_length=100, blank=True)
    shipping_street = models.CharField(max_length=255)
    shipping_landmark = models.CharField(max_length=255, blank=True)
    
    # Pricing
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    shipping_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)]
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)]
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    currency = models.CharField(max_length=3, default='KES')
    
    # Coupon
    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )
    coupon_code = models.CharField(max_length=50, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Notes
    customer_notes = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True)
    
    # Fraud detection
    is_flagged = models.BooleanField(default=False)
    fraud_score = models.IntegerField(default=0)
    fraud_reason = models.TextField(blank=True)
    
    # IP tracking for fraud detection
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'orders'
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['is_flagged']),
        ]

    def __str__(self):
        return f"Order {self.order_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate order number: ORD-KE-YYYY-XXXXXX
            year = timezone.now().year
            last_order = Order.objects.filter(
                order_number__startswith=f'ORD-KE-{year}'
            ).order_by('-order_number').first()
            
            if last_order:
                last_number = int(last_order.order_number.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.order_number = f'ORD-KE-{year}-{new_number:06d}'
        
        super().save(*args, **kwargs)

    @property
    def can_be_cancelled(self):
        """Check if order can be cancelled."""
        return self.status in ['pending', 'paid', 'processing']


class OrderItem(models.Model):
    """
    Individual items in an order.
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        related_name='order_items'
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='order_items'
    )
    
    # Snapshot of product details at time of order
    product_name = models.CharField(max_length=255)
    variant_details = models.JSONField(null=True, blank=True)
    sku = models.CharField(max_length=100)
    
    # Pricing
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'order_items'
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'
        ordering = ['order', 'id']
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['product']),
        ]

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"

    def save(self, *args, **kwargs):
        self.subtotal = self.price * self.quantity
        super().save(*args, **kwargs)


class OrderStatusHistory(models.Model):
    """
    Track order status changes for transparency.
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='status_history'
    )
    old_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)
    notes = models.TextField(blank=True)
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'order_status_history'
        verbose_name = 'Order Status History'
        verbose_name_plural = 'Order Status Histories'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.order.order_number}: {self.old_status} → {self.new_status}"


class Cart(models.Model):
    """
    Shopping cart for authenticated users.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='cart'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Cart recovery
    is_abandoned = models.BooleanField(default=False)
    abandoned_at = models.DateTimeField(null=True, blank=True)
    recovery_email_sent = models.BooleanField(default=False)
    recovery_email_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'carts'
        verbose_name = 'Cart'
        verbose_name_plural = 'Carts'

    def __str__(self):
        return f"Cart for {self.user.email}"

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def subtotal(self):
        return sum(item.subtotal for item in self.items.all())


class CartItem(models.Model):
    """
    Items in a shopping cart.
    """
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name='cart_items'
    )
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cart_items'
        verbose_name = 'Cart Item'
        verbose_name_plural = 'Cart Items'
        unique_together = ['cart', 'variant']
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.variant} x {self.quantity}"

    @property
    def price(self):
        return self.variant.price

    @property
    def subtotal(self):
        return self.variant.price * self.quantity


class Wishlist(models.Model):
    """
    User wishlist.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='wishlist'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'wishlists'
        verbose_name = 'Wishlist'
        verbose_name_plural = 'Wishlists'

    def __str__(self):
        return f"Wishlist for {self.user.email}"


class WishlistItem(models.Model):
    """
    Items in a wishlist.
    """
    wishlist = models.ForeignKey(
        Wishlist,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='wishlist_items'
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'wishlist_items'
        verbose_name = 'Wishlist Item'
        verbose_name_plural = 'Wishlist Items'
        unique_together = ['wishlist', 'product']
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.product.name}"
