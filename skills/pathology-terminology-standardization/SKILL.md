---
name: pathology-terminology-standardization
description: Use when standardizing pathology subspecialty terminology from a terminology source table and historical report exports, generating evidence workbooks, director questionnaires, deck outlines, data-gate logs, and privacy QA through the path-term-kit CLI.
---

# Pathology Terminology Standardization

Use this skill for pathology subspecialty terminology consensus projects.

## Required Process

1. Read `references/runbook.md` before executing.
2. Confirm the project has a terminology table and historical report files.
3. For chat attachments, run inspection before configuring:

```bash
path-term-kit inspect-data <attachment_dir>
path-term-kit inspect-terms <term_file>
```

4. Ask the user to confirm field mapping and target include/exclude terms.
5. Use `path-term-kit create-project` after field confirmation; do not hand-write YAML unless necessary.
6. Run the CLI in order:

```bash
path-term-kit validate <project>/project.yaml
path-term-kit scan <project>/project.yaml
path-term-kit run <project>/project.yaml
path-term-kit qa <project>/project.yaml
path-term-kit package-results <project>/project.yaml
```

7. Stop if any command fails. Do not generate director materials after a data-gate failure.

## Non-Negotiables

- Full scan only; no sampling-only conclusions.
- Authority terms and local evidence must stay separate.
- Output only aggregate statistics and de-identified snippets.
- Do not expose names, phone numbers, IDs, hospitals, barcodes, or patient numbers.
- Keep unresolved terms in a disagreement list; do not force a standard name.
- Chat handoff details: read `references/openclaw-chat-handoff.md`.

## When More Detail Is Needed

- Configuration fields: read `references/config-guide.md`.
- Weaker model guardrails: read `references/weak-model-checklist.md`.
