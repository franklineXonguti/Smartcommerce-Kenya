from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, ProductViewSet, ReviewViewSet, CouponViewSet

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'reviews', ReviewViewSet, basename='review')
router.register(r'coupons', CouponViewSet, basename='coupon')

urlpatterns = [
    path('', include(router.urls)),
]
