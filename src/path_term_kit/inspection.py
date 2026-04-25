from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .privacy import redact
from .readers import iter_table_rows, read_headers
from .term_catalog import REQUIRED_TERM_FIELDS, TermCatalogError, load_term_catalog


SUPPORTED_DATA_SUFFIXES = {".csv", ".xlsx", ".xlsm", ".xls"}


@dataclass(frozen=True)
class InspectionReport:
    status: str
    payload: dict[str, Any]


def inspect_data_dir(
    attachment_dir: Path, max_examples: int = 3, skip_term_like: bool = True
) -> InspectionReport:
    attachment_dir = attachment_dir.expanduser().resolve()
    files = sorted(
        path
        for path in attachment_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_DATA_SUFFIXES
    )
    payload: dict[str, Any] = {
        "attachment_dir": str(attachment_dir),
        "status": "pass",
        "discovered_file_count": len(files),
        "file_count": 0,
        "total_rows": 0,
        "files": [],
        "skipped_files": [],
        "candidate_fields": {},
        "errors": [],
    }
    if not attachment_dir.exists():
        payload["status"] = "fail"
        payload["errors"].append(f"Attachment directory does not exist: {attachment_dir}")
        return InspectionReport(status="fail", payload=payload)
    if not files:
        payload["status"] = "fail"
        payload["errors"].append("No supported CSV/XLSX/XLSM/XLS files found.")
        return InspectionReport(status="fail", payload=payload)

    header_counter: Counter[str] = Counter()
    for file_path in files:
        if skip_term_like and looks_like_term_catalog(file_path):
            payload["skipped_files"].append(
                {
                    "path": str(file_path),
                    "reason": "looks_like_term_catalog",
                }
            )
            continue
        file_payload = {"path": str(file_path), "tables": []}
        table_examples: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
        final_logs = []
        for row, log in iter_table_rows(file_path):
            if row is not None:
                table_key = row.table_name
                for column, value in row.values.items():
                    text = (value or "").strip()
                    if text and len(table_examples[table_key][column]) < max_examples:
                        table_examples[table_key][column].append(redact(text)[:160])
                continue
            final_logs.append(log)

        for log in final_logs:
            header_counter.update(header for header in log.headers if header)
            table_payload = {
                "table": log.table,
                "rows": log.rows,
                "non_empty_rows": log.non_empty_rows,
                "headers": list(log.headers),
                "digest": log.digest,
                "error": log.error,
                "column_examples": dict(table_examples.get(log.table, {})),
            }
            file_payload["tables"].append(table_payload)
            payload["total_rows"] += log.rows
            if log.error:
                payload["errors"].append(f"{file_path.name}::{log.table}: {log.error}")
        payload["files"].append(file_payload)
        payload["file_count"] += 1

    payload["candidate_fields"] = suggest_field_mapping(list(header_counter))
    if payload["file_count"] == 0:
        payload["errors"].append("No report-like data files found after skipping term-like tables.")
    if payload["errors"]:
        payload["status"] = "fail"
    return InspectionReport(status=str(payload["status"]), payload=payload)


def inspect_term_file(term_file: Path) -> InspectionReport:
    term_file = term_file.expanduser().resolve()
    payload: dict[str, Any] = {
        "term_file": str(term_file),
        "status": "pass",
        "required_fields": list(REQUIRED_TERM_FIELDS),
        "missing_fields": [],
        "family_count": 0,
        "errors": [],
    }
    if not term_file.exists():
        payload["status"] = "fail"
        payload["errors"].append(f"Term file does not exist: {term_file}")
        return InspectionReport(status="fail", payload=payload)
    headers_info = read_headers(term_file)
    headers = headers_info[0][1] if headers_info else tuple()
    header_error = headers_info[0][2] if headers_info else "Unable to read headers."
    if header_error:
        payload["status"] = "fail"
        payload["errors"].append(header_error)
        return InspectionReport(status="fail", payload=payload)
    missing = [field for field in REQUIRED_TERM_FIELDS if field not in set(headers)]
    payload["headers"] = list(headers)
    payload["missing_fields"] = missing
    if missing:
        payload["status"] = "fail"
        payload["errors"].append("Missing required term fields: " + ", ".join(missing))
        return InspectionReport(status="fail", payload=payload)
    try:
        families = load_term_catalog(term_file)
    except TermCatalogError as exc:
        payload["status"] = "fail"
        payload["errors"].append(str(exc))
        return InspectionReport(status="fail", payload=payload)
    payload["family_count"] = len(families)
    payload["sample_families"] = [
        {
            "family_id": family.family_id,
            "standard_name": family.standard_name,
            "priority": family.priority,
            "pattern_count": len(family.patterns),
        }
        for family in families[:10]
    ]
    return InspectionReport(status="pass", payload=payload)


