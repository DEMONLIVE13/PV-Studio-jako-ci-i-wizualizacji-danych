"""Uruchamialny kamień milowy laboratorium 6 projektu 2."""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

import pandas as pd

from data_session import DataError, DataSession, RangeRule


def json_safe(value: Any) -> Any:
    """Zamień typy Pandas/NumPy i braki na standardowy, przenośny JSON."""
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    if value is None or value is pd.NA or value is pd.NaT:
        return None
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Lab 6: profil, reguły jakości, czyszczenie i raport przed/po.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("csv", type=Path, help="plik CSV do analizy")
    parser.add_argument("--sep", choices=("auto", ",", ";"), default="auto")
    parser.add_argument("--encoding", default="utf-8-sig")
    parser.add_argument("--decimal", choices=(".", ","), default=".")
    parser.add_argument("--numeric", action="append", default=[], metavar="KOLUMNA",
                        help="jawnie zamień tekst na liczby; błędny tekst/inf -> brak")
    parser.add_argument("--range", dest="ranges", nargs=3, action="append", default=[],
                        metavar=("KOLUMNA", "MIN", "MAX"), help="domknięty zakres poprawnych wartości")
    parser.add_argument("--range-action", choices=("report", "missing", "clip", "drop"),
                        default="report")
    parser.add_argument("--missing", choices=("keep", "drop", "impute"), default="impute",
                        help="impute: mediana liczb, dominanta tekstu")
    parser.add_argument("--missing-column", action="append", metavar="KOLUMNA",
                        help="ogranicz strategię braków do wskazanych kolumn")
    parser.add_argument("--keep-duplicates", action="store_true")
    parser.add_argument("--outlier", action="append", default=[], metavar="KOLUMNA",
                        help="kolumna do jawnej obsługi outlierów")
    parser.add_argument("--outlier-action", choices=("report", "flag", "clip", "drop"),
                        default="report")
    parser.add_argument("--iqr-factor", type=float, default=1.5)
    parser.add_argument("--output", type=Path, default=Path("cleaned.csv"))
    parser.add_argument("--report", type=Path, default=Path("raport_lab6.json"))
    parser.add_argument("--summary", type=Path, default=Path("raport_lab6.md"))
    parser.add_argument("--output-sep", choices=(",", ";"), default=",")
    return parser


def validate_options(args: argparse.Namespace, session: DataSession) -> dict[str, RangeRule]:
    paths = [args.csv.resolve(), args.output.resolve(), args.report.resolve(), args.summary.resolve()]
    if len(set(paths)) != len(paths):
        raise DataError("Plik wejściowy i trzy pliki wynikowe muszą mieć różne ścieżki.")
    if not math.isfinite(args.iqr_factor) or args.iqr_factor <= 0:
        raise DataError("Współczynnik IQR musi być dodatnią, skończoną liczbą.")
    for names in (args.numeric, args.outlier, args.missing_column or []):
        if len(set(names)) != len(names):
            raise DataError("Lista kolumn zawiera powtórzenia.")
        for name in names:
            session._column(name)
    if args.outlier_action != "report" and not args.outlier:
        raise DataError("Wskaż kolumnę przez --outlier, aby obsłużyć jej outliery.")
    rules: dict[str, RangeRule] = {}
    for column, minimum, maximum in args.ranges:
        session._column(column)
        if column in rules:
            raise DataError(f"Kolumna {column} ma więcej niż jedną regułę zakresu.")
        try:
            rules[column] = RangeRule(float(minimum), float(maximum))
        except ValueError as exc:
            raise DataError(f"Niepoprawny zakres dla {column}: {exc}") from exc
    if args.range_action != "report" and not rules:
        raise DataError("Wskaż regułę przez --range, aby zmieniać wartości spoza zakresu.")
    for path in (args.output, args.report, args.summary):
        if not path.parent.is_dir():
            raise DataError(f"Katalog {path.parent} nie istnieje. Wybierz istniejącą lokalizację.")
    return rules


