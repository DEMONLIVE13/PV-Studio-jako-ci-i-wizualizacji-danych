# Projekt 2 — Studio jakości i wizualizacji danych

Programowanie V, laboratoria 6–9. **Gotowy etap: laboratorium 6.**
Skrypt wczytuje CSV, pokazuje profil danych, wykrywa problemy, wykonuje wybrane
operacje czyszczenia oraz zapisuje `cleaned.csv` i raport przed/po.
Wizualizacje i GUI należą do kolejnych etapów z [planu](PLAN_PROJEKTU_2.md).

Wymagania pochodzą z `projekt-2-dane.pdf` (5.10.2026) i
`warunki-programowanie-v (1).pdf` (6.10.2026), dostarczonych w rozmowie.
PDF-y nie są kopiowane do repozytorium. Wszystkie pliki projektu leżą
w katalogu głównym; nie ma dodatkowego folderu `lab6`.

## Wymagania i instalacja

Python 3.10+ i Pandas 2.2.x. Testy korzystają z wbudowanego `unittest`.
Polecenia wykonuj w katalogu repozytorium; na Windows można użyć `py`
zamiast `python`.

```bash
python -m pip install -r requirements.txt
python lab6.py --help
```

Opcjonalne środowisko wirtualne należy utworzyć lokalnie; nie jest częścią
pakietu do oddania ani repozytorium.

## Uruchomienie lab 6

Przykład odtwarzający dołączone `cleaned.csv`, `raport_lab6.json` i
`raport_lab6.md`:

```bash
python lab6.py dane_przecinek.csv --range housing_median_age 1 52 --range-action missing --missing impute --outlier median_income --outlier-action flag
```

Oczekiwany wynik: 12 → 11 rekordów, usunięty 1 nadmiarowy pełny duplikat,
1 wiek spoza zakresu zamieniony na brak, uzupełnione 3 komórki w 3 rekordach
(2 pierwotne braki i 1 po regule zakresu). Dodana flaga
`median_income__outlier` oznacza dokładnie 1 obserwację. Zmieniona wartość
wieku to 37,5; skrajny dochód 90 pozostaje zachowany.

Pozostałe demonstracje (nadpisują domyślne pliki wynikowe):

```bash
python lab6.py dane_srednik.csv --range wiek 0 120 --range-action missing --missing drop
python lab6.py dane_brzegowe.csv --numeric liczba --missing impute
```

Dla danych od prowadzącej, po zapisaniu jej CSV na własnym komputerze:

```bash
python lab6.py california_housing.csv --range housing_median_age 1 52 --range-action report --missing impute
```

Przed zmianą zakresów należy sprawdzić znaczenie kolumn i wartości w danym
pliku. Zakres 1–52 to jawna reguła przykładowa dla wieku w tym zbiorze,
a nie automatycznie narzucana reguła dla każdego CSV. Aplikacja nie wymaga
nazw z California Housing i obsługuje inne poprawne CSV.

## Możliwości

| Obszar lab 6 | Realizacja |
| --- | --- |
| Wczytanie | Automatyczne lub jawne `,` / `;`, kodowanie, separator dziesiętny, podgląd 5 rekordów |
| Profil | Liczba rekordów/kolumn, typy, statystyki opisowe, liczba i procent braków, duplikaty, unikalność |
| Reguły jakości | Wiele domkniętych zakresów, IQR dla kolumn liczbowych, liczba wartości nieskończonych |
| Czyszczenie | Pełne duplikaty, usuwanie braków lub imputacja, konwersja błędnego tekstu, zakresy i outliery |
| Raport | Profil i jakość przed/po, parametry, czas UTC, liczba dotkniętych rekordów, zmienione komórki |
| Reset | `DataSession.reset()` przywraca kopię surową bez ponownego uruchomienia procesu |
| Eksport | `cleaned.csv`, raport JSON i czytelny raport Markdown |
| Powtarzalność | Identyczne dane wyjściowe dla tych samych parametrów; czas w dzienniku odzwierciedla rzeczywiste wykonanie |

Plik wejściowy i pliki wyjściowe muszą mieć różne ścieżki. Program nie tworzy
folderów. Wyniki domyślnie zapisuje w bieżącym katalogu; ponowne uruchomienie
zastępuje poprzednie wyniki. Zapis może być częściowy przy awarii dysku lub
braku uprawnień do jednego z plików — po komunikacie błędu należy ponowić
eksport do zapisywalnej lokalizacji.

### Parametry

