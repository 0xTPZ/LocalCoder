"""Auditoria heurística de segredos antes de commit.

O scanner é um gate auxiliar, não substitui revisão humana do diff e do destino remoto.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


PATTERNS = (
    ("private-key", re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----")),
    ("github-token", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b")),
    ("aws-access-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("generic-secret-assignment", re.compile(
        r"(?i)\b(?:api[_-]?key|access[_-]?token|password|secret)\b\s*[:=]\s*[\"'][^\"']{12,}[\"']"
    )),
)

SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", "var"}
SKIP_SUFFIXES = {".gguf", ".ggml", ".safetensors", ".bin", ".exe", ".dll", ".pdb"}


def iter_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in SKIP_SUFFIXES:
            continue
        yield path


def scan(root: Path) -> list[str]:
    findings: list[str] = []
    for path in iter_files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for line_number, line in enumerate(text.splitlines(), start=1):
            for label, pattern in PATTERNS:
                if pattern.search(line):
                    findings.append(f"{path.relative_to(root)}:{line_number}: {label}")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default=Path(__file__).parents[1], type=Path)
    args = parser.parse_args()
    root = args.path.resolve()
    findings = scan(root)
    if findings:
        print("FAIL: possible secret patterns found")
        print("\n".join(findings))
        return 1
    print(f"PASS: no high-signal secret patterns found under {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
