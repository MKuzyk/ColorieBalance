from django.apps import AppConfig


class CalorieTrackerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'calorie_tracker'


class CalorieTrackerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'calorie_tracker'

    def ready(self):
        import calorie_tracker.signals