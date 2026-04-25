# Weak Model Runbook

This runbook is intentionally strict. A weaker model should follow it without improvising.

## Golden Rules

1. Do not infer missing columns. Stop and report the missing field.
2. Do not use sampling as evidence. Always run the full scan.
3. Do not edit raw input data.
4. Do not generate a questionnaire if data gate fails.
5. Do not copy raw patient text into final materials.
6. Do not silently change target-organ include/exclude terms.

## Phase 1 — Initialize Project Skeleton

Command:

```bash
python scripts/bootstrap_project.py --out <project_dir>
```

Then ask the human to provide:

- terminology table
- historical report files
- company list
- field mapping
- target include/exclude terms

Install the runner only after the project skeleton exists:

```bash
uv venv
uv pip install -e ".[dev]"
```

## Phase 2 — Configure

For chat attachments, prefer `create-project`; do not hand-write YAML unless the CLI cannot express the project:

```bash
path-term-kit create-project \
  --out <project_dir> \
  --term-file <term_file> \
  --report-file <report_file> \
  --company-field "<confirmed company field>" \
  --report-text-field "<confirmed report text field>" \
  --include-term "<target include term>"
```

If hand editing is necessary, edit only `project.yaml`.

Checklist:

- `inputs.term_catalog` exists.
- Every `inputs.reports[].path` exists.
- `company_field` exactly matches a source column.
- `report_text_field` exactly matches a source column.
- `companies` are in decision display order.
- `include_terms` and `exclude_terms` are not empty unless the human explicitly says the project is not organ-specific.

## Phase 3 — Validate

Run:

```bash
path-term-kit validate <project_dir>/project.yaml
```

If it fails:

- Report the exact error.
- Do not continue to `run`.
- Ask for corrected config or corrected input files.

## Phase 4 — Full Scan

Run:

```bash
path-term-kit scan <project_dir>/project.yaml
```

Confirm:

- row counts are recorded
- all files/sheets are listed
- no unreadable sheet exists
- expected rows match when configured

## Phase 5 — Generate Materials

Run:

```bash
path-term-kit run <project_dir>/project.yaml
```

Expected outputs:

- `evidence.xlsx`
- `questionnaire.xlsx`
- `deck_outline.md`
- `deck_outline.html`
- `scan_log.csv`
- `privacy_report.json`
- `run_manifest.json`

## Phase 6 — QA

Run:

```bash
path-term-kit qa <project_dir>/project.yaml
```

Only hand off outputs if:

- command exits successfully
- `privacy_report.json` says `status: pass`
- `run_manifest.json` says `status: pass`

## Phase 7 — Package Chat Results

Run:

```bash
path-term-kit package-results <project_dir>/project.yaml
```

Return `outputs/outputs.zip` plus a concise status summary.

If `package-results` fails, do not create a manual zip; fix the missing output first.

## Human Handoff Summary

Report exactly:

- project name
- input files scanned
- total rows
- term families
- generated output paths
- data gate status
- privacy status
- any warnings
