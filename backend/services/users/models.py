from django.contrib.auth.models import AbstractUser
from django.db import models
from .validators import validate_phone_number


class User(AbstractUser):
    """
    Custom user model for SmartCommerce Kenya.
    Extends Django's AbstractUser with Kenya-specific fields.
    """
    phone_number = models.CharField(
        max_length=15,
        unique=True,
        null=True,
        blank=True,
        validators=[validate_phone_number],
        help_text="Format: 07XXXXXXXX or +2547XXXXXXXX"
    )
    email = models.EmailField(unique=True)
    is_vendor = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['phone_number']),
        ]

    def __str__(self):
        return self.email
    
    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        full_name = f"{self.first_name} {self.last_name}"
        return full_name.strip() or self.email


class Address(models.Model):
    """
    Address model with Kenya-specific fields.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(
        max_length=15,
        validators=[validate_phone_number],
        help_text="Format: 07XXXXXXXX or +2547XXXXXXXX"
    )
    county = models.CharField(max_length=100, help_text="One of the 47 Kenyan counties")
    town = models.CharField(max_length=100)
    ward = models.CharField(max_length=100, blank=True)
    street = models.CharField(max_length=255)
    landmark = models.CharField(max_length=255, blank=True, help_text="e.g., Near XYZ Mall")
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'addresses'
        verbose_name = 'Address'
        verbose_name_plural = 'Addresses'
        ordering = ['-is_default', '-created_at']
        indexes = [
            models.Index(fields=['user', 'is_default']),
        ]

    def __str__(self):
        return f"{self.full_name} - {self.county}, {self.town}"

    def save(self, *args, **kwargs):
        # Ensure only one default address per user
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)
