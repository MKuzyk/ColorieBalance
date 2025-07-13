from rest_framework import serializers
from .models import Activity, UserProfile

class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = ['id', 'user', 'activity', 'calories_burned', 'date', 'raw_api_data']

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'weight', 'height', 'date_of_birth']
