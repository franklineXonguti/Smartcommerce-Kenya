from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Address


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_vendor', 'is_email_verified', 'is_staff')
    list_filter = ('is_vendor', 'is_email_verified', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('email', 'username', 'first_name', 'last_name', 'phone_number')
    ordering = ('-created_at',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('phone_number', 'is_vendor', 'is_email_verified')}),
    )


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user', 'county', 'town', 'is_default', 'created_at')
    list_filter = ('county', 'is_default')
    search_fields = ('full_name', 'user__email', 'county', 'town', 'street')
    ordering = ('-created_at',)
