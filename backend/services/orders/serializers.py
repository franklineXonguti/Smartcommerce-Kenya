from rest_framework import serializers
from django.utils import timezone
from .models import Cart, CartItem, Wishlist, WishlistItem, Order, OrderItem
from services.users.models import Address
from services.products.models import Coupon
from services.products.serializers import ProductListSerializer, ProductVariantSerializer


class CartItemSerializer(serializers.ModelSerializer):
    """Serializer for cart items."""
    variant = ProductVariantSerializer(read_only=True)
    variant_id = serializers.IntegerField(write_only=True)
    product_name = serializers.CharField(source='variant.product.name', read_only=True)
    product_image = serializers.SerializerMethodField()
    price = serializers.ReadOnlyField()
    subtotal = serializers.ReadOnlyField()
    
    class Meta:
        model = CartItem
        fields = [
            'id', 'variant', 'variant_id', 'product_name', 'product_image',
            'quantity', 'price', 'subtotal', 'added_at', 'updated_at'
        ]
        read_only_fields = ['id', 'added_at', 'updated_at']
    
    def get_product_image(self, obj):
        """Get primary product image."""
        primary_image = obj.variant.product.images.filter(is_primary=True).first()
        if primary_image:
            return primary_image.image.url if primary_image.image else None
        first_image = obj.variant.product.images.first()
        return first_image.image.url if first_image and first_image.image else None
    
    def validate_quantity(self, value):
        """Validate quantity is positive and in stock."""
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1")
        return value
    
    def validate_variant_id(self, value):
        """Validate variant exists and is active."""
        from services.products.models import ProductVariant
        try:
            variant = ProductVariant.objects.get(id=value, is_active=True)
            if not variant.is_in_stock:
                raise serializers.ValidationError("This product is out of stock")
        except ProductVariant.DoesNotExist:
            raise serializers.ValidationError("Product variant not found")
        return value


class CartSerializer(serializers.ModelSerializer):
    """Serializer for shopping cart."""
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.ReadOnlyField()
    subtotal = serializers.ReadOnlyField()
    
    class Meta:
        model = Cart
        fields = [
            'id', 'items', 'total_items', 'subtotal',
            'is_abandoned', 'abandoned_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'is_abandoned', 'abandoned_at', 'created_at', 'updated_at']


class AddToCartSerializer(serializers.Serializer):
    """Serializer for adding items to cart."""
    variant_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, default=1)
    
    def validate_variant_id(self, value):
        """Validate variant exists and is active."""
        from services.products.models import ProductVariant
        try:
            variant = ProductVariant.objects.get(id=value, is_active=True)
            if not variant.is_in_stock:
                raise serializers.ValidationError("This product is out of stock")
        except ProductVariant.DoesNotExist:
            raise serializers.ValidationError("Product variant not found")
        return value


class UpdateCartItemSerializer(serializers.Serializer):
    """Serializer for updating cart item quantity."""
    quantity = serializers.IntegerField(min_value=1)


class WishlistItemSerializer(serializers.ModelSerializer):
    """Serializer for wishlist items."""
    product = ProductListSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = WishlistItem
        fields = ['id', 'product', 'product_id', 'added_at']
        read_only_fields = ['id', 'added_at']
    
    def validate_product_id(self, value):
        """Validate product exists and is active."""
        from services.products.models import Product
        try:
            Product.objects.get(id=value, is_active=True)
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found")
        return value


class WishlistSerializer(serializers.ModelSerializer):
    """Serializer for wishlist."""
    items = WishlistItemSerializer(many=True, read_only=True)
    total_items = serializers.SerializerMethodField()
    
    class Meta:
        model = Wishlist
        fields = ['id', 'items', 'total_items', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def get_total_items(self, obj):
        return obj.items.count()



# Checkout & Order Serializers

class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for order items."""
    product_name = serializers.CharField(source='variant.product.name', read_only=True)
    product_slug = serializers.CharField(source='variant.product.slug', read_only=True)
    variant_sku = serializers.CharField(source='variant.sku', read_only=True)
    product_image = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product_name', 'product_slug', 'variant_sku',
            'product_image', 'quantity', 'price', 'subtotal'
        ]
        read_only_fields = ['id']
    
    def get_product_image(self, obj):
        """Get primary product image."""
        primary_image = obj.variant.product.images.filter(is_primary=True).first()
        if primary_image:
            return primary_image.image.url if primary_image.image else None
        first_image = obj.variant.product.images.first()
        return first_image.image.url if first_image and first_image.image else None


class OrderListSerializer(serializers.ModelSerializer):
    """Serializer for listing orders."""
    items_count = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'status', 'status_display',
            'items_count', 'subtotal', 'shipping_cost', 'discount_amount',
            'total', 'currency', 'created_at', 'paid_at'
        ]
        read_only_fields = fields
    
    def get_items_count(self, obj):
        return obj.items.count()


class OrderDetailSerializer(serializers.ModelSerializer):
    """Serializer for order details."""
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'status', 'status_display',
            'shipping_full_name', 'shipping_phone', 'shipping_county',
            'shipping_town', 'shipping_ward', 'shipping_street', 'shipping_landmark',
            'subtotal', 'shipping_cost', 'discount_amount', 'total', 'currency',
            'coupon_code', 'customer_notes', 'items',
            'created_at', 'updated_at', 'paid_at', 'shipped_at', 'delivered_at'
        ]
        read_only_fields = fields


class CheckoutSerializer(serializers.Serializer):
    """Serializer for checkout process."""
    address_id = serializers.IntegerField()
    coupon_code = serializers.CharField(max_length=50, required=False, allow_blank=True)
    customer_notes = serializers.CharField(required=False, allow_blank=True)
    payment_method = serializers.ChoiceField(choices=['stripe', 'mpesa'])
    
    def validate_address_id(self, value):
        """Validate address exists and belongs to user."""
        request = self.context.get('request')
        if not request or not request.user:
            raise serializers.ValidationError("Authentication required")
        
        try:
            address = Address.objects.get(id=value, user=request.user)
        except Address.DoesNotExist:
            raise serializers.ValidationError("Address not found")
        
        return value
    
    def validate_coupon_code(self, value):
        """Validate coupon code if provided."""
        if not value:
            return value
        
        try:
            coupon = Coupon.objects.get(code=value, is_active=True)
            
            # Check if coupon is expired
            now = timezone.now()
            if coupon.valid_from and now < coupon.valid_from:
                raise serializers.ValidationError("Coupon is not yet valid")
            if coupon.valid_until and now > coupon.valid_until:
                raise serializers.ValidationError("Coupon has expired")
            
            # Check usage limit
            if coupon.max_uses and coupon.uses_count >= coupon.max_uses:
                raise serializers.ValidationError("Coupon usage limit reached")
            
        except Coupon.DoesNotExist:
            raise serializers.ValidationError("Invalid coupon code")
        
        return value


class OrderStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating order status."""
    status = serializers.ChoiceField(choices=Order.STATUS_CHOICES)
    admin_notes = serializers.CharField(required=False, allow_blank=True)
