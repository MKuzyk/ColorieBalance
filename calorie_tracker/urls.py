from django.urls import path, include
from rest_framework.authtoken.views import obtain_auth_token
from .views import NutritionixMealAPIView, AddMealAPIView, AddActivityAPIView, add_activity_form, edit_profile_view, \
     profile_view, DailySummaryAPIView, dashboard_view, MealsTodayAPIView
from .views import add_meal_dynamic
from .views import UserProfileAPIView

api_urlpatterns = [
    path('nutritionix-meal/', NutritionixMealAPIView.as_view(), name='nutritionix-meal'),
    path('add-meal/', AddMealAPIView.as_view(), name='add-meal'),
    path('add-activity/', AddActivityAPIView.as_view(), name='add-activity'),
    path('profile/', UserProfileAPIView.as_view(), name='api-profile'),
    path('daily-summary/', DailySummaryAPIView.as_view(), name='daily-summary'),
    path('meals-today/', MealsTodayAPIView.as_view(), name='meals-today'),
]

html_views = [
    path('add-meal-dynamic/', add_meal_dynamic, name='add-meal-dynamic'),
    path('add-activity-form/', add_activity_form, name='add-activity-form'),
    path('profile/', profile_view, name='user-profile'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('edit-profile/', edit_profile_view, name='edit-profile'),
]

urlpatterns = html_views + [path('api/', include(api_urlpatterns))]



