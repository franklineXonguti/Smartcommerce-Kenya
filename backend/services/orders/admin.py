from django.contrib import admin
from django.utils import timezone
from .models import Order, OrderItem, OrderStatusHistory, Cart, CartItem, Wishlist, WishlistItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product_name', 'sku', 'price', 'quantity', 'subtotal')
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'status', 'total', 'is_flagged', 'created_at', 'paid_at')
    list_filter = ('status', 'is_flagged', 'created_at', 'paid_at')
    search_fields = ('order_number', 'user__email', 'shipping_full_name', 'shipping_phone')
    readonly_fields = ('order_number', 'created_at', 'updated_at', 'paid_at', 'shipped_at', 'delivered_at')
    inlines = [OrderItemInline]
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'status')
        }),
        ('Shipping Address', {
            'fields': (
                'shipping_full_name', 'shipping_phone',
                'shipping_county', 'shipping_town', 'shipping_ward',
                'shipping_street', 'shipping_landmark'
            )
        }),
        ('Pricing', {
            'fields': ('subtotal', 'shipping_cost', 'discount_amount', 'total', 'currency')
        }),
        ('Coupon', {
            'fields': ('coupon', 'coupon_code'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('customer_notes', 'admin_notes'),
            'classes': ('collapse',)
        }),
        ('Fraud Detection', {
            'fields': ('is_flagged', 'fraud_score', 'fraud_reason', 'ip_address'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'paid_at', 'shipped_at', 'delivered_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_paid', 'mark_as_processing', 'mark_as_shipped', 'mark_as_delivered', 'flag_as_fraud']
    
    def mark_as_paid(self, request, queryset):
        queryset.update(status='paid', paid_at=timezone.now())
    mark_as_paid.short_description = "Mark as paid"
    
    def mark_as_processing(self, request, queryset):
        queryset.update(status='processing')
    mark_as_processing.short_description = "Mark as processing"
    
    def mark_as_shipped(self, request, queryset):
        queryset.update(status='shipped', shipped_at=timezone.now())
    mark_as_shipped.short_description = "Mark as shipped"
    
    def mark_as_delivered(self, request, queryset):
        queryset.update(status='delivered', delivered_at=timezone.now())
    mark_as_delivered.short_description = "Mark as delivered"
    
    def flag_as_fraud(self, request, queryset):
        queryset.update(is_flagged=True)
    flag_as_fraud.short_description = "Flag as potential fraud"


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('order', 'old_status', 'new_status', 'changed_by', 'created_at')
    list_filter = ('old_status', 'new_status', 'created_at')
    search_fields = ('order__order_number',)
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('variant', 'quantity', 'added_at')


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_items', 'is_abandoned', 'abandoned_at', 'recovery_email_sent', 'updated_at')
    list_filter = ('is_abandoned', 'recovery_email_sent', 'updated_at')
    search_fields = ('user__email',)
    readonly_fields = ('created_at', 'updated_at', 'abandoned_at', 'recovery_email_sent_at')
    inlines = [CartItemInline]
    ordering = ('-updated_at',)


class WishlistItemInline(admin.TabularInline):
    model = WishlistItem
    extra = 0
    readonly_fields = ('product', 'added_at')


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at')
    search_fields = ('user__email',)
    readonly_fields = ('created_at',)
    inlines = [WishlistItemInline]
    ordering = ('-created_at',)
