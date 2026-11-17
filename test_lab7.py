"""Testy wykresów, walidacji i eksportu na ręcznie kontrolowanych danych."""

from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.figure import Figure
from pandas.testing import assert_frame_equal
from PIL import Image

from data_session import DataError
from lab7 import main
from visualizations import build_figure, comparison_figure, pearson_correlation, save_figure


ROOT = Path(__file__).parent


class FigureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.frame = pd.DataFrame({
            "x": [1., 2., 3., 4., 100., np.nan],
            "y": [2., 4., 6., 8., 200., 12.],
            "grupa": ["A", "B", "A", "B", "A", None],
        })
        self.figures: list[Figure] = []
        self.addCleanup(lambda: [fig.clear() for fig in self.figures])

    def build(self, kind: str, x: str = "x", y: str | None = None, **kwargs) -> Figure:
        fig = build_figure(self.frame, kind, x, y, **kwargs)
        self.figures.append(fig)
        return fig

    def test_all_types_return_labeled_figures_without_mutation_or_global_windows(self) -> None:
        original = self.frame.copy(deep=True)
        font_before = matplotlib.rcParams["font.size"]
        windows_before = plt.get_fignums()
        for kind, x, y in (("histogram", "x", None), ("scatter", "x", "y"),
                           ("box", "x", None), ("bar", "grupa", None),
                           ("correlation", "x", "y")):
            with self.subTest(kind=kind):
                fig = self.build(kind, x, y, title="Własny tytuł")
                self.assertIsInstance(fig, Figure)
                ax = fig.axes[0]
                self.assertEqual(ax.get_title(), "Własny tytuł")
                self.assertTrue(ax.get_xlabel())
                self.assertTrue(ax.get_ylabel())
        assert_frame_equal(self.frame, original)
        self.assertEqual(plt.get_fignums(), windows_before)
        self.assertEqual(matplotlib.rcParams["font.size"], font_before)

    def test_histogram_counts_all_finite_observations(self) -> None:
        self.frame.loc[5, "x"] = np.inf
        fig = self.build("histogram", bins=4)
        self.assertEqual(sum(bar.get_height() for bar in fig.axes[0].patches), 5)
        self.assertEqual(len(fig.axes[0].patches), 4)

    def test_scatter_pairs_remain_aligned_and_missing_and_inf_are_excluded(self) -> None:
        self.frame.loc[1, "y"] = np.inf
        fig = self.build("scatter", "x", "y")
        offsets = fig.axes[0].collections[0].get_offsets()
        np.testing.assert_allclose(offsets, [[1, 2], [3, 6], [4, 8], [100, 200]])
        result = pearson_correlation(self.frame, "x", "y")
        self.assertAlmostEqual(result.coefficient, 1)
        self.assertEqual((result.pairs, result.excluded), (4, 2))

    def test_boxplot_keeps_visible_outlier(self) -> None:
        fig = self.build("box")
        visible = [float(value) for line in fig.axes[0].lines for value in line.get_ydata()]
        self.assertIn(100., visible)
        self.assertIn(3., visible)  # Mediana [1, 2, 3, 4, 100].

    def test_bar_counts_categories_instead_of_averaging(self) -> None:
        fig = self.build("bar", "grupa")
        self.assertEqual([bar.get_height() for bar in fig.axes[0].patches], [3, 2])
        self.assertEqual([tick.get_text() for tick in fig.axes[0].get_xticklabels()], ["A", "B"])

    def test_pearson_has_expected_negative_value_and_sample_size(self) -> None:
        frame = pd.DataFrame({"a": [1, 2, 3, None], "b": [8, 6, 4, 999]})
        result = pearson_correlation(frame, "a", "b")
        self.assertAlmostEqual(result.coefficient, -1)
        self.assertEqual((result.pairs, result.excluded), (3, 1))

    def test_comparison_shares_histogram_edges_and_scales(self) -> None:
        after = self.frame.iloc[:4].copy()
        fig = comparison_figure(self.frame, after, "histogram", "x", bins=5)
        self.figures.append(fig)
        first, second = fig.axes
        self.assertEqual(first.get_xlim(), second.get_xlim())
        self.assertEqual(first.get_ylim(), second.get_ylim())
        self.assertEqual([(p.get_x(), p.get_width()) for p in first.patches],
                         [(p.get_x(), p.get_width()) for p in second.patches])
        self.assertEqual(sum(p.get_height() for p in first.patches), 5)
        self.assertEqual(sum(p.get_height() for p in second.patches), 4)
        self.assertIn("n=5/6", first.get_title())

    def test_comparison_bars_include_categories_missing_in_either_phase(self) -> None:
        after = pd.DataFrame({"grupa": ["B", "C", "C"]})
        fig = comparison_figure(self.frame, after, "bar", "grupa")
        self.figures.append(fig)
        self.assertEqual([p.get_height() for p in fig.axes[0].patches], [3, 2, 0])
        self.assertEqual([p.get_height() for p in fig.axes[1].patches], [0, 1, 2])

    def test_invalid_columns_types_empty_constant_and_choices_are_blocked(self) -> None:
        cases = [
            (self.frame, "histogram", "grupa", None),
            (self.frame, "histogram", "brak", None),
            (self.frame, "histogram", "", None),
            (self.frame, "scatter", "x", None),
            (self.frame, "scatter", "x", "x"),
            (self.frame, "bar", "x", None),
            (self.frame, "nieznany", "x", None),
            (pd.DataFrame(), "histogram", "x", None),
            (pd.DataFrame({"x": [7, 7, 7]}), "histogram", "x", None),
            (pd.DataFrame({"x": [7, 7, 7]}), "box", "x", None),
            (pd.DataFrame({"x": [np.inf, None, -np.inf]}), "histogram", "x", None),
            (pd.DataFrame({"x": [True, False, True]}), "histogram", "x", None),
            (pd.DataFrame({"x": [1+2j, 2+1j, 3+1j]}), "histogram", "x", None),
            (pd.DataFrame({"x": ["1", "2", "3"]}), "histogram", "x", None),
            (pd.DataFrame({"x": [None, None]}), "bar", "x", None),
            (pd.DataFrame([[1, 2]], columns=["x", "x"]), "histogram", "x", None),
        ]
        for frame, kind, x, y in cases:
            with self.subTest(kind=kind, x=x), self.assertRaises(DataError):
                build_figure(frame, kind, x, y)

    def test_incomplete_or_constant_pairs_are_blocked(self) -> None:
        for frame in (
            pd.DataFrame({"x": [1, 2, None], "y": [2, 3, 4]}),
            pd.DataFrame({"x": [1, 2, 3, None], "y": [5, 5, 5, 8]}),
        ):
            for kind in ("scatter", "correlation"):
                with self.subTest(kind=kind), self.assertRaises(DataError):
                    build_figure(frame, kind, "x", "y")

    def test_invalid_bins_and_excessive_categories_are_blocked(self) -> None:
        for bins in (0, -1, 201, True, 2.5, "invalid"):
            with self.subTest(bins=bins), self.assertRaises(DataError):
                self.build("histogram", bins=bins)
        with self.assertRaises(DataError):
            build_figure(pd.DataFrame({"x": [str(i) for i in range(21)]}), "bar", "x")

    def test_boolean_and_declared_categories_are_supported(self) -> None:
        for values in ([True, False, True], pd.Categorical([1, 2, 1])):
            fig = build_figure(pd.DataFrame({"x": values}), "bar", "x")
            self.figures.append(fig)
            self.assertEqual(sum(p.get_height() for p in fig.axes[0].patches), 3)

    def test_png_and_svg_can_be_reopened_and_invalid_output_is_controlled(self) -> None:
        fig = self.build("histogram")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            save_figure(fig, root / "chart.png")
            with Image.open(root / "chart.png") as picture:
                picture.verify()
            tree = ET.parse(save_figure(fig, root / "chart.svg"))
            self.assertEqual(tree.getroot().tag, "{http://www.w3.org/2000/svg}svg")
            for path in (root / "chart.txt", root / "missing" / "chart.png", root):
                with self.subTest(path=path), self.assertRaises(DataError):
                    save_figure(fig, path)


class CliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def execute(self, extra: list[str] | None = None) -> tuple[int, str]:
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
            code = main([str(ROOT / "dane_przecinek.csv"), str(ROOT / "cleaned.csv"),
                         "--output-dir", str(self.root), *(extra or [])])
        return code, stream.getvalue()

    def test_default_demo_exports_all_types_and_report(self) -> None:
        originals = [(ROOT / name).read_bytes() for name in ("dane_przecinek.csv", "cleaned.csv")]
        code, message = self.execute()
        self.assertEqual(code, 0, message)
        self.assertEqual(len(list(self.root.glob("*.png"))), 5)
        self.assertEqual(len(list(self.root.glob("*.svg"))), 5)
        for png in self.root.glob("*.png"):
            with Image.open(png) as picture:
                picture.verify()
        for svg in self.root.glob("*.svg"):
            ET.parse(svg)
        text = (self.root / "raport_lab7.md").read_text(encoding="utf-8")
        self.assertIn("Korelacja nie dowodzi przyczynowości", text)
        self.assertIn("Liczba par | 12 | 11", text)
        self.assertEqual(originals, [(ROOT / name).read_bytes() for name in ("dane_przecinek.csv", "cleaned.csv")])

    def test_validation_does_not_write_partial_results_or_overwrite_old_outputs(self) -> None:
        sentinel = self.root / "histogram_przed_po.png"
        sentinel.write_bytes(b"previous result")
        for options in (["--x", "ocean_proximity"], ["--category", "median_income"],
                        ["--hist", "brak"], ["--bins", "0"], ["--formats", "png", "png"]):
            with self.subTest(options=options):
                code, message = self.execute(options)
                self.assertEqual(code, 2)
                self.assertIn("Błąd:", message)
                self.assertNotIn("Traceback", message)
                self.assertEqual(sentinel.read_bytes(), b"previous result")
                self.assertEqual(len(list(self.root.iterdir())), 1)

    def test_other_csv_delimiters_and_column_names_work(self) -> None:
        source = self.root / "other.csv"
        source.write_text("wiek;wynik;segment\n1;3;A\n2;6;B\n3;9;A\n", encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            code = main([str(source), str(source), "--output-dir", str(self.root),
                         "--hist", "wiek", "--x", "wiek", "--y", "wynik",
                         "--box", "wynik", "--category", "segment", "--formats", "png"])
        self.assertEqual(code, 0)
        self.assertTrue((self.root / "barplot_przed_po.png").exists())

    def test_input_path_cannot_be_overwritten(self) -> None:
        source = self.root / "raport_lab7.md"
        content = (ROOT / "dane_przecinek.csv").read_bytes()
        source.write_bytes(content)
        with contextlib.redirect_stderr(io.StringIO()):
            code = main([str(source), str(ROOT / "cleaned.csv"), "--output-dir", str(self.root)])
        self.assertEqual(code, 2)
        self.assertEqual(source.read_bytes(), content)


if __name__ == "__main__":
    unittest.main()
