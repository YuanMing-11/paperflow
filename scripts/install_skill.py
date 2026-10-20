#!/usr/bin/env python3
"""Install this skill locally without replacing an existing installation."""
import argparse
import os
from pathlib import Path
import shutil
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skills-dir", type=Path,
                        default=Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "skills")
    args = parser.parse_args()
    source = Path(__file__).resolve().parent.parent
    dest = args.skills_dir.expanduser().resolve() / "paperflow"
    if dest == source or source in dest.parents:
        print("Installation destination must be outside the source package.", file=sys.stderr)
        return 2
    if dest.exists():
        print(f"Existing installation preserved: {dest}", file=sys.stderr)
        return 2
    try:
        shutil.copytree(source, dest, ignore=shutil.ignore_patterns(
            ".git", ".venv", "__pycache__", "*.pyc", "tests", ".github", "evaluation", ".DS_Store"))
    except OSError as exc:
        print(f"Installation failed: {exc}", file=sys.stderr)
        return 2
    print(f"Installed: {dest}")
    print("Use $paperflow in a new session if discovery has already been cached.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
