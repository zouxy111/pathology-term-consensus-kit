# Runbook

1. Create a project skeleton with `python scripts/bootstrap_project.py --out <project>`.
2. Put terminology and report files under `<project>/data`.
3. Install the runner with `uv venv && uv pip install -e .`, then run `path-term-kit doctor`.
4. Edit `<project>/project.yaml`.
5. Run `validate`, then `scan`, then `run`, then `qa`.
6. Hand off only if both data gate and privacy QA pass.

Never modify raw input files. Never continue after a failed data gate.
