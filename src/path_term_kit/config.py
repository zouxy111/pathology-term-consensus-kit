from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


class ConfigError(ValueError):
    """Raised when a project configuration is incomplete or unsafe."""


@dataclass(frozen=True)
class ReportInput:
    path: Path
    expected_rows: int | None = None
    label: str | None = None


@dataclass(frozen=True)
class FieldMapping:
    company_field: str
    report_text_field: str
    context_fields: tuple[str, ...] = ()


@dataclass(frozen=True)
class TargetFilter:
    include_terms: tuple[str, ...] = ()
    exclude_terms: tuple[str, ...] = ()
    text_split_pattern: str = r"\n|；|;|\r"
    allow_empty_include_terms: bool = False


@dataclass(frozen=True)
class PrivacyConfig:
    extra_patterns: tuple[str, ...] = ()


@dataclass(frozen=True)
class OutputConfig:
    output_dir: Path
    evidence_workbook: str = "evidence.xlsx"
    questionnaire_workbook: str = "questionnaire.xlsx"
    deck_outline_md: str = "deck_outline.md"
    deck_outline_html: str = "deck_outline.html"
    run_manifest: str = "run_manifest.json"
    privacy_report: str = "privacy_report.json"
    scan_log: str = "scan_log.csv"


@dataclass(frozen=True)
class ProjectConfig:
    config_path: Path
    name: str
    subspecialty: str
    term_catalog: Path
    reports: tuple[ReportInput, ...]
    fields: FieldMapping
    companies: tuple[str, ...]
    target_filter: TargetFilter
    privacy: PrivacyConfig
    outputs: OutputConfig
    raw: dict[str, Any] = field(default_factory=dict)


def load_project_config(config_path: str | Path) -> ProjectConfig:
    path = Path(config_path).expanduser().resolve()
    if not path.exists():
        raise ConfigError(f"Config file does not exist: {path}")
    with path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}
    if not isinstance(raw, dict):
        raise ConfigError("Config must be a YAML mapping.")
    base_dir = path.parent

    project = _mapping(raw, "project")
    inputs = _mapping(raw, "inputs")
    fields = _mapping(raw, "field_mapping")
    outputs = _mapping(raw, "outputs")

    report_entries = inputs.get("reports")
    if not isinstance(report_entries, list) or not report_entries:
        raise ConfigError("inputs.reports must contain at least one CSV/XLSX file.")

    reports: list[ReportInput] = []
    for index, entry in enumerate(report_entries, start=1):
        if not isinstance(entry, dict):
            raise ConfigError(f"inputs.reports[{index}] must be a mapping.")
        report_path = _resolve(base_dir, _required(entry, "path", f"inputs.reports[{index}]"))
        expected_rows = entry.get("expected_rows")
        if expected_rows is not None and not isinstance(expected_rows, int):
            raise ConfigError(f"inputs.reports[{index}].expected_rows must be an integer.")
        reports.append(
            ReportInput(path=report_path, expected_rows=expected_rows, label=entry.get("label"))
        )

    target_filter_raw = raw.get("target_filter") or {}
    privacy_raw = raw.get("privacy") or {}

    output_dir = _resolve(base_dir, _required(outputs, "output_dir", "outputs"))
    config = ProjectConfig(
        config_path=path,
        name=str(_required(project, "name", "project")),
        subspecialty=str(_required(project, "subspecialty", "project")),
        term_catalog=_resolve(base_dir, _required(inputs, "term_catalog", "inputs")),
        reports=tuple(reports),
        fields=FieldMapping(
            company_field=str(_required(fields, "company_field", "field_mapping")),
            report_text_field=str(_required(fields, "report_text_field", "field_mapping")),
            context_fields=tuple(str(item) for item in fields.get("context_fields", []) or []),
        ),
        companies=tuple(str(item) for item in raw.get("companies", []) or []),
        target_filter=TargetFilter(
            include_terms=tuple(str(item) for item in target_filter_raw.get("include_terms", []) or []),
            exclude_terms=tuple(str(item) for item in target_filter_raw.get("exclude_terms", []) or []),
            text_split_pattern=str(target_filter_raw.get("text_split_pattern", r"\n|；|;|\r")),
            allow_empty_include_terms=bool(target_filter_raw.get("allow_empty_include_terms", False)),
        ),
        privacy=PrivacyConfig(
            extra_patterns=tuple(str(item) for item in privacy_raw.get("extra_patterns", []) or [])
        ),
        outputs=OutputConfig(
            output_dir=output_dir,
            evidence_workbook=str(outputs.get("evidence_workbook", "evidence.xlsx")),
            questionnaire_workbook=str(outputs.get("questionnaire_workbook", "questionnaire.xlsx")),
            deck_outline_md=str(outputs.get("deck_outline_md", "deck_outline.md")),
            deck_outline_html=str(outputs.get("deck_outline_html", "deck_outline.html")),
            run_manifest=str(outputs.get("run_manifest", "run_manifest.json")),
            privacy_report=str(outputs.get("privacy_report", "privacy_report.json")),
            scan_log=str(outputs.get("scan_log", "scan_log.csv")),
        ),
        raw=raw,
    )
    validate_config(config)
    return config


def validate_config(config: ProjectConfig) -> None:
    if not config.term_catalog.exists():
        raise ConfigError(f"Term catalog does not exist: {config.term_catalog}")
    missing_reports = [str(report.path) for report in config.reports if not report.path.exists()]
    if missing_reports:
        raise ConfigError("Report input files do not exist: " + "; ".join(missing_reports))
    if not config.fields.company_field.strip():
        raise ConfigError("field_mapping.company_field is required.")
    if not config.fields.report_text_field.strip():
        raise ConfigError("field_mapping.report_text_field is required.")
    if not config.companies:
        raise ConfigError("companies must list target companies/labs in decision order.")
    if not config.target_filter.include_terms and not config.target_filter.allow_empty_include_terms:
        raise ConfigError(
            "target_filter.include_terms is required. Set allow_empty_include_terms=true only for "
            "non-organ-specific test projects."
        )


def output_path(config: ProjectConfig, field_name: str) -> Path:
    value = getattr(config.outputs, field_name)
    return config.outputs.output_dir / value


def _mapping(raw: dict[str, Any], key: str) -> dict[str, Any]:
    value = raw.get(key)
    if not isinstance(value, dict):
        raise ConfigError(f"{key} must be a mapping.")
    return value


def _required(mapping: dict[str, Any], key: str, section: str) -> Any:
    value = mapping.get(key)
    if value is None or value == "":
        raise ConfigError(f"{section}.{key} is required.")
    return value


def _resolve(base_dir: Path, value: Any) -> Path:
    path = Path(str(value)).expanduser()
    if not path.is_absolute():
        path = base_dir / path
    return path.resolve()

