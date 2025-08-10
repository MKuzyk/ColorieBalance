# Register your models here.
from django.contrib import admin
from .models import Meal, Activity, UserProfile

@admin.register(Meal)
class MealAdmin(admin.ModelAdmin):
    list_display = ['user', 'meal', 'calories', 'date']
    list_filter = ['date', 'user']
    search_fields = ['meal']

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'get_activity_type_display', 'duration', 'calories_burned', 'date']
    list_filter = ['activity_type', 'date', 'user']