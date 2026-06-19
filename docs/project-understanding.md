# Project Understanding Guide

This guide explains the current ETL project in plain language. The project now
has two connected parts:

- a reusable file processing library
- a business pipeline that turns a raw retail Excel workbook into a finished
  Excel report

## 1. Big Picture

The project goal is to automate messy business file processing.

The generic processor can read common file formats and produce structured
outputs. The Online Retail pipeline shows a more realistic client-style job:
take one messy Excel workbook, clean it, calculate useful business metrics, and
produce a polished multi-sheet Excel report.

```text
raw files -> extract -> clean -> transform -> report
```

For clients, this means fewer manual spreadsheet tasks. For recruiters, this
shows ETL thinking: ingestion, validation, cleaning, transformation, export, and
testing.

## 2. Current Project Map

```mermaid
mindmap
  root((ETL Project))
    Core File Processor Library
      cli.py
        process
        formats
        online-retail-report
      processor.py
        Finds source files
        Processes each file
        Writes JSON when requested
      extractors.py
        TXT MD LOG
        JSON
        CSV TSV
        XML HTML
        XLSX XLSM
        DOCX PPTX PDF
      tabular.py
        Converts extracted content to tables
        Writes combined XLSX or CSV outputs
      cleaning.py
        Validates required columns
        Cleans text columns
        Converts numeric columns
        Converts date columns
        Limits output rows
      excel_builder.py
        Writes multi-sheet Excel reports
        Freezes header rows
        Adds filters
        Auto-sizes columns
    Business Pipelines
      pipelines online_retail.py
        Reads Online Retail workbook
        Cleans transaction rows
        Builds summary statistics
        Builds report tables
        Calls Excel builder
      demos online_retail.py
        Compatibility wrapper
      examples online_retail_excel
        run_demo.py
        input workbook
        output report workbook
    Tests And Docs
      tests
        test_processor.py
        test_online_retail_demo.py
      docs
        project-understanding.md
        project-flow.md
```

## 3. Main CLI Commands

List supported file types:

```bash
python -m file_processor formats
```

Process a folder of supported files:

```bash
python -m file_processor process ./input ./output
```

Build the Online Retail business report:

```bash
python -m file_processor online-retail-report \
  "examples/online_retail_excel/input/Online Retail.xlsx" \
  "examples/online_retail_excel/output/online_retail_business_report.xlsx"
```

## 4. General File Processor Flow

```mermaid
flowchart TD
    A["User runs<br/>python -m file_processor process ./input ./output"] --> B["cli.main()"]
    B --> C["Parse command arguments"]
    C --> D["processor.process_folder()"]
    D --> E["Find supported files"]
    E --> F["processor.process_file()"]
    F --> G["extractors.extract()"]
    G --> H{"File type"}

    H -->|Text| I["Read plain text"]
    H -->|JSON| J["Load JSON"]
    H -->|CSV/TSV| K["Read rows"]
    H -->|Excel| L["Read sheets"]
    H -->|Word| M["Read paragraphs/tables"]
    H -->|PowerPoint| N["Read slide text"]
    H -->|PDF| O["Read page text"]
    H -->|XML/HTML| P["Read structured text"]

    I --> Q["ProcessingResult"]
    J --> Q
    K --> Q
    L --> Q
    M --> Q
    N --> Q
    O --> Q
    P --> Q

    Q --> R{"Requested output"}
    R -->|JSON| S["Write one JSON per source file"]
    R -->|XLSX| T["tabular.write_tabular_outputs()"]
    R -->|CSV| T
    T --> U["Combined tabular output"]
    S --> V["Print run summary"]
    U --> V
```

## 5. Online Retail Pipeline Flow

The Online Retail pipeline is now part of the main package:

```text
file_processor/pipelines/online_retail.py
```

It uses reusable helpers from:

```text
file_processor/cleaning.py
file_processor/excel_builder.py
```

```mermaid
flowchart TD
    A["python -m file_processor online-retail-report input.xlsx output.xlsx"] --> B["cli.py"]
    B --> C["OnlineRetailReportConfig"]
    C --> D["build_online_retail_report()"]

    D --> E["read_online_retail_workbook()"]
    E --> F["pd.read_excel()"]
    F --> G["cleaning.validate_required_columns()"]

    G --> H["clean_transactions()"]
    H --> I["cleaning.clean_text_columns()"]
    H --> J["cleaning.clean_datetime_columns()"]
    H --> K["cleaning.clean_numeric_columns()"]
    H --> L["cleaning.clean_integer_identifier_column()"]

    I --> M["Create Revenue"]
    J --> M
    K --> M
    L --> M
    M --> N["Create InvoiceMonth"]
    N --> O["Flag IsCancellation"]
    O --> P["Flag IsValidSale"]

    P --> Q["Build report tables"]
    Q --> R["Executive Summary"]
    Q --> S["Monthly Revenue"]
    Q --> T["Top Products"]
    Q --> U["Top Customers"]
    Q --> V["Country Sales"]
    Q --> W["Cancelled Orders"]
    Q --> X["Data Quality Issues"]
    Q --> Y["Cleaned Transactions"]

    R --> Z["excel_builder.write_excel_report()"]
    S --> Z
    T --> Z
    U --> Z
    V --> Z
    W --> Z
    X --> Z
    Y --> Z

    Z --> AA["online_retail_business_report.xlsx"]
```

## 6. Function Call Map

