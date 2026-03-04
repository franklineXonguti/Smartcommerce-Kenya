from django.contrib import admin
from .models import Category, Product, ProductVariant, ProductImage, InventoryLog, Review, Coupon


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'is_active', 'created_at')
    list_filter = ('is_active', 'parent')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'alt_text', 'is_primary', 'display_order')


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ('sku', 'size', 'color', 'price', 'stock', 'is_active')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'vendor', 'base_price', 'is_active', 'is_featured', 'created_at')
    list_filter = ('is_active', 'is_featured', 'category', 'vendor', 'requires_approval')
    search_fields = ('name', 'description', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductVariantInline, ProductImageInline]
    readonly_fields = ('created_at', 'updated_at', 'approved_at', 'approved_by')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'short_description', 'category', 'vendor')
        }),
        ('Pricing', {
            'fields': ('base_price', 'currency')
        }),
        ('Inventory', {
            'fields': ('track_inventory',)
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active', 'is_featured', 'requires_approval', 'approved_at', 'approved_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('sku', 'product', 'size', 'color', 'price', 'stock', 'is_low_stock', 'is_active')
    list_filter = ('is_active', 'product__category')
    search_fields = ('sku', 'product__name')
    ordering = ('product', 'sku')


@admin.register(InventoryLog)
class InventoryLogAdmin(admin.ModelAdmin):
    list_display = ('variant', 'change_type', 'quantity_change', 'stock_after', 'created_by', 'created_at')
    list_filter = ('change_type', 'created_at')
    search_fields = ('variant__sku', 'reference_id', 'reason')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'is_verified_purchase', 'is_approved', 'created_at')
    list_filter = ('rating', 'is_verified_purchase', 'is_approved', 'created_at')
    search_fields = ('product__name', 'user__email', 'title', 'comment')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    actions = ['approve_reviews', 'reject_reviews']
    
    def approve_reviews(self, request, queryset):
        from django.utils import timezone
        queryset.update(is_approved=True, approved_at=timezone.now())
    approve_reviews.short_description = "Approve selected reviews"
    
    def reject_reviews(self, request, queryset):
        queryset.update(is_approved=False, approved_at=None)
    reject_reviews.short_description = "Reject selected reviews"


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'discount_value', 'uses_count', 'max_uses', 'valid_from', 'valid_until', 'is_active')
    list_filter = ('discount_type', 'is_active', 'valid_from', 'valid_until')
    search_fields = ('code', 'description')
    filter_horizontal = ('applicable_products', 'applicable_categories')
    readonly_fields = ('uses_count', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'description')
        }),
        ('Discount', {
            'fields': ('discount_type', 'discount_value')
        }),
        ('Usage Limits', {
            'fields': ('max_uses', 'uses_count', 'max_uses_per_user', 'min_purchase_amount')
        }),
        ('Validity', {
            'fields': ('valid_from', 'valid_until')
        }),
        ('Restrictions', {
            'fields': ('applicable_products', 'applicable_categories'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )
