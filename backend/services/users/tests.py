from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import Address
from .constants import validate_kenyan_phone, normalize_kenyan_phone

User = get_user_model()


class PhoneValidationTest(TestCase):
    """Test Kenyan phone number validation."""
    
    def test_valid_phone_formats(self):
        """Test various valid phone formats."""
        valid_phones = [
            '0712345678',
            '0112345678',
            '+254712345678',
            '+254112345678',
        ]
        for phone in valid_phones:
            self.assertTrue(validate_kenyan_phone(phone), f"{phone} should be valid")
    
    def test_invalid_phone_formats(self):
        """Test invalid phone formats."""
        invalid_phones = [
            '12345678',  # Too short
            '07123456789',  # Too long
            '0812345678',  # Wrong prefix
            '+255712345678',  # Wrong country code
        ]
        for phone in invalid_phones:
            self.assertFalse(validate_kenyan_phone(phone), f"{phone} should be invalid")
    
    def test_phone_normalization(self):
        """Test phone number normalization."""
        self.assertEqual(normalize_kenyan_phone('0712345678'), '+254712345678')
        self.assertEqual(normalize_kenyan_phone('0112345678'), '+254112345678')
        self.assertEqual(normalize_kenyan_phone('+254712345678'), '+254712345678')


class UserModelTest(TestCase):
    """Test User model."""
    
    def setUp(self):
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'phone_number': '+254712345678',
            'password': 'testpass123'
        }
    
    def test_create_user(self):
        """Test creating a user."""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpass123'))
        self.assertFalse(user.is_email_verified)
    
    def test_user_string_representation(self):
        """Test user string representation."""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(str(user), 'test@example.com')
    
    def test_get_full_name(self):
        """Test get_full_name method."""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.get_full_name(), 'Test User')


class AddressModelTest(TestCase):
    """Test Address model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.address_data = {
            'user': self.user,
            'full_name': 'Test User',
            'phone_number': '+254712345678',
            'county': 'nairobi',
            'town': 'Nairobi',
            'street': '123 Test Street',
            'is_default': True
        }
    
    def test_create_address(self):
        """Test creating an address."""
        address = Address.objects.create(**self.address_data)
        self.assertEqual(address.user, self.user)
        self.assertTrue(address.is_default)
    
    def test_only_one_default_address(self):
        """Test that only one address can be default."""
        address1 = Address.objects.create(**self.address_data)
        
        address2_data = self.address_data.copy()
        address2_data['street'] = '456 Another Street'
        address2 = Address.objects.create(**address2_data)
        
        # Refresh address1 from database
        address1.refresh_from_db()
        
        # address1 should no longer be default
        self.assertFalse(address1.is_default)
        self.assertTrue(address2.is_default)


class AuthenticationAPITest(APITestCase):
    """Test authentication API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.register_url = '/api/auth/register/'
        self.login_url = '/api/auth/login/'
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'phone_number': '0712345678',
            'password': 'TestPass123!',
            'password_confirm': 'TestPass123!'
        }
    
    def test_user_registration(self):
        """Test user registration."""
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('tokens', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['email'], 'test@example.com')
    
    def test_registration_password_mismatch(self):
        """Test registration with mismatched passwords."""
        data = self.user_data.copy()
        data['password_confirm'] = 'DifferentPass123!'
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_user_login(self):
        """Test user login."""
        # First register a user
        User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        
        # Then try to login
        login_data = {
            'email': 'test@example.com',
            'password': 'TestPass123!'
        }
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)


class UserProfileAPITest(APITestCase):
    """Test user profile API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.profile_url = '/api/users/profile/'
    
    def test_get_user_profile(self):
        """Test retrieving user profile."""
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertEqual(response.data['full_name'], 'Test User')
    
    def test_update_user_profile(self):
        """Test updating user profile."""
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'phone_number': '0712345678'
        }
        response = self.client.patch(self.profile_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Refresh user from database
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.phone_number, '+254712345678')


class AddressAPITest(APITestCase):
    """Test address API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.addresses_url = '/api/users/addresses/'
    
    def test_create_address(self):
        """Test creating an address."""
        data = {
            'full_name': 'Test User',
            'phone_number': '0712345678',
            'county': 'nairobi',
            'town': 'Nairobi',
            'street': '123 Test Street',
            'is_default': True
        }
        response = self.client.post(self.addresses_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Address.objects.count(), 1)
    
    def test_list_user_addresses(self):
        """Test listing user addresses."""
        Address.objects.create(
            user=self.user,
            full_name='Test User',
            phone_number='+254712345678',
            county='nairobi',
            town='Nairobi',
            street='123 Test Street'
        )
        
        response = self.client.get(self.addresses_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_set_default_address(self):
        """Test setting an address as default."""
        address = Address.objects.create(
            user=self.user,
            full_name='Test User',
            phone_number='+254712345678',
            county='nairobi',
            town='Nairobi',
            street='123 Test Street',
            is_default=False
        )
        
        url = f'{self.addresses_url}{address.id}/set_default/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        address.refresh_from_db()
        self.assertTrue(address.is_default)
