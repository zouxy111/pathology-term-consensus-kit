from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field

from .config import ProjectConfig
from .match import match_segment, split_segments
from .privacy import redact
from .readers import ScanLog, iter_table_rows, read_headers
from .term_catalog import TermFamily


@dataclass
class FamilyEvidence:
    family: TermFamily
    total_hits: int = 0
    company_counts: Counter[str] = field(default_factory=Counter)
    variant_counts: dict[str, Counter[str]] = field(default_factory=lambda: defaultdict(Counter))
    examples: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))


@dataclass
class AggregationResult:
    evidence: dict[str, FamilyEvidence]
    logs: tuple[ScanLog, ...]
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    total_rows: int
    total_non_empty_rows: int
    accepted_segments: int
    rejected_segments: Counter[str]


def aggregate_reports(config: ProjectConfig, families: list[TermFamily]) -> AggregationResult:
    evidence = {family.family_id: FamilyEvidence(family=family) for family in families}
    logs: list[ScanLog] = []
    errors: list[str] = _validate_headers(config)
    warnings: list[str] = []
    total_rows = 0
    total_non_empty_rows = 0
    accepted_segments = 0
    rejected_segments: Counter[str] = Counter()

    for report in config.reports:
        file_rows = 0
        final_log_ids: set[tuple[str, str]] = set()
        for row, log in iter_table_rows(report.path):
            if row is None:
                log_id = (log.file, log.table)
                if log_id not in final_log_ids:
                    final_log_ids.add(log_id)
                    logs.append(log)
                    file_rows += log.rows
                    total_rows += log.rows
                    total_non_empty_rows += log.non_empty_rows
                    if log.error:
                        errors.append(f"{log.file}::{log.table}: {log.error}")
                continue
            company = row.values.get(config.fields.company_field, "").strip() or "UNKNOWN"
            if company not in config.companies:
                warnings.append(
                    f"Unlisted company '{company}' in {row.source_file.name}::{row.table_name}:{row.row_number}"
                )
            text = row.values.get(config.fields.report_text_field, "")
            for segment in split_segments(text, config):
                if not segment.accepted:
                    rejected_segments[segment.reason] += 1
                    continue
                accepted_segments += 1
                matches = match_segment(segment.text, families)
                for match in matches:
                    item = evidence[match.family.family_id]
                    item.total_hits += 1
                    item.company_counts[company] += 1
                    item.variant_counts[match.variant][company] += 1
                    if len(item.examples[company]) < 3:
                        item.examples[company].append(redact(match.segment, config.privacy.extra_patterns)[:180])
        if report.expected_rows is not None and file_rows != report.expected_rows:
            errors.append(f"{report.path}: expected_rows={report.expected_rows}, actual_rows={file_rows}")

    if accepted_segments == 0:
        errors.append("Target filter accepted 0 report segments; check include_terms/exclude_terms.")

    return AggregationResult(
        evidence=evidence,
        logs=tuple(logs),
        errors=tuple(dict.fromkeys(errors)),
        warnings=tuple(dict.fromkeys(warnings[:200])),
        total_rows=total_rows,
        total_non_empty_rows=total_non_empty_rows,
        accepted_segments=accepted_segments,
        rejected_segments=rejected_segments,
    )


def _validate_headers(config: ProjectConfig) -> list[str]:
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


def summarize_family(item: FamilyEvidence, companies: tuple[str, ...]) -> dict[str, object]:
    max_company = ""
    max_count = 0
    if item.company_counts:
        max_company, max_count = item.company_counts.most_common(1)[0]
    nonzero_companies = sum(1 for company in companies if item.company_counts.get(company, 0) > 0)
    max_share = round(max_count / item.total_hits, 4) if item.total_hits else 0
    if item.total_hits == 0:
        conflict_summary = "历史数据未命中，需人工确认是否保留为标准项"
    elif nonzero_companies >= 3:
        conflict_summary = "跨多家公司均有使用，优先统一口径"
    elif max_share >= 0.8:
        conflict_summary = f"主要集中在{max_company}，建议确认是否为地方叫法"
    else:
        conflict_summary = "少数公司使用，建议问卷确认兼容或弃用"
    return {
        "family_id": item.family.family_id,
        "category": item.family.category,
        "standard_name": item.family.standard_name,
        "priority": item.family.priority,
        "source_basis": item.family.source_basis,
        "compatible_names": item.family.compatible_names,
        "deprecated_or_discuss": item.family.deprecated_or_discuss,
        "decision_question": item.family.decision_question,
        "total_hits": item.total_hits,
        "nonzero_companies": nonzero_companies,
        "max_company": max_company,
        "max_company_share": max_share,
        "conflict_summary": conflict_summary,
    }
