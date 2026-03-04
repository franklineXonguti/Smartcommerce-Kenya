"""
Custom validators for user-related fields.
"""
from django.core.exceptions import ValidationError
from .constants import validate_kenyan_phone, KENYAN_COUNTIES


def validate_phone_number(value):
    """Validate Kenyan phone number format."""
    if not validate_kenyan_phone(value):
        raise ValidationError(
            'Invalid phone number format. Use: 07XXXXXXXX, 01XXXXXXXX, or +2547XXXXXXXX'
        )


def validate_county(value):
    """Validate that the county is one of the 47 Kenyan counties."""
    valid_counties = [county[0] for county in KENYAN_COUNTIES]
    if value.lower().replace(' ', '_') not in valid_counties:
        raise ValidationError(
            f'{value} is not a valid Kenyan county.'
        )
