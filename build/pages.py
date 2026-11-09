#!/usr/bin/env python3
"""Find the PDF page where each chapter starts (via its heading text) -> out/pages.json."""
import sys, json, re, pathlib
from pypdf import PdfReader

ROOT = pathlib.Path(__file__).resolve().parent.parent
pdf = sys.argv[1]
chapters = json.loads((ROOT / "out/chapters.json").read_text())
r = PdfReader(pdf)
texts = [re.sub(r"\s+", " ", (pg.extract_text() or "")).upper() for pg in r.pages]
pages, start = {}, 0
for c in chapters:
    if c["front"]:
        continue
    key = re.sub(r"\s+", " ", c["title"].upper())[:24]
    for i in range(start, len(texts)):
        if "CONTENTS" not in texts[i][:60] and key in texts[i] and f"{c['num']:02d}" in texts[i][:400].replace(" ", ""):
            pages[c["id"]] = i + 1
            start = i
            break
(ROOT / "out/pages.json").write_text(json.dumps(pages, indent=1))
print(f"{len(r.pages)} pages;", " ".join(f"{k.split('-')[0]}:{v}" for k, v in pages.items()))
missing = [c["id"] for c in chapters if not c["front"] and c["id"] not in pages]
if missing:
    print("WARNING chapter start not found:", missing)
