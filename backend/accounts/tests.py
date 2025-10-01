from django.test import TestCase
from django.contrib.auth.models import User
from accounts.models import LabAssistant, Availability
from datetime import time

class LabAssistantModelTest(TestCase):
    def setUp(self):
        """Run before each test"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@usc.edu',
            first_name='Test',
            last_name='User',
            password='testpass123'
        )
        self.assistant = LabAssistant.objects.create(user=self.user)
    
    def test_lab_assistant_creation(self):
        """Test that lab assistant is created correctly"""
        self.assertEqual(self.assistant.status, 'active')
        self.assertEqual(str(self.assistant), 'Test User')
    
    def test_availability_creation(self):
        """Test adding availability"""
        availability = Availability.objects.create(
            lab_assistant=self.assistant,
            day_of_week=0,
            start_time=time(9, 0),
            end_time=time(17, 0)
        )
        self.assertEqual(availability.day_of_week, 0)
        self.assertEqual(self.assistant.availabilities.count(), 1)