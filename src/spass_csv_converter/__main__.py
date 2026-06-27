from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .converter import ConversionError, convert_spass_to_csv
from .gui import run_gui


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="spass-csv-converter",
        description="Convert a readable .spass export file to CSV.",
    )
    parser.add_argument("input", nargs="?", help="Path to a .spass file")
    parser.add_argument("output", nargs="?", help="Path for the output CSV")
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Open the desktop app instead of running in command-line mode.",
    )
    args = parser.parse_args(argv)

    if args.gui or not args.input:
        run_gui()
        return 0

    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else input_path.with_suffix(".csv")

    try:
        result = convert_spass_to_csv(input_path, output_path)
    except ConversionError as exc:
        print(f"Conversion failed: {exc}", file=sys.stderr)
        return 2

    print(f"Saved {result.row_count} rows to {result.output_path}")
    if result.warnings:
        print("Warnings:")
        for warning in result.warnings:
            print(f"- {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
