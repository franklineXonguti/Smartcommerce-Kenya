"""
URL configuration for orders service.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CartViewSet, WishlistViewSet

router = DefaultRouter()
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'wishlist', WishlistViewSet, basename='wishlist')

urlpatterns = [
    path('', include(router.urls)),
]
