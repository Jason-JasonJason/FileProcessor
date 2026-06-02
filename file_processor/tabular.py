from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Any

import pandas as pd

from .processor import ProcessingResult


TABULAR_OUTPUT_FORMATS = ("json", "xlsx", "csv")


def write_tabular_outputs(results: list[ProcessingResult], output_dir: Path, output_format: str) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    tables = build_tabular_frames(results)

    if output_format == "xlsx":
        return [write_xlsx(tables, output_dir / "processed_output.xlsx")]
    if output_format == "csv":
        return write_csv_files(tables, output_dir)
    if output_format == "json":
        return []
    raise ValueError(f"Unsupported output format: {output_format}")


def build_tabular_frames(results: list[ProcessingResult]) -> dict[str, pd.DataFrame]:
    rows_by_table: dict[str, list[pd.DataFrame]] = defaultdict(list)
    rows_by_table["RunSummary"].append(build_run_summary(results))

    for result in results:
        if result.status != "ok" or not result.content:
            continue

        context = build_source_context(result)
        content = result.content
        kind = content.get("kind")

        if kind == "workbook":
            for sheet_name, rows in content.get("sheets", {}).items():
                frame = rows_to_frame(rows)
                if frame.empty:
                    continue
                add_context_columns(frame, context)
                rows_by_table[sheet_name].append(frame)
        elif kind == "table":
            frame = pd.DataFrame(content.get("rows", []))
            if frame.empty:
                continue
            add_context_columns(frame, context)
            rows_by_table["Rows"].append(frame)
        elif kind == "json":
            frame = json_to_frame(content.get("data"))
            if frame.empty:
                continue
            add_context_columns(frame, context)
            rows_by_table["JsonData"].append(frame)

    return {
        table_name: pd.concat(frames, ignore_index=True, sort=False)
        for table_name, frames in rows_by_table.items()
        if frames
    }


def build_run_summary(results: list[ProcessingResult]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "source_path": result.source_path,
                "file_name": result.file_name,
                "extension": result.extension,
                "status": result.status,
                "error": result.error,
                "size_bytes": result.metadata.get("size_bytes"),
                "modified_epoch": result.metadata.get("modified_epoch"),
            }
            for result in results
        ]
    )


def build_source_context(result: ProcessingResult) -> dict[str, Any]:
    context: dict[str, Any] = {
        "SourceFile": result.file_name,
        "SourcePath": result.source_path,
    }
    content = result.content or {}
    client_info_rows = content.get("sheets", {}).get("ClientInfo", [])
    if client_info_rows:
        client_fields = rows_to_mapping(client_info_rows)
        for key in ("ClientID", "ClientName", "Adviser", "RiskProfile", "BaseCurrency"):
            if key in client_fields:
                context[key] = client_fields[key]
    return context


def rows_to_mapping(rows: list[list[Any]]) -> dict[str, Any]:
    mapping = {}
    for row in rows[1:]:
        if len(row) >= 2 and row[0]:
            mapping[str(row[0])] = row[1]
    return mapping


def rows_to_frame(rows: list[list[Any]]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    header = [normalize_header(value, index) for index, value in enumerate(rows[0])]
    return pd.DataFrame(rows[1:], columns=header).dropna(how="all")


def normalize_header(value: Any, index: int) -> str:
    if value is None or str(value).strip() == "":
        return f"Column{index + 1}"
    return str(value).strip()


def add_context_columns(frame: pd.DataFrame, context: dict[str, Any]) -> None:
    for column, value in reversed(context.items()):
        if column not in frame.columns:
            frame.insert(0, column, value)


def json_to_frame(data: Any) -> pd.DataFrame:
    if isinstance(data, list):
        return pd.json_normalize(data)
    if isinstance(data, dict):
        return pd.json_normalize(data)
    return pd.DataFrame({"value": [data]})


def write_xlsx(tables: dict[str, pd.DataFrame], output_path: Path) -> Path:
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        used_names: set[str] = set()
        for table_name, frame in tables.items():
            safe_name = unique_sheet_name(table_name, used_names)
            frame.to_excel(writer, sheet_name=safe_name, index=False)
            worksheet = writer.sheets[safe_name]
            worksheet.freeze_panes = "A2"
            for column_cells in worksheet.columns:
                max_len = max(len(str(cell.value)) if cell.value is not None else 0 for cell in column_cells)
                worksheet.column_dimensions[column_cells[0].column_letter].width = min(max(max_len + 2, 12), 48)
    return output_path


def write_csv_files(tables: dict[str, pd.DataFrame], output_dir: Path) -> list[Path]:
    paths = []
    used_names: set[str] = set()
    for table_name, frame in tables.items():
        file_name = unique_file_stem(table_name, used_names)
        output_path = output_dir / f"{file_name}.csv"
        frame.to_csv(output_path, index=False)
        paths.append(output_path)
    return paths


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


def unique_file_stem(name: str, used_names: set[str]) -> str:
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._-") or "table"
    candidate = base
    counter = 2
    while candidate in used_names:
        candidate = f"{base}_{counter}"
        counter += 1
    used_names.add(candidate)
    return candidate