| Opcja | Działanie |
| --- | --- |
| `--sep auto` / `--sep ";"` / `--sep ","` | Separator CSV; domyślnie wykrywany |
| `--encoding cp1250` | Jawne kodowanie; domyślnie UTF-8 z obsługą BOM, bez cichego zastępowania znaków |
| `--decimal ","` | Liczby zapisane z przecinkiem dziesiętnym, zwykle z separatorem `;` |
| `--numeric KOLUMNA` | Konwersja jednej kolumny na liczby; błędny tekst i ±inf stają się brakami; można powtarzać |
| `--range KOLUMNA MIN MAX` | Reguła domkniętego zakresu; można wskazać wiele różnych kolumn |
| `--range-action report\|missing\|clip\|drop` | Raportowanie, zamiana na brak, przycięcie lub usunięcie rekordów; domyślnie `report` |
| `--missing keep\|drop\|impute` | Pozostawienie, usuwanie lub imputacja braków; domyślnie `impute` |
| `--missing-column KOLUMNA` | Ograniczenie strategii braków do wybranych kolumn; można powtarzać |
| `--keep-duplicates` | Zachowanie pełnych duplikatów; domyślnie usuwane |
| `--outlier KOLUMNA` | Wskazanie kolumny do obsługi outlierów; można powtarzać |
| `--outlier-action report\|flag\|clip\|drop` | Raportowanie, flaga, przycięcie lub usuwanie; domyślnie `report` |
| `--iqr-factor 1.5` | Dodatni współczynnik reguły IQR |
| `--output PLIK` / `--output-sep ";"` | Ścieżka i separator eksportu CSV |
| `--report PLIK` / `--summary PLIK` | Ścieżki raportów JSON i Markdown |

### Decyzje dotyczące czyszczenia

1. Pełne duplikaty są usuwane jako pierwsze, z pozostawieniem pierwszego
   wystąpienia. Kolumny nie są zmieniane, a różniące się rekordy nie są łączone.
   Duplikaty powstałe dopiero po imputacji nie są automatycznie usuwane;
   ujawni je profil po operacjach.
2. Konwersja na liczby wymaga wskazania kolumny. Niepoprawne tokeny i ±inf
   zamieniają się na braki; liczba takich wartości trafia do dziennika.
   Domyślnie tekst i wartości nieskończone pozostają zachowane.
3. Zakresy dotyczą wyłącznie wybranych kolumn liczbowych. Tryb `report`
   pokazuje problem bez zmiany danych. Tryby `missing`, `clip` i `drop`
   wymagają jawnego parametru użytkownika.
4. Imputacja stosuje medianę skończonych liczb oraz dominantę tekstu i wartości
   logicznych. Przy remisie wybierana jest pierwsza dominanta w kolejności
   Pandas. Całkowicie pusta kolumna nie ma wiarygodnej mediany/dominanty:
   zostaje pusta i trafia do `unfilled_columns` w raporcie.
5. IQR = Q3 − Q1. Wartości poniżej Q1 − k·IQR lub powyżej Q3 + k·IQR
   są odstające. Kwartyle mają interpolację liniową. Przy IQR=0 albo braku
   skończonych danych metoda jest nieaktywna; taki stan jest raportowany.
6. Outlier nie musi być błędem, dlatego domyślnie jest raportowany.
   Przykład oznacza dochód flagą i zachowuje jego wartość. Przycinanie lub
   usuwanie należy uzasadnić znaczeniem danych. Flaga tworzy kolumnę logiczną
   dla wszystkich rekordów, więc jej `affected_records` obejmuje wszystkie
   rekordy; `detected` wskazuje wyłącznie liczbę outlierów.
7. Kolejność pipeline: duplikaty → konwersje → zakresy → braki → wybrane
   operacje IQR. Każda operacja IQR oblicza progi z aktualnych danych.
   Kolejność kilku operacji usuwających rekordy może wpływać na późniejsze
   progi; parametry i kolejność są zapisywane w raporcie.

`before` w JSON opisuje oryginalny plik. `quality_before` ocenia osobną kopię
surowych danych po jawnej konwersji kolumn `--numeric`, aby możliwa była
ocena ich zakresów. Oryginalne typy pozostają widoczne w `before`.
`after` i `quality_after` dotyczą wyniku całego pipeline.
`affected_records` nie należy sumować pomiędzy operacjami, ponieważ jeden
rekord może zostać dotknięty kilkukrotnie.

### Reset w tym samym procesie

Logika sesji jest oddzielona od interfejsu. Można używać jej interaktywnie,
a w lab 8 zostanie połączona z GUI:

```python
from data_session import DataSession, RangeRule

session = DataSession.from_csv("dane_przecinek.csv")
session.drop_exact_duplicates()
session.apply_range("housing_median_age", RangeRule(1, 52), "missing")
session.handle_missing("impute")
session.reset()  # 12 oryginalnych rekordów, bez zmienionych wartości i flag
print(session.profile()["rows"])
```

## Dane testowe i testy

Dołączone CSV są małymi, syntetycznymi przykładami, **nie zmodyfikowanym
zbiorem referencyjnym prowadzącej**. Nie został on dołączony do rozmowy;
PDF zawiera jego opis, a nie same dane. Pierwszy przykład zachowuje typowe
nazwy kolumn California Housing, żeby ułatwić późniejszą demonstrację.

