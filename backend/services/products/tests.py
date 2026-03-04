from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Category, Product, ProductVariant, Review, Coupon
from services.vendors.models import VendorProfile

User = get_user_model()


class CategoryModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Electronics",
            description="Electronic devices and accessories"
        )
    
    def test_category_creation(self):
        self.assertEqual(self.category.name, "Electronics")
        self.assertEqual(self.category.slug, "electronics")
        self.assertTrue(self.category.is_active)
    
    def test_category_hierarchy(self):
        subcategory = Category.objects.create(
            name="Smartphones",
            parent=self.category
        )
        self.assertEqual(subcategory.parent, self.category)
        self.assertIn(subcategory, self.category.children.all())


class ProductModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name="Electronics")
        self.product = Product.objects.create(
            name="Test Product",
            description="Test description",
            category=self.category,
            base_price=1000.00
        )
    
    def test_product_creation(self):
        self.assertEqual(self.product.name, "Test Product")
        self.assertEqual(self.product.slug, "test-product")
        self.assertEqual(self.product.base_price, 1000.00)
        self.assertEqual(self.product.currency, "KES")
    
    def test_product_variant(self):
        variant = ProductVariant.objects.create(
            product=self.product,
            sku="TEST-001",
            size="M",
            color="Blue",
            price=1200.00,
            stock=50
        )
        self.assertEqual(variant.product, self.product)
        self.assertTrue(variant.is_in_stock)
        self.assertFalse(variant.is_low_stock)


class ReviewModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='reviewer',
            email='reviewer@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name="Electronics")
        self.product = Product.objects.create(
            name="Test Product",
            description="Test description",
            category=self.category,
            base_price=1000.00
        )
    
    def test_review_creation(self):
        review = Review.objects.create(
            product=self.product,
            user=self.user,
            rating=5,
            title="Great product",
            comment="Really satisfied with this purchase",
            is_verified_purchase=True
        )
        self.assertEqual(review.rating, 5)
        self.assertTrue(review.is_verified_purchase)
        self.assertFalse(review.is_approved)  # Default is not approved


class CouponModelTest(TestCase):
    def setUp(self):
        from django.utils import timezone
        from datetime import timedelta
        
        self.coupon = Coupon.objects.create(
            code="TEST10",
            discount_type="percentage",
            discount_value=10.00,
            valid_from=timezone.now(),
            valid_until=timezone.now() + timedelta(days=30)
        )
    
    def test_coupon_creation(self):
        self.assertEqual(self.coupon.code, "TEST10")
        self.assertEqual(self.coupon.discount_type, "percentage")
        self.assertTrue(self.coupon.is_valid)
    
    def test_coupon_usage_limit(self):
        self.coupon.max_uses = 10
        self.coupon.uses_count = 10
        self.coupon.save()
        self.assertFalse(self.coupon.is_valid)