def markdown_report(report: dict[str, Any]) -> str:
    before, after = report["before"], report["after"]
    lines = [
        "# Lab 6 — raport profilu i czyszczenia", "",
        f"Plik: `{report['source']}`. Dołączone do repozytorium dane demonstracyjne są syntetyczne.", "",
        "| Miara | Przed | Po |", "| --- | ---: | ---: |",
    ]
    for key, label in (
        ("rows", "Rekordy"), ("columns", "Kolumny"),
        ("duplicate_records", "Nadmiarowe pełne duplikaty"), ("missing_cells", "Brakujące komórki"),
    ):
        lines.append(f"| {label} | {before[key]} | {after[key]} |")
    lines += ["", "## Profil kolumn przed/po", "",
              "| Kolumna | Typ przed → po | Braki przed → po | % braków przed → po | Unikalne przed → po |",
              "| --- | --- | ---: | ---: | ---: |"]
    for name in dict.fromkeys([*before["column_profile"], *after["column_profile"]]):
        old, new = before["column_profile"].get(name, {}), after["column_profile"].get(name, {})
        label = name.replace("|", "\\|").replace("\n", " ")
        lines.append(
            f"| {label} | {old.get('dtype', '—')} → {new.get('dtype', '—')} "
            f"| {old.get('missing', '—')} → {new.get('missing', '—')} "
            f"| {old.get('missing_pct', '—')} → {new.get('missing_pct', '—')} "
            f"| {old.get('unique', '—')} → {new.get('unique', '—')} |"
        )
    lines += ["", "## Jakość danych", "",
              "`quality_before` dotyczy kopii surowych danych po jawnej konwersji wskazanych "
              "kolumn na liczby. `before` przedstawia oryginalny plik, również jego typy.", ""]
    for phase, title in (("quality_before", "Przed pipeline"), ("quality_after", "Po pipeline")):
        lines += [f"### {title}", ""]
        quality = report[phase]
        if not quality["ranges"]:
            lines.append("Nie zdefiniowano reguł zakresu; podaj `--range KOLUMNA MIN MAX`.")
        for name, rule in quality["ranges"].items():
            lines.append(f"- Zakres {name} [{rule['minimum']}, {rule['maximum']}]: {rule['detected']} rekordów poza zakresem.")
        for name, details in quality["outliers_iqr"].items():
            lines.append(
                f"- IQR {name}: {details['detected']} outlierów; granice "
                f"{details['lower']} / {details['upper']}; reguła aktywna: {details['applicable']}."
            )
        for name, count in quality["non_finite"].items():
            if count:
                lines.append(f"- {name}: {count} wartości nieskończonych; jawnie użyj `--numeric {name}`.")
        lines.append("")
    lines += ["## Ślad zmian", "",
              "| Operacja | Rekordy przed | Rekordy po | Dotknięte rekordy | Zmienione komórki |",
              "| --- | ---: | ---: | ---: | ---: |"]
    for entry in report["audit_log"]:
        lines.append(
            f"| {entry['operation']} | {entry['rows_before']} | {entry['rows_after']} "
            f"| {entry['affected_records']} | {entry['changed_cells']} |"
        )
    lines += ["", "Pełne statystyki opisowe, parametry operacji, wartości imputacji i czas UTC "
              "znajdują się w raporcie JSON. Liczby dotkniętych rekordów z różnych operacji "
              "mogą obejmować ten sam rekord, więc nie należy ich sumować.", "",
              "## Decyzje", "",
              "- Pełne duplikaty są rozpatrywane przed konwersją i imputacją; zachowywana jest pierwsza kopia.",
              "- Imputacja: mediana skończonych liczb i dominanta tekstu. Całkowicie pusta kolumna pozostaje pusta.",
              "- Granice IQR = Q1 − k·IQR, Q3 + k·IQR, kwartyle z interpolacją liniową. "
              "Dla IQR=0 lub braku danych reguła jest nieaktywna.",
              "- Outlier nie oznacza automatycznie błędu. Działanie i kolumnę wybiera użytkownik; "
              "domyślnie obowiązuje raportowanie. Flaga dodaje komórkę do każdego rekordu.",
              "- Kolejność: duplikaty → konwersje → zakresy → braki → wybrane operacje IQR. "
              "Granice danej operacji IQR oblicza się na aktualnych danych.",
              "- Plik źródłowy i kopia surowa sesji pozostają zachowane; `session.reset()` przywraca kopię surową.", ""]
    return "\n".join(lines)


def run(args: argparse.Namespace) -> dict[str, Any]:
    session = DataSession.from_csv(
        args.csv, separator=None if args.sep == "auto" else args.sep,
        encoding=args.encoding, decimal=args.decimal,
    )
    rules = validate_options(args, session)
    before = session.profile()
    # Jakość przed operacjami oceniamy na osobnej kopii. Konwersja tekstowych
    # liczb nie zmienia oryginalnego profilu i nie powoduje utraty duplikatów.
    baseline = DataSession(session.raw)
    for column in args.numeric:
        baseline.convert_numeric(column)
    quality_before = baseline.quality_report(rules, args.iqr_factor)
    print("Podgląd danych surowych:")
    print(session.raw.head(5).to_string(index=False))
    if not args.keep_duplicates:
        session.drop_exact_duplicates()
    for column in args.numeric:
        session.convert_numeric(column)
    for column, rule in rules.items():
        session.apply_range(column, rule, args.range_action)
    session.handle_missing(args.missing, args.missing_column)
    for column in args.outlier:
        session.handle_outliers(column, factor=args.iqr_factor, action=args.outlier_action)
    report = json_safe({
        "schema_version": 1,
        "source": args.csv.name,
        "parameters": {key: str(value) if isinstance(value, Path) else value for key, value in vars(args).items()},
        "before": before,
        "after": session.profile(),
        "quality_before": quality_before,
        "quality_after": session.quality_report(rules, args.iqr_factor),
        "audit_log": [asdict(entry) for entry in session.audit_log],
    })
    report_json = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    summary = markdown_report(report)
    try:
        session.current.to_csv(args.output, sep=args.output_sep, index=False, encoding="utf-8", lineterminator="\n")
        args.report.write_text(report_json, encoding="utf-8")
        args.summary.write_text(summary, encoding="utf-8")
    except OSError as exc:
        raise DataError(f"Nie można zapisać wyników: {exc}. Sprawdź ścieżkę i prawa zapisu.") from exc
    print(f"\nRekordy: {before['rows']} → {report['after']['rows']}; "
          f"brakujące komórki: {before['missing_cells']} → {report['after']['missing_cells']}.")
    print(f"Zapisano: {args.output}, {args.report}, {args.summary}")
    return report


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
