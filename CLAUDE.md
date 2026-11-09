# Notes repo — instructions for Claude

## @marrow
When the user writes **@marrow**, write notes in the "marrow" handwritten revision style. The full spec is in `marrow/STYLE.md`. In short:
- Cream paper `#FFFEF2`. Handwriting font **Coming Soon** in navy `#28377C` for the body. **Pink `#C62E7C`** for key terms. **Dark green `#1B6E3C`** "Filled" boxes for added high-yield points. Black serif (**Crimson Pro**) for chapter and section headings, with a grey rule under section headings.
- Handwritten sub-headings end with " :" and are underlined in grey. Use bullets, numbered lists (one cause or risk factor per line), arrow flowcharts, trees, tables, dashed-pink mnemonic boxes and yellow exam-pearl boxes.
- Never include source branding or references (no "Marrow", headers, footers, timestamps or "active space"). Content only.
- Build with the existing pipeline. Write `content/NN-topic.md` using the custom blocks documented in `build/build.py`, then run `build/make.sh`. The PDF goes to `out/`. Diagrams are SVGs in `img/gen/` (handwriting-font labels); check them with `build/svgprev.py`.

## Layout of this repo
- `content/` — chapter sources (custom markdown).
- `img/` — `resp/` (crops from the user's own pages), `gen/` (hand-made labelled SVGs), `gen-png/` (rasterised for the HTML apps).
- `qbank/` — MCQs (`mcq-*.txt`) and flashcards (`cards-*.txt`). `build/build_qbank.py` compiles them to `out/Pathology_MCQs.html` and `out/Pathology_Flashcards.html` (self-contained).
- `out/` — built deliverables.
