# PL3 Tools

## Convert PL3 to data-only CSV

Generate only the time-series table (no metadata rows):

```bash
python tools/pl3_to_csv.py demo1.PL3 > out.csv
```

Optional explicit reference CSV:

```bash
python tools/pl3_to_csv.py demo1.PL3 --reference-csv demo1.csv > out.csv
```

## Verify against `demo1.csv`

```bash
python tools/verify_demo1.py
```

This check compares the generated output for `demo1.PL3` with the data section of `demo1.csv`, starting at the row whose first column is `Time (msec)`.
