from django.contrib import admin
from django.utils import timezone
from .models import VendorProfile, VendorPayout, VendorEarning


@admin.register(VendorProfile)
class VendorProfileAdmin(admin.ModelAdmin):
    list_display = ('business_name', 'user', 'approval_status', 'commission_rate', 'payout_balance', 'created_at')
    list_filter = ('approval_status', 'county', 'created_at')
    search_fields = ('business_name', 'user__email', 'business_email', 'registration_number')
    readonly_fields = ('payout_balance', 'created_at', 'updated_at', 'approved_at', 'approved_by')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Business Information', {
            'fields': ('business_name', 'business_description', 'business_email', 'business_phone')
        }),
        ('Registration', {
            'fields': ('registration_number', 'tax_id')
        }),
        ('Address', {
            'fields': ('county', 'town', 'street_address', 'postal_code')
        }),
        ('Warehouse Location', {
            'fields': ('warehouse_latitude', 'warehouse_longitude'),
            'classes': ('collapse',)
        }),
        ('Financial', {
            'fields': ('commission_rate', 'payout_balance')
        }),
        ('Payout Details', {
            'fields': ('bank_name', 'bank_account_number', 'bank_account_name', 'mpesa_number'),
            'classes': ('collapse',)
        }),
        ('Approval', {
            'fields': ('approval_status', 'approved_at', 'approved_by', 'rejection_reason')
        }),
        ('Branding', {
            'fields': ('logo', 'banner'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_vendors', 'reject_vendors', 'suspend_vendors']
    
    def approve_vendors(self, request, queryset):
        queryset.update(
            approval_status='approved',
            approved_at=timezone.now(),
            approved_by=request.user
        )
        # Update user's is_vendor flag
        for vendor in queryset:
            vendor.user.is_vendor = True
            vendor.user.save()
    approve_vendors.short_description = "Approve selected vendors"
    
    def reject_vendors(self, request, queryset):
        queryset.update(approval_status='rejected')
    reject_vendors.short_description = "Reject selected vendors"
    
    def suspend_vendors(self, request, queryset):
        queryset.update(approval_status='suspended')
    suspend_vendors.short_description = "Suspend selected vendors"


@admin.register(VendorPayout)
class VendorPayoutAdmin(admin.ModelAdmin):
    list_display = ('vendor', 'amount', 'payout_method', 'status', 'requested_at', 'completed_at')
    list_filter = ('status', 'payout_method', 'requested_at')
    search_fields = ('vendor__business_name', 'transaction_reference')
    readonly_fields = ('requested_at', 'processed_at', 'completed_at')
    ordering = ('-requested_at',)
    
    fieldsets = (
        ('Vendor', {
            'fields': ('vendor',)
        }),
        ('Payout Details', {
            'fields': ('amount', 'payout_method', 'account_details')
        }),
        ('Status', {
            'fields': ('status', 'transaction_reference', 'notes')
        }),
        ('Processing', {
            'fields': ('processed_by', 'requested_at', 'processed_at', 'completed_at')
        }),
    )
    
    actions = ['mark_as_processing', 'mark_as_completed']
    
    def mark_as_processing(self, request, queryset):
        queryset.update(status='processing', processed_by=request.user, processed_at=timezone.now())
    mark_as_processing.short_description = "Mark as processing"
    
    def mark_as_completed(self, request, queryset):
        queryset.update(status='completed', completed_at=timezone.now())
    mark_as_completed.short_description = "Mark as completed"


@admin.register(VendorEarning)
class VendorEarningAdmin(admin.ModelAdmin):
    list_display = ('vendor', 'order', 'gross_amount', 'commission_amount', 'net_amount', 'is_paid_out', 'created_at')
    list_filter = ('is_paid_out', 'created_at')
    search_fields = ('vendor__business_name', 'order__order_number')
    readonly_fields = ('created_at', 'paid_out_at')
    ordering = ('-created_at',)
