from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .aggregate import AggregationResult
from .config import ProjectConfig, output_path


def write_run_manifest(
    config: ProjectConfig,
    result: AggregationResult,
    outputs: dict[str, str],
    privacy_report: dict[str, Any] | None = None,
) -> Path:
    status = "pass" if not result.errors and (privacy_report or {}).get("status", "pass") == "pass" else "fail"
    manifest = {
        "project": config.name,
        "subspecialty": config.subspecialty,
        "status": status,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "config_path": str(config.config_path),
        "term_catalog": str(config.term_catalog),
        "report_inputs": [
            {"path": str(report.path), "expected_rows": report.expected_rows, "label": report.label}
            for report in config.reports
        ],
        "companies": list(config.companies),
        "data_gate": {
            "total_rows": result.total_rows,
            "total_non_empty_rows": result.total_non_empty_rows,
            "accepted_segments": result.accepted_segments,
            "rejected_segments": dict(result.rejected_segments),
            "errors": list(result.errors),
            "warnings": list(result.warnings),
        },
        "outputs": outputs,
        "privacy": privacy_report or {},
    }
    path = output_path(config, "run_manifest")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return path