```mermaid
flowchart LR
    A["cli.py<br/>online-retail-report"] --> B["OnlineRetailReportConfig"]
    A --> C["build_online_retail_report()"]

    C --> D["read_online_retail_workbook()"]
    D --> E["validate_required_columns()"]

    C --> F["clean_transactions()"]
    F --> G["clean_text_columns()"]
    F --> H["clean_datetime_columns()"]
    F --> I["clean_numeric_columns()"]
    F --> J["clean_integer_identifier_column()"]

    C --> K["build_report_tables()"]
    K --> L["build_executive_summary()"]
    K --> M["build_monthly_revenue()"]
    K --> N["build_top_products()"]
    K --> O["build_top_customers()"]
    K --> P["build_country_sales()"]
    K --> Q["build_cancelled_orders()"]
    K --> R["build_data_quality_issues()"]
    K --> S["limit_rows()"]

    C --> T["write_excel_report()"]
    T --> U["format_worksheet()"]
    U --> V["auto_size_columns()"]
```

## 7. Before And After Data Cleaning

### Raw Input Example

| InvoiceNo | StockCode | Description | Quantity | InvoiceDate | UnitPrice | CustomerID | Country |
|---|---|---|---:|---|---:|---:|---|
| `" 536365 "` | `" 85123A "` | `" WHITE HANGING HEART "` | 6 | `"2010-12-01 08:26"` | 2.55 | 17850 | `" United Kingdom "` |
| `"C536383"` | `"35004C"` | `"SET OF 3 COLOURED DUCKS"` | -1 | `"2010-12-01 09:49"` | 4.65 | 15311 | `"United Kingdom"` |
| `"536500"` | `"POST"` | null | 1 | `"bad date"` | 0 | null | null |

### After `clean_transactions()`

| InvoiceNo | StockCode | Description | Quantity | InvoiceDate | UnitPrice | CustomerID | Country | Revenue | InvoiceMonth | IsCancellation | IsValidSale |
|---|---|---|---:|---|---:|---:|---|---:|---|---|---|
| `"536365"` | `"85123A"` | `"WHITE HANGING HEART"` | 6 | 2010-12-01 08:26 | 2.55 | 17850 | `"United Kingdom"` | 15.30 | `"2010-12"` | false | true |
| `"C536383"` | `"35004C"` | `"SET OF 3 COLOURED DUCKS"` | -1 | 2010-12-01 09:49 | 4.65 | 15311 | `"United Kingdom"` | -4.65 | `"2010-12"` | true | false |
| `"536500"` | `"POST"` | `""` | 1 | missing date | 0 | missing | `"Unknown"` | 0.00 | missing month | false | false |

## 8. Why The Cleaning Helpers Matter

| Helper | What it does | Why it matters |
|---|---|---|
| `validate_required_columns()` | Checks that required input fields exist | Fails early when the client sends the wrong file shape |
| `clean_text_columns()` | Fills missing text and strips spaces | Prevents duplicate categories caused by extra spaces |
| `clean_numeric_columns()` | Converts numbers safely | Allows revenue and quantity calculations |
| `clean_datetime_columns()` | Converts dates safely | Enables monthly reporting and date ranges |
| `clean_integer_identifier_column()` | Keeps IDs as integers while allowing missing IDs | Good for customer IDs and account IDs |
| `limit_rows()` | Caps large output sheets | Keeps reports usable and file sizes reasonable |

## 9. Report Sheets

The Online Retail report writes these sheets:

| Sheet | Meaning |
|---|---|
| `Executive Summary` | High-level metrics such as raw rows, valid sales, customers, products, revenue, and date range |
| `Monthly Revenue` | Revenue, orders, customers, and units sold by month |
| `Top Products` | Highest-revenue products |
| `Top Customers` | Highest-revenue customers |
| `Country Sales` | Revenue and order metrics by country |
| `Cancelled Orders` | Rows identified as cancellations or returns |
| `Data Quality Issues` | Counts and percentages for missing or invalid data |
| `Cleaned Transactions` | Cleaned transaction rows, capped by the configured row limit |

## 10. Business Translation

### Short Pitch

This project turns messy business files into clean, structured, client-ready
outputs. It can process general files, and it also includes a realistic Excel
reporting pipeline for ecommerce transaction data.

### Client Version

This automation reads a raw sales workbook, cleans the data, separates returns
from valid sales, calculates revenue, builds business summary tables, and
delivers a formatted Excel report that is ready to review.

### Recruiter Version

This is an ETL-style Python project. It includes file ingestion, format-specific
extractors, reusable data cleaning utilities, a business-specific transformation
pipeline, Excel report generation, CLI commands, and tests.

## 11. Library Versus Pipeline

```mermaid
flowchart TD
    A["Reusable file_processor library"] --> B["extractors.py<br/>Read files"]
    A --> C["processor.py<br/>Process folders"]
    A --> D["tabular.py<br/>Generic CSV/XLSX output"]
    A --> E["cleaning.py<br/>Reusable cleaning helpers"]
    A --> F["excel_builder.py<br/>Reusable Excel report writer"]

    G["Business pipelines"] --> H["pipelines/online_retail.py"]
    H --> I["Client-specific rules"]
    H --> J["Industry-specific metrics"]
    H --> K["Business-ready workbook"]

    E --> H
    F --> H
    B --> G
    C --> G
```

The important design change is that the Online Retail work is no longer just an
isolated demo. Its general pieces now live in the main program:

- cleaning helpers live in `file_processor/cleaning.py`
- Excel report formatting lives in `file_processor/excel_builder.py`
- the ecommerce workflow lives in `file_processor/pipelines/online_retail.py`

That is the shape we want for future client work: reusable platform pieces plus
small, focused business pipelines.
