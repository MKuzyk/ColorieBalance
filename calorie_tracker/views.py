from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from calorie_tracker.models import Meal, Activity, UserProfile
from calorie_tracker.serializers import ActivitySerializer, UserProfileSerializer
from django.shortcuts import render, redirect
from rest_framework.authtoken.models import Token
import requests

# --- Widok logowania sesyjnego (HTML) ---

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('user-profile')
        else:
            return render(request, 'registration/login.html', {'error': 'Nieprawidłowe dane logowania'})

    return render(request, 'registration/login.html')

# --- Endpoint API do pobrania tokena, tylko dla zalogowanych sesyjnie użytkowników ---

class GetAuthTokenView(APIView):
    permission_classes = [IsAuthenticated]  # musisz być zalogowany sesyjnie lub tokenem

    def get(self, request):
        token, _ = Token.objects.get_or_create(user=request.user)
        return Response({"token": token.key})

# --- API do dodawania posiłków i aktywności ---

class NutritionixMealAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        meal_name = request.data.get("meal")
        if not meal_name:
            return Response({"error": "Meal name is required"}, status=status.HTTP_400_BAD_REQUEST)

        url = "https://trackapi.nutritionix.com/v2/natural/nutrients"
        headers = {
            "x-app-id": "55e405f5",
            "x-app-key": "60ffec6ca6a509a11fdc34925da69be4",
            "Content-Type": "application/json"
        }
        data = {"query": meal_name}

        try:
            api_response = requests.post(url, json=data, headers=headers)
            api_response.raise_for_status()
            nutrition_data = api_response.json()
            return Response(nutrition_data)
        except requests.exceptions.RequestException as e:
            return Response({"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

class AddMealAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        foods = request.data.get("foods", [])
        if not foods:
            return Response({"error": "No foods data provided"}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user

        for food in foods:
            Meal.objects.create(
                user=user,
                meal=food.get("food_name", ""),
                calories=food.get("nf_calories", 0),
                protein=food.get("nf_protein", 0),
                carbs=food.get("nf_total_carbohydrate", 0),
                fat=food.get("nf_total_fat", 0),
                serving_qty=food.get("serving_qty", 0),
                serving_unit=food.get("serving_unit", ""),
                raw_api_data=food
            )

        return Response({"status": "Meals added successfully"}, status=status.HTTP_201_CREATED)

class AddActivityAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        activity_name = request.data.get("activity")
        calories = request.data.get("calories_burned")

        if not activity_name or calories is None:
            return Response(
                {"error": "activity and calories_burned are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user

        activity = Activity.objects.create(
            user=user,
            activity=activity_name,
            calories_burned=calories,
        )

        serializer = ActivitySerializer(activity)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class UserProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)

    def put(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# --- Widoki HTML z sesyjnym dostępem ---

def profile_view(request):
    return render(request, "profile.html")

def edit_profile_view(request):
    return render(request, "edit_profile.html")

def add_activity_form(request):
    return render(request, "add_activity.html")

def add_meal_dynamic(request):
    return render(request, "add_meal_dynamic.html")
