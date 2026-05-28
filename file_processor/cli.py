from __future__ import annotations

import argparse
import json
from pathlib import Path

from .extractors import supported_extensions
from .processor import process_folder


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="file-process",
        description="Extract normalized JSON content from common document formats.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    process = subparsers.add_parser("process", help="Process files from an input folder.")
    process.add_argument("input_dir", type=Path, help="Folder containing files to process.")
    process.add_argument("output_dir", type=Path, help="Folder where JSON results are written.")
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
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "formats":
        for extension in supported_extensions():
            print(extension)
        return 0

    results = process_folder(args.input_dir, args.output_dir, recursive=args.recursive)

    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(
            json.dumps([result.to_dict() for result in results], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    ok_count = sum(result.status == "ok" for result in results)
    error_count = len(results) - ok_count
    print(f"Processed {len(results)} file(s): {ok_count} ok, {error_count} error(s).")
    return 1 if error_count else 0
