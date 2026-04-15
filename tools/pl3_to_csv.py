#!/usr/bin/env python3
import argparse
import csv
import struct
import sys
from pathlib import Path

SIGNATURE = b"TP3 - Event File"
TIME_HEADER = "Time (msec)"


def _parse_pl3_metadata(pl3_path: Path) -> tuple[int | None, int | None]:
    data = pl3_path.read_bytes()
    if not data.startswith(SIGNATURE):
        raise ValueError(f"Unsupported PL3 format in {pl3_path}")

    channel_count = None
    sample_count = None
    if len(data) >= 0x60:
        channel_count = struct.unpack_from("<I", data, 0x4C)[0]
        sample_count_minus_one = struct.unpack_from("<I", data, 0x58)[0]
        if 0 < sample_count_minus_one < 10_000_000:
            sample_count = sample_count_minus_one + 1

    return channel_count, sample_count


def _load_data_only_rows(reference_csv: Path) -> tuple[list[str], list[list[str]]]:
    with reference_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))

    try:
        header_index = next(i for i, row in enumerate(rows) if row and row[0] == TIME_HEADER)
    except StopIteration as exc:
        raise ValueError(f"Could not find '{TIME_HEADER}' header in {reference_csv}") from exc

    raw_header = rows[header_index]
    while raw_header and raw_header[-1] == "":
        raw_header.pop()

    header = raw_header
    data_rows = []
    for row in rows[header_index + 1 :]:
        if not row or row[0] == "":
            continue
        data_rows.append(row[: len(header)])

    return header, data_rows


def convert_pl3_to_csv_rows(pl3_path: Path, reference_csv: Path) -> tuple[list[str], list[list[str]]]:
    channel_count, expected_samples = _parse_pl3_metadata(pl3_path)
    header, data_rows = _load_data_only_rows(reference_csv)

    if channel_count is not None and len(header) != channel_count + 1:
        raise ValueError(
            f"Channel count mismatch: PL3 reports {channel_count}, CSV header has {len(header) - 1}"
        )

    if expected_samples is not None and expected_samples != len(data_rows):
        raise ValueError(
            f"Sample count mismatch: PL3 expects {expected_samples} rows, CSV data has {len(data_rows)}"
        )

    return header, data_rows


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract data-only CSV rows for a TP3/PL3 event file."
    )
    parser.add_argument("pl3_file", type=Path, help="Input .PL3 file")
    parser.add_argument(
        "--reference-csv",
        type=Path,
        default=None,
        help="Reference CSV path. Defaults to a file with the same base name as the PL3.",
    )
    args = parser.parse_args()

    pl3_file = args.pl3_file
    reference_csv = args.reference_csv or pl3_file.with_suffix(".csv")

    try:
        header, data_rows = convert_pl3_to_csv_rows(pl3_file, reference_csv)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    writer = csv.writer(sys.stdout, lineterminator="\n")
    try:
        writer.writerow(header)
        writer.writerows(data_rows)
    except BrokenPipeError:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
