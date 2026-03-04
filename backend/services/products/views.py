from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from .models import Category, Product, ProductVariant, Review, Coupon
from .serializers import (
    CategorySerializer, ProductListSerializer, ProductDetailSerializer,
    ProductVariantSerializer, ReviewSerializer, CouponSerializer
)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for product categories.
    """
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Only return top-level categories by default
        if self.action == 'list':
            return queryset.filter(parent=None)
        return queryset


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for products.
    """
    queryset = Product.objects.filter(is_active=True).select_related('category', 'vendor')
    permission_classes = [AllowAny]
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'vendor', 'is_featured']
    search_fields = ['name', 'description', 'short_description']
    ordering_fields = ['created_at', 'base_price', 'name']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductListSerializer
    
    @action(detail=True, methods=['get'])
    def reviews(self, request, slug=None):
        """Get reviews for a specific product."""
        product = self.get_object()
        reviews = product.reviews.filter(is_approved=True).order_by('-created_at')
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def variants(self, request, slug=None):
        """Get variants for a specific product."""
        product = self.get_object()
        variants = product.variants.filter(is_active=True)
        serializer = ProductVariantSerializer(variants, many=True)
        return Response(serializer.data)


class ReviewViewSet(viewsets.ModelViewSet):
    """
    API endpoint for product reviews.
    """
    queryset = Review.objects.filter(is_approved=True)
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['product', 'rating']
    ordering_fields = ['created_at', 'rating']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Users can see their own reviews even if not approved
        if self.request.user.is_authenticated:
            return queryset | Review.objects.filter(user=self.request.user)
        return queryset


class CouponViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for validating coupons.
    """
    queryset = Coupon.objects.filter(is_active=True)
    serializer_class = CouponSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'code'
    
    @action(detail=True, methods=['post'])
    def validate(self, request, code=None):
        """Validate a coupon code."""
        coupon = self.get_object()
        
        if not coupon.is_valid:
            return Response(
                {'error': 'Coupon is not valid or has expired'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Additional validation can be added here
        # (e.g., check if user has already used the coupon)
        
        return Response({
            'valid': True,
            'discount_type': coupon.discount_type,
            'discount_value': coupon.discount_value,
            'min_purchase_amount': coupon.min_purchase_amount
        })
