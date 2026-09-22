from __future__ import annotations

import argparse
import sys

import pandas as pd

from src.faire_formatter import format_faire_export


def main() -> int:
    parser = argparse.ArgumentParser(description="Format raw Faire export for the dashboard")
    parser.add_argument("input_csv")
    parser.add_argument("output_csv")
    parser.add_argument(
        "--aggregate-orders",
        action="store_true",
        help="Collapse to one row per order (default keeps line items with product names)",
    )
    args = parser.parse_args()

    raw = pd.read_csv(args.input_csv)
    out = format_faire_export(raw, aggregate_orders=args.aggregate_orders)

    out.to_csv(args.output_csv, index=False)
    print(f"Wrote formatted CSV: {args.output_csv}")
    print(f"Rows: {len(out)}")
    print(f"Columns: {', '.join(out.columns)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
