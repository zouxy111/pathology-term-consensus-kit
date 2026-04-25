# Pathology Term Consensus Kit

Reusable SOP execution toolkit for pathology subspecialty terminology standardization.

The kit turns a terminology source table plus historical report exports into:

- full-scan data gate logs
- evidence workbook
- director questionnaire workbook
- meeting deck outline in Markdown and HTML
- privacy QA report
- run manifest for traceability

It is designed for repeatable agent execution: deterministic Python code does the fragile work,
while the bundled Codex skill and weak-model runbook keep the agent on a narrow, auditable path.

## Quick Start

```bash
git clone <your-repo-url>
cd pathology-term-consensus-kit
python scripts/bootstrap_project.py --out my_project
uv venv
uv pip install -e ".[dev]"
```

Edit `my_project/project.yaml`, put your data under `my_project/data/`, then run:

```bash
path-term-kit validate my_project/project.yaml
path-term-kit scan my_project/project.yaml
path-term-kit run my_project/project.yaml
path-term-kit qa my_project/project.yaml
```

For chat-based OpenClaw reuse, send the public GitHub URL plus report/term attachments and ask it
to follow `docs/OPENCLAW_ONE_SHOT_PROMPT.md`.

Run the fake example:

```bash
path-term-kit run examples/fake_subspecialty/project.yaml
```

If the CLI is already installed, you can also initialize a project with:

```bash
path-term-kit init --out my_project
```

## What You Provide

1. A terminology table with the required columns documented in `docs/INITIALIZATION.md`.
2. Historical report CSV/XLSX files.
3. A `project.yaml` mapping your real column names to:
   - company/lab field
   - final report text field
   - optional context fields
4. Target-organ include/exclude keywords.
5. Target company/lab list in decision order.

## Safety Defaults

- No real patient data or copyrighted terminology source content is shipped in this repo.
- No local machine paths are required or stored in the repository.
- The pipeline reads all rows; it is not a sampling workflow.
- Missing fields, unreadable files, row-count mismatch, zero accepted target segments, or privacy
  findings in generated outputs fail the run.
- PPTX generation is intentionally optional; the stable v1 output is a deck-ready Markdown/HTML
  outline plus Excel workbooks.

## Repository Map

- `src/path_term_kit/` — CLI and deterministic SOP pipeline.
- `templates/project.yaml` — reusable config template.
- `examples/fake_subspecialty/` — public-safe fake data.
- `docs/SOP.md` — reusable workflow.
- `docs/OPENCLAW_CHAT_HANDOFF.md` — prompt and gate rules for cloud OpenClaw chat reuse.
- `docs/OPENCLAW_ONE_SHOT_PROMPT.md` — shortest reusable prompt for non-technical users.
- `docs/ATTACHMENT_CONTRACT.md` — attachment naming and data handoff contract.
- `docs/WEAK_MODEL_RUNBOOK.md` — guardrails for weaker agents.
- `skills/pathology-terminology-standardization/` — Codex skill wrapper.
