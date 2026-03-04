"""
Celery tasks for product management.
"""
import csv
import io
from celery import shared_task
from django.core.exceptions import ValidationError
from .models import Product, ProductVariant, Category
from services.vendors.models import VendorProfile


@shared_task
def process_product_csv(csv_content, vendor_id):
    """
    Process CSV file for bulk product upload.
    Expected CSV format:
    name,description,category,base_price,sku,size,color,stock,variant_price
    """
    results = {
        'success': 0,
        'failed': 0,
        'errors': []
    }
    
    try:
        vendor = VendorProfile.objects.get(id=vendor_id)
    except VendorProfile.DoesNotExist:
        results['errors'].append('Vendor not found')
        return results
    
    # Parse CSV
    csv_file = io.StringIO(csv_content)
    reader = csv.DictReader(csv_file)
    
    for row_num, row in enumerate(reader, start=2):
        try:
            # Get or create category
            category_name = row.get('category', '').strip()
            category = None
            if category_name:
                category, _ = Category.objects.get_or_create(
                    name=category_name,
                    defaults={'slug': category_name.lower().replace(' ', '-')}
                )
            
            # Create or get product
            product_name = row.get('name', '').strip()
            if not product_name:
                raise ValidationError('Product name is required')
            
            product, created = Product.objects.get_or_create(
                name=product_name,
                vendor=vendor,
                defaults={
                    'description': row.get('description', '').strip(),
                    'category': category,
                    'base_price': float(row.get('base_price', 0)),
                }
            )
            
            # Create variant
            variant_data = {
                'product': product,
                'sku': row.get('sku', '').strip(),
                'size': row.get('size', '').strip(),
                'color': row.get('color', '').strip(),
                'stock': int(row.get('stock', 0)),
                'price': float(row.get('variant_price', product.base_price)),
            }
            
            ProductVariant.objects.create(**variant_data)
            results['success'] += 1
            
        except Exception as e:
            results['failed'] += 1
            results['errors'].append(f"Row {row_num}: {str(e)}")
    
    return results


@shared_task
def update_product_search_index(product_id):
    """
    Update search index for a product (Meilisearch/Elasticsearch).
    This will be implemented in Phase 13.
    """
    pass


@shared_task
def check_low_stock_alerts():
    """
    Check for low stock products and send alerts to vendors.
    """
    from django.core.mail import send_mail
    from django.conf import settings
    
    low_stock_variants = ProductVariant.objects.filter(
        is_active=True,
        stock__lte=models.F('low_stock_threshold')
    ).select_related('product', 'product__vendor')
    
    # Group by vendor
    vendor_alerts = {}
    for variant in low_stock_variants:
        vendor = variant.product.vendor
        if vendor:
            if vendor.id not in vendor_alerts:
                vendor_alerts[vendor.id] = {
                    'vendor': vendor,
                    'products': []
                }
            vendor_alerts[vendor.id]['products'].append(variant)
    
    # Send emails (placeholder - will be enhanced in Phase 6)
    for vendor_id, data in vendor_alerts.items():
        vendor = data['vendor']
        products = data['products']
        
        # TODO: Send actual email
        print(f"Low stock alert for {vendor.business_name}: {len(products)} products")
    
    return len(vendor_alerts)
