from __future__ import annotations

import argparse
import sys
from importlib import resources
from pathlib import Path

from .aggregate import aggregate_reports
from .config import ConfigError, load_project_config, output_path
from .inspection import (
    inspect_data_dir,
    inspect_term_file,
    render_data_inspection_for_chat,
    render_term_inspection_for_chat,
    write_inspection_json,
)
from .manifest import write_run_manifest
from .package import PackagingError, package_outputs
from .privacy import scan_output_files, write_privacy_report
from .project_builder import ProjectBuilderError, create_project_from_inputs
from .scan import scan_report_inputs, write_scan_log
from .term_catalog import TermCatalogError, load_term_catalog
from .outputs.deck import write_deck_outline
from .outputs.workbooks import write_evidence_workbook, write_questionnaire_workbook


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="path-term-kit")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create a new project workspace.")
    init_parser.add_argument("--out", required=True, help="Output project directory.")
    init_parser.add_argument("--with-example", action="store_true", help="Copy fake example data.")

    validate_parser = subparsers.add_parser("validate", help="Validate config and input headers.")
    validate_parser.add_argument("config")

    scan_parser = subparsers.add_parser("scan", help="Full-scan report inputs and write scan_log.csv.")
    scan_parser.add_argument("config")

    run_parser = subparsers.add_parser("run", help="Run full SOP pipeline.")
    run_parser.add_argument("config")

    qa_parser = subparsers.add_parser("qa", help="Run privacy QA on generated outputs.")
    qa_parser.add_argument("config")

    inspect_data_parser = subparsers.add_parser(
        "inspect-data", help="Inspect uploaded report attachments before project config."
    )
    inspect_data_parser.add_argument("attachment_dir")
    inspect_data_parser.add_argument("--max-examples", type=int, default=3)
    inspect_data_parser.add_argument("--json-output")
    inspect_data_parser.add_argument(
        "--include-term-tables",
        action="store_true",
        help="Do not auto-skip files that look like terminology catalogs.",
    )

    inspect_terms_parser = subparsers.add_parser(
        "inspect-terms", help="Inspect a terminology table before running the SOP."
    )
    inspect_terms_parser.add_argument("term_file")
    inspect_terms_parser.add_argument("--json-output")

    package_parser = subparsers.add_parser(
        "package-results", help="Zip generated outputs for chat handoff."
    )
    package_parser.add_argument("config")
    package_parser.add_argument("--out")
    package_parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="Create a zip even if some expected outputs are missing.",
    )

    create_parser = subparsers.add_parser(
        "create-project", help="Create project.yaml from chat-confirmed fields and attachments."
    )
    create_parser.add_argument("--out", required=True)
    create_parser.add_argument("--term-file", required=True)
    create_parser.add_argument("--report-file", action="append", required=True)
    create_parser.add_argument("--project-name", default="病理亚专科术语标准化项目")
    create_parser.add_argument("--subspecialty", default="待确认亚专科")
    create_parser.add_argument("--company-field", required=True)
    create_parser.add_argument("--report-text-field", required=True)
    create_parser.add_argument("--context-field", action="append", default=[])
    create_parser.add_argument("--company", action="append", default=[])
    create_parser.add_argument("--include-term", action="append", required=True)
    create_parser.add_argument("--exclude-term", action="append", default=[])

    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            return _cmd_init(Path(args.out), with_example=args.with_example)
        if args.command == "validate":
            return _cmd_validate(args.config)
        if args.command == "scan":
            return _cmd_scan(args.config)
        if args.command == "run":
            return _cmd_run(args.config)
        if args.command == "qa":
            return _cmd_qa(args.config)
        if args.command == "inspect-data":
            return _cmd_inspect_data(
                args.attachment_dir,
                args.max_examples,
                args.json_output,
                include_term_tables=args.include_term_tables,
            )
        if args.command == "inspect-terms":
            return _cmd_inspect_terms(args.term_file, args.json_output)
        if args.command == "package-results":
            return _cmd_package_results(args.config, args.out, allow_missing=args.allow_missing)
        if args.command == "create-project":
            return _cmd_create_project(args)
    except (ConfigError, TermCatalogError, PackagingError, ProjectBuilderError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 2


def _cmd_init(out_dir: Path, with_example: bool = False) -> int:
    out_dir = out_dir.expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "data").mkdir(exist_ok=True)
    (out_dir / "outputs").mkdir(exist_ok=True)
    template_text = resources.files("path_term_kit.assets").joinpath("project.yaml").read_text(
        encoding="utf-8"
    )
    (out_dir / "project.yaml").write_text(template_text, encoding="utf-8")
    if with_example:
        _copy_packaged_example(out_dir / "fake_subspecialty")
    print(f"Initialized project workspace: {out_dir}")
    print(f"Edit config: {out_dir / 'project.yaml'}")
    return 0


def _copy_packaged_example(target_dir: Path) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    source_dir = resources.files("path_term_kit.assets").joinpath("fake_subspecialty")
    for file_name in ("project.yaml", "terms.csv", "reports.csv"):
        target = target_dir / file_name
        target.write_text(source_dir.joinpath(file_name).read_text(encoding="utf-8"), encoding="utf-8")


