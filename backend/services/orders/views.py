from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Cart, CartItem, Wishlist, WishlistItem
from .serializers import (
    CartSerializer, CartItemSerializer, AddToCartSerializer,
    UpdateCartItemSerializer, WishlistSerializer, WishlistItemSerializer
)
from services.products.models import Product, ProductVariant


class CartViewSet(viewsets.ViewSet):
    """
    API endpoint for shopping cart management.
    """
    permission_classes = [IsAuthenticated]
    
    def get_or_create_cart(self, user):
        """Get or create cart for user."""
        cart, created = Cart.objects.get_or_create(user=user)
        return cart
    
    def list(self, request):
        """Get user's cart."""
        cart = self.get_or_create_cart(request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def add_item(self, request):
        """Add item to cart."""
        serializer = AddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        cart = self.get_or_create_cart(request.user)
        variant_id = serializer.validated_data['variant_id']
        quantity = serializer.validated_data['quantity']
        
        variant = get_object_or_404(ProductVariant, id=variant_id, is_active=True)
        
        # Check stock availability
        if variant.stock < quantity:
            return Response(
                {'error': f'Only {variant.stock} items available in stock'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if item already in cart
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            variant=variant,
            defaults={'quantity': quantity}
        )
        
        if not created:
            # Update quantity if item already exists
            new_quantity = cart_item.quantity + quantity
            if variant.stock < new_quantity:
                return Response(
                    {'error': f'Only {variant.stock} items available in stock'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            cart_item.quantity = new_quantity
            cart_item.save()
        
        # Update cart timestamp
        cart.save()
        
        return Response(
            CartItemSerializer(cart_item).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['patch'], url_path='items/(?P<item_id>[^/.]+)')
    def update_item(self, request, item_id=None):
        """Update cart item quantity."""
        cart = self.get_or_create_cart(request.user)
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        
        serializer = UpdateCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        quantity = serializer.validated_data['quantity']
        
        # Check stock availability
        if cart_item.variant.stock < quantity:
            return Response(
                {'error': f'Only {cart_item.variant.stock} items available in stock'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        cart_item.quantity = quantity
        cart_item.save()
        
        # Update cart timestamp
        cart.save()
        
        return Response(CartItemSerializer(cart_item).data)
    
    @action(detail=False, methods=['delete'], url_path='items/(?P<item_id>[^/.]+)')
    def remove_item(self, request, item_id=None):
        """Remove item from cart."""
        cart = self.get_or_create_cart(request.user)
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        cart_item.delete()
        
        # Update cart timestamp
        cart.save()
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['delete'])
    def clear(self, request):
        """Clear all items from cart."""
        cart = self.get_or_create_cart(request.user)
        cart.items.all().delete()
        
        # Update cart timestamp
        cart.save()
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['post'], url_path='items/(?P<item_id>[^/.]+)/move-to-wishlist')
    def move_to_wishlist(self, request, item_id=None):
        """Move item from cart to wishlist."""
        cart = self.get_or_create_cart(request.user)
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        
        # Get or create wishlist
        wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
        
        # Add to wishlist
        WishlistItem.objects.get_or_create(
            wishlist=wishlist,
            product=cart_item.variant.product
        )
        
        # Remove from cart
        cart_item.delete()
        
        return Response({'message': 'Item moved to wishlist'}, status=status.HTTP_200_OK)


class WishlistViewSet(viewsets.ViewSet):
    """
    API endpoint for wishlist management.
    """
    permission_classes = [IsAuthenticated]
    
    def get_or_create_wishlist(self, user):
        """Get or create wishlist for user."""
        wishlist, created = Wishlist.objects.get_or_create(user=user)
        return wishlist
    
    def list(self, request):
        """Get user's wishlist."""
        wishlist = self.get_or_create_wishlist(request.user)
        serializer = WishlistSerializer(wishlist)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def add_item(self, request):
        """Add item to wishlist."""
        serializer = WishlistItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        wishlist = self.get_or_create_wishlist(request.user)
        product_id = serializer.validated_data['product_id']
        
        product = get_object_or_404(Product, id=product_id, is_active=True)
        
        # Check if item already in wishlist
        wishlist_item, created = WishlistItem.objects.get_or_create(
            wishlist=wishlist,
            product=product
        )
        
        if not created:
            return Response(
                {'message': 'Item already in wishlist'},
                status=status.HTTP_200_OK
            )
        
        return Response(
            WishlistItemSerializer(wishlist_item).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['delete'], url_path='items/(?P<item_id>[^/.]+)')
    def remove_item(self, request, item_id=None):
        """Remove item from wishlist."""
        wishlist = self.get_or_create_wishlist(request.user)
        wishlist_item = get_object_or_404(WishlistItem, id=item_id, wishlist=wishlist)
        wishlist_item.delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['delete'])
    def clear(self, request):
        """Clear all items from wishlist."""
        wishlist = self.get_or_create_wishlist(request.user)
        wishlist.items.all().delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['post'], url_path='items/(?P<item_id>[^/.]+)/move-to-cart')
    def move_to_cart(self, request, item_id=None):
        """Move item from wishlist to cart."""
        wishlist = self.get_or_create_wishlist(request.user)
        wishlist_item = get_object_or_404(WishlistItem, id=item_id, wishlist=wishlist)
        
        # Get or create cart
        cart, _ = Cart.objects.get_or_create(user=request.user)
        
        # Get first available variant
        variant = wishlist_item.product.variants.filter(is_active=True, stock__gt=0).first()
        
        if not variant:
            return Response(
                {'error': 'Product is out of stock'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Add to cart
        CartItem.objects.get_or_create(
            cart=cart,
            variant=variant,
            defaults={'quantity': 1}
        )
        
        # Remove from wishlist
        wishlist_item.delete()
        
        return Response({'message': 'Item moved to cart'}, status=status.HTTP_200_OK)
