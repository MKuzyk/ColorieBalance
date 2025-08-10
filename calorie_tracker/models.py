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
    ACTIVITY_CHOICES = [
        ('RUN', 'Bieganie'),
        ('SWIM', 'Pływanie'),
        ('CYCLE', 'Jazda na rowerze'),
        ('GYM', 'Siłownia'),
        ('OTHER', 'Inne')
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    activity_type = models.CharField(
        max_length=20,
        choices=ACTIVITY_CHOICES,
        default='OTHER'  # Dodajemy domyślną wartość
    )
    duration = models.PositiveIntegerField(default=30)  # w minutach
    calories_burned = models.PositiveIntegerField()
    date = models.DateField()
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.get_activity_type_display()} - {self.duration}min, {self.calories_burned} kcal"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    weight = models.FloatField(null=True, blank=True)
    height = models.FloatField(null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    GENDER_CHOICES = (
        ('M', 'Mężczyzna'),
        ('K', 'Kobieta'),
    )
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True,default='M')

    def __str__(self):
        return f"{self.first_name} {self.last_name}" if self.first_name else self.user.username

    def age(self):
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None


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

    @property
    def gender_display(self):
        return self.get_gender_display()

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'weight', 'height', 'date_of_birth', 'age']