def _cmd_validate(config_path: str) -> int:
    config = load_project_config(config_path)
    families = load_term_catalog(config.term_catalog)
    result = scan_report_inputs(config)
    print(f"Config OK: {config.name}")
    print(f"Term families: {len(families)}")
    print(f"Report rows scanned: {result.total_rows}")
    if result.errors:
        for error in result.errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Data gate: pass")
    return 0


def _cmd_scan(config_path: str) -> int:
    config = load_project_config(config_path)
    result = scan_report_inputs(config)
    scan_path = write_scan_log(config, result.logs)
    print(f"Wrote scan log: {scan_path}")
    print(f"Rows scanned: {result.total_rows}")
    if result.errors:
        for error in result.errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


def _cmd_run(config_path: str) -> int:
    config = load_project_config(config_path)
    families = load_term_catalog(config.term_catalog)
    result = aggregate_reports(config, families)
    scan_path = write_scan_log(config, result.logs)
    outputs = {"scan_log": str(scan_path)}
    if result.errors:
        write_run_manifest(config, result, outputs)
        for error in result.errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print("Data gate failed; questionnaire and evidence were not generated.", file=sys.stderr)
        return 1

    evidence_path = write_evidence_workbook(config, result)
    questionnaire_path = write_questionnaire_workbook(config, result)
    deck_md_path, deck_html_path = write_deck_outline(config, result)
    outputs.update(
        {
            "evidence_workbook": str(evidence_path),
            "questionnaire_workbook": str(questionnaire_path),
            "deck_outline_md": str(deck_md_path),
            "deck_outline_html": str(deck_html_path),
        }
    )
    privacy_report = scan_output_files(
        [evidence_path, questionnaire_path, deck_md_path, deck_html_path],
        extra_patterns=config.privacy.extra_patterns,
    )
    privacy_path = output_path(config, "privacy_report")
    write_privacy_report(privacy_path, privacy_report)
    outputs["privacy_report"] = str(privacy_path)
    manifest_path = write_run_manifest(config, result, outputs, privacy_report=privacy_report)
    outputs["run_manifest"] = str(manifest_path)
    print("Generated outputs:")
    for key, value in outputs.items():
        print(f"- {key}: {value}")
    if privacy_report["status"] != "pass":
        print("ERROR: privacy scan failed on generated outputs.", file=sys.stderr)
        return 1
    return 0


def _cmd_qa(config_path: str) -> int:
    config = load_project_config(config_path)
    paths = [
        output_path(config, "evidence_workbook"),
        output_path(config, "questionnaire_workbook"),
        output_path(config, "deck_outline_md"),
        output_path(config, "deck_outline_html"),
        output_path(config, "run_manifest"),
    ]
    report = scan_output_files(paths, extra_patterns=config.privacy.extra_patterns)
    privacy_path = output_path(config, "privacy_report")
    write_privacy_report(privacy_path, report)
    print(f"Wrote privacy report: {privacy_path}")
    if report["status"] != "pass":
        print("ERROR: privacy scan failed.", file=sys.stderr)
        return 1
    print("QA privacy scan: pass")
    return 0


def _cmd_inspect_data(
    attachment_dir: str,
    max_examples: int,
    json_output: str | None,
    include_term_tables: bool = False,
) -> int:
    directory = Path(attachment_dir).expanduser().resolve()
    report = inspect_data_dir(
        directory, max_examples=max_examples, skip_term_like=not include_term_tables
    )
    output_path = Path(json_output).expanduser().resolve() if json_output else directory / "inspect_data_report.json"
    write_inspection_json(report, output_path)
    print(render_data_inspection_for_chat(report))
    print(f"Wrote inspection JSON: {output_path}")
    return 0 if report.status == "pass" else 1


def _cmd_inspect_terms(term_file: str, json_output: str | None) -> int:
    path = Path(term_file).expanduser().resolve()
    report = inspect_term_file(path)
    default_output = path.with_suffix(path.suffix + ".inspect_terms.json")
    output_path = Path(json_output).expanduser().resolve() if json_output else default_output
    write_inspection_json(report, output_path)
    print(render_term_inspection_for_chat(report))
    print(f"Wrote inspection JSON: {output_path}")
    return 0 if report.status == "pass" else 1


def _cmd_package_results(config_path: str, zip_output: str | None, allow_missing: bool = False) -> int:
    config = load_project_config(config_path)
    zip_path = Path(zip_output).expanduser().resolve() if zip_output else None
    result_path = package_outputs(config, zip_path=zip_path, strict=not allow_missing)
    print(f"Packaged outputs: {result_path}")
    return 0


def _cmd_create_project(args: argparse.Namespace) -> int:
    created = create_project_from_inputs(
        out_dir=Path(args.out),
        term_file=Path(args.term_file),
        report_files=[Path(path) for path in args.report_file],
        project_name=args.project_name,
        subspecialty=args.subspecialty,
        company_field=args.company_field,
        report_text_field=args.report_text_field,
        context_fields=args.context_field,
        companies=args.company,
        include_terms=args.include_term,
        exclude_terms=args.exclude_term,
    )
    print(f"Created project: {created.project_dir}")
    print(f"Config: {created.config_path}")
    print(f"Term catalog: {created.term_catalog}")
    for report in created.reports:
        print(f"Report: {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
