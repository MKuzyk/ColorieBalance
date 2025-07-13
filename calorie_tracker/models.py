from django.db import models
from django.contrib.auth.models import User

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




