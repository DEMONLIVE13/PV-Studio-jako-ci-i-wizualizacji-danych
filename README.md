# Projekt 2 — Studio jakości i wizualizacji danych

Programowanie V, laboratoria 6–9. Autor: **Szymon Głogowski**.

Projekt służy do wczytywania CSV, oceny jakości danych, kontrolowanego
czyszczenia i porównywania wykresów przed oraz po operacjach.

| Etap | Stan |
| --- | --- |
| Lab 6 — Pandas, profil i czyszczenie | Ukończony |
| Lab 7 — Matplotlib, Seaborn i korelacja | Ukończony |
| Lab 8 — GUI Tkinter/ttk | Do wykonania |
| Lab 9 — integracja GUI, eksport i oddanie | Do wykonania |

## Wymagania i instalacja

Python 3.10 lub nowszy. Zależności są zapisane w `requirements.txt`:
Pandas 2.x, NumPy, Matplotlib 3.9–3.10, Seaborn 0.13 i Pillow.
Testy korzystają z `unittest`.

Polecenia dla Windows PowerShell, wykonywane w katalogu projektu:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Na innych systemach interpreter środowiska znajduje się w `.venv/bin/python`.

## Uruchomienie

Najpierw przygotuj oczyszczone dane i raport zmian:

```powershell
.venv\Scripts\python.exe lab6.py dane_przecinek.csv --range housing_median_age 1 52 --range-action missing --missing impute --outlier median_income --outlier-action flag
```

Wynik: `cleaned.csv`, `raport_lab6.json` i `raport_lab6.md`.
Przykład zmniejsza zbiór z 12 do 11 rekordów i liczbę brakujących komórek
z 2 do 0. Wiek 120 zamienia na brak, następnie uzupełnia medianą 37,5.
Dochód 90 pozostaje w danych i otrzymuje flagę wartości odstającej.

Następnie utwórz wykresy dla danych przed i po czyszczeniu:

```powershell
.venv\Scripts\python.exe lab7.py dane_przecinek.csv cleaned.csv
```

Powstaje pięć porównań, każde w PNG i SVG, oraz `raport_lab7.md`:

| Pliki `*_przed_po` | Zawartość |
| --- | --- |
| `histogram` | Rozkład `housing_median_age` |
| `scatter` | `median_income` względem `median_house_value` |
| `boxplot` | Rozkład i wartości odstające `median_income` |
| `barplot` | Liczebność kategorii `ocean_proximity` |
| `korelacja` | Macierz Pearsona dla dwóch zmiennych wykresu punktowego |

Wykresy można otworzyć bezpośrednio z katalogu projektu. Niebieski panel
pokazuje dane przed czyszczeniem, zielony panel dane po czyszczeniu.
Oba panele mają wspólne skale, histogram wspólne przedziały, a wykres
słupkowy wspólną kolejność kategorii. Licznik `n` podaje liczbę rekordów
wykorzystanych na wykresie względem wszystkich rekordów danej wersji zbioru.
Ponowne uruchomienie zastępuje poprzednie pliki wynikowe.

### Inny CSV i parametry wykresu

Nazwy kolumn można podać samodzielnie; program nie wymaga schematu
California Housing:

```powershell
.venv\Scripts\python.exe lab7.py surowe.csv oczyszczone.csv --hist wiek --x wiek --y wynik --box wynik --category segment --bins 8 --formats png svg
```

`--sep` przyjmuje `auto`, przecinek lub średnik. `--encoding` określa
kodowanie, `--decimal` separator dziesiętny, a `--output-dir` istniejący
katalog wynikowy. Wejścia mogą mieć różne separatory przy `--sep auto`;
kodowanie i separator dziesiętny są wspólne. `--formats` obsługuje PNG,
SVG i PDF. Pełna lista opcji:

```powershell
.venv\Scripts\python.exe lab6.py --help
.venv\Scripts\python.exe lab7.py --help
```

### Funkcja budująca wykres z parametrów

```python
from data_session import read_csv
from visualizations import build_figure, save_figure

frame = read_csv("cleaned.csv")
figure = build_figure(frame, "histogram", "housing_median_age", bins=8,
                      title="Rozkład wieku zabudowy")
save_figure(figure, "wiek.png")
```

`build_figure()` obsługuje `histogram`, `scatter`, `box`, `bar` i `correlation`.
`comparison_figure(before, after, kind, x, y=None, ...)` buduje porównanie
przed/po. Obie funkcje zwracają `matplotlib.figure.Figure`, nie zmieniają
danych i działają bez GUI. Ten sam obiekt będzie można osadzić w Tkinter.

## Obsługiwane funkcje i reguły

- Wczytywanie CSV z przecinkiem i średnikiem, kontrola kodowania,
  nagłówków i liczby pól oraz podgląd danych.
- Profil: rozmiar, typy, statystyki, liczba i procent braków,
  pełne duplikaty i liczba unikalnych wartości.
