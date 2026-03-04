from django.contrib import admin
from django.utils import timezone
from .models import Payment, StripePayment, MPesaPayment, Refund


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'order', 'user', 'payment_method', 'amount', 'status', 'created_at', 'completed_at')
    list_filter = ('payment_method', 'status', 'created_at')
    search_fields = ('transaction_id', 'external_reference', 'order__order_number', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'completed_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order', 'user')
        }),
        ('Payment Details', {
            'fields': ('payment_method', 'amount', 'currency', 'status')
        }),
        ('Transaction References', {
            'fields': ('transaction_id', 'external_reference')
        }),
        ('Response Data', {
            'fields': ('response_data', 'error_message'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(StripePayment)
class StripePaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_intent_id', 'payment', 'card_brand', 'card_last4', 'created_at')
    search_fields = ('payment_intent_id', 'checkout_session_id', 'charge_id')
    readonly_fields = ('created_at', 'updated_at', 'refunded_at')
    ordering = ('-created_at',)


@admin.register(MPesaPayment)
class MPesaPaymentAdmin(admin.ModelAdmin):
    list_display = ('checkout_request_id', 'payment', 'phone_number', 'mpesa_receipt_number', 'callback_received', 'created_at')
    list_filter = ('callback_received', 'result_code', 'created_at')
    search_fields = ('checkout_request_id', 'merchant_request_id', 'mpesa_receipt_number', 'phone_number')
    readonly_fields = ('created_at', 'updated_at', 'callback_received_at', 'transaction_date')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Payment', {
            'fields': ('payment',)
        }),
        ('M-Pesa Transaction', {
            'fields': ('merchant_request_id', 'checkout_request_id', 'mpesa_receipt_number', 'phone_number')
        }),
        ('Transaction Details', {
            'fields': ('transaction_date', 'result_code', 'result_desc')
        }),
        ('Callback', {
            'fields': ('callback_received', 'callback_data', 'callback_received_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ('order', 'amount', 'reason', 'status', 'requested_at', 'completed_at')
    list_filter = ('status', 'reason', 'requested_at')
    search_fields = ('order__order_number', 'refund_transaction_id', 'description')
    readonly_fields = ('requested_at', 'processed_at', 'completed_at')
    ordering = ('-requested_at',)
    
    fieldsets = (
        ('Order & Payment', {
            'fields': ('order', 'payment')
        }),
        ('Refund Details', {
            'fields': ('amount', 'reason', 'description')
        }),
        ('Status', {
            'fields': ('status', 'refund_transaction_id')
        }),
        ('Processing', {
            'fields': ('requested_by', 'processed_by', 'admin_notes')
        }),
        ('Timestamps', {
            'fields': ('requested_at', 'processed_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_refunds', 'reject_refunds', 'mark_as_completed']
    
    def approve_refunds(self, request, queryset):
        queryset.update(status='approved', processed_by=request.user, processed_at=timezone.now())
    approve_refunds.short_description = "Approve selected refunds"
    
    def reject_refunds(self, request, queryset):
        queryset.update(status='rejected', processed_by=request.user, processed_at=timezone.now())
    reject_refunds.short_description = "Reject selected refunds"
    
    def mark_as_completed(self, request, queryset):
        queryset.update(status='completed', completed_at=timezone.now())
    mark_as_completed.short_description = "Mark as completed"
