# File Automated Processing Program

This project provides a small ETL-friendly command-line tool that reads many
file formats, extracts normalized content, and writes one JSON document per
input file.

## Supported formats

- Text: `.txt`, `.md`, `.log`
- Structured text: `.json`, `.csv`, `.tsv`, `.xml`, `.html`, `.htm`
- Microsoft Office: `.xlsx`, `.xlsm`, `.docx`, `.pptx`
- PDF: `.pdf`

Office and PDF support uses optional third-party packages listed in
`requirements.txt`.

## Quick start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m file_processor process .\input .\output
```

The Office/PDF extractors depend on these third-party packages:

- Excel `.xlsx` / `.xlsm`: install package `openpyxl`, import name `openpyxl`
- Word `.docx`: install package `python-docx`, import name `docx`
- PowerPoint `.pptx`: install package `python-pptx`, import name `pptx`
- PDF `.pdf`: install package `pypdf`, import name `pypdf`

If you are using the project as an installable package instead of
`requirements.txt`, install the project dependencies with:

```powershell
pip install -e .
```

Each processed file produces a JSON output containing:

- source path
- file name and extension
- processing status
- extracted content
- basic metadata
- error message, when a file could not be processed

## Examples

Process every supported file in a folder:

```powershell
python -m file_processor process C:\data\incoming C:\data\processed
```

Include files in nested folders:

```powershell
python -m file_processor process C:\data\incoming C:\data\processed --recursive
```

Write a combined manifest file:

```powershell
python -m file_processor process .\input .\output --manifest manifest.json
```

List supported extensions:

```powershell
python -m file_processor formats
```
