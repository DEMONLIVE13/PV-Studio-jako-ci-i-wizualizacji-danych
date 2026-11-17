"""Wykresy Matplotlib/Seaborn niezależne od CLI i przyszłego GUI."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from textwrap import fill

import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import rc_context
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from pandas.api.types import (
    is_bool_dtype, is_complex_dtype, is_numeric_dtype, is_object_dtype,
    is_string_dtype,
)

from data_session import DataError


PlotKind = Literal["histogram", "scatter", "box", "bar", "correlation"]
KINDS = ("histogram", "scatter", "box", "bar", "correlation")
STYLE = {"font.size": 11, "axes.titlesize": 12, "axes.labelsize": 11,
         "axes.spines.top": False, "axes.spines.right": False}
TITLES = {"histogram": "Histogram", "scatter": "Wykres punktowy",
          "box": "Wykres pudełkowy", "bar": "Liczebność kategorii",
          "correlation": "Korelacja Pearsona"}


@dataclass(frozen=True)
class CorrelationResult:
    coefficient: float
    pairs: int
    excluded: int


def _column(frame: pd.DataFrame, name: str | None) -> pd.Series:
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        raise DataError("Brak danych do wykresu. Wczytaj niepusty zbiór.")
    if not frame.columns.is_unique:
        raise DataError("Nazwy kolumn muszą być unikalne.")
    if not isinstance(name, str) or not name.strip():
        raise DataError("Wybierz kolumnę do wykresu.")
    if name not in frame.columns:
        raise DataError(f"Brak kolumny: {name}. Wybierz kolumnę z aktualnego zbioru.")
    return frame[name]


def _numeric(frame: pd.DataFrame, name: str | None) -> pd.Series:
    values = _column(frame, name)
    if (not is_numeric_dtype(values.dtype) or is_bool_dtype(values.dtype)
            or is_complex_dtype(values.dtype)):
        raise DataError(f"Kolumna {name} musi zawierać liczby rzeczywiste. Wybierz kolumnę liczbową.")
    finite = values.replace([np.inf, -np.inf], np.nan).dropna().astype(float)
    if finite.empty:
        raise DataError(f"Kolumna {name} nie zawiera skończonych danych liczbowych.")
    if finite.nunique() < 2:
        raise DataError(f"Kolumna {name} jest stała. Wybierz kolumnę o różnych wartościach.")
    return finite


def _categorical(frame: pd.DataFrame, name: str | None) -> pd.Series:
    values = _column(frame, name)
    categorical = isinstance(values.dtype, pd.CategoricalDtype)
    textual = (is_string_dtype(values.dtype) or is_object_dtype(values.dtype)) and all(
        isinstance(value, str) for value in values.dropna()
    )
    if not (categorical or textual or is_bool_dtype(values.dtype)):
        raise DataError(f"Kolumna {name} musi być tekstowa, logiczna lub kategorialna.")
    values = values.dropna().astype(str)
    if values.empty:
        raise DataError(f"Kolumna {name} nie zawiera kategorii do wykresu.")
    if values.nunique() > 20:
        raise DataError("Wykres słupkowy obsługuje do 20 kategorii. Wybierz mniej szczegółową kolumnę.")
    return values


def _prepare(frame: pd.DataFrame, kind: str, x: str, y: str | None) -> pd.DataFrame:
    if kind not in KINDS:
        raise DataError(f"Nieznany rodzaj wykresu: {kind}. Wybierz: {', '.join(KINDS)}.")
    if kind == "bar":
        return _categorical(frame, x).to_frame(name=x)
    numeric = _numeric(frame, x)
    if kind in ("histogram", "box"):
        return numeric.to_frame(name=x)
    _numeric(frame, y)
    if x == y:
        raise DataError("Wybierz dwie różne kolumny do analizy zależności.")
    # Usuwamy całe pary, a nie braki osobno na każdej osi.
    pairs = frame[[x, y]].replace([np.inf, -np.inf], np.nan).dropna().astype(float)
    if len(pairs) < 3:
        raise DataError("Potrzeba co najmniej 3 kompletnych, skończonych par danych.")
    for name in (x, y):
        if pairs[name].nunique() < 2:
            raise DataError(f"Kolumna {name} jest stała w kompletnych parach danych.")
    return pairs


def pearson_correlation(frame: pd.DataFrame, x: str, y: str) -> CorrelationResult:
    """Pearson na kompletnych parach; NaN i ±inf nie trafiają do obliczenia."""
    pairs = _prepare(frame, "correlation", x, y)
    coefficient = float(pairs[x].corr(pairs[y], method="pearson"))
    if not np.isfinite(coefficient):
        raise DataError("Nie można wyznaczyć skończonej korelacji dla wybranych danych.")
    return CorrelationResult(coefficient, len(pairs), len(frame) - len(pairs))


def _bins(values: np.ndarray, bins: int | str) -> np.ndarray:
    if not ((isinstance(bins, int) and not isinstance(bins, bool) and 1 <= bins <= 200)
            or (isinstance(bins, str) and bins == "auto")):
        raise DataError("Liczba przedziałów histogramu musi być od 1 do 200 albo 'auto'.")
    edges = np.histogram_bin_edges(values, bins=bins)
    if len(edges) > 201:
        raise DataError("Automatyczny histogram ma ponad 200 przedziałów. Podaj mniejszą liczbę.")
    return edges


def _draw(
    ax: Axes, data: pd.DataFrame, kind: str, x: str, y: str | None,
    *, color: str, edges: np.ndarray | None, order: list[str] | None,
) -> None:
    label = lambda name: str(name).replace("_", " ")
    if kind == "histogram":
        ax.hist(data[x], bins=edges, color=color, edgecolor="white")
        ax.set(xlabel=label(x), ylabel="Liczba rekordów")
    elif kind == "scatter":
        sns.scatterplot(data=data, x=x, y=y, ax=ax, color=color, s=65, alpha=.8)
        ax.set(xlabel=label(x), ylabel=label(y))
    elif kind == "box":
        sns.boxplot(y=data[x], ax=ax, color=color, width=.45, whis=1.5)
        ax.set(xlabel="Zbiór", ylabel=label(x))
        ax.set_xticks([0], ["Wszystkie rekordy"])
    elif kind == "bar":
        counts = data[x].value_counts().reindex(order, fill_value=0)
        bars = ax.bar(range(len(counts)), counts.to_numpy(), color=color)
        ax.set_xticks(range(len(counts)), [fill(str(value), 18) for value in counts.index])
        ax.bar_label(bars, padding=3, fontsize=10)
        ax.margins(y=.15)
        ax.set(xlabel=label(x), ylabel="Liczba rekordów")
    else:
        matrix = data[[x, y]].corr(method="pearson")
        matrix.index = matrix.columns = [label(x), label(y)]
        sns.heatmap(matrix, annot=True, fmt=".3f", vmin=-1, vmax=1, center=0,
                    cmap="vlag", square=True, cbar=False, ax=ax)
        ax.set(xlabel="Zmienna", ylabel="Zmienna")
    if kind != "correlation":
        ax.grid(axis="y", alpha=.18)
        ax.set_axisbelow(True)


def build_figure(
    frame: pd.DataFrame, kind: PlotKind, x: str, y: str | None = None,
    *, title: str | None = None, bins: int | str = 10,
) -> Figure:
    """Zbuduj Figure na podstawie parametrów, bez okna i zmieniania danych."""
    data = _prepare(frame, kind, x, y)
    edges = _bins(data[x].to_numpy(), bins) if kind == "histogram" else None
    order = sorted(data[x].unique()) if kind == "bar" else None
    with rc_context(STYLE):
        fig = Figure(figsize=(8, 5), dpi=120, layout="constrained")
        ax = fig.add_subplot()
        _draw(ax, data, kind, x, y, color="#2563eb", edges=edges, order=order)
        ax.set_title(title or TITLES[kind], pad=12)
        fig.supxlabel(f"Wykorzystano {len(data)}/{len(frame)} rekordów; pominięto {len(frame)-len(data)}.",
                      fontsize=9)
    return fig


def comparison_figure(
    before: pd.DataFrame, after: pd.DataFrame, kind: PlotKind,
    x: str, y: str | None = None, *, title: str | None = None,
    bins: int | str = 10,
) -> Figure:
    """Przed/po na wspólnej skali, z tymi samymi przedziałami i kategoriami."""
    first, second = _prepare(before, kind, x, y), _prepare(after, kind, x, y)
    edges = _bins(np.concatenate([first[x].to_numpy(), second[x].to_numpy()]), bins) \
        if kind == "histogram" else None
    order = sorted(set(first[x]) | set(second[x])) if kind == "bar" else None
    if order is not None and len(order) > 20:
        raise DataError("Porównanie zawiera ponad 20 kategorii. Wybierz inną kolumnę.")
    with rc_context(STYLE):
        fig = Figure(figsize=(14, 5.5), dpi=120, layout="constrained")
        axes = fig.subplots(1, 2, sharex=True, sharey=True)
        for ax, data, source, stage, color in zip(
            axes, (first, second), (before, after),
            ("Przed czyszczeniem", "Po czyszczeniu"), ("#2563eb", "#0f766e"),
        ):
            _draw(ax, data, kind, x, y, color=color, edges=edges, order=order)
            ax.set_title(f"{stage} | n={len(data)}/{len(source)}", pad=12)
        axes[1].tick_params(labelleft=True)
        fig.suptitle(title or f"{TITLES[kind]}: {x}" + (f" / {y}" if y else ""), fontsize=15)
        note = "n = wykorzystane rekordy / wszystkie rekordy; braki i ±inf pominięto tylko w wykresie."
        if kind == "correlation":
            note += " Korelacja nie dowodzi przyczynowości."
        fig.supxlabel(note, fontsize=9)
    return fig


def save_figure(figure: Figure, path: str | Path) -> Path:
    """Eksport bez pyplot, gotowy również do użycia przez GUI."""
    path = Path(path)
    if path.suffix.lower() not in (".png", ".svg", ".pdf"):
        raise DataError("Wybierz format wykresu PNG, SVG lub PDF.")
    if not path.parent.is_dir():
        raise DataError(f"Katalog {path.parent} nie istnieje. Wybierz istniejącą lokalizację.")
    try:
        figure.savefig(path, format=path.suffix[1:].lower(), dpi=120, facecolor="white")
    except (OSError, ValueError) as exc:
        raise DataError(f"Nie można zapisać wykresu: {exc}. Sprawdź ścieżkę i prawa zapisu.") from exc
    return path
