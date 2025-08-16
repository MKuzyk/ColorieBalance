from datetime import date, timedelta, datetime
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.db.models.aggregates import Sum, Count
from django.shortcuts import render, redirect
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from calorie_tracker.models import Meal, Activity, UserProfile
from calorie_tracker.serializers import ActivitySerializer, UserProfileSerializer, MealSerializer
import requests
from django.contrib import messages
from .forms import ExtendedUserCreationForm, ActivityForm, UserProfileForm, MealForm


# ------------------------------------ Funkcje pomocnicze np. PPM, BMI, calculate age itd. --------------------

def calculate_age(birth_date):
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

def calculate_ppm(profile):
    if profile.date_of_birth and profile.weight and profile.height and profile.gender:
        age = calculate_age(profile.date_of_birth)
        if profile.gender == 'F':
            return 655 + (9.6 * profile.weight) + (1.8 * profile.height) - (4.7 * age)
        else:
            return 66 + (13.7 * profile.weight) + (5 * profile.height) - (6.8 * age)
    return None

def calculate_bmi(weight: float, height: float) -> float:
    return weight / (height ** 2)

# ----------------------------------- Klasy ------------------------------------------------------------------------


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
        meal_date_str = request.data.get("date")

        if not foods:
            return Response({"error": "No foods data provided"}, status=status.HTTP_400_BAD_REQUEST)

        # Dokładne parsowanie daty z walidacją
        try:
            meal_date = datetime.strptime(meal_date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = request.user
        created_meals = []

        for food in foods:
            meal = Meal(
                user=user,
                meal=food.get("food_name", ""),
                calories=food.get("nf_calories", 0),
                protein=food.get("nf_protein", 0),
                carbs=food.get("nf_total_carbohydrate", 0),
                fat=food.get("nf_total_fat", 0),
                serving_qty=food.get("serving_qty", 0),
                serving_unit=food.get("serving_unit", ""),
                raw_api_data=food,
                date=meal_date
            )
            meal.full_clean()
            meal.save()
            created_meals.append(meal)

        return Response({
            "status": f"Added {len(created_meals)} meals",
            "date": meal_date.isoformat(),
            "meals": MealSerializer(created_meals, many=True).data
        }, status=status.HTTP_201_CREATED)


class AddActivityAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        activity_type = request.data.get("activity_type")
        duration = request.data.get("duration", 30)
        calories_burned = request.data.get("calories_burned")
        notes = request.data.get("notes", "")
        date = request.data.get("date")

        if not all([activity_type, calories_burned]):
            return Response(
                {"error": "activity_type and calories_burned are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            activity = Activity.objects.create(
                user=request.user,
                activity_type=activity_type,
                duration=duration,
                calories_burned=calories_burned,
                notes=notes,
                date=date or date.today()
            )

            return Response({
                "status": "success",
                "activity": ActivitySerializer(activity).data,
                "weekly_summary": self.get_weekly_summary(request.user)
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_weekly_summary(self, user):

        today = date.today()
        week_ago = today - timedelta(days=7)

        activities = Activity.objects.filter(
            user=user,
            date__range=[week_ago, today]
        )

        return {
            "total_calories": activities.aggregate(Sum('calories_burned'))['calories_burned__sum'] or 0,
            "total_duration": activities.aggregate(Sum('duration'))['duration__sum'] or 0,
            "activity_count": activities.count()
        }


class ActivityStatsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        time_range = request.query_params.get('range', 'week')  # week/month/year

        today = date.today()
        if time_range == 'month':
            start_date = today - timedelta(days=30)
        elif time_range == 'year':
            start_date = today - timedelta(days=365)
        else:  # default to week
            start_date = today - timedelta(days=7)

        activities = Activity.objects.filter(
            user=request.user,
            date__range=[start_date, today]
        )

        # Grupowanie po typie aktywności
        by_type = activities.values('activity_type').annotate(
            total_duration=Sum('duration'),
            total_calories=Sum('calories_burned'),
            count=Count('id')
        )

        return Response({
            "total_calories": activities.aggregate(Sum('calories_burned'))['calories_burned__sum'] or 0,
            "total_duration": activities.aggregate(Sum('duration'))['duration__sum'] or 0,
            "activities_by_type": by_type,
            "start_date": start_date,
            "end_date": today
        })


class UserProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = UserProfile.objects.get(user=request.user)
            serializer = UserProfileSerializer(profile)
            return Response(serializer.data)
        except UserProfile.DoesNotExist:
            return Response({"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request):
        profile = request.user.userprofile
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MealsTodayAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        selected_date = request.query_params.get('date')
        if selected_date:
            try:
                meal_date = date.fromisoformat(selected_date)
            except (ValueError, TypeError):
                meal_date = date.today()
        else:
            meal_date = date.today()

        meals = Meal.objects.filter(user=request.user, date=meal_date)
        serializer = MealSerializer(meals, many=True)
        return Response({
            "date": meal_date,
            "meals": serializer.data
        })


class DailySummaryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Pobranie daty z parametrów URL
        selected_date = request.query_params.get('date')
        if selected_date:
            try:
                summary_date = date.fromisoformat(selected_date)
            except (ValueError, TypeError):
                summary_date = date.today()
        else:
            summary_date = date.today()

        user = request.user

        # Posiłki i aktywności
        meals = Meal.objects.filter(user=user, date=summary_date)
        activities = Activity.objects.filter(user=user, date=summary_date)

        # Sumy kalorii
        total_eaten = sum(meal.calories for meal in meals)
        total_burned = sum(activity.calories_burned for activity in activities)

        # Przetworzone dane do frontendu
        meals_data = [{"meal": m.meal, "calories": m.calories} for m in meals]
        activities_data = [
            {"activity_type": a.get_activity_type_display(),
             "duration": a.duration,
             "calories_burned": a.calories_burned}
            for a in activities
        ]

        # Dane użytkownika
        profile = UserProfile.objects.filter(user=user).first()
        bmi = None
        bmi_status = None
        ppm = None
        age = None

        if profile:
            age = calculate_age(profile.date_of_birth) if profile.date_of_birth else None
            ppm = calculate_ppm(profile)
            weight = profile.weight
            height = profile.height

            if profile.weight and profile.height:
                height_m = profile.height / 100
                bmi = calculate_bmi(profile.weight, height_m)

                if bmi < 18.5:
                    bmi_status = 'Niedowaga'
                elif 18.5 <= bmi < 25:
                    bmi_status = 'Waga prawidłowa'
                elif 25 <= bmi < 30:
                    bmi_status = 'Nadwaga'
                else:
                    bmi_status = 'Otyłość'

        # Bilans z uwzględnieniem PPM
        if ppm is not None:
            balance = total_eaten - (total_burned - ppm)
        else:
            balance = total_eaten - total_burned

        # Status kaloryczny (opcjonalny)
        if balance > 0:
            calorie_status = "Nadwyżka"
        elif balance < 0:
            calorie_status = "Deficyt"
        else:
            calorie_status = "Zero"

        return Response({
            "date": summary_date,
            "total_eaten": total_eaten,
            "total_burned": total_burned,
            "ppm": round(ppm, 0) if ppm else None,
            "balance": round(balance,0) if balance else None,
            "calorie_status": calorie_status,
            "bmi": round(bmi, 0) if bmi else None,
            "bmi_status": bmi_status,
            "age": age,
            "meals": meals_data,
            "activities": activities_data,
            "weight": weight,
            "height": height
        })

class WeeklySummaryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        end_date = date.today()
        start_date = end_date - timedelta(days=6)  # ostatnie 7 dni

        try:
            profile = UserProfile.objects.get(user=user)
            ppm_value = calculate_ppm(profile) or 0
        except UserProfile.DoesNotExist:
            ppm_value = 0

        weekly_data = []
        total_week_eaten = 0
        total_week_burned = 0
        total_week_ppm = 0

        for single_date in (start_date + timedelta(n) for n in range(7)):
            meals = Meal.objects.filter(user=user, date=single_date)
            activities = Activity.objects.filter(user=user, date=single_date)

            total_eaten = round(sum(meal.calories for meal in meals), 0)
            total_burned = round(sum(activity.calories_burned for activity in activities), 0)
            balance = round(total_eaten - total_burned - ppm_value, 0)

            status = "Nadwyżka" if balance > 0 else "Deficyt" if balance < 0 else "Zerowy"

            weekly_data.append({
                'date': single_date,
                'total_eaten': total_eaten,
                'total_burned': total_burned,
                'ppm': round(ppm_value, 0),
                'balance': round(balance, 0),
                'status': status,
                'meals': [f"{m.meal} ({m.calories} kcal)" for m in meals],
                'activities': [
                    f"{a.get_activity_type_display()} - {a.duration} min, {a.calories_burned} kcal"
                    for a in activities
                ]
            })

            # Agregacja tygodniowa
            total_week_eaten += total_eaten
            total_week_burned += total_burned
            total_week_ppm += ppm_value

        weekly_summary = {
            'total_eaten': round(total_week_eaten,0),
            'total_burned': round(total_week_burned,0),
            'total_ppm': round(total_week_ppm,0),
            'balance': round(total_week_eaten - total_week_burned - total_week_ppm,0)
        }

        return Response({
            'weekly_summary': weekly_summary,
            'daily_data': weekly_data
        })


#----------------------------------------- Widoki funkcyjne (szablony) ----------------------------------------------

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

@login_required
def dashboard_view(request):
    profile = request.user.userprofile

    age = calculate_age(profile.date_of_birth) if profile.date_of_birth else None
    ppm = calculate_ppm(profile)
    bmi = calculate_bmi(profile.weight, profile.height / 100) if profile.weight and profile.height else None

    # Dane tygodniowe
    today = date.today()
    week_ago = today - timedelta(days=6)

    meals = Meal.objects.filter(user=request.user, date__range=[week_ago, today])
    activities = Activity.objects.filter(user=request.user, date__range=[week_ago, today])

    total_eaten = meals.aggregate(total=Sum('calories'))['total'] or 0
    total_burned = activities.aggregate(total=Sum('calories_burned'))['total'] or 0

    avg_ppm = ppm
    balance = total_eaten - total_burned - avg_ppm

    context = {
        'age': age,
        'height': profile.height,
        'weight': profile.weight,
        'bmi': round(bmi, 1) if bmi else None,
        'ppm': round(ppm) if ppm else None,
        # agregaty tygodniowe
        'weekly_aggregates': {
            'total_eaten': round(total_eaten),
            'total_burned': round(total_burned),
            'avg_ppm': round(avg_ppm) if avg_ppm else 0,
            'balance': round(balance),
        },
        'weekly_meals': meals,
        'weekly_activities': activities,
    }

    return render(request, 'dashboard.html', context)

def home_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'home.html')

@login_required
def profile_view(request):
    try:
        profile = request.user.userprofile
        context = {
            'weight': profile.weight,
            'height': profile.height,
            'date_of_birth': profile.date_of_birth,
            'gender': profile.get_gender_display() if profile.gender else None,
        }
        return render(request, "profile.html", context)
    except UserProfile.DoesNotExist:
        return redirect('edit-profile')

@login_required
def edit_profile_view(request):
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = UserProfile(user=request.user)
        profile.save()

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('user-profile')
    else:
        form = UserProfileForm(instance=profile)

    return render(request, "edit_profile.html", {
        'form': form,
        'profile': profile
    })

def register_view(request):
    if request.method == 'POST':
        form = ExtendedUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'first_name': form.cleaned_data['first_name'],
                    'last_name': form.cleaned_data['last_name'],
                    'email': form.cleaned_data['email']
                }
            )

            login(request, user)

            messages.info(request, "Uzupełnij wszystkie dane w profilu, aby zostały obliczone BMI i PPM")

            return redirect('user-profile')
    else:
        form = ExtendedUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


def daily_summary_view(request):
    user = request.user
    profile = getattr(user, 'userprofile', None)

    # Pobierz datę z parametru GET lub użyj dzisiejszej
    selected_date_str = request.GET.get('date')
    if selected_date_str:
        try:
            selected_date = date.fromisoformat(selected_date_str)
        except (ValueError, TypeError):
            selected_date = date.today()
    else:
        selected_date = date.today()

    # Pobierz dane dla wybranej daty
    meals = Meal.objects.filter(user=user, date=selected_date).order_by('-id')
    activities = Activity.objects.filter(user=user, date=selected_date).order_by('-id')
    ppm = calculate_ppm(profile) if profile else None
    total_eaten = sum(meal.calories for meal in meals)
    total_burned = sum(activity.calories_burned for activity in activities)
    total_activity_duration = sum(activity.duration for activity in activities)
    balance = total_eaten - total_burned - ppm
    age = calculate_age(profile.date_of_birth) if profile.date_of_birth else None

    bmi = None
    if profile and profile.weight and profile.height:
        height_m = profile.height / 100
        bmi = calculate_bmi(profile.weight, height_m)

    context = {
        'today': date.today(),
        'yesterday': date.today() - timedelta(days=1),
        'week_ago': date.today() - timedelta(days=7),
        'selected_date': selected_date,
        'total_eaten': total_eaten,
        'total_burned': total_burned,
        'total_activity_duration': total_activity_duration,
        'balance': round(balance,0) if balance else None,
        'meals': meals,
        'activities': activities,
        'bmi': round(bmi,0) if bmi else None,
        'ppm': round(ppm,0)if ppm else None,
        'height': profile.height if profile else None,
        'weight': profile.weight if profile else None,
        'age':age
    }
    return render(request, "daily_summary.html", context)

@login_required
def add_meal_dynamic(request):
    if request.method == 'POST':
        form = MealForm(request.POST)
        if form.is_valid():
            meal = form.save(commit=False)
            meal.user = request.user
            if 'date' in request.POST:  # Jeśli data jest przekazana w formularzu
                meal.date = request.POST['date']
            meal.save()
            return redirect('daily-summary-html')
    else:
        form = MealForm(initial={'date': date.today()})  # Domyślna data

    return render(request, "add_meal_dynamic.html", {'form': form})


@login_required
def add_activity_form(request):
    if request.method == 'POST':
        form = ActivityForm(request.POST)
        if form.is_valid():
            activity = form.save(commit=False)
            activity.user = request.user
            activity.save()
            return redirect('daily-summary-html')
    else:
        form = ActivityForm()

    return render(request, "add_activity.html", {'form': form})

