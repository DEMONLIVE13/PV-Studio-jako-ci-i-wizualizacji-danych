# Lab 6 — raport profilu i czyszczenia

Plik: `dane_przecinek.csv`. Dołączone do repozytorium dane demonstracyjne są syntetyczne.

| Miara | Przed | Po |
| --- | ---: | ---: |
| Rekordy | 12 | 11 |
| Kolumny | 10 | 11 |
| Nadmiarowe pełne duplikaty | 1 | 0 |
| Brakujące komórki | 2 | 0 |

## Profil kolumn przed/po

| Kolumna | Typ przed → po | Braki przed → po | % braków przed → po | Unikalne przed → po |
| --- | --- | ---: | ---: | ---: |
| longitude | float64 → float64 | 0 → 0 | 0.0 → 0.0 | 11 → 11 |
| latitude | float64 → float64 | 0 → 0 | 0.0 → 0.0 | 10 → 10 |
| housing_median_age | int64 → float64 | 0 → 0 | 0.0 → 0.0 | 9 → 9 |
| total_rooms | int64 → int64 | 0 → 0 | 0.0 → 0.0 | 11 → 11 |
| total_bedrooms | float64 → float64 | 1 → 0 | 8.33 → 0.0 | 10 → 11 |
| population | int64 → int64 | 0 → 0 | 0.0 → 0.0 | 11 → 11 |
| households | int64 → int64 | 0 → 0 | 0.0 → 0.0 | 11 → 11 |
| median_income | float64 → float64 | 0 → 0 | 0.0 → 0.0 | 11 → 11 |
| median_house_value | int64 → int64 | 0 → 0 | 0.0 → 0.0 | 11 → 11 |
| ocean_proximity | object → object | 1 → 0 | 8.33 → 0.0 | 2 → 2 |
| median_income__outlier | — → bool | — → 0 | — → 0.0 | — → 2 |

## Jakość danych

`quality_before` dotyczy kopii surowych danych po jawnej konwersji wskazanych kolumn na liczby. `before` przedstawia oryginalny plik, również jego typy.

### Przed pipeline

- Zakres housing_median_age [1.0, 52.0]: 1 rekordów poza zakresem.
- IQR longitude: 0 outlierów; granice -127.18125 / -114.01124999999999; reguła aktywna: True.
- IQR latitude: 0 outlierów; granice 30.600000000000005 / 42.2; reguła aktywna: True.
- IQR housing_median_age: 1 outlierów; granice -6.125 / 86.875; reguła aktywna: True.
- IQR total_rooms: 1 outlierów; granice 134.375 / 3559.375; reguła aktywna: True.
- IQR total_bedrooms: 1 outlierów; granice -57.5 / 722.5; reguła aktywna: True.
- IQR population: 1 outlierów; granice -480.0 / 2288.0; reguła aktywna: True.
- IQR households: 1 outlierów; granice -48.75 / 665.25; reguła aktywna: True.
- IQR median_income: 1 outlierów; granice 1.0973999999999986 / 11.371; reguła aktywna: True.
- IQR median_house_value: 1 outlierów; granice 150700.0 / 475500.0; reguła aktywna: True.

### Po pipeline

- Zakres housing_median_age [1.0, 52.0]: 0 rekordów poza zakresem.
- IQR longitude: 0 outlierów; granice -127.3875 / -113.6475; reguła aktywna: True.
- IQR latitude: 0 outlierów; granice 29.975000000000005 / 42.575; reguła aktywna: True.
- IQR housing_median_age: 0 outlierów; granice -1.0 / 75.0; reguła aktywna: True.
- IQR total_rooms: 1 outlierów; granice 342.5 / 3554.5; reguła aktywna: True.
- IQR total_bedrooms: 1 outlierów; granice 48.75 / 658.75; reguła aktywna: True.
- IQR population: 0 outlierów; granice -546.25 / 2407.75; reguła aktywna: True.
- IQR households: 1 outlierów; granice -10.0 / 654.0; reguła aktywna: True.
- IQR median_income: 1 outlierów; granice 0.33090000000000064 / 12.248499999999998; reguła aktywna: True.
- IQR median_house_value: 1 outlierów; granice 129550.0 / 490750.0; reguła aktywna: True.

## Ślad zmian

| Operacja | Rekordy przed | Rekordy po | Dotknięte rekordy | Zmienione komórki |
| --- | ---: | ---: | ---: | ---: |
| drop_exact_duplicates | 12 | 11 | 1 | 0 |
| range | 11 | 11 | 1 | 1 |
| missing | 11 | 11 | 3 | 3 |
| outliers_iqr | 11 | 11 | 11 | 11 |

Pełne statystyki opisowe, parametry operacji, wartości imputacji i czas UTC znajdują się w raporcie JSON. Liczby dotkniętych rekordów z różnych operacji mogą obejmować ten sam rekord, więc nie należy ich sumować.

## Decyzje

- Pełne duplikaty są rozpatrywane przed konwersją i imputacją; zachowywana jest pierwsza kopia.
- Imputacja: mediana skończonych liczb i dominanta tekstu. Całkowicie pusta kolumna pozostaje pusta.
- Granice IQR = Q1 − k·IQR, Q3 + k·IQR, kwartyle z interpolacją liniową. Dla IQR=0 lub braku danych reguła jest nieaktywna.
- Outlier nie oznacza automatycznie błędu. Działanie i kolumnę wybiera użytkownik; domyślnie obowiązuje raportowanie. Flaga dodaje komórkę do każdego rekordu.
- Kolejność: duplikaty → konwersje → zakresy → braki → wybrane operacje IQR. Granice danej operacji IQR oblicza się na aktualnych danych.
- Plik źródłowy i kopia surowa sesji pozostają zachowane; `session.reset()` przywraca kopię surową.
