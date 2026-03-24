from __future__ import annotations

import re
import sys
from pathlib import Path


FORBIDDEN_PATTERNS = (
    re.compile(r"https?://(?:www\.)?kaisha3\.com", re.IGNORECASE),
    re.compile(r"(?:href|src)=[\"']https?://(?:www\.)?kaisha3\.com", re.IGNORECASE),
)

TEXT_EXTENSIONS = {
    ".html",
    ".xml",
    ".json",
    ".js",
    ".css",
    ".txt",
    ".webmanifest",
}


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv
    if len(argv) != 2:
        print("usage: validate_site.py <site_dir>", file=sys.stderr)
        return 2

    site_dir = Path(argv[1])
    if not site_dir.exists():
        print(f"site directory not found: {site_dir}", file=sys.stderr)
        return 2

    violations: list[str] = []
    for path in site_dir.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if any(pattern.search(text) for pattern in FORBIDDEN_PATTERNS):
            violations.append(str(path))

    if violations:
        print("Forbidden kaisha3.com references found in built site:", file=sys.stderr)
        for violation in violations:
            print(f"- {violation}", file=sys.stderr)
        return 1

    print("Built site validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