| Plik | Przygotowane problemy | Oczekiwany rezultat |
| --- | --- | --- |
| `dane_przecinek.csv` | 12×10, 1 nadmiarowy duplikat, 2 braki, wiek 120, dochód 90 | Główne polecenie: 11×11, 0 braków, 1 flaga dochodu |
| `dane_srednik.csv` | 6×4, polskie znaki, duplikat, brak wieku i segmentu, wiek 200 | Po deduplikacji, zakresie 0–120→brak i `drop`: 3×4 |
| `dane_brzegowe.csv` | 5×4, błędny tekst, inf, braki, stała i całkowicie pusta kolumna | `--numeric liczba --missing impute`: 10,15,15,20,15; `pusta` pozostaje pusta; IQR stałej nieaktywny |

```bash
python -m unittest -v
```

Wynik weryfikacji etapu: **31 testów zaliczonych**, Pandas 2.2.3.
Testy obejmują profil, strategie braków, pełne duplikaty, zakresy bez zmian
niepowiązanych kolumn, wszystkie akcje IQR, reset, błędne pliki i parametry,
kodowanie, ochronę wejścia, błędy zapisu, odtwarzalność i ponowny odczyt CSV.
Przypadki wejściowe są małe i mają ręcznie określone oczekiwania.
GUI i eksport wykresów zostaną przetestowane w odpowiadających im etapach.

## Pliki

| Plik | Rola |
| --- | --- |
| `data_session.py` | Model sesji, wczytywanie, profil, reguły, czyszczenie, reset i audyt |
| `lab6.py` | Parametry CLI, podgląd, uruchomienie pipeline, CSV i raporty |
| `test_lab6.py` | Automatyczna macierz testów logiki i eksportu |
| `dane_*.csv` | Trzy reprezentatywne wejścia testowe |
| `cleaned.csv` | Przykładowy wynik głównego polecenia |
| `raport_lab6.json`, `raport_lab6.md` | Pełny raport oraz czytelne podsumowanie |
| `requirements.txt` | Zależności bieżącego etapu |
| `PLAN_PROJEKTU_2.md`, `CHANGELOG.md` | Zadania dalszych etapów i rzeczywisty dziennik zmian |

## Znane ograniczenia i oddanie

To etap lab 6: nie zawiera jeszcze wykresów Matplotlib/Seaborn ani GUI
Tkinter/ttk. Ich termin realizacji i kryteria są zapisane w planie. Dane są
wczytywane do pamięci; dla plików większych od dostępnej pamięci potrzebne
byłoby przetwarzanie porcjami. CSV musi mieć nagłówek z unikalnymi,
niepustymi nazwami i stałą liczbą pól. Automatyczne rozpoznanie separatora
można zastąpić jawnym `--sep`. Tekst z przecinkiem dziesiętnym należy
wczytać z `--decimal ","` przed konwersją numeryczną.

Zgodnie z zasadami przedmiotu gotowy projekt 2 oddaje się na końcu lab 9
przez platformę jako `Nazwisko_Imie_P2.zip`; sam GitHub nie zastępuje
oddania. Dokładna data i godzina pochodzą z platformy. Archiwum końcowe ma
zawierać pełną aplikację, dane testowe, zależności, README, wyniki,
raport testów i minimum dwa wyeksportowane wykresy. Nie należy dołączać
środowiska wirtualnego, sekretów ani plików generowanych przez narzędzia.

## Autor, źródła i pomoc AI

Repozytorium użytkownika `DEMONLIVE13`. Imię i nazwisko autora oraz nazwę
archiwum należy uzupełnić przed formalnym oddaniem.

**Wykorzystano OpenAI Codex / ChatGPT:** odczyt obu dostarczonych PDF-ów,
przygotowanie implementacji lab 6, testów, przykładowych danych,
dokumentacji i harmonogramu dalszych etapów. Kod został uruchomiony
i sprawdzony testami automatycznymi. Student powinien samodzielnie
przejrzeć rozwiązanie, rozumieć jego działanie i potrafić wykonać drobną
modyfikację podczas obrony. Historia Git i CHANGELOG opisują faktyczne
prace; nie symulują wcześniejszych tygodni pracy.

Biblioteki i materiały:

- Pandas — profilowanie i operacje na DataFrame, licencja BSD-3-Clause;
  [read_csv](https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html),
  [braki danych](https://pandas.pydata.org/docs/user_guide/missing_data.html),
  [quantile](https://pandas.pydata.org/docs/reference/api/pandas.Series.quantile.html).
- Python — biblioteka standardowa `argparse`, `csv`, `dataclasses`, `json`,
  `unittest`, [dokumentacja](https://docs.python.org/3/).
- Instrukcja projektu, str. 2–3: kamienie milowe i macierz testów;
  str. 5–6: wzorzec sesji, pakiet do oddania i deklaracja AI.
- Warunki przedmiotu, str. 3 i 5–7: oddanie ZIP, samodzielność, AI
  i koniec lab 9 jako moment oddania projektu 2.

Wzorzec oddzielenia danych surowych i aktualnych pochodzi z materiału
prowadzącej; implementacja rozwija go o walidację, strategie i audyt.
