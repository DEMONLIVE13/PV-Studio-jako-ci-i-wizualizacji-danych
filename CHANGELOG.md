# Dziennik zmian

## 2026-11-17 — laboratorium 7 i dokumentacja

- Dodanie `visualizations.py`: funkcje zwracające `Figure`, histogram,
  scatter, box plot, bar plot i korelacja Pearsona.
- Porównania przed/po ze wspólnymi skalami, przedziałami histogramu
  i kolejnością kategorii oraz licznikami wykorzystanych rekordów.
- Walidacja kolumn, typów, pustych i stałych danych, kompletnych par,
  parametrów i ścieżek eksportu; brak zmiany wejściowych DataFrame.
- CLI `lab7.py`, pięć porównań w PNG/SVG i raport z wyliczonymi wnioskami.
- Dodanie 17 testów wykresów, korelacji, walidacji i ponownego otwarcia eksportów.
- Uporządkowanie README według wymagań projektu, usunięcie dopisków
  z nazwą konta, aktualizacja planu i raportu testów.
- Porównanie z GitHubem: bazowy kod i dane lab 6 były aktualne;
  różnice wejściowego raportu JSON dotyczyły czasu wykonania.
- Dodanie zasad zakończeń linii dla powtarzalnych plików CSV na Windows.

Prace wykonano z pomocą OpenAI Codex / ChatGPT.

## 2026-11-10 — poprawka kodowania testów na Windows

- Odtworzenie zgłoszonego wyniku 31 testów: 1 niepowodzenie i 1 błąd przy
  domyślnym CP1252. Powodem był odczyt raportów UTF-8 bez jawnego kodowania.
- Ustawienie `encoding="utf-8"` przy każdym odczycie JSON i Markdown w testach.
- Po poprawce 31 testów zaliczonych; dodatkowo po 31 zaliczonych testów przy
  symulacji domyślnego odczytu CP1252 i CP1250.

## 2026-11-10 — autor i weryfikacja do prezentacji

- Uzupełnienie autora: Szymon Głogowski.
- Ponowna kontrola zakresu lab 6 względem tabeli kamieni milowych w PDF-ie.
- Ponowne uruchomienie 31 testów: wszystkie zaliczone.
- Weryfikacja głównego polecenia, identyczności eksportu i powtarzalności,
  zachowania niepowiązanych kolumn, resetu, średnika i kontrolowanego błędu.
- Dodanie instrukcji prezentacji lab 6 do README i nazwy archiwum końcowego.

## 2026-11-10 — laboratorium 6

- Odczyt wymagań z dwóch PDF-ów dostarczonych przez użytkownika.
- Model sesji Pandas oddzielony od interfejsu; osobne dane surowe i aktualne.
- Wczytanie CSV, profil, duplikaty, zakresy, braki, IQR, reset i dziennik operacji.
- CLI, eksport CSV, raport przed/po JSON i Markdown.
- Trzy syntetyczne dane testowe oraz 31 zaliczonych testów automatycznych.
- README z instalacją, regułami, ograniczeniami, źródłami i deklaracją AI.
- Plan lab 7–9: wtorki o 12:00 czasu Europe/Warsaw przez kolejne trzy tygodnie.

Prace tego dnia wykonano z pomocą OpenAI Codex / ChatGPT.
To pierwszy etap implementacji; nie oznacza ukończenia całego projektu 2.
