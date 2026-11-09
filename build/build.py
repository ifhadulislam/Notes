#!/usr/bin/env python3
"""Marrow-style notes builder.

content/*.md  --(custom markdown)-->  out/pathology.html  --(chromium)-->  out/Pathology_Revision_Notes.pdf

Inline:
  ==text==   pink key term
  %%text%%   dark-green "filled" addition
Blocks (may nest; close with a line ':::'):
  :::green [title]     filled (added) box
  :::mnemo [title]     mnemonic box
  :::note              'Note :' dotted heading block
  :::pearl [title]     exam pearl box
  :::flow [title]      vertical flowchart; one step per line; ' || ' splits a row into branches
  :::hflow             horizontal chain: items separated by ' > '
  :::tree              indented outline (2 spaces) -> arrow tree
  :::cols [n]          columns separated by a line '---'
  :::figs              one figure per line: src | caption [| width]
"""
import re, sys, html, json, pathlib, subprocess
import markdown

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
OUT = ROOT / "out"
IMG = ROOT / "img"

MD_EXT = ["tables", "attr_list", "md_in_html", "sane_lists"]


def inline(s):
    s = re.sub(r"==(.+?)==", r'<span class="k">\1</span>', s)
    s = re.sub(r"%%(.+?)%%", r'<span class="g">\1</span>', s)
    return s


def md(text):
    text = inline(text)
    h = markdown.markdown(text, extensions=MD_EXT, output_format="html5")
    return re.sub(r'<ol start="(\d+)">', lambda m: f'<ol start="{m.group(1)}" style="counter-reset:n {int(m.group(1)) - 1}">', h)


def md_inline(text):
    h = md(text).strip()
    if h.startswith("<p>") and h.endswith("</p>") and h.count("<p>") == 1:
        h = h[3:-4]
    return h


def split_blocks(lines):
    """Yield ('md', text) or ('block', kind, args, body_lines)."""
    i, buf = 0, []
    while i < len(lines):
        m = re.match(r"^:::(\w+)\s*(.*)$", lines[i])
        if m:
            if buf:
                yield ("md", "\n".join(buf)); buf = []
            kind, args = m.group(1), m.group(2).strip()
            depth, j, body = 1, i + 1, []
            while j < len(lines):
                if re.match(r"^:::\w+", lines[j]):
                    depth += 1
                elif lines[j].strip() == ":::":
                    depth -= 1
                    if depth == 0:
                        break
                body.append(lines[j]); j += 1
            yield ("block", kind, args, body)
            i = j + 1
        else:
            buf.append(lines[i]); i += 1
    if buf:
        yield ("md", "\n".join(buf))


def render(text):
    out = []
    for b in split_blocks(text.split("\n")):
        if b[0] == "md":
            out.append(md(b[1]))
        else:
            out.append(render_block(*b[1:]))
    return "\n".join(out)


def box(cls, tag, title, body):
    t = f'<div class="box-tag">{tag}{(" : " + md_inline(title)) if title else ""}</div>' if tag else ""
    return f'<div class="box {cls}">{t}{render(chr(10).join(body))}</div>'


def fig_html(line):
    parts = [p.strip() for p in line.split("|")]
    src, cap = parts[0], parts[1] if len(parts) > 1 else ""
    w = parts[2] if len(parts) > 2 else ""
    style = f' style="width:{w}"' if w else ""
    if src.endswith(".svg") and (IMG / src).exists():
        inner = (IMG / src).read_text()
        inner = re.sub(r"<\?xml.*?\?>", "", inner)
        media = f'<div class="svgwrap">{inner}</div>'
    else:
        media = f'<img src="../img/{src}" alt="{html.escape(cap)}">'
    return f'<figure{style}>{media}<figcaption>{md_inline(cap)}</figcaption></figure>'


