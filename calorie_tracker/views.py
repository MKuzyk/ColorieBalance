from datetime import date
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from calorie_tracker.models import Meal, Activity, UserProfile
from calorie_tracker.serializers import ActivitySerializer, UserProfileSerializer, MealSerializer
import requests
from math import pow
from .forms import ExtendedUserCreationForm

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
        try:
            profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            return Response({"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)

    def put(self, request):
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def calculate_age(birth_date):
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

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

        profile = UserProfile.objects.filter(user=user).first()
        bmi = None
        bmi_status = None
        ppm = None
        age = None

        if profile and profile.weight and profile.height and profile.gender:  # Używamy weight i height zamiast weight_kg i height_cm
            height_m = profile.height / 100  # height jest w cm, dzielimy przez 100 aby uzyskać metry
            bmi = profile.weight / pow(height_m, 2)  # weight jest w kg

            # BMI status
            if bmi < 18.5:
                bmi_status = 'Niedowaga'
            elif 18.5 <= bmi < 25:
                bmi_status = 'Waga prawidłowa'
            elif 25 <= bmi < 30:
                bmi_status = 'Nadwaga'
            else:
                bmi_status = 'Otyłość'

            if profile.date_of_birth:
                age = calculate_age(profile.date_of_birth)

            # Oblicz PPM wg płci
            if age is not None:
                if profile.gender.lower() == 'f':
                    ppm = 655 + (9.6 * profile.weight) + (1.8 * profile.height) - (4.7 * age)  # weight w kg, height w cm
                elif profile.gender.lower() == 'm':
                    ppm = 66 + (13.7 * profile.weight) + (5 * profile.height) - (6.8 * age)  # weight w kg, height w cm

        calorie_status = "Nadwyżka kaloryczna" if balance > 0 else "Deficyt kaloryczny" if balance < 0 else "Bilans zerowy"

        meals_data = [{"meal": m.meal, "calories": m.calories} for m in meals]
        activities_data = [{"activity": a.activity, "calories_burned": a.calories_burned} for a in activities]

        return Response({
            "total_eaten": total_eaten,
            "total_burned": total_burned,
            "balance": balance,
            "calorie_status": calorie_status,
            "bmi": round(bmi, 2) if bmi else None,
            "bmi_status": bmi_status,
            "ppm": round(ppm, 2) if ppm else None,
            "age": age,
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
    user = request.user
    profile = getattr(user, 'userprofile', None)

    today = date.today()

    meals = Meal.objects.filter(user=user, date=today)
    activities = Activity.objects.filter(user=user, date=today)

    total_eaten = sum(meal.calories for meal in meals)
    total_burned = sum(activity.calories_burned for activity in activities)
    balance = total_eaten - total_burned

    # Oblicz BMI
    if profile and profile.weight and profile.height:  # Używamy weight i height
        height_m = profile.height / 100  # height jest w cm, konwertujemy na metry
        bmi = profile.weight / (height_m ** 2)  # weight jest w kg
        bmi = round(bmi, 2)
    else:
        bmi = None

    # Oblicz wiek
    if profile and profile.date_of_birth:
        today = date.today()
        age = today.year - profile.date_of_birth.year - (
                    (today.month, today.day) < (profile.date_of_birth.month, profile.date_of_birth.day))
    else:
        age = None

    # Oblicz PPM (wzór Harrisa-Benedicta)
    ppm = None
    if profile and profile.weight and profile.height and age is not None and profile.gender:
        if profile.gender == 'F':
            ppm = 655 + (9.6 * profile.weight) + (1.8 * profile.height) - (4.7 * age)  # weight w kg, height w cm
        else:  # assuming 'M'
            ppm = 66 + (13.7 * profile.weight) + (5 * profile.height) - (6.8 * age)  # weight w kg, height w cm
        ppm = round(ppm, 2)

    # Oblicz deficyt/nadwyżkę względem PPM (jeśli ppm jest dostępne)
    calorie_status = None
    if ppm is not None:
        calorie_diff = balance - ppm
        if calorie_diff < 0:
            calorie_status = f"Deficyt kaloryczny: {abs(calorie_diff):.2f} kcal"
        elif calorie_diff > 0:
            calorie_status = f"Nadwyżka kaloryczna: {calorie_diff:.2f} kcal"
        else:
            calorie_status = "Bilans kaloryczny na poziomie PPM"

    context = {
        'total_eaten': total_eaten,
        'total_burned': total_burned,
        'balance': balance,
        'meals': meals,
        'activities': activities,
        'bmi': bmi,
        'ppm': ppm,
        'calorie_status': calorie_status,
    }
    return render(request, "daily_summary.html", context)


def home_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'home.html')


def register_view(request):
    if request.method == 'POST':
        form = ExtendedUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Użyj get_or_create zamiast create, aby uniknąć duplikatów
            UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'first_name': form.cleaned_data['first_name'],
                    'last_name': form.cleaned_data['last_name'],
                    'email': form.cleaned_data['email']
                }
            )

            login(request, user)
            return redirect('dashboard')
    else:
        form = ExtendedUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})