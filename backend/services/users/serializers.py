from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import Address
from .constants import KENYAN_COUNTIES, normalize_kenyan_phone

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = [
            'email', 'username', 'first_name', 'last_name',
            'phone_number', 'password', 'password_confirm'
        ]
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def validate_phone_number(self, value):
        """Normalize and validate phone number."""
        if value:
            return normalize_kenyan_phone(value)
        return value
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        
        # Generate email verification token
        import secrets
        user.email_verification_token = secrets.token_urlsafe(32)
        user.save()
        
        # TODO: Send verification email in Phase 6
        
        return user


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user profile."""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'full_name', 'phone_number', 'is_vendor', 'is_email_verified',
            'created_at'
        ]
        read_only_fields = ['id', 'email', 'is_vendor', 'is_email_verified', 'created_at']


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile."""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number']
    
    def validate_phone_number(self, value):
        """Normalize and validate phone number."""
        if value:
            return normalize_kenyan_phone(value)
        return value


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change."""
    old_password = serializers.CharField(required=True, style={'input_type': 'password'})
    new_password = serializers.CharField(
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(required=True, style={'input_type': 'password'})
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password": "Password fields didn't match."})
        return attrs


class AddressSerializer(serializers.ModelSerializer):
    """Serializer for user addresses."""
    county_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Address
        fields = [
            'id', 'full_name', 'phone_number', 'county', 'county_display',
            'town', 'ward', 'street', 'landmark', 'is_default',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_county_display(self, obj):
        """Get the display name for the county."""
        county_dict = dict(KENYAN_COUNTIES)
        return county_dict.get(obj.county.lower().replace(' ', '_'), obj.county)
    
    def validate_phone_number(self, value):
        """Normalize and validate phone number."""
        return normalize_kenyan_phone(value)
    
    def validate_county(self, value):
        """Validate county is one of the 47 Kenyan counties."""
        valid_counties = [county[0] for county in KENYAN_COUNTIES]
        county_normalized = value.lower().replace(' ', '_')
        
        if county_normalized not in valid_counties:
            raise serializers.ValidationError(
                f"Invalid county. Must be one of the 47 Kenyan counties."
            )
        
        return county_normalized


class EmailVerificationSerializer(serializers.Serializer):
    """Serializer for email verification."""
    token = serializers.CharField(required=True)


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for password reset request."""
    email = serializers.EmailField(required=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for password reset confirmation."""
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(required=True, style={'input_type': 'password'})
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password": "Password fields didn't match."})
        return attrs
