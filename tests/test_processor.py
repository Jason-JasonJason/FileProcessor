from __future__ import annotations

import json

from file_processor.extractors import supported_extensions
from file_processor.processor import process_folder


def test_supported_extensions_include_core_formats() -> None:
    extensions = supported_extensions()
    assert ".txt" in extensions
    assert ".json" in extensions
    assert ".csv" in extensions
    assert ".xlsx" in extensions
    assert ".docx" in extensions
    assert ".pptx" in extensions


def test_process_folder_writes_json_results(tmp_path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    (input_dir / "note.txt").write_text("hello ETL", encoding="utf-8")
    (input_dir / "data.json").write_text('{"name": "sample"}', encoding="utf-8")

    results = process_folder(input_dir, output_dir)

    assert len(results) == 2
    assert all(result.status == "ok" for result in results)
    output_files = sorted(output_dir.glob("*.json"))
    assert len(output_files) == 2

    payload = json.loads(output_files[0].read_text(encoding="utf-8"))
    assert payload["source_path"]
    assert payload["metadata"]["size_bytes"] > 0
