from datetime import date
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from calorie_tracker.models import Meal, Activity, UserProfile
from calorie_tracker.serializers import ActivitySerializer, UserProfileSerializer, MealSerializer
import requests

# --- Widok logowania sesyjnego (HTML) ---
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        next_url = request.POST.get('next') or '/dashboard/'  # domyślnie dashboard

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect(next_url)
        else:
            return render(request, 'registration/login.html', {'error': 'Nieprawidłowe dane logowania'})

    next_url = request.GET.get('next', '/dashboard/')
    return render(request, 'registration/login.html', {'next': next_url})

# --- API do pobrania danych z Nutritionix i zapisu do bazy ---
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

class DailySummaryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = date.today()
        user = request.user

        meals = Meal.objects.filter(user=user, date=today)
        activities = Activity.objects.filter(user=user, date=today)

        total_eaten = sum(meal.calories for meal in meals)
        total_burned = sum(activity.calories_burned for activity in activities)
        balance = total_eaten - total_burned

        meals_data = [{"meal": m.meal, "calories": m.calories} for m in meals]
        activities_data = [{"activity": a.activity, "calories_burned": a.calories_burned} for a in activities]

        return Response({
            "total_eaten": total_eaten,
            "total_burned": total_burned,
            "balance": balance,
            "meals": meals_data,
            "activities": activities_data
        })

class MealsTodayAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = date.today()
        meals = Meal.objects.filter(user=request.user, date=today)
        serializer = MealSerializer(meals, many=True)
        return Response(serializer.data)

# --- Widoki HTML z sesyjnym dostępem ---
@login_required
def profile_view(request):
    return render(request, "profile.html")

@login_required
def edit_profile_view(request):
    return render(request, "edit_profile.html")

@login_required
def add_activity_form(request):
    return render(request, "add_activity.html")

@login_required
def add_meal_dynamic(request):
    return render(request, "add_meal_dynamic.html")

@login_required
def dashboard_view(request):
    return render(request, 'dashboard.html')


@login_required
def daily_summary_view(request):
    today = date.today()
    user = request.user

    meals = Meal.objects.filter(user=user, date=today)
    activities = Activity.objects.filter(user=user, date=today)

    total_eaten = sum(meal.calories for meal in meals)
    total_burned = sum(activity.calories_burned for activity in activities)
    balance = total_eaten - total_burned

    context = {
        "total_eaten": total_eaten,
        "total_burned": total_burned,
        "balance": balance,
        "meals": meals,
        "activities": activities,
    }
    return render(request, "daily_summary.html", context)
