"""
URL configuration for orders service.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CartViewSet, WishlistViewSet, OrderViewSet

router = DefaultRouter()
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'wishlist', WishlistViewSet, basename='wishlist')
router.register(r'orders', OrderViewSet, basename='order')

urlpatterns = [
    path('', include(router.urls)),
]