- Czyszczenie: pełne duplikaty, jawna konwersja liczb, reguły zakresów,
  usuwanie albo imputacja braków oraz raportowanie, flagowanie,
  przycinanie lub usuwanie outlierów.
- Osobne kopie `raw` i `current`, reset sesji i dziennik operacji
  z parametrami, czasem, liczbą rekordów i zmienionych komórek.
- Cztery wymagane rodzaje wykresów, analiza Pearsona i eksport wykresów.

Kolejność czyszczenia: duplikaty → konwersja → zakresy → braki → IQR.
Imputacja korzysta z mediany skończonych liczb i dominanty tekstu.
Całkowicie pusta kolumna pozostaje pusta i jest wskazana w raporcie.
Zakres wieku 1–52 jest jawną regułą przykładu, a nie regułą narzucaną
każdemu CSV. Pełne duplikaty usuwane są przed imputacją.

IQR = Q3 − Q1; progi to Q1 − 1,5·IQR i Q3 + 1,5·IQR.
Przy IQR=0 lub braku skończonych danych reguła czyszczenia jest nieaktywna.
Outlier nie oznacza automatycznie błędu: domyślnie jest raportowany,
a inną akcję i kolumnę wskazuje użytkownik. Standardowy box plot pokazuje
wąsy 1,5·IQR i punkty poza nimi; jego narysowanie nie usuwa obserwacji.

Histogram i box plot wymagają zmiennej liczbowej o różnych wartościach.
Scatter i korelacja wymagają dwóch różnych kolumn liczbowych, co najmniej
3 kompletnych par oraz zmienności obu kolumn w tych parach. Kolumny
logiczne nie są traktowane jak liczby. Bar plot liczy kategorie tekstowe,
logiczne lub jawnie kategorialne; przyjmuje do 20 kategorii. NaN i ±inf
w zmiennych liczbowych pomija się wyłącznie na potrzeby wykresu i korelacji.
Nie wykonuje się niejawnej konwersji tekstu na liczby.

### Wnioski z dołączonego przykładu

- Na histogramie po czyszczeniu znika niepoprawny wiek 120; maksimum
  wynosi 52. Raport zmian wyjaśnia zastąpienie tej wartości medianą 37,5.
- Dochód 90 pozostaje widoczny na scatterze i box plocie, ponieważ
  wybrano jego oznaczenie, a nie usunięcie.
- Słupki kategorii pozostają równe: `INLAND` 4→4, `NEAR BAY` 7→7.
  Usunięcie duplikatu `NEAR BAY` i imputacja brakującej kategorii tą samą
  wartością równoważą się. Przed operacjami wykres obejmuje 11/12 rekordów,
  a po operacjach 11/11.
- Pearson dochód/wartość domu zmienia się z **0,660885** dla 12 par
  na **0,668561** dla 11 par. Związek liniowy jest dodatni.
  **Korelacja nie dowodzi przyczynowości.** Mała próba i skrajny dochód
  ograniczają wnioski; większe `r` nie oznacza lepszego czyszczenia.

## Dane testowe i testy

Pliki `dane_*.csv` są syntetyczne. Zbiór referencyjny znajduje się w
`california_housing_projekt2.csv` (dodany 18.11.2026).

| Plik | Przygotowany przypadek | Oczekiwany wynik |
| --- | --- | --- |
| `dane_przecinek.csv` | 12×10, duplikat, 2 braki, wiek 120, dochód 90 | Główne polecenie: 11×11, 0 braków, 1 flaga dochodu |
| `dane_srednik.csv` | 6×4, polskie znaki, duplikat, braki, wiek 200 | Zakres 0–120→brak, usuwanie braków: 3×4 |
| `dane_brzegowe.csv` | 5×4, błędny tekst, inf, kolumna stała i pusta | Konwersja `liczba` i imputacja: 10,15,15,20,15; kolumna `pusta` pozostaje pusta |

```powershell
.venv\Scripts\python.exe -m unittest -v
```

Opis weryfikacji znajduje się w [raporcie testów](RAPORT_TESTOW.md).
Testy obejmują logikę lab 6, poprawność danych na wykresach, wspólne skale,
walidację, korelację, ochronę wejść oraz ponowne otwarcie PNG i SVG.

Kontrolowany błąd złego typu kolumny na lab 7:

```powershell
.venv\Scripts\python.exe lab7.py dane_przecinek.csv cleaned.csv --x ocean_proximity
```

Program pokazuje komunikat o wymaganej kolumnie liczbowej, zwraca kod 2
i zachowuje wcześniejsze wyniki. Walidacja całego zestawu poprzedza zapis.

## Struktura projektu

