from rest_framework import serializers
from .models import Cart, CartItem, Wishlist, WishlistItem
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
