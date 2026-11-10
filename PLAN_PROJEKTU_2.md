# Projekt 2 — zadania na kolejne tygodnie

Autor: **Szymon Głogowski** (`DEMONLIVE13`).

Źródła: `projekt-2-dane.pdf` z 5.10.2026 oraz
`warunki-programowanie-v (1).pdf` z 6.10.2026, udostępnione w rozmowie.
Nie kopiować PDF-ów do repozytorium. Pliki kodu, testów, danych i wyników
zapisywać w katalogu głównym repozytorium, bez dodatkowych podfolderów.

Repozytorium: https://github.com/DEMONLIVE13/PV-Studio-jako-ci-i-wizualizacji-danych

Uzgodniona pora pracy automatycznej: **wtorek, 12:00, Europe/Warsaw**.
Następne trzy etapy: 17.11.2026, 24.11.2026, 1.12.2026.
To harmonogram pracy użytkownika, nie daty oddania ogłoszone przez uczelnię.
Każde wykonanie ma odczytać stan repozytorium i kontynuować pierwszy
nieukończony etap, zachowując zmiany użytkownika. Status oznaczać dopiero
po rzeczywistej realizacji i testach. Ukończonych etapów nie powtarzać.

## Lab 6 — Pandas i pipeline (10.11.2026)

**Status: ukończony.**

- [x] CSV z przecinkiem i średnikiem, podgląd, kontrolowane błędy.
- [x] Pełny profil: rozmiar, typy, statystyki, braki i procenty, pełne duplikaty, unikalność.
- [x] Konfigurowalne zakresy poprawnych wartości i reguła IQR.
- [x] Pełne duplikaty, usuwanie braków i imputacja medianą/dominantą.
- [x] Obsługa błędnego tekstu i wartości spoza zakresu; jawny wybór obsługi outlierów.
- [x] Kopia surowa, reset bez restartu, audyt parametrów i liczby zmian.
- [x] `cleaned.csv`, raport przed/po JSON i Markdown.
- [x] Trzy małe dane testowe, 31 zaliczonych testów, README, zależności i deklaracja AI.

## Lab 7 — Matplotlib i Seaborn (17.11.2026)

**Status: do wykonania.**

- [ ] Dodać zależności Matplotlib i Seaborn w `requirements.txt`.
- [ ] Utworzyć funkcje przyjmujące dane/parametry i zwracające `Figure`, bez zależności od GUI.
- [ ] Zrealizować histogram, scatter, box plot i bar plot z tytułem i opisami osi.
- [ ] Walidować wybór, istnienie i typ kolumn, brak danych oraz kolumnę stałą; nie generować mylących wykresów.
- [ ] Dodać analizę korelacji dla danych liczbowych i poprawną interpretację: korelacja nie dowodzi przyczynowości.
- [ ] Pokazać wykresy dla danych przed i po czyszczeniu, wyjaśniając wpływ operacji.
- [ ] Zapisać minimum dwa przykładowe wykresy w katalogu głównym; testować funkcje z backendem bez okna.
- [ ] Zaktualizować README, rzeczywisty dziennik zmian, raport testów i status etapu.

**Odbiór:** funkcja tworząca wykres na podstawie parametrów, cztery rodzaje
wykresów, czytelne opisy, walidacja typów i krótki opis wniosków.

## Lab 8 — Tkinter/ttk i sesja (24.11.2026)

**Status: do wykonania.**

- [ ] Utworzyć GUI Tkinter/ttk korzystające z istniejącego `DataSession`; logikę sesji zachować poza GUI.
- [ ] Dodać wybór CSV, separatora i kodowania; błędny plik ma pokazywać komunikat bez zamykania aplikacji.
- [ ] Wyświetlać podgląd, profil danych, problemy i listę operacji.
- [ ] Dodać wybór kolumn, strategii braków, zakresów, akcji IQR oraz reset danych surowych.
- [ ] Udostępnić cztery rodzaje wykresów z listami poprawnych kolumn dopasowanymi do typu wykresu.
- [ ] Po zmianie zbioru odświeżać listy i stan kontrolek; unikać ukrytych zmiennych globalnych.
- [ ] Sprawdzić scenariusz pustego pliku, złego typu, braku wyboru i złych parametrów reguły.
- [ ] Udokumentować rzeczywiste testy GUI, instrukcję uruchomienia i ograniczenia środowiska.
- [ ] Zaktualizować README, CHANGELOG, raport testów i status etapu.

**Odbiór:** GUI wczytuje CSV, pokazuje profil i pozwala wybierać poprawne
kolumny; błędny plik nie zamyka programu.

## Lab 9 — integracja, eksport i pakiet końcowy (1.12.2026)

**Status: do wykonania.**

- [ ] Osadzić `Figure` przez `FigureCanvasTkAgg`; przy nowym wykresie poprawnie usuwać poprzedni canvas.
- [ ] Dokończyć pełny przepływ: wczytanie → diagnoza → wybrane czyszczenie → wykres → eksport.
- [ ] Dodać wybór ścieżki zapisu oczyszczonego CSV i wykresu w PNG oraz co najmniej PDF albo SVG.
- [ ] Obsłużyć błędy zapisu i anulowanie okien; komunikaty mają wskazywać rozwiązanie problemu.
- [ ] Przejść minimalną macierz: oba separatory, braki liczbowe/tekstowe, duplikaty, zakresy, kolumna stała/nienumeryczna, eksport.
- [ ] Przetestować ponowny odczyt CSV oraz otwarcie PNG i PDF/SVG; udokumentować test GUI.
- [ ] Zachować w katalogu głównym `cleaned.csv`, przykładowy raport i minimum dwa wyeksportowane wykresy.
- [ ] Uzupełnić README: instalacja, uruchomienie, funkcje, ograniczenia, autor, źródła, biblioteki i faktyczny zakres AI.
- [ ] Uzupełnić raport testów i prawdziwą historię pracy; sprawdzić uruchomienie według README.
- [ ] Przygotować instrukcję pakowania `Glogowski_Szymon_P2.zip` bez środowiska wirtualnego, sekretów i zbędnych artefaktów.
- [ ] Zaktualizować status etapu i podsumować wynik wraz z linkiem do zmian w GitHub.

**Odbiór:** pełna aplikacja, powtarzalne wyniki, eksporty, dokumentacja,
testy i materiały do krótkiej obrony. Repozytorium nie zastępuje oddania
ZIP na platformie; dokładny termin pochodzi z kursu.

## Kryteria wspólne z PDF-ów

| Obszar | Punkty |
| --- | ---: |
| Wczytywanie i profil | 15 |
| Czyszczenie i ślad zmian | 25 |
| Wizualizacje i interpretacja | 15 |
| GUI i eksport | 15 |
| Architektura i jakość kodu | 10 |
| Walidacja i obsługa błędów | 8 |
| Testy | 5 |
| Dokumentacja, proces i obrona | 7 |
| Razem | 100 |

Nie usuwać outlierów bez pokazania reguły i liczby zmian. Operacje mają
być konfigurowalne, a dane surowe zachowane. Samodzielna obrona i co
najmniej 50/100 pkt są warunkami zaliczenia projektu. Nie deklarować
nieprzeprowadzonych testów, gotowości niewykonanych funkcji ani fikcyjnej
historii pracy. Użycie Codex/ChatGPT ujawniać zgodnie z faktycznym zakresem.
