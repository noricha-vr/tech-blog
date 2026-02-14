#!/usr/bin/env bash
set -euo pipefail

pip install -r requirements.txt
mkdocs build -f mkdocs.yml
mkdocs build -f mkdocs.en.yml
