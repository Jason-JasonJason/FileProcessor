from __future__ import annotations

import argparse
import json
from pathlib import Path

from .extractors import supported_extensions
from .pipelines.online_retail import OnlineRetailReportConfig, build_online_retail_report
from .processor import process_folder
from .tabular import TABULAR_OUTPUT_FORMATS, write_tabular_outputs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="file-process",
        description="Extract normalized content from common document formats.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    process = subparsers.add_parser("process", help="Process files from an input folder.")
    process.add_argument("input_dir", type=Path, help="Folder containing files to process.")
    process.add_argument("output_dir", type=Path, help="Folder where processed results are written.")
    process.add_argument(
        "--format",
        choices=TABULAR_OUTPUT_FORMATS,
        default="json",
        help="Output format to write. JSON writes one file per source; XLSX and CSV write combined tabular outputs.",
    )
    process.add_argument(
        "--recursive",
        action="store_true",
        help="Process files inside nested folders.",
    )
    process.add_argument(
        "--manifest",
        type=Path,
        help="Optional path for a combined JSON manifest of all results.",
    )

    subparsers.add_parser("formats", help="Print supported file extensions.")

    retail = subparsers.add_parser(
        "online-retail-report",
        help="Build the demo ecommerce business report from an Online Retail Excel workbook.",
    )
    retail.add_argument("input_file", type=Path, help="Path to Online Retail.xlsx.")
    retail.add_argument("output_file", type=Path, help="Path where the report workbook should be written.")
    retail.add_argument(
        "--cleaned-transaction-limit",
        type=int,
        default=50_000,
        help="Maximum rows to write to the Cleaned Transactions sheet. Use -1 for no limit.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "formats":
        for extension in supported_extensions():
            print(extension)
        return 0

    if args.command == "online-retail-report":
        limit = None if args.cleaned_transaction_limit < 0 else args.cleaned_transaction_limit
        output_path = build_online_retail_report(
            OnlineRetailReportConfig(
                input_path=args.input_file,
                output_path=args.output_file,
                cleaned_transaction_limit=limit,
            )
        )
        print(f"Wrote {output_path}")
        return 0

    results = process_folder(
        args.input_dir,
        args.output_dir,
        recursive=args.recursive,
        write_json=args.format == "json",
    )
    output_paths = write_tabular_outputs(results, args.output_dir, args.format)

    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(
            json.dumps([result.to_dict() for result in results], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    ok_count = sum(result.status == "ok" for result in results)
    error_count = len(results) - ok_count
    print(f"Processed {len(results)} file(s): {ok_count} ok, {error_count} error(s).")
    for output_path in output_paths:
        print(f"Wrote {output_path}")
    return 1 if error_count else 0
