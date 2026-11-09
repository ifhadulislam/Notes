#!/usr/bin/env python3
"""Lay every PDF page on a cream 'paper' background (Chromium leaves @page margins white)."""
import sys, io
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

src = sys.argv[1]
buf = io.BytesIO()
c = canvas.Canvas(buf, pagesize=A4)
c.setFillColorRGB(1, 254/255, 242/255)
c.rect(0, 0, A4[0], A4[1], stroke=0, fill=1)
c.save()
r = PdfReader(src)
w = PdfWriter()
for pg in r.pages:
    paper = PdfReader(io.BytesIO(buf.getvalue())).pages[0]
    paper.merge_page(pg)
    w.add_page(paper)
w.clone_reader_document_root  # keep simple
# carry outline (bookmarks) over
def copy_outline(items, parent=None):
    last = None
    for it in items:
        if isinstance(it, list):
            copy_outline(it, last)
        else:
            try:
                idx = r.get_destination_page_number(it)
                last = w.add_outline_item(it.title, idx, parent=parent)
            except Exception:
                pass
copy_outline(r.outline)
w.compress_identical_objects()
with open(src, "wb") as f:
    w.write(f)
print("bg ok", len(r.pages))
