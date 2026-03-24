#!/usr/bin/env bash
set -euo pipefail

python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
rm -rf site
mkdocs build -f mkdocs.yml
mkdocs build -f mkdocs.en.yml
python3 scripts/validate_site.py site
