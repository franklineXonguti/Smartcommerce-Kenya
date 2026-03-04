from rest_framework import viewsets, filters, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from .models import Category, Product, ProductVariant, ProductImage, Review, Coupon
from .serializers import (
    CategorySerializer, ProductListSerializer, ProductDetailSerializer,
    ProductVariantSerializer, ReviewSerializer, CouponSerializer
)
from .permissions import IsVendorOrReadOnly, IsProductOwner
from .tasks import process_product_csv


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


class ProductViewSet(viewsets.ModelViewSet):
    """
    API endpoint for products.
    """
    queryset = Product.objects.filter(is_active=True).select_related('category', 'vendor')
    permission_classes = [IsVendorOrReadOnly]
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
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Vendors can see their own products including inactive ones
        if self.request.user.is_authenticated and self.request.user.is_vendor:
            vendor_profile = getattr(self.request.user, 'vendor_profile', None)
            if vendor_profile:
                return Product.objects.filter(vendor=vendor_profile).select_related('category', 'vendor')
        
        return queryset
    
    def perform_create(self, serializer):
        # Assign vendor to product
        vendor_profile = getattr(self.request.user, 'vendor_profile', None)
        serializer.save(vendor=vendor_profile)
    
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
    
    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def bulk_upload(self, request):
        """Bulk upload products via CSV."""
        if not request.user.is_vendor:
            return Response(
                {'error': 'Only vendors can upload products'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        csv_file = request.FILES.get('file')
        if not csv_file:
            return Response(
                {'error': 'No file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not csv_file.name.endswith('.csv'):
            return Response(
                {'error': 'File must be a CSV'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Read CSV content
        csv_content = csv_file.read().decode('utf-8')
        
        # Get vendor profile
        vendor_profile = getattr(request.user, 'vendor_profile', None)
        if not vendor_profile:
            return Response(
                {'error': 'Vendor profile not found'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Process CSV asynchronously
        task = process_product_csv.delay(csv_content, vendor_profile.id)
        
        return Response({
            'message': 'CSV upload started. Processing in background.',
            'task_id': task.id
        }, status=status.HTTP_202_ACCEPTED)
    
    @action(detail=False, methods=['get'])
    def my_products(self, request):
        """Get products for the authenticated vendor."""
        if not request.user.is_vendor:
            return Response(
                {'error': 'Only vendors can access this endpoint'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        vendor_profile = getattr(request.user, 'vendor_profile', None)
        if not vendor_profile:
            return Response([], status=status.HTTP_200_OK)
        
        products = Product.objects.filter(vendor=vendor_profile).select_related('category')
        serializer = self.get_serializer(products, many=True)
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
