from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Cart, CartItem, Wishlist, WishlistItem, Order, OrderItem, OrderStatusHistory
from .serializers import (
    CartSerializer, CartItemSerializer, AddToCartSerializer,
    UpdateCartItemSerializer, WishlistSerializer, WishlistItemSerializer,
    OrderListSerializer, OrderDetailSerializer, CheckoutSerializer
)
from services.products.models import Product, ProductVariant, Coupon
from services.users.models import Address


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



class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for order management.
    Read-only for customers, with admin actions.
    """
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return OrderDetailSerializer
        return OrderListSerializer
    
    def get_queryset(self):
        """Return orders for the authenticated user."""
        return Order.objects.filter(user=self.request.user).prefetch_related('items__variant__product')
    
    @action(detail=False, methods=['post'])
    def checkout(self, request):
        """
        Create an order from the user's cart.
        """
        serializer = CheckoutSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        # Get user's cart
        try:
            cart = Cart.objects.get(user=request.user)
        except Cart.DoesNotExist:
            return Response(
                {'error': 'Cart is empty'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if cart.items.count() == 0:
            return Response(
                {'error': 'Cart is empty'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get address
        address = get_object_or_404(Address, id=serializer.validated_data['address_id'], user=request.user)
        
        # Calculate totals
        subtotal = cart.subtotal
        shipping_cost = self._calculate_shipping(address.county)
        discount_amount = 0
        coupon = None
        coupon_code = serializer.validated_data.get('coupon_code', '')
        
        # Apply coupon if provided
        if coupon_code:
            try:
                coupon = Coupon.objects.get(code=coupon_code, is_active=True)
                if coupon.discount_type == 'percentage':
                    discount_amount = (subtotal * coupon.discount_value) / 100
                else:  # fixed
                    discount_amount = coupon.discount_value
                
                # Ensure discount doesn't exceed subtotal
                discount_amount = min(discount_amount, subtotal)
            except Coupon.DoesNotExist:
                pass
        
        total = subtotal + shipping_cost - discount_amount
        
        # Validate stock availability for all items
        for cart_item in cart.items.all():
            if cart_item.variant.stock < cart_item.quantity:
                return Response(
                    {'error': f'{cart_item.variant.product.name} has insufficient stock'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Create order
        order = Order.objects.create(
            user=request.user,
            shipping_address=address,
            shipping_full_name=address.full_name,
            shipping_phone=address.phone_number,
            shipping_county=address.county,
            shipping_town=address.town,
            shipping_ward=address.ward,
            shipping_street=address.street,
            shipping_landmark=address.landmark,
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            discount_amount=discount_amount,
            total=total,
            coupon=coupon,
            coupon_code=coupon_code,
            customer_notes=serializer.validated_data.get('customer_notes', ''),
            ip_address=self._get_client_ip(request)
        )
        
        # Create order items and update stock
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                variant=cart_item.variant,
                quantity=cart_item.quantity,
                price=cart_item.variant.price
            )
            
            # Reduce stock
            cart_item.variant.stock -= cart_item.quantity
            cart_item.variant.save()
        
        # Update coupon usage if applied
        if coupon:
            coupon.uses_count += 1
            coupon.save()
        
        # Clear cart
        cart.items.all().delete()
        
        # Create order status history
        OrderStatusHistory.objects.create(
            order=order,
            old_status='',
            new_status='pending',
            notes='Order created'
        )
        
        # Return order details with payment info
        return Response({
            'order': OrderDetailSerializer(order).data,
            'payment_method': serializer.validated_data['payment_method'],
            'message': 'Order created successfully. Proceed to payment.'
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an order (only if pending or paid)."""
        order = self.get_object()
        
        if order.status not in ['pending', 'paid']:
            return Response(
                {'error': 'Order cannot be cancelled at this stage'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Restore stock
        for item in order.items.all():
            item.variant.stock += item.quantity
            item.variant.save()
        
        # Update order status
        order.status = 'cancelled'
        order.save()
        
        # Create status history
        OrderStatusHistory.objects.create(
            order=order,
            old_status=order.status,
            new_status='cancelled',
            notes='Cancelled by customer'
        )
        
        return Response({'message': 'Order cancelled successfully'})
    
    def _calculate_shipping(self, county):
        """
        Calculate shipping cost based on county.
        Simplified version - can be enhanced with distance/weight calculations.
        """
        # Nairobi and surrounding counties
        nairobi_counties = ['Nairobi', 'Kiambu', 'Machakos', 'Kajiado']
        
        if county in nairobi_counties:
            return 200  # KES 200
        else:
            return 500  # KES 500 for other counties
    
    def _get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
