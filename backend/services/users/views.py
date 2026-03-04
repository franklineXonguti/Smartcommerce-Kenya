from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from .models import Address
from .serializers import (
    UserRegistrationSerializer, UserSerializer, UserUpdateSerializer,
    ChangePasswordSerializer, AddressSerializer, EmailVerificationSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer
)
from .constants import KENYAN_COUNTIES

User = get_user_model()


class UserRegistrationView(generics.CreateAPIView):
    """
    API endpoint for user registration.
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'message': 'Registration successful. Please verify your email.'
        }, status=status.HTTP_201_CREATED)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    API endpoint for viewing and updating user profile.
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserUpdateSerializer
        return UserSerializer


class ChangePasswordView(generics.UpdateAPIView):
    """
    API endpoint for changing password.
    """
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            # Check old password
            if not user.check_password(serializer.data.get('old_password')):
                return Response(
                    {'old_password': ['Wrong password.']},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Set new password
            user.set_password(serializer.data.get('new_password'))
            user.save()
            
            return Response({
                'message': 'Password updated successfully.'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmailVerificationView(generics.GenericAPIView):
    """
    API endpoint for email verification.
    """
    serializer_class = EmailVerificationSerializer
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token = serializer.validated_data['token']
        
        try:
            user = User.objects.get(email_verification_token=token)
            
            if user.is_email_verified:
                return Response({
                    'message': 'Email already verified.'
                }, status=status.HTTP_200_OK)
            
            user.is_email_verified = True
            user.email_verification_token = ''
            user.save()
            
            return Response({
                'message': 'Email verified successfully.'
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({
                'error': 'Invalid verification token.'
            }, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(generics.GenericAPIView):
    """
    API endpoint for requesting password reset.
    """
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        
        try:
            user = User.objects.get(email=email)
            
            # Generate reset token
            import secrets
            reset_token = secrets.token_urlsafe(32)
            
            # Store token (in production, use a separate model with expiry)
            user.email_verification_token = reset_token
            user.save()
            
            # TODO: Send password reset email in Phase 6
            
            return Response({
                'message': 'Password reset email sent. Please check your inbox.'
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            # Don't reveal if email exists
            return Response({
                'message': 'If the email exists, a password reset link has been sent.'
            }, status=status.HTTP_200_OK)


class PasswordResetConfirmView(generics.GenericAPIView):
    """
    API endpoint for confirming password reset.
    """
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']
        
        try:
            user = User.objects.get(email_verification_token=token)
            user.set_password(new_password)
            user.email_verification_token = ''
            user.save()
            
            return Response({
                'message': 'Password reset successfully.'
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({
                'error': 'Invalid reset token.'
            }, status=status.HTTP_400_BAD_REQUEST)


class AddressViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing user addresses.
    """
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """Set an address as default."""
        address = self.get_object()
        
        # Remove default from all other addresses
        Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
        
        # Set this address as default
        address.is_default = True
        address.save()
        
        return Response({
            'message': 'Address set as default.'
        }, status=status.HTTP_200_OK)


class CountyListView(generics.GenericAPIView):
    """
    API endpoint to get list of Kenyan counties.
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        counties = [
            {'value': county[0], 'label': county[1]}
            for county in KENYAN_COUNTIES
        ]
        return Response(counties, status=status.HTTP_200_OK)
