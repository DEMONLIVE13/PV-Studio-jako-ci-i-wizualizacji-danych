# Lab 7 — wizualizacje i interpretacja

Wejścia: `dane_przecinek.csv` → `cleaned.csv`. Skrypt porównuje pliki; nie wykonuje ponownie czyszczenia.

## Zbiór przed i po

| Miara | Przed | Po |
| --- | ---: | ---: |
| Rekordy | 12 | 11 |
| Brakujące komórki | 2 | 0 |
| Nadmiarowe pełne duplikaty | 1 | 0 |

## Wykresy

- Histogram `housing_median_age`, 10 wspólnych przedziałów: przed min=15.000, mediana=40.500, max=120.000; po min=15.000, mediana=37.500, max=52.000.
- Scatter `median_income` / `median_house_value`: 12 par przed, 11 par po. Każdy punkt odpowiada kompletnej parze; braków osi nie usuwa się osobno.
- Box plot `median_income`: przed min=3.846, mediana=5.922, max=90.000; po min=3.846, mediana=6.200, max=90.000. Wąsy: 1,5·IQR; punkty poza nimi pozostają widoczne.
- Bar plot `ocean_proximity`: liczba rekordów w każdej kategorii, bez agregacji średnią. Braki są pomijane i uwzględnione w liczniku wykorzystanych rekordów.

Porównania mają wspólne skale. Histogram ma te same granice przedziałów, a słupki tę samą kolejność i pełną sumę kategorii z obu plików.

| Kategoria | Przed | Po |
| --- | ---: | ---: |
| INLAND | 4 | 4 |
| NEAR BAY | 7 | 7 |

## Korelacja

Pearson dla `median_income` i `median_house_value`. Do obliczenia wchodzą wyłącznie kompletne pary skończonych liczb; minimum 3 pary i zmienność obu kolumn.

| Miara | Przed | Po |
| --- | ---: | ---: |
| r Pearsona | 0.660885 | 0.668561 |
| Liczba par | 12 | 11 |
| Pominięte rekordy | 0 | 0 |

Po przygotowaniu danych związek liniowy jest dodatni; zmiana współczynnika r wynosi +0.007676. Sama zmiana r nie jest miarą jakości czyszczenia.

**Korelacja nie dowodzi przyczynowości.** Współczynnik opisuje związek liniowy w wybranej próbie, a nie wpływ jednej zmiennej na drugą. Mała próba, duplikaty, imputacja i wartości odstające mogą zmieniać wynik. Należy ocenić równocześnie scatter i liczebność próby.

Różnice przed/po opisują łączny efekt przygotowania wskazanych plików. Sam wykres nie pozwala przypisać różnicy jednej konkretnej operacji; jej parametry i liczby zmian należy sprawdzić w raporcie czyszczenia.

## Eksport

- [histogram_przed_po.png](histogram_przed_po.png)
- [histogram_przed_po.svg](histogram_przed_po.svg)
- [scatter_przed_po.png](scatter_przed_po.png)
- [scatter_przed_po.svg](scatter_przed_po.svg)
- [boxplot_przed_po.png](boxplot_przed_po.png)
- [boxplot_przed_po.svg](boxplot_przed_po.svg)
- [barplot_przed_po.png](barplot_przed_po.png)
- [barplot_przed_po.svg](barplot_przed_po.svg)
- [korelacja_przed_po.png](korelacja_przed_po.png)
- [korelacja_przed_po.svg](korelacja_przed_po.svg)

## Walidacja i ograniczenia

Błędny typ, brak wyboru, brak kolumny, pusty zbiór, stała kolumna liczbowa i niewystarczająca liczba par kończą się czytelnym komunikatem. Wykres kategorii przyjmuje do 20 kategorii. Na wykresie podano n/rozmiar zbioru; pomijanie NaN i ±inf nie zmienia danych wejściowych.

Domyślny przykład korzysta z małych danych syntetycznych. Nie stanowi analizy zbioru referencyjnego prowadzącej.
