from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import pandas as pd


def validate_required_columns(frame: pd.DataFrame, required_columns: Iterable[str]) -> None:
    missing_columns = set(required_columns) - set(frame.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Input data is missing required columns: {missing}")


def clean_text_columns(frame: pd.DataFrame, columns: Iterable[str], fill_value: str = "") -> pd.DataFrame:
    out = frame.copy()
    for column in columns:
        out[column] = out[column].fillna(fill_value).astype(str).str.strip()
    return out


def clean_numeric_columns(frame: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    out = frame.copy()
    for column in columns:
        out[column] = pd.to_numeric(out[column], errors="coerce")
    return out


def clean_datetime_columns(frame: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    out = frame.copy()
    for column in columns:
        out[column] = pd.to_datetime(out[column], errors="coerce")
    return out


def clean_integer_identifier_column(frame: pd.DataFrame, column: str) -> pd.DataFrame:
    out = frame.copy()
    out[column] = pd.to_numeric(out[column], errors="coerce").astype("Int64")
    return out


def add_calculated_column(frame: pd.DataFrame, column: str, values: Any) -> pd.DataFrame:
    out = frame.copy()
    out[column] = values
    return out


def limit_rows(frame: pd.DataFrame, limit: int | None) -> pd.DataFrame:
    if limit is None:
        return frame
    return frame.head(limit)
