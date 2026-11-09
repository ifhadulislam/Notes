#!/usr/bin/env bash
# Two-pass build: render, locate chapter start pages, fill TOC page numbers, render again.
set -euo pipefail
cd "$(dirname "$0")/.."
rm -f out/pages.json
python3 build/build.py
node build/pdf.js out/_pass1.pdf
python3 build/pages.py out/_pass1.pdf
python3 build/build.py
node build/pdf.js
python3 build/pages.py out/Pathology_Revision_Notes.pdf --check
python3 build/bg.py out/Pathology_Revision_Notes.pdf
rm -f out/_pass1.pdf
