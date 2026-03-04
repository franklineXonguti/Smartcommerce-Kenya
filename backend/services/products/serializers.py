from rest_framework import serializers
from .models import Category, Product, ProductVariant, ProductImage, Review, Coupon


class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'parent', 'image', 'is_active', 'children']
        read_only_fields = ['slug']
    
    def get_children(self, obj):
        if obj.children.exists():
            return CategorySerializer(obj.children.filter(is_active=True), many=True).data
        return []


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text', 'is_primary', 'display_order']


class ProductVariantSerializer(serializers.ModelSerializer):
    is_low_stock = serializers.ReadOnlyField()
    is_in_stock = serializers.ReadOnlyField()
    discount_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = ProductVariant
        fields = [
            'id', 'sku', 'size', 'color', 'material',
            'price', 'compare_at_price', 'stock', 'low_stock_threshold',
            'is_active', 'is_low_stock', 'is_in_stock', 'discount_percentage'
        ]
        read_only_fields = ['sku']


class ProductListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    vendor_name = serializers.CharField(source='vendor.business_name', read_only=True, allow_null=True)
    primary_image = serializers.SerializerMethodField()
    min_price = serializers.ReadOnlyField()
    max_price = serializers.ReadOnlyField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'short_description',
            'category', 'category_name', 'vendor', 'vendor_name',
            'base_price', 'min_price', 'max_price', 'currency',
            'primary_image', 'is_featured', 'created_at'
        ]
    
    def get_primary_image(self, obj):
        primary = obj.images.filter(is_primary=True).first()
        if primary:
            return ProductImageSerializer(primary).data
        first_image = obj.images.first()
        if first_image:
            return ProductImageSerializer(first_image).data
        return None


class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    vendor_name = serializers.CharField(source='vendor.business_name', read_only=True, allow_null=True)
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    total_stock = serializers.ReadOnlyField()
    min_price = serializers.ReadOnlyField()
    max_price = serializers.ReadOnlyField()
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'short_description',
            'category', 'vendor', 'vendor_name',
            'base_price', 'min_price', 'max_price', 'currency',
            'track_inventory', 'total_stock',
            'meta_title', 'meta_description',
            'is_active', 'is_featured',
            'images', 'variants',
            'average_rating', 'review_count',
            'created_at', 'updated_at'
        ]
    
    def get_average_rating(self, obj):
        approved_reviews = obj.reviews.filter(is_approved=True)
        if approved_reviews.exists():
            from django.db.models import Avg
            return approved_reviews.aggregate(Avg('rating'))['rating__avg']
        return None
    
    def get_review_count(self, obj):
        return obj.reviews.filter(is_approved=True).count()


class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = Review
        fields = [
            'id', 'product', 'user', 'user_name',
            'rating', 'title', 'comment',
            'is_verified_purchase', 'is_approved',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'is_verified_purchase', 'is_approved']


class CouponSerializer(serializers.ModelSerializer):
    is_valid = serializers.ReadOnlyField()
    
    class Meta:
        model = Coupon
        fields = [
            'id', 'code', 'description',
            'discount_type', 'discount_value',
            'max_uses', 'uses_count', 'max_uses_per_user',
            'min_purchase_amount',
            'valid_from', 'valid_until',
            'is_active', 'is_valid'
        ]
        read_only_fields = ['uses_count']
