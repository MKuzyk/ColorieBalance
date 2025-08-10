from rest_framework import serializers
from .models import Activity, UserProfile
from .models import Meal


class ActivitySerializer(serializers.ModelSerializer):
    activity_type_display = serializers.CharField(source='get_activity_type_display', read_only=True)
    date = serializers.DateField(format="%Y-%m-%d", required=False)

    class Meta:
        model = Activity
        fields = [
            'id',
            'activity_type',
            'activity_type_display',
            'duration',
            'calories_burned',
            'date',
            'notes'
        ]
        extra_kwargs = {
            'user': {'read_only': True}
        }


class MealSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meal
        fields = '__all__'
        extra_kwargs = {
            'user': {'read_only': True}
        }


class UserProfileSerializer(serializers.ModelSerializer):
    age = serializers.SerializerMethodField()
    bmi = serializers.SerializerMethodField()
    gender_display = serializers.CharField(source='get_gender_display', read_only=True)

    class Meta:
        model = UserProfile
        fields = ['id', 'age', 'bmi', 'gender', 'gender_display', 'first_name',
                  'last_name', 'email', 'weight', 'height', 'date_of_birth', 'user']
        extra_kwargs = {
            'gender': {'allow_null': True, 'required': False}
        }

    def get_age(self, obj):
        return obj.age

    def get_bmi(self, obj):
        return obj.calculate_bmi()

