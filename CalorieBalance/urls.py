"""
URL configuration for CalorieBalance project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.http import HttpResponse
from django.urls import path, include

def profile_view(request):
    username = request.user.username if request.user.is_authenticated else "Gość"
    return HttpResponse(f"Witaj {username}!")

urlpatterns = [
    path('api/', include('calorie_tracker.urls')),
    # usuń jeśli nie chcesz logowania:
    # path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/profile/', profile_view, name='profile'),
]