from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from .config import ProjectConfig, output_path
from .readers import ScanLog, iter_table_rows, read_headers


@dataclass(frozen=True)
class DataGateResult:
    status: str
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    logs: tuple[ScanLog, ...]
    total_rows: int
    total_non_empty_rows: int


def validate_input_headers(config: ProjectConfig) -> list[str]:
    required = {config.fields.company_field, config.fields.report_text_field, *config.fields.context_fields}
    errors: list[str] = []
    for report in config.reports:
        table_headers = read_headers(report.path)
        found_any_complete_table = False
        for table_name, headers, error in table_headers:
            if error:
                errors.append(f"{report.path}::{table_name}: {error}")
                continue
            missing = sorted(required - set(headers))
            if not missing:
                found_any_complete_table = True
        if not found_any_complete_table:
            errors.append(f"{report.path}: no sheet/table contains required fields {sorted(required)}")
    return errors


def scan_report_inputs(config: ProjectConfig) -> DataGateResult:
    logs: list[ScanLog] = []
    errors: list[str] = validate_input_headers(config)
    warnings: list[str] = []
    total_rows = 0
    total_non_empty_rows = 0

    for report in config.reports:
        file_rows = 0
        seen_final_log_ids: set[tuple[str, str]] = set()
        for row, log in iter_table_rows(report.path):
            if row is not None:
                continue
            log_id = (log.file, log.table)
            if log_id in seen_final_log_ids:
                continue
            seen_final_log_ids.add(log_id)
            logs.append(log)
            file_rows += log.rows
            total_rows += log.rows
            total_non_empty_rows += log.non_empty_rows
            if log.error:
                errors.append(f"{log.file}::{log.table}: {log.error}")
        if report.expected_rows is not None and file_rows != report.expected_rows:
            errors.append(
                f"{report.path}: expected_rows={report.expected_rows}, actual_rows={file_rows}"
            )

    status = "pass" if not errors else "fail"
    return DataGateResult(
        status=status,
        errors=tuple(errors),
        warnings=tuple(warnings),
        logs=tuple(logs),
        total_rows=total_rows,
        total_non_empty_rows=total_non_empty_rows,
    )


def write_scan_log(config: ProjectConfig, logs: tuple[ScanLog, ...] | list[ScanLog]) -> Path:
    path = output_path(config, "scan_log")
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["file", "table", "rows", "non_empty_rows", "headers", "digest", "error"]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for log in logs:
            writer.writerow(log.as_dict())
    return path


def scan_logs_to_rows(logs: tuple[ScanLog, ...] | list[ScanLog]) -> list[dict[str, object]]:
    return [log.as_dict() for log in logs]

