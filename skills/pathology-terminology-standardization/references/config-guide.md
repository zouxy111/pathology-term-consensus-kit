# Config Guide

`project.yaml` controls every project-specific decision.

Required mappings:

- `company_field`: source column for company/lab.
- `report_text_field`: source column for final report text.
- `context_fields`: optional source columns for human context only.

Target filtering:

- `include_terms`: target organ/subspecialty terms.
- `exclude_terms`: non-target organ/subspecialty terms.
- `text_split_pattern`: regex for splitting report text into segments.

Terminology catalog:

- `patterns` accepts `|` separated terms.
- Prefix a pattern with `regex:` only when regex is necessary.
- Keep CAP/WHO/guideline source text out of public repos unless rights are clear.

