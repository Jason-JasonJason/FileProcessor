from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from file_processor.cleaning import (
    clean_datetime_columns,
    clean_integer_identifier_column,
    clean_numeric_columns,
    clean_text_columns,
    limit_rows,
    validate_required_columns,
)
from file_processor.excel_builder import write_excel_report


REQUIRED_COLUMNS = {
    "InvoiceNo",
    "StockCode",
    "Description",
    "Quantity",
    "InvoiceDate",
    "UnitPrice",
    "CustomerID",
    "Country",
}


@dataclass(frozen=True)
class OnlineRetailReportConfig:
    input_path: Path
    output_path: Path
    cleaned_transaction_limit: int | None = 50_000


def build_online_retail_report(config: OnlineRetailReportConfig) -> Path:
    raw = read_online_retail_workbook(config.input_path)
    clean = clean_transactions(raw)
    active_sales = clean.loc[clean["IsValidSale"]].copy()

    tables = build_report_tables(clean, active_sales, config.cleaned_transaction_limit)
    return write_excel_report(tables, config.output_path)


def read_online_retail_workbook(input_path: Path) -> pd.DataFrame:
    frame = pd.read_excel(input_path)
    validate_required_columns(frame, REQUIRED_COLUMNS)
    return frame


def clean_transactions(raw: pd.DataFrame) -> pd.DataFrame:
    frame = raw.copy()
    frame = clean_text_columns(frame, ["InvoiceNo", "StockCode", "Description"])
    frame = clean_text_columns(frame, ["Country"], fill_value="Unknown")
    frame = clean_datetime_columns(frame, ["InvoiceDate"])
    frame = clean_numeric_columns(frame, ["Quantity", "UnitPrice"])
    frame = clean_integer_identifier_column(frame, "CustomerID")

    frame["Revenue"] = frame["Quantity"] * frame["UnitPrice"]
    frame["InvoiceMonth"] = frame["InvoiceDate"].dt.to_period("M").astype(str)
    frame["IsCancellation"] = frame["InvoiceNo"].str.upper().str.startswith("C") | (frame["Quantity"] < 0)
    frame["IsValidSale"] = (
        ~frame["IsCancellation"]
        & frame["InvoiceDate"].notna()
        & frame["Quantity"].gt(0)
        & frame["UnitPrice"].gt(0)
        & frame["Description"].ne("")
    )
    return frame


def build_report_tables(
    clean: pd.DataFrame,
    active_sales: pd.DataFrame,
    cleaned_transaction_limit: int | None,
) -> dict[str, pd.DataFrame]:
    return {
        "Executive Summary": build_executive_summary(clean, active_sales),
        "Monthly Revenue": build_monthly_revenue(active_sales),
        "Top Products": build_top_products(active_sales),
        "Top Customers": build_top_customers(active_sales),
        "Country Sales": build_country_sales(active_sales),
        "Cancelled Orders": build_cancelled_orders(clean),
        "Data Quality Issues": build_data_quality_issues(clean),
        "Cleaned Transactions": limit_rows(clean, cleaned_transaction_limit),
    }


def build_executive_summary(clean: pd.DataFrame, active_sales: pd.DataFrame) -> pd.DataFrame:
    metrics = [
        ("Raw rows processed", len(clean)),
        ("Valid sales rows", len(active_sales)),
        ("Cancelled / return rows", int(clean["IsCancellation"].sum())),
        ("Unique invoices", active_sales["InvoiceNo"].nunique()),
        ("Unique customers", active_sales["CustomerID"].nunique()),
        ("Unique products", active_sales["StockCode"].nunique()),
        ("Countries", active_sales["Country"].nunique()),
        ("Total revenue", round(float(active_sales["Revenue"].sum()), 2)),
        ("Average order value", round(float(active_sales.groupby("InvoiceNo")["Revenue"].sum().mean()), 2)),
        ("Date range start", active_sales["InvoiceDate"].min()),
        ("Date range end", active_sales["InvoiceDate"].max()),
    ]
    return pd.DataFrame(metrics, columns=["Metric", "Value"])


def build_monthly_revenue(active_sales: pd.DataFrame) -> pd.DataFrame:
    return (
        active_sales.groupby("InvoiceMonth", dropna=False)
        .agg(
            Revenue=("Revenue", "sum"),
            Orders=("InvoiceNo", "nunique"),
            Customers=("CustomerID", "nunique"),
            UnitsSold=("Quantity", "sum"),
        )
        .reset_index()
        .sort_values("InvoiceMonth")
    )


def build_top_products(active_sales: pd.DataFrame, limit: int = 25) -> pd.DataFrame:
    return (
        active_sales.groupby(["StockCode", "Description"], dropna=False)
        .agg(
            Revenue=("Revenue", "sum"),
            UnitsSold=("Quantity", "sum"),
            Orders=("InvoiceNo", "nunique"),
        )
        .reset_index()
        .sort_values("Revenue", ascending=False)
        .head(limit)
    )


def build_top_customers(active_sales: pd.DataFrame, limit: int = 25) -> pd.DataFrame:
    return (
        active_sales.dropna(subset=["CustomerID"])
        .groupby("CustomerID", dropna=False)
        .agg(
            Revenue=("Revenue", "sum"),
            Orders=("InvoiceNo", "nunique"),
            UnitsBought=("Quantity", "sum"),
            FirstOrder=("InvoiceDate", "min"),
            LastOrder=("InvoiceDate", "max"),
        )
        .reset_index()
        .sort_values("Revenue", ascending=False)
        .head(limit)
    )


def build_country_sales(active_sales: pd.DataFrame) -> pd.DataFrame:
    return (
        active_sales.groupby("Country", dropna=False)
        .agg(
            Revenue=("Revenue", "sum"),
            Orders=("InvoiceNo", "nunique"),
            Customers=("CustomerID", "nunique"),
            UnitsSold=("Quantity", "sum"),
        )
        .reset_index()
        .sort_values("Revenue", ascending=False)
    )


def build_cancelled_orders(clean: pd.DataFrame) -> pd.DataFrame:
    columns = ["InvoiceNo", "StockCode", "Description", "Quantity", "InvoiceDate", "UnitPrice", "CustomerID", "Country"]
    return clean.loc[clean["IsCancellation"], columns].sort_values("InvoiceDate")


def build_data_quality_issues(clean: pd.DataFrame) -> pd.DataFrame:
    checks = [
        ("Missing customer id", clean["CustomerID"].isna()),
        ("Missing invoice date", clean["InvoiceDate"].isna()),
        ("Missing description", clean["Description"].eq("")),
        ("Non-positive quantity", clean["Quantity"].le(0)),
        ("Non-positive unit price", clean["UnitPrice"].le(0)),
    ]
    rows = [
        {
            "Issue": issue,
            "RowsAffected": int(mask.sum()),
            "PercentOfRawRows": round(float(mask.mean() * 100), 2),
        }
        for issue, mask in checks
    ]
    return pd.DataFrame(rows)