| Plik | Rola |
| --- | --- |
| `data_session.py` | Dane surowe i aktualne, profil, czyszczenie, reset, audyt |
| `lab6.py` | CLI czyszczenia oraz raporty przed/po |
| `visualizations.py` | Walidacja, funkcje zwracające `Figure`, Pearson, eksport |
| `lab7.py` | CLI porównań przed/po i generowanie wniosków |
| `test_lab6.py`, `test_lab7.py` | Testy automatyczne |
| `dane_*.csv` | Trzy wejścia testowe |
| `cleaned.csv`, `raport_lab6.*` | Wynik i raport czyszczenia |
| `*_przed_po.png`, `*_przed_po.svg`, `raport_lab7.md` | Wykresy i interpretacja |
| `RAPORT_TESTOW.md` | Przebieg i wyniki weryfikacji |
| `PLAN_PROJEKTU_2.md`, `CHANGELOG.md` | Plan etapów i dziennik rzeczywistych zmian |

## Znane ograniczenia i oddanie

Obecna wersja działa z terminala; GUI i osadzenie wykresu należą do lab 8–9.
Dane są wczytywane do pamięci. CSV wymaga nagłówka z unikalnymi,
niepustymi nazwami i stałej liczby pól. Folder wynikowy musi istnieć.
Wejścia są chronione przed nadpisaniem. Przy awarii dysku lub błędzie
uprawnień eksport kilku plików może pozostać częściowy; należy ponowić
zapis do dostępnego katalogu. Testy GUI będą wykonane po jego dodaniu.

Końcowy projekt oddaje się przez platformę jako `Glogowski_Szymon_P2.zip`
na koniec lab 9, w terminie wskazanym w kursie. ZIP powinien zawierać
kod, zależności, README, dane testowe, raport testów, `cleaned.csv`, raport
zmian i minimum dwa wyeksportowane wykresy. Nie należy pakować `.venv`,
`.git`, `__pycache__`, `.review`, cache, sekretów ani pomocniczych plików.

## Źródła, biblioteki i narzędzia AI

Wymagania: instrukcja „Projekt 2. Studio jakości i wizualizacji danych”
(5.10.2026) oraz „Warunki prowadzenia przedmiotu i zasady zaliczenia”
(6.10.2026). Wzorzec oddzielenia danych surowych i aktualnych oraz funkcji
zwracającej `Figure` pochodzi z instrukcji projektu.

- [Pandas](https://pandas.pydata.org/docs/) — DataFrame, profil i czyszczenie; BSD-3-Clause.
- [Matplotlib](https://matplotlib.org/stable/users/index.html) — obiekt `Figure`, histogram, słupki i eksport; licencja Matplotlib.
- [Seaborn](https://seaborn.pydata.org/tutorial.html) — scatter, box plot i mapa korelacji; BSD-3-Clause.
- [NumPy](https://numpy.org/doc/) — granice przedziałów i obsługa wartości nieskończonych; BSD-3-Clause, zależność Pandas/Matplotlib.
- [Python](https://docs.python.org/3/) — `argparse`, `csv`, `dataclasses`, `json`, `unittest` i pozostała biblioteka standardowa.
- Pillow — ponowne otwieranie PNG w testach; licencja HPND, zależność Matplotlib.

**Pomoc AI: OpenAI Codex / ChatGPT** — przygotowanie implementacji lab 6
oraz lab 7, syntetycznych danych, testów i dokumentacji; analiza wymagań,
uruchomienie kodu i weryfikacja wyników. Zakres kolejnych zmian jest
zapisywany w dzienniku zmian. Historia rozmów nie jest częścią projektu.

## Weryfikacja zbioru referencyjnego — lab 7

```powershell
.venv\Scripts\python.exe demo_california.py
```

Skrypt korzysta z kolumn `MedInc`, `HouseAge`, `MedHouseVal` i pozostałych
kolumn rzeczywistego CSV. Jawnie konwertuje błędne tokeny na braki,
usuwając pełne duplikaty, stosując zakres wieku 1–52, globalne zakresy
współrzędnych oraz nieujemność pozostałych wielkości. Dodatnie outliery
pozostają zachowane; dochód otrzymuje flagę IQR. Imputacja używa mediany.

Do słupków tworzona jest pomocnicza kategoria wieku: do 20, 21–40 i ponad
40 lat. Braki pozostają brakami do czasu imputacji. Zbiór źródłowy pozostaje
niezmieniony. CSV przed wykresami pokazuje dane po jawnej konwersji tokenów;
raport lab 6 zachowuje profil oryginalnych typów i liczbę konwersji.

Wyniki trafiają do lokalnego `wyniki_california/`: oczyszczony CSV,
raporty i pięć porównań PNG/SVG. Wyniki można odtworzyć powyższym poleceniem.
Sprawdzenie: 20 840→20 640 rekordów, 1080→0 pierwotnych braków,
Pearson MedInc/MedHouseVal 0,564612→0,563704. Korelacja nie dowodzi
przyczynowości. Szczegóły: [WERYFIKACJA_LAB7.md](WERYFIKACJA_LAB7.md).
Lab 8 i lab 9 pozostają do wykonania.
