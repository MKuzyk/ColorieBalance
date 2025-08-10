from django.test import TestCase
from django.contrib.auth.models import User
from .models import Meal, Activity, UserProfile
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status


class ModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.profile = UserProfile.objects.create(
            user=self.user,
            weight=70,
            height=175,
            date_of_birth='1990-01-01',
            gender='M'
        )

    def test_profile_age(self):
        self.assertGreater(self.profile.age, 25)  # Zakładając, że test jest wykonywany po 2015 roku

    def test_profile_bmi(self):
        self.assertAlmostEqual(self.profile.calculate_bmi(), 22.86, places=2)


class APITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.force_authenticate(user=self.user)

    def test_daily_summary(self):
        url = reverse('daily-summary')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


from django.test import TestCase

# Create your tests here.
