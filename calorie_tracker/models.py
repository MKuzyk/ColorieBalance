from django.db import models
from django.contrib.auth.models import User
from datetime import date
from django.contrib import admin

class Meal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    calories = models.FloatField()
    meal = models.CharField(max_length=100)
    protein = models.FloatField(default=0)
    carbs = models.FloatField(default=0)
    fat = models.FloatField(default=0)
    serving_qty = models.FloatField(default=0)
    serving_unit = models.CharField(max_length=50, blank=True)
    date = models.DateField(auto_now_add=True)
    raw_api_data = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.meal} - {self.calories} kcal"

class Activity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    activity = models.CharField(max_length=100)
    calories_burned = models.FloatField()
    date = models.DateField(auto_now_add=True)
    raw_api_data = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.activity} - {self.calories_burned} kcal burned"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    weight = models.FloatField(null=True, blank=True)  # w kg
    height = models.FloatField(null=True, blank=True)  # w cm
    date_of_birth = models.DateField(null=True, blank=True)
    GENDER_CHOICES = (
        ('M', 'Mężczyzna'),
        ('K', 'Kobieta'),
    )
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True)

    def age(self):
        if self.birth_date:
            today = date.today()
            return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        return None

    def __str__(self):
        return f"Profil użytkownika {self.user.username}"

    def calculate_bmi(self):
        if self.weight and self.height:
            height_in_m = self.height / 100
            return round(self.weight / (height_in_m ** 2), 2)
        return None

    @property
    def age(self):
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None

    def __str__(self):
        return f"Profil {self.user.username}"

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'weight', 'height', 'date_of_birth', 'age']