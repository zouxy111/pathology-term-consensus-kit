from __future__ import annotations

import json
import shutil
import tempfile
from importlib import resources
from pathlib import Path

from .aggregate import aggregate_reports
from .config import load_project_config, output_path
from .outputs.deck import write_deck_outline
from .outputs.workbooks import write_evidence_workbook, write_questionnaire_workbook
from .package import package_outputs
from .privacy import scan_output_files, write_privacy_report
from .scan import write_scan_log
from .term_catalog import load_term_catalog


def run_doctor() -> dict[str, object]:
    """Run a tiny packaged-data smoke test in a temporary directory."""
    with tempfile.TemporaryDirectory(prefix="path-term-kit-doctor-") as tmp:
        project_dir = Path(tmp) / "fake_subspecialty"
        project_dir.mkdir(parents=True, exist_ok=True)
        source_dir = resources.files("path_term_kit.assets").joinpath("fake_subspecialty")
        for file_name in ("project.yaml", "terms.csv", "reports.csv"):
            (project_dir / file_name).write_text(
                source_dir.joinpath(file_name).read_text(encoding="utf-8"), encoding="utf-8"
            )

        config = load_project_config(project_dir / "project.yaml")
        families = load_term_catalog(config.term_catalog)
        result = aggregate_reports(config, families)
        if result.errors:
            return {
                "status": "fail",
                "stage": "aggregate",
                "errors": list(result.errors),
            }

        scan_path = write_scan_log(config, result.logs)
        evidence_path = write_evidence_workbook(config, result)
        questionnaire_path = write_questionnaire_workbook(config, result)
        deck_md_path, deck_html_path = write_deck_outline(config, result)
        privacy_report = scan_output_files(
            [evidence_path, questionnaire_path, deck_md_path, deck_html_path],
            extra_patterns=config.privacy.extra_patterns,
        )
        privacy_path = output_path(config, "privacy_report")
        write_privacy_report(privacy_path, privacy_report)
        if privacy_report["status"] != "pass":
            return {
                "status": "fail",
                "stage": "privacy",
                "privacy": privacy_report,
            }

        manifest_path = output_path(config, "run_manifest")
        manifest_path.write_text(
            json.dumps(
                {
                    "project": config.name,
                    "subspecialty": config.subspecialty,
                    "status": "pass",
                    "data_gate": {
                        "total_rows": result.total_rows,
                        "accepted_segments": result.accepted_segments,
                    },
                    "outputs": {
                        "scan_log": str(scan_path),
                        "evidence_workbook": str(evidence_path),
                        "questionnaire_workbook": str(questionnaire_path),
                        "deck_outline_md": str(deck_md_path),
                        "deck_outline_html": str(deck_html_path),
                        "privacy_report": str(privacy_path),
                    },
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        zip_path = package_outputs(config)
        zip_size = zip_path.stat().st_size
        shutil.rmtree(config.outputs.output_dir, ignore_errors=True)
        return {
            "status": "pass",
            "term_families": len(families),
            "rows": result.total_rows,
            "accepted_segments": result.accepted_segments,
            "zip_size_bytes": zip_size,
        }

