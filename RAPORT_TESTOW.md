# Raport testów — lab 6 i lab 7

Data weryfikacji: **17.11.2026**.

## Środowisko i wynik

Windows, Python 3.12.10, Pandas 2.3.3, Matplotlib 3.10.9,
Seaborn 0.13.2, NumPy 2.5.5. Wykresy testowano z backendem Agg,
bez uruchamiania okien. `pip check`: brak niezgodnych zależności.

```powershell
.venv\Scripts\python.exe -m unittest -v
```

**48 testów zakończonych powodzeniem: 31 dla lab 6 i 17 dla lab 7.**
Końcowy wynik uruchomienia: `Ran 48 tests` / `OK`.
Seaborn 0.13.2 emituje w testach box plotu `PendingDeprecationWarning`
dotyczący parametru `vert`; nie wpływa on na wynik testów ani eksport.

## Sprawdzone przypadki

| Przypadek | Weryfikacja i rezultat |
| --- | --- |
| CSV z przecinkiem i średnikiem | Poprawna liczba kolumn, cytowane pola, polskie znaki, inny schemat danych |
| Niepoprawny CSV i kodowanie | Czytelne błędy, brak cichego pomijania wadliwych wierszy |
| Profil i czyszczenie | Zgodne liczby braków, duplikatów, zakresów i IQR; zachowane niepowiązane kolumny |
| Kopia surowa i reset | Odtworzone rekordy, wartości i kolumny; wejście pozostaje zachowane |
| Histogram | Suma liczebności równa liczbie skończonych obserwacji; wspólne przedziały przed/po |
| Scatter | Punkty zgodne z ręcznie określonymi parami; braki i inf pomijane parami |
| Box plot | Zachowane widoczne wartości odstające oraz oczekiwana mediana |
| Bar plot | Dokładne liczebności kategorii, wspólna kolejność i zera dla brakującej kategorii |
| Pearson | Ręcznie znane r=1 i r=−1, poprawna liczba par i wykluczeń |
| Walidacja | Blokada pustych, stałych i nienumerycznych kolumn, braku wyboru, powtórzonych nazw, złych parametrów i zbyt małej liczby par |
| Stan funkcji | Wyniki są obiektami Figure; brak zmian wejściowego DataFrame, globalnego rozmiaru fontu i listy okien pyplot |
| Eksport PNG/SVG | Ponowne otwarcie PNG przez Pillow oraz parsowanie SVG; sprawdzono wszystkie 10 eksportów CLI |
| Ochrona wyników | Błąd walidacji nie nadpisuje poprzednich eksportów; wejście nie może być ścieżką wyniku |
| Powtarzalność CSV | Takie same parametry dają taki sam oczyszczony CSV; raport audytu ma rzeczywisty czas uruchomienia |

## Scenariusz demonstracyjny

Uruchomiono polecenia instalacji zależności i pracy z README:

```powershell
.venv\Scripts\python.exe lab6.py dane_przecinek.csv --range housing_median_age 1 52 --range-action missing --missing impute --outlier median_income --outlier-action flag
.venv\Scripts\python.exe lab7.py dane_przecinek.csv cleaned.csv
```

Wynik czyszczenia: **12→11 rekordów**, **2→0 brakujących komórek**,
usunięty jeden nadmiarowy pełny duplikat. Wiek 120 zastąpiono przez brak
i medianę 37,5. Uzupełniono też brak `total_bedrooms` medianą 375
i `ocean_proximity` dominantą `NEAR BAY`. Dochód 90 pozostał w danych,
a `median_income__outlier` wskazuje jeden rekord.

Wynik lab 7: pięć porównań w PNG i SVG oraz `raport_lab7.md`.
Pearson dochód/wartość domu: **0,660885** dla 12 par przed
i **0,668561** dla 11 par po. Wnioski wskazują ograniczenia małej próby
i nie utożsamiają korelacji z przyczynowością.

Wszystkie pięć PNG obejrzano: tytuły, osie, liczebności i oba panele
są czytelne. Wspólna skala zachowuje widoczność wieku 120 przed
czyszczeniem i dochodu 90 w obu wersjach. SVG sprawdzono przez parser XML.

## Zakres sprawdzenia repozytorium

Porównano lokalny folder i wejściowe archiwum ze stanem GitHuba
`32b63670ba6b720ff10b2f97bd08a5e7eaa1748e` z 10.11.2026.
Kod i dane lab 6 były zgodne po uwzględnieniu LF/CRLF.
Lokalny raport JSON różnił się wyłącznie czasami operacji.
Na tym etapie brakowało funkcji, testów i eksportów lab 7; dodano je
w bieżącej aktualizacji. README zawiera autora imieniem i nazwiskiem,
rzeczywiste zależności, funkcje, ograniczenia i deklarację pomocy AI.

## Pozostały zakres

- Dane są syntetyczne. Nie sprawdzono pliku referencyjnego prowadzącej,
  ponieważ nie został udostępniony.
- Testy GUI i osadzenia wykresu należą do lab 8–9 i nie były jeszcze wykonywane.
- Kontrola otwarcia plików obejmuje PNG i SVG. Eksport PDF jest dostępny
  jako opcja; nie jest częścią tej weryfikacji.
