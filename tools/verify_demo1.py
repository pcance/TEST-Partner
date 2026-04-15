#!/usr/bin/env python3
import csv
import io
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PL3_FILE = ROOT / "demo1.PL3"
CSV_FILE = ROOT / "demo1.csv"
SCRIPT_FILE = ROOT / "tools" / "pl3_to_csv.py"


def load_expected_data_only() -> list[list[str]]:
    with CSV_FILE.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))

    header_index = next(i for i, row in enumerate(rows) if row and row[0] == "Time (msec)")
    header = [c for c in rows[header_index] if c]
    data_rows = [row[: len(header)] for row in rows[header_index + 1 :] if row and row[0]]
    return [header] + data_rows


def main() -> int:
    result = subprocess.run(
        [sys.executable, str(SCRIPT_FILE), str(PL3_FILE)],
        check=True,
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )

    actual_rows = list(csv.reader(io.StringIO(result.stdout)))
    expected_rows = load_expected_data_only()

    if actual_rows != expected_rows:
        print("Verification failed: generated CSV does not match demo1.csv data section.")
        print(f"Expected rows: {len(expected_rows)} | Actual rows: {len(actual_rows)}")
        return 1

    print("Verification passed: generated CSV matches demo1.csv data section.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
