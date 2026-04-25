from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from zipfile import ZipFile


DEFAULT_PRIVACY_PATTERNS: tuple[tuple[str, str], ...] = (
    ("phone", r"(?<!\d)(?:1[3-9]\d{9}|0\d{2,3}[- ]?\d{7,8})(?!\d)"),
    ("id_card", r"(?<!\d)\d{17}[\dXx](?!\d)"),
    ("barcode", r"(?:条码|病理号|蜡块号|玻片号|住院号|门诊号|身份证号)[:：]?\s*[A-Za-z0-9\-]{4,}"),
    ("hospital", r"[\u4e00-\u9fa5A-Za-z0-9（）()]{2,}(?:医院|医学院|门诊部|卫生院)"),
    ("patient_name_label", r"(?:姓名|患者|病人)[:：]\s*[\u4e00-\u9fa5A-Za-z·]{2,12}"),
)


@dataclass(frozen=True)
class PrivacyFinding:
    pattern: str
    text: str


def compiled_patterns(extra_patterns: tuple[str, ...] = ()) -> list[tuple[str, re.Pattern[str]]]:
    patterns = [(name, re.compile(pattern)) for name, pattern in DEFAULT_PRIVACY_PATTERNS]
    patterns.extend((f"extra_{index}", re.compile(pattern)) for index, pattern in enumerate(extra_patterns, start=1))
    return patterns


def find_privacy(text: str, extra_patterns: tuple[str, ...] = (), limit: int = 50) -> list[PrivacyFinding]:
    findings: list[PrivacyFinding] = []
    for name, pattern in compiled_patterns(extra_patterns):
        for match in pattern.finditer(text or ""):
            findings.append(PrivacyFinding(pattern=name, text=match.group(0)))
            if len(findings) >= limit:
                return findings
    return findings


def redact(text: str, extra_patterns: tuple[str, ...] = ()) -> str:
    redacted = text or ""
    for name, pattern in compiled_patterns(extra_patterns):
        redacted = pattern.sub(f"[已脱敏:{name}]", redacted)
    return redacted


def scan_output_files(paths: list[Path], extra_patterns: tuple[str, ...] = ()) -> dict[str, object]:
    files = []
    total = 0
    for path in paths:
        text = _extract_text(path)
        findings = find_privacy(text, extra_patterns=extra_patterns)
        total += len(findings)
        files.append(
            {
                "path": str(path),
                "exists": path.exists(),
                "finding_count": len(findings),
                "findings": [finding.__dict__ for finding in findings[:20]],
            }
        )
    return {"status": "pass" if total == 0 else "fail", "finding_count": total, "files": files}


def write_privacy_report(path: Path, report: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def _extract_text(path: Path) -> str:
    if not path.exists():
        return ""
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md", ".html", ".json", ".csv", ".yaml", ".yml"}:
        return path.read_text(encoding="utf-8", errors="ignore")
    if suffix in {".xlsx", ".xlsm"}:
        pieces: list[str] = []
        with ZipFile(path) as archive:
            for name in archive.namelist():
                if name.endswith(".xml") and (name.startswith("xl/sharedStrings") or name.startswith("xl/worksheets")):
                    pieces.append(archive.read(name).decode("utf-8", errors="ignore"))
        return "\n".join(pieces)
    return ""

