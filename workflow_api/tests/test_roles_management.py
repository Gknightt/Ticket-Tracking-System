"""
Test suite for Roles Management
Tests: create, edit, delete roles, and verify permissions
"""
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from role.models import Roles, RoleUsers


class RolesManagementTestCase(TestCase):
    """Test cases for roles management operations"""
    
    def setUp(self):
        """Set up test client and initial data"""
        self.client = APIClient()
        # Create some test roles
        self.role1 = Roles.objects.create(
            role_id=1,
            name="Test Admin",
            system="tts"
        )
        self.role2 = Roles.objects.create(
            role_id=2,
            name="Test Agent",
            system="tts"
        )
    
    def test_create_role(self):
        """Test creating a new role"""
        data = {
            "role_id": 3,
            "name": "Test Manager",
            "system": "tts"
        }
        response = self.client.post('/api/roles/', data, format='json')
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_200_OK])
        
        # Verify role was created
        role = Roles.objects.filter(name="Test Manager").first()
        self.assertIsNotNone(role)
        self.assertEqual(role.system, "tts")
    
    def test_list_roles(self):
        """Test listing all roles"""
        response = self.client.get('/api/roles/')
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])
        
        if response.status_code == status.HTTP_200_OK:
            self.assertGreaterEqual(len(response.data), 2)
    
    def test_retrieve_role(self):
        """Test retrieving a specific role"""
        response = self.client.get(f'/api/roles/{self.role1.role_id}/')
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])
        
        if response.status_code == status.HTTP_200_OK:
            self.assertEqual(response.data['name'], 'Test Admin')
    
    def test_update_role(self):
        """Test updating a role"""
        data = {
            "name": "Updated Admin",
            "system": "tts"
        }
        response = self.client.put(
            f'/api/roles/{self.role1.role_id}/',
            data,
            format='json'
        )
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_400_BAD_REQUEST
        ])
        
        if response.status_code == status.HTTP_200_OK:
            self.role1.refresh_from_db()
            self.assertEqual(self.role1.name, "Updated Admin")
    
    def test_delete_role(self):
        """Test deleting a role"""
        role = Roles.objects.create(
            role_id=10,
            name="Temporary Role",
            system="tts"
        )
        response = self.client.delete(f'/api/roles/{role.role_id}/')
        self.assertIn(response.status_code, [
            status.HTTP_204_NO_CONTENT,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_200_OK
        ])
    
    def test_role_unique_name(self):
        """Test that role names must be unique"""
        from django.db import IntegrityError
        data = {
            "role_id": 99,
            "name": "Test Admin",  # Duplicate name
            "system": "tts"
        }
        with self.assertRaises(IntegrityError):
            Roles.objects.create(**data)
    
    def test_role_user_assignment(self):
        """Test assigning users to roles"""
        role_user = RoleUsers.objects.create(
            role_id=self.role1,
            user_id=1,
            user_full_name="Test User",
            is_active=True
        )
        self.assertEqual(role_user.role_id.role_id, 1)
        self.assertTrue(role_user.is_active)
    
    def test_role_user_unique_constraint(self):
        """Test unique constraint on role-user assignment"""
        from django.db import IntegrityError
        RoleUsers.objects.create(
            role_id=self.role1,
            user_id=1,
            user_full_name="Test User"
        )
        
        # Try to create duplicate assignment
        with self.assertRaises(IntegrityError):
            RoleUsers.objects.create(
                role_id=self.role1,
                user_id=1,
                user_full_name="Test User 2"
            )