def write_inspection_json(report: InspectionReport, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report.payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


def render_data_inspection_for_chat(report: InspectionReport) -> str:
    payload = report.payload
    lines = [
        "# 数据附件扫描结果",
        f"- 状态：{payload['status']}",
        f"- 文件数：{payload['file_count']}",
        f"- 全量行数：{payload['total_rows']}",
    ]
    if payload["errors"]:
        lines.extend(["- 错误：", *[f"  - {error}" for error in payload["errors"]]])
    if payload.get("skipped_files"):
        lines.append("- 已自动跳过疑似术语表：")
        for item in payload["skipped_files"]:
            lines.append(f"  - {Path(item['path']).name} ({item['reason']})")
    lines.append("")
    lines.append("## 候选字段")
    candidates = payload.get("candidate_fields", {})
    lines.append(f"- 子公司/实验室列候选：{', '.join(candidates.get('company_field', [])) or '未识别'}")
    lines.append(f"- 报告结果列候选：{', '.join(candidates.get('report_text_field', [])) or '未识别'}")
    lines.append(f"- 辅助上下文列候选：{', '.join(candidates.get('context_fields', [])) or '未识别'}")
    lines.append("")
    lines.append("## 文件与示例")
    for file_payload in payload["files"]:
        lines.append(f"### {Path(file_payload['path']).name}")
        for table in file_payload["tables"]:
            lines.append(
                f"- sheet/table：{table['table']}；行数：{table['rows']}；列：{', '.join(table['headers'])}"
            )
            examples = table.get("column_examples", {})
            for column in table["headers"][:12]:
                values = examples.get(column, [])
                if values:
                    lines.append(f"  - {column} 示例：{' / '.join(values[:2])}")
    lines.append("")
    lines.append("请用户确认：子公司/实验室列、报告结果列、辅助列、目标器官纳入词、排除词。")
    return "\n".join(lines) + "\n"


def render_term_inspection_for_chat(report: InspectionReport) -> str:
    payload = report.payload
    lines = [
        "# 术语表扫描结果",
        f"- 状态：{payload['status']}",
        f"- 术语家族数：{payload.get('family_count', 0)}",
    ]
    if payload.get("missing_fields"):
        lines.append("- 缺失字段：" + ", ".join(payload["missing_fields"]))
    if payload.get("errors"):
        lines.extend(["- 错误：", *[f"  - {error}" for error in payload["errors"]]])
    if payload.get("sample_families"):
        lines.append("## 样例术语")
        for family in payload["sample_families"]:
            lines.append(
                f"- {family['family_id']}：{family['standard_name']}；priority={family['priority']}；patterns={family['pattern_count']}"
            )
    if report.status != "pass":
        lines.append("")
        lines.append("请用户补齐术语表字段后重新上传。")
    return "\n".join(lines) + "\n"


def suggest_field_mapping(headers: list[str]) -> dict[str, list[str]]:
    unique_headers = sorted(set(headers))
    return {
        "company_field": _score_headers(
            unique_headers, ("最终检测子公司", "子公司", "公司", "实验室", "lab", "company", "机构")
        ),
        "report_text_field": _score_headers(
            unique_headers, ("单一结果", "病理结果", "诊断结果", "报告结果", "结果", "report", "diagnosis")
        ),
        "context_fields": _score_headers(
            unique_headers, ("诊断", "送检", "标本", "部位", "材料", "context", "specimen")
        ),
    }


def _score_headers(headers: list[str], keywords: tuple[str, ...]) -> list[str]:
    scored = []
    for header in headers:
        normalized = header.lower()
        score = sum(1 for keyword in keywords if keyword.lower() in normalized)
        if score:
            scored.append((score, len(header), header))
    scored.sort(key=lambda item: (-item[0], item[1], item[2]))
    return [item[2] for item in scored[:8]]


def looks_like_term_catalog(path: Path) -> bool:
    try:
        headers_info = read_headers(path)
    except Exception:
        return False
    for _, headers, error in headers_info:
        if error:
            continue
        if set(REQUIRED_TERM_FIELDS).issubset(set(headers)):
            return True
    return False
