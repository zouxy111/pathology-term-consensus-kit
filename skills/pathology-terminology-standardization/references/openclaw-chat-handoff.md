# OpenClaw Chat Handoff

When the user sends this repo link plus chat attachments:

1. Clone and install the repo.
2. Save attachments into a temporary workspace outside Git.
3. Run `path-term-kit inspect-data <attachment_dir>`.
4. Run `path-term-kit inspect-terms <term_file>`.
5. Ask the user to confirm company field, report text field, context fields, include terms, and exclude terms.
6. Generate `project.yaml` only after confirmation.
7. Run `validate`, `scan`, `run`, `qa`, and `package-results`.
8. Return a concise summary and `outputs.zip`.

Never guess field mapping. Never continue after data gate or privacy failure.
