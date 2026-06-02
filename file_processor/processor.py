from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .extractors import MissingDependencyError, extract, supported_extensions


@dataclass
class ProcessingResult:
    source_path: str
    output_path: str | None
    file_name: str
    extension: str
    status: str
    content: dict[str, Any] | None
    metadata: dict[str, Any]
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def process_file(path: Path, output_dir: Path, write_json: bool = True) -> ProcessingResult:
    path = path.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{path.stem}.{short_hash(path)}.json" if write_json else None
    metadata = build_metadata(path)

    try:
        content = extract(path)
    except (MissingDependencyError, ValueError, OSError, json.JSONDecodeError) as exc:
        result = ProcessingResult(
            source_path=str(path),
            output_path=str(output_path),
            file_name=path.name,
            extension=path.suffix.lower(),
            status="error",
            content=None,
            metadata=metadata,
            error=str(exc),
        )
    else:
        result = ProcessingResult(
            source_path=str(path),
            output_path=str(output_path),
            file_name=path.name,
            extension=path.suffix.lower(),
            status="ok",
            content=content,
            metadata=metadata,
        )

    if write_json and output_path is not None:
        output_path.write_text(json.dumps(result.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def process_folder(
    input_dir: Path,
    output_dir: Path,
    recursive: bool = False,
    write_json: bool = True,
) -> list[ProcessingResult]:
    if not input_dir.exists():
        raise FileNotFoundError(f"Input folder does not exist: {input_dir}")
    if not input_dir.is_dir():
        raise NotADirectoryError(f"Input path is not a folder: {input_dir}")

    pattern = "**/*" if recursive else "*"
    extensions = set(supported_extensions())
    files = sorted(
        path for path in input_dir.glob(pattern)
        if path.is_file() and path.suffix.lower() in extensions
    )
    return [process_file(path, output_dir, write_json=write_json) for path in files]


def build_metadata(path: Path) -> dict[str, Any]:
    stat = path.stat()
    return {
        "size_bytes": stat.st_size,
        "modified_epoch": stat.st_mtime,
    }


def short_hash(path: Path) -> str:
    digest = hashlib.sha1(str(path).encode("utf-8")).hexdigest()
    return digest[:10]
