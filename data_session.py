"""Profilowanie i czyszczenie danych niezależne od CLI i przyszłego GUI."""

from __future__ import annotations

import csv
import io
import math
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, Mapping, Sequence

import pandas as pd
from pandas.api.types import is_bool_dtype, is_numeric_dtype


class DataError(ValueError):
    """Błąd danych lub parametrów możliwy do pokazania użytkownikowi."""


@dataclass(frozen=True)
class RangeRule:
    minimum: float
    maximum: float

    def __post_init__(self) -> None:
        if not all(math.isfinite(x) for x in (self.minimum, self.maximum)):
            raise DataError("Granice zakresu muszą być skończonymi liczbami.")
        if self.minimum > self.maximum:
            raise DataError("Dolna granica zakresu nie może przekraczać górnej.")


@dataclass(frozen=True)
class AuditEntry:
    operation: str
    timestamp_utc: str
    parameters: dict[str, Any]
    rows_before: int
    rows_after: int
    affected_records: int
    changed_cells: int


def read_csv(
    path: str | Path,
    *,
    separator: str | None = None,
    encoding: str = "utf-8-sig",
    decimal: str = ".",
) -> pd.DataFrame:
    """Wczytaj CSV bez pomijania wadliwych wierszy i zgadywania kodowania."""
    if separator not in (None, ",", ";"):
        raise DataError("Separator musi być przecinkiem albo średnikiem.")
    if decimal not in (".", ","):
        raise DataError("Separator dziesiętny musi być kropką albo przecinkiem.")
    try:
        text = Path(path).read_text(encoding=encoding)
    except UnicodeError as exc:
        raise DataError(
            "Nie można odczytać kodowania. Wskaż je przez --encoding, np. cp1250."
        ) from exc
    except LookupError as exc:
        raise DataError(f"Nieznane kodowanie: {encoding}.") from exc
    except OSError as exc:
        raise DataError(f"Nie można odczytać pliku {path}: {exc.strerror}.") from exc
    if not text.strip():
        raise DataError("Plik CSV jest pusty.")
    if "\x00" in text:
        raise DataError("Plik zawiera znaki NUL. Sprawdź format i kodowanie CSV.")
    try:
        if separator is None:
            try:
                separator = csv.Sniffer().sniff(text[:65536], delimiters=",;").delimiter
            except csv.Error:
                first_line = text.lstrip().splitlines()[0]
                widths = {
                    sep: len(next(csv.reader([first_line], delimiter=sep)))
                    for sep in (",", ";")
                }
                separator = max(widths, key=widths.get)
        # Pandas potrafi uznać nadmiarową pierwszą komórkę za indeks.
        # Osobna walidacja wykrywa też zbyt krótkie wiersze i powtórzone nagłówki.
        reader = csv.reader(io.StringIO(text), delimiter=separator, strict=True)
        header: list[str] | None = None
        records = 0
        for row in reader:
            if not row or (len(row) == 1 and not row[0].strip()):
                continue
            if header is None:
                header = row
                if any(not name.strip() for name in header):
                    raise DataError("Każda kolumna CSV musi mieć niepustą nazwę.")
                if len(set(header)) != len(header):
                    raise DataError("Nazwy kolumn CSV muszą być unikalne.")
            elif len(row) != len(header):
                raise DataError(
                    f"Wadliwy wiersz kończący się w linii {reader.line_num}: "
                    f"oczekiwano {len(header)} pól, otrzymano {len(row)}. "
                    "Sprawdź separator i cudzysłowy."
                )
            else:
                records += 1
        if not records:
            raise DataError("Plik CSV nie zawiera rekordów danych.")
        frame = pd.read_csv(
            io.StringIO(text), sep=separator, decimal=decimal, on_bad_lines="error"
        )
    except (csv.Error, pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
        raise DataError(f"Niepoprawny CSV. Sprawdź separator i cudzysłowy: {exc}") from exc
    return frame


@dataclass
class DataSession:
    raw: pd.DataFrame
    current: pd.DataFrame = field(init=False)
    audit_log: list[AuditEntry] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        if self.raw.empty:
            raise DataError("Zbiór nie zawiera rekordów ani kolumn.")
        if not self.raw.columns.is_unique:
            raise DataError("Nazwy kolumn muszą być unikalne.")
        self.raw = self.raw.copy(deep=True).reset_index(drop=True)
        self.current = self.raw.copy(deep=True)

    @classmethod
    def from_csv(cls, path: str | Path, **options: Any) -> DataSession:
        return cls(read_csv(path, **options))

    def _column(self, column: str, *, numeric: bool = False) -> pd.Series:
        if column not in self.current.columns:
            raise DataError(f"Brak kolumny: {column}.")
        values = self.current[column]
        if numeric and (not is_numeric_dtype(values) or is_bool_dtype(values)):
            raise DataError(
                f"Kolumna {column} musi być liczbowa. "
                "Dla tekstowych liczb użyj najpierw --numeric."
            )
        return values

    def _log(
        self, operation: str, parameters: dict[str, Any], before: int,
        affected: int, changed_cells: int = 0,
    ) -> int:
        self.audit_log.append(AuditEntry(
            operation=operation,
            timestamp_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            parameters=parameters,
            rows_before=before,
            rows_after=len(self.current),
            affected_records=int(affected),
            changed_cells=int(changed_cells),
        ))
        return int(affected)

    def profile(self) -> dict[str, Any]:
        frame = self.current
        return {
            "rows": len(frame),
            "columns": len(frame.columns),
            # Liczba nadmiarowych kopii; pierwszy rekord z grupy pozostaje.
            "duplicate_records": int(frame.duplicated().sum()),
            "records_in_duplicate_groups": int(frame.duplicated(keep=False).sum()),
            "missing_cells": int(frame.isna().sum().sum()),
            "column_profile": {
                str(name): {
                    "dtype": str(frame[name].dtype),
                    "missing": int(frame[name].isna().sum()),
                    "missing_pct": round(float(frame[name].isna().mean() * 100), 2)
                    if len(frame) else 0.0,
                    "unique": int(frame[name].nunique(dropna=True)),
                }
                for name in frame.columns
            },
            "statistics": frame.describe(include="all").to_dict(),
        }

    def convert_numeric(self, column: str) -> int:
        """Jawna konwersja jednej kolumny; błędny tekst/inf staje się brakiem."""
        values = self._column(column)
        converted = pd.to_numeric(values, errors="coerce").replace(
            [float("inf"), float("-inf")], float("nan")
        )
        invalid = values.notna() & converted.isna()
        changed = values.notna() & (
            invalid | values.map(lambda value: isinstance(value, str))
        )
        self.current[column] = converted
        return self._log(
            "convert_numeric", {"column": column, "invalid_to_missing": int(invalid.sum())},
            len(self.current), int(changed.sum()), int(changed.sum()),
        )

    def drop_exact_duplicates(self) -> int:
        before = len(self.current)
        self.current = self.current.drop_duplicates().copy()
        return self._log("drop_exact_duplicates", {}, before, before - len(self.current))

    def range_mask(self, column: str, rule: RangeRule) -> pd.Series:
        values = self._column(column, numeric=True)
        return values.notna() & ~values.between(rule.minimum, rule.maximum)

    def apply_range(
        self, column: str, rule: RangeRule,
        action: Literal["report", "missing", "clip", "drop"] = "report",
    ) -> int:
        if action not in ("report", "missing", "clip", "drop"):
            raise DataError("Nieznana operacja dla wartości spoza zakresu.")
        mask = self.range_mask(column, rule)
        before, detected = len(self.current), int(mask.sum())
        if action == "missing":
            self.current.loc[mask, column] = float("nan")
        elif action == "clip":
            self.current[column] = self.current[column].clip(rule.minimum, rule.maximum)
        elif action == "drop":
            self.current = self.current.loc[~mask].copy()
        return self._log(
            "range", {"column": column, **asdict(rule), "action": action, "detected": detected},
            before, detected if action != "report" else 0,
            detected if action in ("missing", "clip") else 0,
        )

    def handle_missing(
        self, strategy: Literal["keep", "drop", "impute"] = "impute",
        columns: Sequence[str] | None = None,
    ) -> int:
        if strategy not in ("keep", "drop", "impute"):
            raise DataError("Strategia braków to keep, drop albo impute.")
        names = list(self.current.columns if columns is None else columns)
        if len(set(names)) != len(names):
            raise DataError("Lista kolumn zawiera powtórzenia.")
        for name in names:
            self._column(name)
        before = len(self.current)
        missing = self.current[names].isna()
        affected = int(missing.any(axis=1).sum())
        changed_cells = 0
        parameters: dict[str, Any] = {"strategy": strategy, "columns": names}
        if strategy == "drop":
            self.current = self.current.dropna(subset=names).copy()
        elif strategy == "impute":
            fill_values: dict[str, Any] = {}
            unfilled: list[str] = []
            # Wszystkie wartości wyznaczamy przed zmianą danych.
            for name in names:
                values = self.current[name]
                if not values.isna().any():
                    continue
                if is_numeric_dtype(values) and not is_bool_dtype(values):
                    finite = values.replace([float("inf"), float("-inf")], float("nan")).dropna()
                    if finite.empty:
                        unfilled.append(name)
                        continue
                    fill_values[name] = float(finite.median())
                else:
                    modes = values.mode(dropna=True)
                    if modes.empty:
                        unfilled.append(name)
                        continue
                    fill_values[name] = modes.iloc[0]
            for name, value in fill_values.items():
                values = self.current[name]
                # Mediana 1.5 musi dać się zapisać również dla nullable Int64.
                if is_numeric_dtype(values) and not is_bool_dtype(values):
                    values = values.astype(float)
                self.current[name] = values.fillna(value)
                changed_cells += int(missing[name].sum())
            parameters.update(fill_values=fill_values, unfilled_columns=unfilled)
            affected = int(missing[list(fill_values)].any(axis=1).sum())
        elif strategy == "keep":
            affected = 0
        return self._log("missing", parameters, before, affected, changed_cells)

    def iqr_details(self, column: str, factor: float = 1.5) -> dict[str, Any]:
        values = self._column(column, numeric=True)
        if not math.isfinite(factor) or factor <= 0:
            raise DataError("Współczynnik IQR musi być dodatnią, skończoną liczbą.")
        finite = values.replace([float("inf"), float("-inf")], float("nan")).dropna()
        q1, q3 = finite.quantile([0.25, 0.75])
        iqr = q3 - q1
        applicable = bool(pd.notna(iqr) and iqr > 0)
        lower = float(q1 - factor * iqr) if applicable else None
        upper = float(q3 + factor * iqr) if applicable else None
        mask = values.notna() & ((values < lower) | (values > upper)) if applicable else pd.Series(
            False, index=self.current.index
        )
        return {
            "factor": factor, "q1": q1, "q3": q3, "iqr": iqr,
            "lower": lower, "upper": upper, "applicable": applicable,
            "detected": int(mask.sum()), "mask": mask,
        }

    def quality_report(
        self, ranges: Mapping[str, RangeRule], factor: float = 1.5,
    ) -> dict[str, Any]:
        numeric = [
            name for name in self.current.columns
            if is_numeric_dtype(self.current[name]) and not is_bool_dtype(self.current[name])
        ]
        return {
            "ranges": {
                name: {**asdict(rule), "detected": int(self.range_mask(name, rule).sum())}
                for name, rule in ranges.items()
            },
            "outliers_iqr": {
                name: {key: value for key, value in self.iqr_details(name, factor).items() if key != "mask"}
                for name in numeric
            },
            "non_finite": {
                name: int(self.current[name].isin([float("inf"), float("-inf")]).sum())
                for name in numeric
            },
        }

    def handle_outliers(
        self, column: str, *, factor: float = 1.5,
        action: Literal["report", "flag", "clip", "drop"] = "report",
    ) -> int:
        if action not in ("report", "flag", "clip", "drop"):
            raise DataError("Nieznana operacja dla wartości odstających.")
        details = self.iqr_details(column, factor)
        mask = details.pop("mask")
        before, detected = len(self.current), details["detected"]
        affected = detected if action != "report" else 0
        changed_cells = 0
        if action == "flag":
            flag = f"{column}__outlier"
            if flag in self.current.columns:
                raise DataError(f"Kolumna flagi {flag} już istnieje. Zresetuj dane lub zmień nazwę.")
            self.current[flag] = mask
            # Nowa kolumna opisuje wszystkie rekordy; detected liczy same outliery.
            affected = changed_cells = len(self.current)
        elif action == "clip" and details["applicable"]:
            self.current[column] = self.current[column].clip(details["lower"], details["upper"])
            changed_cells = detected
        elif action == "drop":
            self.current = self.current.loc[~mask].copy()
        return self._log(
            "outliers_iqr", {"column": column, "action": action, **details},
            before, affected, changed_cells,
        )

    def reset(self) -> None:
        before = len(self.current)
        self.current = self.raw.copy(deep=True)
        self._log("reset", {"scope": "all_raw_records"}, before, len(self.raw))
