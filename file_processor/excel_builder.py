from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


def write_excel_report(tables: dict[str, pd.DataFrame], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        used_names: set[str] = set()
        for table_name, frame in tables.items():
            sheet_name = unique_sheet_name(table_name, used_names)
            frame.to_excel(writer, sheet_name=sheet_name, index=False)
            format_worksheet(writer.sheets[sheet_name])
    return output_path


def format_worksheet(worksheet) -> None:
    worksheet.freeze_panes = "A2"
    worksheet.auto_filter.ref = worksheet.dimensions
    auto_size_columns(worksheet)


def auto_size_columns(worksheet, min_width: int = 12, max_width: int = 48) -> None:
    for column_cells in worksheet.columns:
        max_len = max(len(str(cell.value)) if cell.value is not None else 0 for cell in column_cells)
        worksheet.column_dimensions[column_cells[0].column_letter].width = min(max(max_len + 2, min_width), max_width)


def unique_sheet_name(name: str, used_names: set[str]) -> str:
    base = re.sub(r"[\[\]:*?/\\]", "_", name).strip() or "Sheet"
    base = base[:31]
    candidate = base
    counter = 2
    while candidate in used_names:
        suffix = f"_{counter}"
        candidate = f"{base[:31 - len(suffix)]}{suffix}"
        counter += 1
    used_names.add(candidate)
    return candidate
