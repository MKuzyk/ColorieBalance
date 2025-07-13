from django.urls import path, include
from rest_framework.authtoken.views import obtain_auth_token
from .views import NutritionixMealAPIView, AddMealAPIView, AddActivityAPIView, add_activity_form, edit_profile_view, \
    GetAuthTokenView, profile_view
from .views import add_meal_dynamic
from .views import UserProfileAPIView

urlpatterns = [
    path('nutritionix-meal/', NutritionixMealAPIView.as_view(), name='nutritionix-meal'),
    path('add-meal/', AddMealAPIView.as_view(), name='add-meal'),
    path('add-meal-dynamic/', add_meal_dynamic, name='add-meal-dynamic'),
    path('add-activity/', AddActivityAPIView.as_view(), name='add-activity'),
    path('add-activity-form/', add_activity_form, name='add-activity-form'),
    path('profile/', profile_view, name='user-profile'),
    path('edit-profile/', edit_profile_view, name='edit-profile'),
    path('api/profile/', UserProfileAPIView.as_view(), name='api-profile'),
    path('api-token-auth/', obtain_auth_token, name='api_token_auth'),
    path('api/get-token/', GetAuthTokenView.as_view(), name='get-token'),
    ]



