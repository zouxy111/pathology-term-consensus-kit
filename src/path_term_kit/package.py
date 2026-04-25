from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from .config import ProjectConfig


class PackagingError(RuntimeError):
    """Raised when required output files are missing."""


RESULT_FILES = (
    "evidence_workbook",
    "questionnaire_workbook",
    "deck_outline_md",
    "deck_outline_html",
    "run_manifest",
    "privacy_report",
    "scan_log",
)


def package_outputs(config: ProjectConfig, zip_path: Path | None = None, strict: bool = True) -> Path:
    output_dir = config.outputs.output_dir
    if zip_path is None:
        zip_path = output_dir / "outputs.zip"
    zip_path = zip_path.expanduser().resolve()
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    missing = [
        output_dir / getattr(config.outputs, field_name)
        for field_name in RESULT_FILES
        if not (output_dir / getattr(config.outputs, field_name)).exists()
    ]
    if strict and missing:
        raise PackagingError("Missing required output files: " + "; ".join(str(path) for path in missing))
    with ZipFile(zip_path, "w", ZIP_DEFLATED) as archive:
        for field_name in RESULT_FILES:
            file_name = getattr(config.outputs, field_name)
            path = output_dir / file_name
            if path.exists():
                archive.write(path, arcname=path.name)
    return zip_path
