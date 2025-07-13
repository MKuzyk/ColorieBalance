import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CalorieBalance.settings')  # dokładna nazwa Twojego projektu!

django.setup()

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

user = User.objects.get(username='testuser')  # upewnij się, że taki user jest w DB
token, created = Token.objects.get_or_create(user=user)
print(token.key)

