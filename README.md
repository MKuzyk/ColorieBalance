# Moja Aplikacja do śledzenia bilansu kalorycznego "CalorieBalance"

## Cel aplikacji
Aplikacja pozwala użytkownikom śledzić swoje posiłki, aktywności i bilans kalorii, a także monitorować postępy tygodniowe.

## Technologie
- **Django** – framework backendowy
- **Django REST Framework** – do tworzenia API
- **Bootstrap** – frontend i responsywny wygląd
- **JavaScript** – dynamiczne ładowanie danych w dashboardzie

## MVP (Minimum Viable Product)
Minimalnie działający produkt obejmuje:
- Rejestracja użytkownika i zapis podstawowych danych (wiek, waga, wzrost)
- Dodawanie i przeglądanie posiłków
- Pobieranie kaloryczności z open API https://www.nutritionix.com/
- Obliczanie i wyświetlanie podstawowego bilansu kalorii
- Wyświetlanie podsumowania tygodniowego w tabeli

Funkcje dodatkowe planowane w przyszłości:
- Zaawansowane statystyki i wykresy
- Powiadomienia o przekroczeniu kalorii
- Integracja z innymi aplikacjami fitness (Garmin itd.)
- Pobieranie spalania kalori aktywnych z open API

## API
Aplikacja została przystosowana do komunikacji przez REST API. 
Dane posiłków, aktywności i bilansu są pobierane dynamicznie z endpointów Django, co umożliwia łatwe rozwijanie frontendów lub integrację z innymi systemami.