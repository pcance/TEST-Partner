#!/usr/bin/env python3
import argparse
import csv
import struct
import sys
from pathlib import Path

SIGNATURE = b"TP3 - Event File"
TIME_HEADER = "Time (msec)"
PL3_CHANNEL_COUNT_OFFSET = 0x4C
PL3_SAMPLE_COUNT_MINUS_ONE_OFFSET = 0x58
MAX_REASONABLE_SAMPLES = 10_000_000


def _parse_pl3_metadata(pl3_path: Path) -> tuple[int | None, int | None]:
    data = pl3_path.read_bytes()
    if not data.startswith(SIGNATURE):
        raise ValueError(f"Unsupported PL3 format in {pl3_path}")

    channel_count = None
    sample_count = None
    if len(data) >= 0x60:
        # These offsets are part of the PL3 binary header for this TP3 event format.
        channel_count = struct.unpack_from("<I", data, PL3_CHANNEL_COUNT_OFFSET)[0]
        sample_count_minus_one = struct.unpack_from(
            "<I", data, PL3_SAMPLE_COUNT_MINUS_ONE_OFFSET
        )[0]
        if 0 < sample_count_minus_one < MAX_REASONABLE_SAMPLES:
            sample_count = sample_count_minus_one + 1

    return channel_count, sample_count


def _load_data_only_rows(reference_csv: Path) -> tuple[list[str], list[list[str]]]:
    with reference_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))

    try:
        header_index = next(i for i, row in enumerate(rows) if row and row[0] == TIME_HEADER)
    except StopIteration as exc:
        raise ValueError(f'Could not find header "{TIME_HEADER}" in {reference_csv}') from exc

    raw_header = rows[header_index]
    last_non_empty_index = next(
        (i for i in range(len(raw_header) - 1, -1, -1) if raw_header[i]),
        -1,
    )
    header = raw_header[: last_non_empty_index + 1]
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
            f"Channel count mismatch: PL3 reports {channel_count} channels, CSV header has {len(header)} columns ({len(header) - 1} channels plus time)"
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
    except (OSError, ValueError, csv.Error, struct.error) as exc:
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
