from rest_framework import permissions


class IsVendorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow vendors to edit their own products.
    """
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated and request.user.is_vendor
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_staff:
            return True
        return obj.vendor and obj.vendor.user == request.user


class IsProductOwner(permissions.BasePermission):
    """
    Custom permission to only allow product owners to edit.
    """
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        if hasattr(obj, 'vendor'):
            return obj.vendor and obj.vendor.user == request.user
        if hasattr(obj, 'product'):
            return obj.product.vendor and obj.product.vendor.user == request.user
        return False
