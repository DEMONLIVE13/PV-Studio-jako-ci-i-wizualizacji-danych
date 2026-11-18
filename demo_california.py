"""Demonstracja lab 6–7 na referencyjnym CSV, bez GUI."""
from pathlib import Path
import pandas as pd
from data_session import read_csv
from lab6 import main as clean
from lab7 import main as charts


def main():
    source = Path("california_housing_projekt2.csv")
    target = Path("wyniki_california")
    target.mkdir(exist_ok=True)
    raw = read_csv(source)
    options = [str(source), "--output", str(target / "cleaned.csv"),
               "--report", str(target / "raport_lab6.json"),
               "--summary", str(target / "raport_lab6.md"),
               "--range-action", "missing", "--missing", "impute",
               "--outlier", "MedInc", "--outlier-action", "flag"]
    for column in raw.columns:
        options += ["--numeric", column]
    for column, lower, upper in [("HouseAge", 1, 52), ("Latitude", -90, 90),
                                 ("Longitude", -180, 180)]:
        options += ["--range", column, str(lower), str(upper)]
    # Dla wielkości nieujemnych górna granica to obserwowane maksimum:
    # wykrywamy wartości ujemne, zachowując dodatnie obserwacje odstające.
    for column in ["MedInc", "AveRooms", "AveBedrms", "Population", "AveOccup", "MedHouseVal"]:
        values = pd.to_numeric(raw[column], errors="coerce")
        options += ["--range", column, "0", str(values.max())]
    if clean(options):
        return 2
    before = raw.copy()
    for column in before.columns:
        before[column] = pd.to_numeric(before[column], errors="coerce")
    after = read_csv(target / "cleaned.csv")
    for frame in (before, after):
        frame["grupa_wieku"] = pd.cut(frame["HouseAge"],
            bins=[float("-inf"), 20, 40, float("inf")],
            labels=["do 20 lat", "21–40 lat", "powyżej 40 lat"])
    before.to_csv(target / "przed_wykresami.csv", index=False)
    after.to_csv(target / "po_wykresach.csv", index=False)
    return charts([str(target / "przed_wykresami.csv"), str(target / "po_wykresach.csv"),
        "--hist", "HouseAge", "--x", "MedInc", "--y", "MedHouseVal", "--box", "MedInc",
        "--category", "grupa_wieku", "--output-dir", str(target)])


if __name__ == "__main__":
    raise SystemExit(main())
