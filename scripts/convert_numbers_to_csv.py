from __future__ import annotations

import csv
import os
import sys

from numbers_parser import Document


def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: convert_numbers_to_csv.py <input.numbers> <output.csv>")
        return 1

    src = sys.argv[1]
    dst = sys.argv[2]

    if not os.path.exists(src):
        print(f"Input file not found: {src}")
        return 1

    doc = Document(src)
    sheet = doc.sheets[0]
    table = sheet.tables[0]
    rows = table.rows(values_only=True)

    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for row in rows:
            writer.writerow(row)

    print(f"Sheet: {sheet.name}")
    print(f"Table: {table.name}")
    print(f"Rows exported: {len(rows)}")
    print(f"Wrote: {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
