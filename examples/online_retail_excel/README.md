# Online Retail Excel-to-Excel Demo

This demo turns a raw ecommerce transaction workbook into a polished business
report workbook.

## Dataset

Use the UCI Machine Learning Repository's **Online Retail** dataset:

https://archive.ics.uci.edu/dataset/352/online+retail

The dataset is a real transaction dataset from a UK online retailer and is
provided as `Online Retail.xlsx`.

Place the workbook here:

```text
examples/online_retail_excel/input/Online Retail.xlsx
```

## Run

From the project root:

```powershell
python -m file_processor online-retail-report `
  "examples/online_retail_excel/input/Online Retail.xlsx" `
  "examples/online_retail_excel/output/online_retail_business_report.xlsx"
```

The output report will be written to:

```text
examples/online_retail_excel/output/online_retail_business_report.xlsx
```

## Report Sheets

- `Executive Summary`
- `Monthly Revenue`
- `Top Products`
- `Top Customers`
- `Country Sales`
- `Cancelled Orders`
- `Data Quality Issues`
- `Cleaned Transactions`

This is the first portfolio demo for the project: Excel input to Excel output.
