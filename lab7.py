"""Kamień milowy lab 7: cztery wykresy przed/po i korelacja."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from data_session import DataError, read_csv
from visualizations import comparison_figure, pearson_correlation, save_figure


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Lab 7: porównaj surowy i oczyszczony CSV; zapisz wykresy i wnioski.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("before", type=Path, help="surowy CSV")
    parser.add_argument("after", type=Path, help="oczyszczony CSV")
    parser.add_argument("--sep", choices=("auto", ",", ";"), default="auto")
    parser.add_argument("--encoding", default="utf-8-sig")
    parser.add_argument("--decimal", choices=(".", ","), default=".")
    parser.add_argument("--hist", default="housing_median_age", help="liczbowa kolumna histogramu")
    parser.add_argument("--x", default="median_income", help="liczbowa oś X i pierwsza zmienna korelacji")
    parser.add_argument("--y", default="median_house_value", help="liczbowa oś Y i druga zmienna korelacji")
    parser.add_argument("--box", default="median_income", help="liczbowa kolumna wykresu pudełkowego")
    parser.add_argument("--category", default="ocean_proximity", help="kolumna kategorialna wykresu słupkowego")
    parser.add_argument("--bins", type=int, default=10, help="wspólna liczba przedziałów, 1–200")
    parser.add_argument("--formats", choices=("png", "svg", "pdf"), nargs="+", default=["png", "svg"])
    parser.add_argument("--output-dir", type=Path, default=Path("."), help="istniejący katalog wynikowy")
    return parser


def _numeric_summary(frame: pd.DataFrame, name: str) -> str:
    values = frame[name].replace([np.inf, -np.inf], np.nan).dropna()
    return f"min={values.min():.3f}, mediana={values.median():.3f}, max={values.max():.3f}"


def markdown_report(
    args: argparse.Namespace, before: pd.DataFrame, after: pd.DataFrame,
    outputs: list[Path],
) -> str:
    old = pearson_correlation(before, args.x, args.y)
    new = pearson_correlation(after, args.x, args.y)
    direction = "dodatni" if new.coefficient > 0 else "ujemny" if new.coefficient < 0 else "zerowy"
    counts = pd.DataFrame({
        "Przed": before[args.category].dropna().astype(str).value_counts(),
        "Po": after[args.category].dropna().astype(str).value_counts(),
    }).fillna(0).astype(int).sort_index()
    lines = [
        "# Lab 7 — wizualizacje i interpretacja", "",
        f"Wejścia: `{args.before.name}` → `{args.after.name}`. "
        "Skrypt porównuje pliki; nie wykonuje ponownie czyszczenia.", "",
        "## Zbiór przed i po", "",
        "| Miara | Przed | Po |", "| --- | ---: | ---: |",
        f"| Rekordy | {len(before)} | {len(after)} |",
        f"| Brakujące komórki | {int(before.isna().sum().sum())} | {int(after.isna().sum().sum())} |",
        f"| Nadmiarowe pełne duplikaty | {int(before.duplicated().sum())} | {int(after.duplicated().sum())} |",
        "", "## Wykresy", "",
        f"- Histogram `{args.hist}`, {args.bins} wspólnych przedziałów: "
        f"przed {_numeric_summary(before, args.hist)}; po {_numeric_summary(after, args.hist)}.",
        f"- Scatter `{args.x}` / `{args.y}`: {old.pairs} par przed, {new.pairs} par po. "
        "Każdy punkt odpowiada kompletnej parze; braków osi nie usuwa się osobno.",
        f"- Box plot `{args.box}`: przed {_numeric_summary(before, args.box)}; "
        f"po {_numeric_summary(after, args.box)}. Wąsy: 1,5·IQR; punkty poza nimi pozostają widoczne.",
        f"- Bar plot `{args.category}`: liczba rekordów w każdej kategorii, bez agregacji średnią. "
        "Braki są pomijane i uwzględnione w liczniku wykorzystanych rekordów.", "",
        "Porównania mają wspólne skale. Histogram ma te same granice przedziałów, "
        "a słupki tę samą kolejność i pełną sumę kategorii z obu plików.", "",
        "| Kategoria | Przed | Po |", "| --- | ---: | ---: |",
    ]
    for category, row in counts.iterrows():
        label = str(category).replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {label} | {row['Przed']} | {row['Po']} |")
    lines += [
        "", "## Korelacja", "",
        f"Pearson dla `{args.x}` i `{args.y}`. Do obliczenia wchodzą wyłącznie "
        "kompletne pary skończonych liczb; minimum 3 pary i zmienność obu kolumn.", "",
        "| Miara | Przed | Po |", "| --- | ---: | ---: |",
        f"| r Pearsona | {old.coefficient:.6f} | {new.coefficient:.6f} |",
        f"| Liczba par | {old.pairs} | {new.pairs} |",
        f"| Pominięte rekordy | {old.excluded} | {new.excluded} |", "",
        f"Po przygotowaniu danych związek liniowy jest {direction}; "
        f"zmiana współczynnika r wynosi {new.coefficient-old.coefficient:+.6f}. "
        "Sama zmiana r nie jest miarą jakości czyszczenia.", "",
        "**Korelacja nie dowodzi przyczynowości.** Współczynnik opisuje związek liniowy "
        "w wybranej próbie, a nie wpływ jednej zmiennej na drugą. Mała próba, "
        "duplikaty, imputacja i wartości odstające mogą zmieniać wynik. "
        "Należy ocenić równocześnie scatter i liczebność próby.", "",
        "Różnice przed/po opisują łączny efekt przygotowania wskazanych plików. "
        "Sam wykres nie pozwala przypisać różnicy jednej konkretnej operacji; "
        "jej parametry i liczby zmian należy sprawdzić w raporcie czyszczenia.", "",
        "## Eksport", "",
    ]
    lines.extend(f"- [{path.name}]({path.name})" for path in outputs)
    lines += ["", "## Walidacja i ograniczenia", "",
              "Błędny typ, brak wyboru, brak kolumny, pusty zbiór, stała kolumna liczbowa "
              "i niewystarczająca liczba par kończą się czytelnym komunikatem. "
              "Wykres kategorii przyjmuje do 20 kategorii. Na wykresie podano n/rozmiar zbioru; "
              "pomijanie NaN i ±inf nie zmienia danych wejściowych.", "",
              "Domyślny przykład korzysta z małych danych syntetycznych. "
              "Nie stanowi analizy zbioru referencyjnego prowadzącej.", ""]
    return "\n".join(lines)


def run(args: argparse.Namespace) -> dict[str, Any]:
    if not args.output_dir.is_dir():
        raise DataError("Katalog wynikowy nie istnieje. Wskaż istniejący katalog przez --output-dir.")
    if len(set(args.formats)) != len(args.formats):
        raise DataError("Lista formatów zawiera powtórzenia.")
    options = {"separator": None if args.sep == "auto" else args.sep,
               "encoding": args.encoding, "decimal": args.decimal}
    before, after = read_csv(args.before, **options), read_csv(args.after, **options)
    specs = [
        ("histogram_przed_po", "histogram", args.hist, None),
        ("scatter_przed_po", "scatter", args.x, args.y),
        ("boxplot_przed_po", "box", args.box, None),
        ("barplot_przed_po", "bar", args.category, None),
        ("korelacja_przed_po", "correlation", args.x, args.y),
    ]
    outputs = [args.output_dir / f"{stem}.{fmt}" for stem, *_ in specs for fmt in args.formats]
    report_path = args.output_dir / "raport_lab7.md"
    protected = {args.before.resolve(), args.after.resolve()}
    if any(path.resolve() in protected for path in [*outputs, report_path]):
        raise DataError("Plik wejściowy nie może być nadpisany wynikiem. Wybierz inny katalog wynikowy.")
    # Walidacja i budowa całego zestawu poprzedzają pierwszy zapis.
    figures = []
    try:
        for stem, kind, x, y in specs:
            figures.append((stem, comparison_figure(before, after, kind, x, y, bins=args.bins)))
        text = markdown_report(args, before, after, outputs)
        for stem, fig in figures:
            for fmt in args.formats:
                save_figure(fig, args.output_dir / f"{stem}.{fmt}")
        report_path.write_text(text, encoding="utf-8")
    except OSError as exc:
        raise DataError(f"Nie można zapisać raportu: {exc}. Sprawdź ścieżkę i prawa zapisu.") from exc
    finally:
        for _, fig in figures:
            fig.clear()
    print(f"Zapisano {len(specs)} porównań ({len(outputs)} plików) oraz {report_path}.")
    print(f"Pearson: {pearson_correlation(before, args.x, args.y).coefficient:.6f} → "
          f"{pearson_correlation(after, args.x, args.y).coefficient:.6f}.")
    print("Korelacja nie dowodzi przyczynowości.")
    return {"outputs": outputs, "report": report_path}


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        run(args)
    except (DataError, TypeError, OverflowError) as exc:
        print(f"Błąd: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
