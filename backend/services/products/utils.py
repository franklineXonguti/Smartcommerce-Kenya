"""
Utility functions for product management.
"""
import random
import string
from django.utils.text import slugify


def generate_sku(product_name, variant_attrs=None):
    """
    Generate a unique SKU for a product variant.
    Format: PREFIX-RANDOM-SUFFIX
    Example: ELEC-A7B9C2-BLU-L
    """
    # Get first 4 letters of product name
    prefix = ''.join(filter(str.isalpha, product_name.upper()))[:4]
    if len(prefix) < 4:
        prefix = prefix.ljust(4, 'X')
    
    # Generate random alphanumeric string
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    # Add variant attributes if provided
    suffix_parts = []
    if variant_attrs:
        if variant_attrs.get('color'):
            suffix_parts.append(variant_attrs['color'][:3].upper())
        if variant_attrs.get('size'):
            suffix_parts.append(variant_attrs['size'][:2].upper())
    
    suffix = '-'.join(suffix_parts) if suffix_parts else ''
    
    # Combine parts
    if suffix:
        sku = f"{prefix}-{random_part}-{suffix}"
    else:
        sku = f"{prefix}-{random_part}"
    
    return sku


def calculate_discount_percentage(original_price, discounted_price):
    """Calculate discount percentage."""
    if original_price and discounted_price and original_price > discounted_price:
        return int(((original_price - discounted_price) / original_price) * 100)
    return 0


def format_price(amount, currency='KES'):
    """Format price with currency symbol."""
    if currency == 'KES':
        return f"KES {amount:,.2f}"
    elif currency == 'USD':
        return f"${amount:,.2f}"
    elif currency == 'EUR':
        return f"€{amount:,.2f}"
    return f"{currency} {amount:,.2f}"
