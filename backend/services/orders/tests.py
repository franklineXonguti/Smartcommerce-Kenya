"""
Tests for orders service (Cart & Wishlist).
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal

from services.products.models import Product, ProductVariant, Category
from .models import Cart, CartItem, Wishlist, WishlistItem

User = get_user_model()


class CartAPITestCase(TestCase):
    """Test cases for Cart API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create test user
        self.user = User.objects.create_user(username='testuser', 
            email='test@example.com',
            phone_number='+254712345678',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Create test category
        self.category = Category.objects.create(
            name='Electronics',
            slug='electronics'
        )
        
        # Create test products
        self.product1 = Product.objects.create(
            name='Test Product 1',
            slug='test-product-1',
            description='Test description',
            category=self.category,
            base_price=Decimal('1000.00'),
            is_active=True
        )
        
        self.product2 = Product.objects.create(
            name='Test Product 2',
            slug='test-product-2',
            description='Test description 2',
            category=self.category,
            base_price=Decimal('2000.00'),
            is_active=True
        )
        
        # Create product variants
        self.variant1 = ProductVariant.objects.create(
            product=self.product1,
            sku='TEST-001',
            price=Decimal('1000.00'),
            stock=10,
            is_active=True
        )
        
        self.variant2 = ProductVariant.objects.create(
            product=self.product2,
            sku='TEST-002',
            price=Decimal('2000.00'),
            stock=5,
            is_active=True
        )
        
        # Authenticate client
        self.client.force_authenticate(user=self.user)
    
    def test_get_empty_cart(self):
        """Test getting an empty cart."""
        response = self.client.get('/api/orders/cart/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_items'], 0)
        self.assertEqual(response.data['subtotal'], 0)
        self.assertEqual(len(response.data['items']), 0)
    
    def test_add_item_to_cart(self):
        """Test adding an item to cart."""
        data = {
            'variant_id': self.variant1.id,
            'quantity': 2
        }
        
        response = self.client.post('/api/orders/cart/add_item/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['quantity'], 2)
        self.assertEqual(response.data['variant']['id'], self.variant1.id)
        
        # Verify cart was created
        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.items.count(), 1)
        self.assertEqual(cart.total_items, 2)
    
    def test_add_duplicate_item_increases_quantity(self):
        """Test adding same item twice increases quantity."""
        data = {
            'variant_id': self.variant1.id,
            'quantity': 2
        }
        
        # Add first time
        self.client.post('/api/orders/cart/add_item/', data)
        
        # Add second time
        response = self.client.post('/api/orders/cart/add_item/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['quantity'], 4)
        
        # Verify only one cart item exists
        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.items.count(), 1)
    
    def test_add_item_exceeds_stock(self):
        """Test adding more items than available stock."""
        data = {
            'variant_id': self.variant1.id,
            'quantity': 15  # Stock is only 10
        }
        
        response = self.client.post('/api/orders/cart/add_item/', data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Only 10 items available', response.data['error'])
    
    def test_update_cart_item_quantity(self):
        """Test updating cart item quantity."""
        # Add item first
        CartItem.objects.create(
            cart=Cart.objects.create(user=self.user),
            variant=self.variant1,
            quantity=2
        )
        
        cart_item = CartItem.objects.get(variant=self.variant1)
        
        data = {'quantity': 5}
        response = self.client.patch(f'/api/orders/cart/items/{cart_item.id}/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['quantity'], 5)
        
        # Verify database
        cart_item.refresh_from_db()
        self.assertEqual(cart_item.quantity, 5)
    
    def test_update_cart_item_exceeds_stock(self):
        """Test updating quantity beyond stock."""
        cart = Cart.objects.create(user=self.user)
        cart_item = CartItem.objects.create(
            cart=cart,
            variant=self.variant1,
            quantity=2
        )
        
        data = {'quantity': 15}  # Stock is only 10
        response = self.client.patch(f'/api/orders/cart/items/{cart_item.id}/', data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_remove_item_from_cart(self):
        """Test removing an item from cart."""
        cart = Cart.objects.create(user=self.user)
        cart_item = CartItem.objects.create(
            cart=cart,
            variant=self.variant1,
            quantity=2
        )
        
        response = self.client.delete(f'/api/orders/cart/items/{cart_item.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(CartItem.objects.filter(id=cart_item.id).exists())
    
    def test_clear_cart(self):
        """Test clearing all items from cart."""
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, variant=self.variant1, quantity=2)
        CartItem.objects.create(cart=cart, variant=self.variant2, quantity=1)
        
        response = self.client.delete('/api/orders/cart/clear/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(cart.items.count(), 0)
    
    def test_move_item_to_wishlist(self):
        """Test moving item from cart to wishlist."""
        cart = Cart.objects.create(user=self.user)
        cart_item = CartItem.objects.create(
            cart=cart,
            variant=self.variant1,
            quantity=2
        )
        
        response = self.client.post(f'/api/orders/cart/items/{cart_item.id}/move-to-wishlist/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(CartItem.objects.filter(id=cart_item.id).exists())
        
        # Verify item in wishlist
        wishlist = Wishlist.objects.get(user=self.user)
        self.assertTrue(wishlist.items.filter(product=self.product1).exists())
    
    def test_cart_requires_authentication(self):
        """Test cart endpoints require authentication."""
        self.client.force_authenticate(user=None)
        
        response = self.client.get('/api/orders/cart/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class WishlistAPITestCase(TestCase):
    """Test cases for Wishlist API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create test user
        self.user = User.objects.create_user(username='testuser', 
            email='test@example.com',
            phone_number='+254712345678',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Create test category
        self.category = Category.objects.create(
            name='Electronics',
            slug='electronics'
        )
        
        # Create test products
        self.product1 = Product.objects.create(
            name='Test Product 1',
            slug='test-product-1',
            description='Test description',
            category=self.category,
            base_price=Decimal('1000.00'),
            is_active=True
        )
        
        self.product2 = Product.objects.create(
            name='Test Product 2',
            slug='test-product-2',
            description='Test description 2',
            category=self.category,
            base_price=Decimal('2000.00'),
            is_active=True
        )
        
        # Create product variants
        self.variant1 = ProductVariant.objects.create(
            product=self.product1,
            sku='TEST-001',
            price=Decimal('1000.00'),
            stock=10,
            is_active=True
        )
        
        # Authenticate client
        self.client.force_authenticate(user=self.user)
    
    def test_get_empty_wishlist(self):
        """Test getting an empty wishlist."""
        response = self.client.get('/api/orders/wishlist/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_items'], 0)
        self.assertEqual(len(response.data['items']), 0)
    
    def test_add_item_to_wishlist(self):
        """Test adding an item to wishlist."""
        data = {'product_id': self.product1.id}
        
        response = self.client.post('/api/orders/wishlist/add_item/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['product']['id'], self.product1.id)
        
        # Verify wishlist was created
        wishlist = Wishlist.objects.get(user=self.user)
        self.assertEqual(wishlist.items.count(), 1)
    
    def test_add_duplicate_item_to_wishlist(self):
        """Test adding same item twice to wishlist."""
        data = {'product_id': self.product1.id}
        
        # Add first time
        self.client.post('/api/orders/wishlist/add_item/', data)
        
        # Add second time
        response = self.client.post('/api/orders/wishlist/add_item/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('already in wishlist', response.data['message'])
        
        # Verify only one wishlist item exists
        wishlist = Wishlist.objects.get(user=self.user)
        self.assertEqual(wishlist.items.count(), 1)
    
    def test_remove_item_from_wishlist(self):
        """Test removing an item from wishlist."""
        wishlist = Wishlist.objects.create(user=self.user)
        wishlist_item = WishlistItem.objects.create(
            wishlist=wishlist,
            product=self.product1
        )
        
        response = self.client.delete(f'/api/orders/wishlist/items/{wishlist_item.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(WishlistItem.objects.filter(id=wishlist_item.id).exists())
    
    def test_clear_wishlist(self):
        """Test clearing all items from wishlist."""
        wishlist = Wishlist.objects.create(user=self.user)
        WishlistItem.objects.create(wishlist=wishlist, product=self.product1)
        WishlistItem.objects.create(wishlist=wishlist, product=self.product2)
        
        response = self.client.delete('/api/orders/wishlist/clear/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(wishlist.items.count(), 0)
    
    def test_move_item_to_cart(self):
        """Test moving item from wishlist to cart."""
        wishlist = Wishlist.objects.create(user=self.user)
        wishlist_item = WishlistItem.objects.create(
            wishlist=wishlist,
            product=self.product1
        )
        
        response = self.client.post(f'/api/orders/wishlist/items/{wishlist_item.id}/move-to-cart/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(WishlistItem.objects.filter(id=wishlist_item.id).exists())
        
        # Verify item in cart
        cart = Cart.objects.get(user=self.user)
        self.assertTrue(cart.items.filter(variant__product=self.product1).exists())
    
    def test_move_out_of_stock_item_to_cart(self):
        """Test moving out of stock item from wishlist to cart."""
        # Create product with no stock
        product_no_stock = Product.objects.create(
            name='No Stock Product',
            slug='no-stock-product',
            description='Test',
            category=self.category,
            base_price=Decimal('1000.00'),
            is_active=True
        )
        
        wishlist = Wishlist.objects.create(user=self.user)
        wishlist_item = WishlistItem.objects.create(
            wishlist=wishlist,
            product=product_no_stock
        )
        
        response = self.client.post(f'/api/orders/wishlist/items/{wishlist_item.id}/move-to-cart/')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('out of stock', response.data['error'])
    
    def test_wishlist_requires_authentication(self):
        """Test wishlist endpoints require authentication."""
        self.client.force_authenticate(user=None)
        
        response = self.client.get('/api/orders/wishlist/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
