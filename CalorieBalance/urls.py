from django.urls import path, include
from calorie_tracker import views

urlpatterns = [
    path('login/', views.login_view, name='login'),  # sesyjne logowanie HTML
    path('accounts/', include('django.contrib.auth.urls')),  # auth: /accounts/login, logout itd.

    # Dołącz całą aplikację calorie_tracker - np pod prefixem '' lub 'api/' jeśli chcesz
    path('', include('calorie_tracker.urls')),
]
