#!/usr/bin/env python3
"""Create a project skeleton before installing path-term-kit.

This script uses only the Python standard library so a weaker agent can initialize
`project.yaml`, `data/`, and `outputs/` before dependency installation.
"""

from __future__ import annotations

import argparse
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, help="Output project directory.")
    args = parser.parse_args()
    out_dir = Path(args.out).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "data").mkdir(exist_ok=True)
    (out_dir / "outputs").mkdir(exist_ok=True)
    template = REPO_ROOT / "templates" / "project.yaml"
    (out_dir / "project.yaml").write_text(template.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Initialized project workspace: {out_dir}")
    print(f"Edit config: {out_dir / 'project.yaml'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

