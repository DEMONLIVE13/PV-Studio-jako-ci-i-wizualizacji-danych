"""Małe, ręcznie kontrolowane przypadki z macierzy projektu (unittest)."""

from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path

import pandas as pd
from pandas.testing import assert_frame_equal, assert_series_equal

from data_session import DataError, DataSession, RangeRule, read_csv
from lab6 import json_safe, main


ROOT = Path(__file__).parent


class CsvTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "input.csv"

    def load_text(self, text: str, **options: object) -> pd.DataFrame:
        self.path.write_text(text, encoding="utf-8")
        return read_csv(self.path, **options)

    def test_both_delimiters_and_quoted_fields(self) -> None:
        for sep in (",", ";"):
            with self.subTest(separator=sep):
                frame = self.load_text(f'nazwa{sep}liczba\n"Łódź, centrum; północ"{sep}2\n')
                self.assertEqual(frame.shape, (1, 2))
                self.assertEqual(frame.iloc[0, 0], "Łódź, centrum; północ")

    def test_decimal_comma(self) -> None:
        frame = self.load_text("nazwa;wartosc\na;1,25\nb;2,5\n", decimal=",")
        self.assertEqual(frame["wartosc"].tolist(), [1.25, 2.5])

    def test_single_column_and_multiline_quotes(self) -> None:
        frame = self.load_text('opis\n"pierwsza\ndruga"\ntrzecia\n')
        self.assertEqual(frame.shape, (2, 1))
        self.assertEqual(frame.iloc[0, 0], "pierwsza\ndruga")

    def test_invalid_rows_are_rejected_including_first_row(self) -> None:
        for text in ("a,b\n1,2,3\n", "a,b\n1\n", 'a,b\n"1,2\n'):
            with self.subTest(text=text), self.assertRaises(DataError):
                self.load_text(text, separator=",")

    def test_empty_and_invalid_headers(self) -> None:
        for text in ("", " \n", "a,b\n", "a,a\n1,2\n", "a,\n1,2\n"):
            with self.subTest(text=text), self.assertRaises(DataError):
                self.load_text(text)

    def test_encoding_failure_and_explicit_recovery(self) -> None:
        self.path.write_bytes("miasto;liczba\nŁódź;2\n".encode("cp1250"))
        with self.assertRaises(DataError):
            read_csv(self.path)
        frame = read_csv(self.path, encoding="cp1250")
        self.assertEqual(frame.iloc[0, 0], "Łódź")
        with self.assertRaises(DataError):
            read_csv(self.path, encoding="nieistniejace-kodowanie")

    def test_missing_file_and_nul(self) -> None:
        with self.assertRaises(DataError):
            read_csv(self.path)
        with self.assertRaises(DataError):
            self.load_text("a,b\n1,\x00\n")

    def test_supplied_fixtures_have_expected_sizes(self) -> None:
        for filename, shape in (
            ("dane_przecinek.csv", (12, 10)), ("dane_srednik.csv", (6, 4)),
            ("dane_brzegowe.csv", (5, 4)),
        ):
            with self.subTest(filename=filename):
                self.assertEqual(read_csv(ROOT / filename).shape, shape)


class SessionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.frame = pd.DataFrame({
            "liczba": [1.0, 1.0, 3.0, None, 100.0],
            "tekst": ["A", "A", "B", None, "C"],
            "niezalezna": [5, 5, 6, 7, 8],
        })
        self.session = DataSession(self.frame)

    def test_profile_counts_types_statistics_and_missing_percentage(self) -> None:
        profile = self.session.profile()
        self.assertEqual((profile["rows"], profile["columns"]), (5, 3))
        self.assertEqual(profile["duplicate_records"], 1)
        self.assertEqual(profile["records_in_duplicate_groups"], 2)
        self.assertEqual(profile["missing_cells"], 2)
        self.assertEqual(profile["column_profile"]["liczba"]["missing_pct"], 20.0)
        self.assertEqual(profile["column_profile"]["tekst"]["unique"], 3)
        self.assertEqual(profile["column_profile"]["liczba"]["dtype"], "float64")
        self.assertEqual(profile["statistics"]["liczba"]["max"], 100.0)

    def test_session_copies_input_and_keeps_raw(self) -> None:
        self.frame.loc[0, "liczba"] = 999
        self.assertEqual(self.session.raw.loc[0, "liczba"], 1)
        self.session.handle_missing()
        self.assertTrue(pd.isna(self.session.raw.loc[3, "liczba"]))

    def test_only_full_duplicates_are_removed(self) -> None:
        self.assertEqual(self.session.drop_exact_duplicates(), 1)
        self.assertEqual(self.session.current.index.tolist(), [0, 2, 3, 4])
        frame = pd.DataFrame({"a": [1, 1], "b": ["A", "B"]})
        session = DataSession(frame)
        self.assertEqual(session.drop_exact_duplicates(), 0)
        assert_frame_equal(session.current, frame)

    def test_range_report_does_not_change_data(self) -> None:
        self.assertEqual(self.session.apply_range("liczba", RangeRule(1, 3)), 0)
        assert_frame_equal(self.session.current, self.frame)
        self.assertEqual(self.session.audit_log[-1].parameters["detected"], 1)
        self.assertEqual(self.session.range_mask("liczba", RangeRule(1, 3)).tolist(),
                         [False, False, False, False, True])

    def test_range_missing_and_clip_change_only_selected_column(self) -> None:
        for action, expected in (("missing", None), ("clip", 3.0)):
            with self.subTest(action=action):
                session = DataSession(self.frame)
                self.assertEqual(session.apply_range("liczba", RangeRule(1, 3), action), 1)
                assert_frame_equal(session.current[["tekst", "niezalezna"]],
                                   self.frame[["tekst", "niezalezna"]])
                if expected is None:
                    self.assertTrue(pd.isna(session.current.loc[4, "liczba"]))
                else:
                    self.assertEqual(session.current.loc[4, "liczba"], expected)
                self.assertEqual(session.audit_log[-1].changed_cells, 1)

    def test_range_drop_removes_only_invalid_rows(self) -> None:
        self.assertEqual(self.session.apply_range("liczba", RangeRule(1, 3), "drop"), 1)
        assert_frame_equal(self.session.current, self.frame.iloc[:4])

    def test_missing_imputes_median_and_mode_with_correct_audit(self) -> None:
        self.assertEqual(self.session.handle_missing("impute"), 1)
        self.assertEqual(self.session.current.loc[3, "liczba"], 2.0)
        self.assertEqual(self.session.current.loc[3, "tekst"], "A")
        self.assertEqual(self.session.audit_log[-1].changed_cells, 2)
        assert_series_equal(self.session.current["niezalezna"], self.frame["niezalezna"])

    def test_missing_drop_keep_and_column_selection(self) -> None:
        self.session.handle_missing("keep")
        assert_frame_equal(self.session.current, self.frame)
        self.session.handle_missing("impute", ["liczba"])
        self.assertTrue(pd.isna(self.session.current.loc[3, "tekst"]))
        self.assertEqual(self.session.handle_missing("drop", ["tekst"]), 1)
        self.assertEqual(len(self.session.current), 4)

    def test_all_missing_column_remains_missing_and_is_reported(self) -> None:
        session = DataSession(pd.DataFrame({"pusta": [None, None], "x": [1, 2]}))
        self.assertEqual(session.handle_missing(), 0)
        self.assertTrue(session.current["pusta"].isna().all())
        self.assertEqual(session.audit_log[-1].parameters["unfilled_columns"], ["pusta"])

    def test_nullable_integer_can_receive_fractional_median(self) -> None:
        session = DataSession(pd.DataFrame({"x": pd.Series([1, 2, None], dtype="Int64")}))
        session.handle_missing()
        self.assertEqual(session.current.loc[2, "x"], 1.5)

    def test_explicit_numeric_conversion_does_not_touch_other_columns(self) -> None:
        frame = pd.DataFrame({"x": ["1", "blad", None, "inf"], "y": ["a", "b", "c", "d"]})
        session = DataSession(frame)
        self.assertEqual(session.convert_numeric("x"), 3)
        self.assertEqual(session.current["x"].isna().sum(), 3)
        self.assertEqual(session.audit_log[-1].parameters["invalid_to_missing"], 2)
        assert_series_equal(session.current["y"], frame["y"])
        assert_frame_equal(session.raw, frame)

    def test_iqr_bounds_and_all_actions(self) -> None:
        frame = pd.DataFrame({"x": [1, 2, 3, 4, 100], "y": [9, 8, 7, 6, 5]})
        for action in ("report", "flag", "clip", "drop"):
            with self.subTest(action=action):
                session = DataSession(frame)
                details = session.iqr_details("x")
                self.assertEqual((details["lower"], details["upper"], details["detected"]), (-1, 7, 1))
                session.handle_outliers("x", action=action)
                if action == "report":
                    assert_frame_equal(session.current, frame)
                    self.assertEqual(session.audit_log[-1].affected_records, 0)
                elif action == "flag":
                    assert_frame_equal(session.current[["x", "y"]], frame)
                    self.assertEqual(session.current["x__outlier"].tolist(), [False]*4 + [True])
                    self.assertEqual(session.audit_log[-1].affected_records, 5)
                elif action == "clip":
                    self.assertEqual(session.current["x"].tolist(), [1, 2, 3, 4, 7])
                    assert_series_equal(session.current["y"], frame["y"])
                else:
                    assert_frame_equal(session.current, frame.iloc[:4])

    def test_zero_iqr_and_all_missing_are_inactive(self) -> None:
        for values in ([7, 7, 7], [None, None], [1, 1, 1, 1, 99]):
            with self.subTest(values=values):
                session = DataSession(pd.DataFrame({"x": pd.Series(values, dtype=float)}))
                self.assertFalse(session.iqr_details("x")["applicable"])
                self.assertEqual(session.handle_outliers("x", action="drop"), 0)

    def test_flag_does_not_overwrite_existing_column(self) -> None:
        self.session.handle_outliers("liczba", action="flag")
        before = self.session.current.copy(deep=True)
        with self.assertRaises(DataError):
            self.session.handle_outliers("liczba", action="flag")
        assert_frame_equal(self.session.current, before)

    def test_invalid_parameters_do_not_change_data(self) -> None:
        cases = [
            lambda: RangeRule(2, 1), lambda: RangeRule(0, float("inf")),
            lambda: self.session.apply_range("tekst", RangeRule(0, 10)),
            lambda: self.session.apply_range("brak", RangeRule(0, 10)),
            lambda: self.session.apply_range("liczba", RangeRule(0, 10), "unknown"),
            lambda: self.session.handle_missing("unknown"),
            lambda: self.session.handle_missing(columns=["liczba", "liczba"]),
            lambda: self.session.handle_outliers("tekst"),
            lambda: self.session.handle_outliers("liczba", factor=0),
            lambda: self.session.handle_outliers("liczba", factor=float("nan")),
            lambda: self.session.handle_outliers("liczba", action="unknown"),
        ]
        for operation in cases:
            with self.subTest(operation=operation), self.assertRaises(DataError):
                operation()
            assert_frame_equal(self.session.current, self.frame)

    def test_reset_restores_removed_records_values_and_columns(self) -> None:
        self.session.drop_exact_duplicates()
        self.session.handle_missing()
        self.session.handle_outliers("liczba", action="flag")
        self.session.reset()
        assert_frame_equal(self.session.current, self.frame)
        self.assertEqual(self.session.audit_log[-1].operation, "reset")
        self.assertEqual(len(self.session.audit_log), 4)

    def test_empty_after_dropping_can_be_profiled_and_reset(self) -> None:
        self.session.apply_range("liczba", RangeRule(200, 300), "drop")
        self.session.handle_missing("drop")
        self.assertEqual(self.session.profile()["rows"], 0)
        self.assertEqual(self.session.quality_report({})["outliers_iqr"]["liczba"]["detected"], 0)
        self.session.reset()
        assert_frame_equal(self.session.current, self.frame)

    def test_audit_and_profiles_are_valid_json(self) -> None:
        self.session.handle_missing()
        text = json.dumps(json_safe({"profile": self.session.profile(),
                                    "audit": [asdict(x) for x in self.session.audit_log]}), allow_nan=False)
        self.assertIn("timestamp_utc", json.loads(text)["audit"][0])


class CliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.output = self.root / "cleaned.csv"
        self.report = self.root / "report.json"
        self.summary = self.root / "report.md"

    def execute(self, options: list[str]) -> tuple[int, str]:
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(captured):
            code = main([*options, "--output", str(self.output), "--report", str(self.report),
                         "--summary", str(self.summary)])
        return code, captured.getvalue()

    def test_end_to_end_expected_results_and_roundtrip(self) -> None:
        source = ROOT / "dane_przecinek.csv"
        original = source.read_bytes()
        code, _ = self.execute([str(source), "--range", "housing_median_age", "1", "52",
                                "--range-action", "missing", "--outlier", "median_income",
                                "--outlier-action", "flag"])
        self.assertEqual(code, 0)
        report = json.loads(self.report.read_text(encoding="utf-8"))
        self.assertEqual((report["before"]["rows"], report["after"]["rows"]), (12, 11))
        self.assertEqual(report["before"]["missing_cells"], 2)
        self.assertEqual(report["after"]["missing_cells"], 0)
        self.assertEqual(report["quality_before"]["ranges"]["housing_median_age"]["detected"], 1)
        self.assertEqual(report["quality_after"]["ranges"]["housing_median_age"]["detected"], 0)
        frame = read_csv(self.output)
        self.assertEqual(frame.shape, (11, 11))
        self.assertEqual(frame["median_income__outlier"].sum(), 1)
        self.assertEqual(source.read_bytes(), original)
        self.assertIn("Ślad zmian", self.summary.read_text(encoding="utf-8"))

    def test_pipeline_is_repeatable_except_timestamps(self) -> None:
        options = [str(ROOT / "dane_srednik.csv"), "--range", "wiek", "0", "120",
                   "--range-action", "missing"]
        self.assertEqual(self.execute(options)[0], 0)
        first_csv, first = self.output.read_bytes(), json.loads(self.report.read_text(encoding="utf-8"))
        self.assertEqual(self.execute(options)[0], 0)
        second = json.loads(self.report.read_text(encoding="utf-8"))
        self.assertEqual(first_csv, self.output.read_bytes())
        for report in (first, second):
            for entry in report["audit_log"]:
                entry.pop("timestamp_utc")
        self.assertEqual(first, second)

    def test_bad_numeric_input_fixture(self) -> None:
        code, _ = self.execute([str(ROOT / "dane_brzegowe.csv"), "--numeric", "liczba"])
        self.assertEqual(code, 0)
        frame = read_csv(self.output)
        self.assertEqual(frame["liczba"].tolist(), [10, 15, 15, 20, 15])
        self.assertTrue(frame["pusta"].isna().all())
        report = json.loads(self.report.read_text(encoding="utf-8"))
        self.assertFalse(report["quality_before"]["outliers_iqr"]["stala"]["applicable"])

    def test_invalid_config_produces_no_outputs(self) -> None:
        for flags in (
            ["--range", "housing_median_age", "60", "1"],
            ["--outlier-action", "drop"], ["--outlier", "ocean_proximity"],
            ["--numeric", "nieistniejaca"], ["--range-action", "clip"],
            ["--iqr-factor", "nan"], ["--outlier", "median_income", "--outlier", "median_income"],
        ):
            with self.subTest(flags=flags):
                code, output = self.execute([str(ROOT / "dane_przecinek.csv"), *flags])
                self.assertEqual(code, 2)
                self.assertIn("Błąd:", output)
                self.assertNotIn("Traceback", output)
                self.assertFalse(self.output.exists())

    def test_input_cannot_be_overwritten_and_write_errors_are_controlled(self) -> None:
        source = ROOT / "dane_srednik.csv"
        original = source.read_bytes()
        self.output = source
        self.assertEqual(self.execute([str(source)])[0], 2)
        self.assertEqual(source.read_bytes(), original)
        self.output = self.root / "missing" / "cleaned.csv"
        self.assertEqual(self.execute([str(source)])[0], 2)
        self.output = self.root  # istniejący katalog, nie plik
        code, message = self.execute([str(source)])
        self.assertEqual(code, 2)
        self.assertIn("Nie można zapisać", message)


if __name__ == "__main__":
    unittest.main()
