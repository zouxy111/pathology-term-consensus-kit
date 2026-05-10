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

## I only use chat / cloud OpenClaw

If you use cloud OpenClaw through Feishu, Telegram, WeChat, or another chat client, you do **not**
need to install anything locally.

Start here:

- [`CHAT-ONLY-START-HERE.md`](CHAT-ONLY-START-HERE.md) — copy one prompt, upload report data and a terminology table, then let OpenClaw inspect the attachments and ask you to confirm fields.
- [`docs/OPENCLAW_ONE_SHOT_PROMPT.md`](docs/OPENCLAW_ONE_SHOT_PROMPT.md) — shortest prompt for chat-only reuse.
- [`docs/ATTACHMENT_CONTRACT.md`](docs/ATTACHMENT_CONTRACT.md) — what files to upload and how OpenClaw should handle them.

Expected chat flow:

1. User sends the GitHub URL and uploads report/term attachments.
2. OpenClaw clones this repo and runs `inspect-data` / `inspect-terms`.
3. OpenClaw asks the user to confirm field mapping and include/exclude terms.
4. OpenClaw runs the deterministic CLI pipeline.
5. OpenClaw returns a short summary plus `outputs.zip`.

## Developer / local CLI quick start

```bash
git clone <your-repo-url>
cd pathology-term-consensus-kit
python scripts/bootstrap_project.py --out my_project
uv venv
uv pip install -e .
path-term-kit doctor
```

Edit `my_project/project.yaml`, put your data under `my_project/data/`, then run:

```bash
path-term-kit validate my_project/project.yaml
path-term-kit scan my_project/project.yaml
path-term-kit run my_project/project.yaml
path-term-kit qa my_project/project.yaml
```

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
- `CHAT-ONLY-START-HERE.md` — top-level entry for non-technical chat-only OpenClaw users.
- `docs/SOP.md` — reusable workflow.
- `docs/OPENCLAW_CHAT_HANDOFF.md` — prompt and gate rules for cloud OpenClaw chat reuse.
- `docs/OPENCLAW_ONE_SHOT_PROMPT.md` — shortest reusable prompt for non-technical users.
- `docs/ATTACHMENT_CONTRACT.md` — attachment naming and data handoff contract.
- `docs/WEAK_MODEL_RUNBOOK.md` — guardrails for weaker agents.
- `skills/pathology-terminology-standardization/` — Codex skill wrapper.
