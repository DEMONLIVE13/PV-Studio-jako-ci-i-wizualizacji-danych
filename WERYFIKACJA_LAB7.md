# Weryfikacja zakresu do lab 7 — 18.11.2026

Dane źródłowe: california_housing_projekt2.csv, zachowane bez zmian.

- Wczytano 20 840 rekordów, 9 kolumn, 1080 braków, 200 nadmiarowych duplikatów.
- Jawna konwersja wszystkich kolumn obsłużyła błędne tokeny tekstowe.
- Pipeline pozostawił 20 640 rekordów bez braków; outliery dochodu oznaczono flagą.
- Wygenerowano histogram HouseAge, scatter MedInc/MedHouseVal, box plot MedInc,
  słupki grup wieku oraz korelację przed/po, łącznie 10 plików PNG/SVG.
- Pearson na kompletnych parach po konwersji: 0,564612 przed i 0,563704 po.
  Korelacja nie dowodzi przyczynowości.
- Oryginalne dane i profil przed konwersją pozostają zachowane.

## Zgodność z instrukcją

Lab 6: profil, reguły, konfigurowalne czyszczenie, audyt, reset i eksport CSV
są zaimplementowane w data_session.py i lab6.py.

Lab 7: cztery wymagane typy wykresów przed/po, walidacja typów i stałych
kolumn, tytuły, osie, funkcje zwracające Figure i interpretacja korelacji
są zaimplementowane w visualizations.py i lab7.py.

Uruchomienie rzeczywistego CSV: `python demo_california.py` po instalacji
zależności. Wyniki lokalne: wyniki_california/. Wcześniejszy raport testów
z 17.11 opisywał dostępne wtedy dane syntetyczne; niniejsza weryfikacja
uzupełnia go o otrzymany zbiór referencyjny.

Lab 8 (GUI) i lab 9 (integracja GUI i oddanie) pozostają niewykonane.

Testy automatyczne 18.11.2026: 48 testów / OK. Wszystkie 5 PNG
ponownie otwarto przez Pillow, a 5 SVG sprawdzono parserem XML.
