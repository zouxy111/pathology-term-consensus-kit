from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

import yaml

from .readers import iter_table_rows


class ProjectBuilderError(ValueError):
    """Raised when a chat-confirmed project cannot be created."""


@dataclass(frozen=True)
class CreatedProject:
    project_dir: Path
    config_path: Path
    term_catalog: Path
    reports: tuple[Path, ...]


def create_project_from_inputs(
    out_dir: Path,
    term_file: Path,
    report_files: list[Path],
    project_name: str,
    subspecialty: str,
    company_field: str,
    report_text_field: str,
    context_fields: list[str],
    companies: list[str],
    include_terms: list[str],
    exclude_terms: list[str],
) -> CreatedProject:
    out_dir = out_dir.expanduser().resolve()
    term_file = term_file.expanduser().resolve()
    report_files = [path.expanduser().resolve() for path in report_files]
    if not term_file.exists():
        raise ProjectBuilderError(f"Term file does not exist: {term_file}")
    missing_reports = [str(path) for path in report_files if not path.exists()]
    if missing_reports:
        raise ProjectBuilderError("Report files do not exist: " + "; ".join(missing_reports))
    if not report_files:
        raise ProjectBuilderError("At least one --report-file is required.")
    if not company_field:
        raise ProjectBuilderError("--company-field is required.")
    if not report_text_field:
        raise ProjectBuilderError("--report-text-field is required.")
    if not include_terms:
        raise ProjectBuilderError("At least one --include-term is required.")

    data_dir = out_dir / "data"
    output_dir = out_dir / "outputs"
    data_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    copied_term = _copy_unique(term_file, data_dir, preferred_name="terms" + term_file.suffix.lower())
    copied_reports = tuple(_copy_unique(path, data_dir) for path in report_files)
    final_companies = companies or infer_companies(copied_reports, company_field)
    if not final_companies:
        raise ProjectBuilderError(
            "Could not infer companies. Pass one or more --company values after confirming the company field."
        )

    config = {
        "project": {
            "name": project_name,
            "subspecialty": subspecialty,
        },
        "inputs": {
            "term_catalog": _relative_to_project(copied_term, out_dir),
            "reports": [
                {
                    "path": _relative_to_project(path, out_dir),
                    "expected_rows": count_rows(path),
                    "label": path.name,
                }
                for path in copied_reports
            ],
        },
        "field_mapping": {
            "company_field": company_field,
            "report_text_field": report_text_field,
            "context_fields": context_fields,
        },
        "companies": final_companies,
        "target_filter": {
            "include_terms": include_terms,
            "exclude_terms": exclude_terms,
            "text_split_pattern": r"\n|；|;|\r",
            "allow_empty_include_terms": False,
        },
        "privacy": {"extra_patterns": []},
        "outputs": {
            "output_dir": "outputs",
            "evidence_workbook": "evidence.xlsx",
            "questionnaire_workbook": "questionnaire.xlsx",
            "deck_outline_md": "deck_outline.md",
            "deck_outline_html": "deck_outline.html",
            "run_manifest": "run_manifest.json",
            "privacy_report": "privacy_report.json",
            "scan_log": "scan_log.csv",
        },
    }
    config_path = out_dir / "project.yaml"
    config_path.write_text(yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return CreatedProject(
        project_dir=out_dir,
        config_path=config_path,
        term_catalog=copied_term,
        reports=copied_reports,
    )


def infer_companies(report_files: tuple[Path, ...], company_field: str) -> list[str]:
    counts: dict[str, int] = {}
    for report_file in report_files:
        for row, _ in iter_table_rows(report_file):
            if row is None:
                continue
            company = row.values.get(company_field, "").strip()
            if company:
                counts[company] = counts.get(company, 0) + 1
    return [company for company, _ in sorted(counts.items(), key=lambda item: (-item[1], item[0]))]


def count_rows(path: Path) -> int:
    total = 0
    for row, log in iter_table_rows(path):
        if row is not None:
            continue
        total += log.rows
    return total


def _copy_unique(source: Path, data_dir: Path, preferred_name: str | None = None) -> Path:
    base_name = preferred_name or source.name
    target = data_dir / base_name
    stem = target.stem
    suffix = target.suffix
    index = 2
    while target.exists() and target.resolve() != source.resolve():
        target = data_dir / f"{stem}_{index}{suffix}"
        index += 1
    if target.resolve() != source.resolve():
        shutil.copy2(source, target)
    return target


def _relative_to_project(path: Path, project_dir: Path) -> str:
    return str(path.resolve().relative_to(project_dir.resolve()))
