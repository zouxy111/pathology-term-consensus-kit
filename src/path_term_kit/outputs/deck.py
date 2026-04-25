from __future__ import annotations

from html import escape
from pathlib import Path

from path_term_kit.aggregate import AggregationResult, summarize_family
from path_term_kit.config import ProjectConfig, output_path


def write_deck_outline(config: ProjectConfig, result: AggregationResult) -> tuple[Path, Path]:
    md_path = output_path(config, "deck_outline_md")
    html_path = output_path(config, "deck_outline_html")
    md_path.parent.mkdir(parents=True, exist_ok=True)
    markdown = _build_markdown(config, result)
    md_path.write_text(markdown, encoding="utf-8")
    html_path.write_text(_markdown_to_basic_html(markdown), encoding="utf-8")
    return md_path, html_path


def _build_markdown(config: ProjectConfig, result: AggregationResult) -> str:
    summaries = [summarize_family(item, config.companies) for item in result.evidence.values()]
    high_priority = sorted(summaries, key=lambda row: int(row["total_hits"]), reverse=True)[:10]
    lines = [
        f"# {config.name}：{config.subspecialty}术语标准化主任会前材料",
        "",
        "## 1. 本次要拍板什么",
        "- 统一推荐标准名、兼容名、弃用/待议名。",
        "- 证据来自权威术语表和历史报告全量扫描。",
        "- 未收敛项进入分歧清单，不强行落地。",
        "",
        "## 2. Data Gate",
        f"- 历史报告读取行数：{result.total_rows}",
        f"- 非空行数：{result.total_non_empty_rows}",
        f"- 目标片段数：{result.accepted_segments}",
        f"- 扫描错误数：{len(result.errors)}",
        "",
        "## 3. 本轮纳入/排除范围",
        f"- 纳入关键词：{'、'.join(config.target_filter.include_terms) or '未设置'}",
        f"- 排除关键词：{'、'.join(config.target_filter.exclude_terms) or '未设置'}",
        f"- 目标公司：{'、'.join(config.companies)}",
        "",
        "## 4. 高频优先项",
    ]
    for row in high_priority:
        lines.append(
            f"- {row['standard_name']}：{row['total_hits']} 次；{row['conflict_summary']}"
        )
    lines.extend(
        [
            "",
            "## 5. 问卷填写规则",
            "- 主任选择：同意推荐名 / 建议兼容保留 / 建议弃用 / 需会议讨论。",
            "- 必须填写理由或修改建议，便于总负责人确认。",
            "- 多数意见 + 总负责人确认；未收敛项进入分歧清单。",
            "",
            "## 6. 交付物",
            "- 证据底稿：`evidence.xlsx`",
            "- 主任问卷：`questionnaire.xlsx`",
            "- 隐私扫描：`privacy_report.json`",
            "- 扫描日志：`scan_log.csv`",
        ]
    )
    if result.errors:
        lines.extend(["", "## 7. 阻断问题", *[f"- {error}" for error in result.errors]])
    return "\n".join(lines) + "\n"


def _markdown_to_basic_html(markdown: str) -> str:
    body_lines = []
    for line in markdown.splitlines():
        escaped = escape(line)
        if line.startswith("# "):
            body_lines.append(f"<h1>{escape(line[2:])}</h1>")
        elif line.startswith("## "):
            body_lines.append(f"<h2>{escape(line[3:])}</h2>")
        elif line.startswith("- "):
            body_lines.append(f"<p>• {escape(line[2:])}</p>")
        elif not line.strip():
            body_lines.append("")
        else:
            body_lines.append(f"<p>{escaped}</p>")
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>Pathology Terminology Deck Outline</title>"
        "<style>body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;max-width:980px;"
        "margin:40px auto;line-height:1.6;color:#172033}h1{font-size:30px}h2{margin-top:28px;"
        "border-bottom:1px solid #ddd;padding-bottom:6px}p{font-size:16px}</style>"
        "</head><body>"
        + "\n".join(body_lines)
        + "</body></html>"
    )

