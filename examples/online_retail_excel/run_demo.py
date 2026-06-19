from __future__ import annotations

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from file_processor.pipelines.online_retail import OnlineRetailReportConfig, build_online_retail_report


DEMO_DIR = Path(__file__).resolve().parent
INPUT_FILE = DEMO_DIR / "input" / "Online Retail.xlsx"
OUTPUT_FILE = DEMO_DIR / "output" / "online_retail_business_report.xlsx"


def main() -> int:
    if not INPUT_FILE.exists():
        print(f"Input workbook not found: {INPUT_FILE}")
        print("Download the UCI Online Retail dataset and place Online Retail.xlsx in the input folder.")
        return 1

    output_path = build_online_retail_report(
        OnlineRetailReportConfig(input_path=INPUT_FILE, output_path=OUTPUT_FILE)
    )
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
