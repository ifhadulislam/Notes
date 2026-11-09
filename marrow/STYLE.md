# @marrow — handwritten revision-notes style

When the user writes **@marrow**, produce notes in this exact style. It is taken from their Noteful screenshots of handwritten-style pathology notes. All source branding is removed: no header or footer lines, no "Active space", no video timestamps, no page tabs. Only the content stays.

## Page
- Paper : cream `#FFFEF2` (whole page, margins included). A4 for the PDF.
- Margins : ~13 mm top, right and bottom; ~16 mm left. The content column fills the width.
- No running headers or footers.

## Typography
| Element | Font | Colour | Size (A4 PDF) |
|---|---|---|---|
| Chapter title | Crimson Pro 500, UPPERCASE, centred | black `#1A1919` | 21 px, small grey chapter number above |
| Section heading (e.g. "Emphysema") | Crimson Pro 600 | black | 16.5 px, grey 1.5 px rule under the full width |
| Sub-heading ("Types :", "Note :") | Coming Soon (handwriting) | black | body size, grey underline (dotted for "Note :") |
| Body text | **Coming Soon** (handwriting) | navy `#28377C` | 12.7 px / line-height 1.47 |
| Key terms, buzzwords | same | pink `#C62E7C` | — |
| Added high-yield points ("Filled") | same | dark green `#1B6E3C`, in a pale green box with a "Filled" tag | — |
| Figure captions, diagram labels | Coming Soon | black | ~12 px |

- Headings end with " :" in the handwritten parts ("Types :", "Lined by :").
- Bullets are small navy dots. Sub-points use "–". Numbered lists ("1.", "2.") are used for causes, risk factors and criteria, one item per line.
- Arrows : "→" and "⟶" in navy. Flowcharts are rounded navy-outlined boxes with ↓ arrows. Trees branch from a centred label with thin grey lines and arrowheads.
- Tables : thin grey borders, a pale lavender header row, navy text, first column black.
- Boxes : mnemonic = dashed pink border; exam pearl = pale yellow with a gold left bar; filled = pale green with a green left bar.

## Files
- `marrow/marrow.css` — screen styles and colour tokens.
- `marrow/print.css` — the A4 book layer (sizes, boxes, flowcharts, tables).
- `build/build.py` — markdown with blocks → HTML. Inline `==pink==` and `%%green%%`. Blocks : `:::green`, `:::mnemo`, `:::pearl`, `:::note`, `:::flow`, `:::hflow`, `:::tree`, `:::cols`, `:::figs`.
- `build/make.sh` — two-pass PDF build (TOC page numbers, bookmarks, cream background).