def render_block(kind, args, body):
    if kind == "green":
        return box("filled", "Filled", args, body)
    if kind == "mnemo":
        return box("mnemo", "Mnemonic", args, body)
    if kind == "pearl":
        return box("pearl", "Exam pearl", args, body)
    if kind == "note":
        return f'<div class="note"><h3 class="dotted">Note :</h3>{render(chr(10).join(body))}</div>'
    if kind == "flow":
        rows = []
        for ln in [l for l in body if l.strip()]:
            cells = [c.strip() for c in ln.split("||")]
            row = "".join(f'<div class="step">{md_inline(c)}</div>' for c in cells)
            rows.append(f'<div class="frow{" branch" if len(cells) > 1 else ""}">{row}</div>')
        title = f'<div class="flow-title">{md_inline(args)}</div>' if args else ""
        return f'<div class="flow">{title}{"<div class=\"farrow\">↓</div>".join(rows)}</div>'
    if kind == "hflow":
        items = [i.strip() for i in " ".join(l.strip() for l in body).split(" > ")]
        return '<div class="hflow">' + '<span class="harrow">⟶</span>'.join(
            f'<span class="hstep">{md_inline(i)}</span>' for i in items) + "</div>"
    if kind == "tree":
        return tree_html([l for l in body if l.strip()])
    if kind == "cols":
        cols, cur = [], []
        for l in body:
            if l.strip() == "---":
                cols.append(cur); cur = []
            else:
                cur.append(l)
        cols.append(cur)
        n = len(cols)
        return f'<div class="cols" style="grid-template-columns:repeat({n},1fr)">' + "".join(
            f'<div class="col">{render(chr(10).join(c))}</div>' for c in cols) + "</div>"
    if kind == "figs":
        figs = [fig_html(l) for l in body if l.strip()]
        return f'<div class="figs n{len(figs)}">' + "".join(figs) + "</div>"
    raise ValueError(f"unknown block {kind}")


def tree_html(lines):
    def parse(idx, level):
        nodes = []
        while idx < len(lines):
            ind = (len(lines[idx]) - len(lines[idx].lstrip())) // 2
            if ind < level:
                break
            if ind > level:
                nodes[-1]["kids"], idx = parse(idx, ind)
                continue
            nodes.append({"t": lines[idx].strip(), "kids": []}); idx += 1
        return nodes, idx

    roots, _ = parse(0, 0)

    def leaf_list(nodes):
        if not nodes:
            return ""
        return "<ul>" + "".join(f"<li>{md_inline(n['t'])}{leaf_list(n['kids'])}</li>" for n in nodes) + "</ul>"

    def node(n, top=False):
        lab = f'<span class="node">{md_inline(n["t"])}</span>'
        if not n["kids"]:
            return lab
        # only the root branches; deeper levels become bullet lists (readable, no cramping)
        if top:
            kids = "".join(f'<div class="kid">{node(k)}</div>' for k in n["kids"])
            e = 50 / len(n["kids"])
            return f'{lab}<div class="kids" style="--bar-l:{e:.2f}%;--bar-r:{e:.2f}%">{kids}</div>'
        return lab + leaf_list(n["kids"])

    return '<div class="tree">' + "".join(node(r, True) for r in roots) + "</div>"


def build():
    files = sorted(CONTENT.glob("*.md"))
    chapters, body = [], []
    for f in files:
        src = f.read_text()
        m = re.search(r"^# (.+)$", src, re.M)
        title = m.group(1).strip() if m else f.stem
        cid = f.stem
        num = len([c for c in chapters if not c["front"]]) + 1
        front = f.stem.startswith("00")
        src = src.replace(m.group(0), "", 1) if m else src
        h2s = re.findall(r"^## (.+)$", src, re.M)
        chapters.append({"id": cid, "title": title, "front": front, "num": num, "h2": h2s})
        head = "" if front else f'<h1 class="chapter" id="{cid}"><span class="cnum">{num:02d}</span>{html.escape(title)}</h1>'
        body.append(f'<section class="chap{" front" if front else ""}">{head}{render(src)}</section>')
    (OUT).mkdir(exist_ok=True)
    pages = {}
    pf = OUT / "pages.json"
    if pf.exists():
        pages = json.loads(pf.read_text())
    toc = '<section class="chap toc"><h1 class="chapter">Contents</h1><ol class="toc-list">' + "".join(
        f'<li><a href="#{c["id"]}"><span class="tn">{c["num"]:02d}</span><span class="tt">{html.escape(c["title"])}</span>'
        f'<span class="tp">{pages.get(c["id"], "")}</span></a></li>' for c in chapters if not c["front"]) + "</ol></section>"
    # front matter (cover) first, then TOC, then chapters
    fronts = [b for b, c in zip(body, chapters) if c["front"]]
    rest = [b for b, c in zip(body, chapters) if not c["front"]]
    doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Pathology Revision Notes</title>
<link rel="stylesheet" href="../marrow/marrow.css"><link rel="stylesheet" href="../marrow/print.css">
</head><body class="book">{''.join(fronts)}{toc}{''.join(rest)}</body></html>"""
    (OUT / "pathology.html").write_text(doc)
    (OUT / "chapters.json").write_text(json.dumps(chapters, indent=1))
    print("html ok", len(chapters), "files")


if __name__ == "__main__":
    build()
