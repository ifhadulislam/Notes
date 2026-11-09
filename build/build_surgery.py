#!/usr/bin/env python3
"""qbank/surgery/*.txt -> out/Surgery_QBank.html (self-contained app) + out/Surgery_QBank.xlsx.

Block format (blank line between questions):
  @topic Name          (applies until the next @topic)
  Q: stem
  A) .. B) .. C) .. D) ..
  ANS: B
  TAGS: PQ, Clinical   (PQ = high-probability repeat theme; second tag = question type)
  EX: explanation      (**bold** allowed)
  OTH: A: why wrong | C: why wrong     (optional)
  PEARL: extra high-yield point        (optional)

Usage: build_surgery.py [fragment_out.html]   (optional body-only copy for publishing)
"""
import re, sys, json, random, hashlib, pathlib, collections
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC, OUT = ROOT / "qbank" / "surgery", ROOT / "out"
KEYS = ("Q:", "ANS:", "TAGS:", "EX:", "OTH:", "PEARL:")


ORDERED = re.compile(r"^(less than|more than|type|stage|grade|class|level|zone|[ivx]+\b|c?\d|red$|yellow$|green$|black$)", re.I)


def shuffle(q):
    """Spread the answer key evenly. Options that form a natural sequence stay in their written order."""
    if all(ORDERED.match(o) for o in q["o"]):
        return
    order = list(range(4))
    random.Random(int(hashlib.md5(q["q"].encode()).hexdigest(), 16)).shuffle(order)
    q["o"] = [q["o"][i] for i in order]
    q["a"] = order.index(q["a"])
    q["oth"] = {order.index(k): v for k, v in q["oth"].items()}


def parse():
    qs, topic = [], None
    for f in sorted(SRC.glob("*.txt")):
        for b in re.split(r"\n\s*\n", f.read_text()):
            lines = [l.strip() for l in b.strip().split("\n") if l.strip()]
            if lines and lines[0].startswith("@topic"):
                topic = lines[0][6:].strip()
                lines = lines[1:]
            if not lines:
                continue
            q = {"t": topic, "o": [], "tags": [], "ex": "", "oth": {}, "pearl": ""}
            for l in lines:
                if l.startswith("Q:"):
                    q["q"] = l[2:].strip()
                elif re.match(r"^[A-D]\) ", l):
                    q["o"].append(l[3:].strip())
                elif l.startswith("ANS:"):
                    q["a"] = "ABCD".index(l[4:].strip())
                elif l.startswith("TAGS:"):
                    q["tags"] = [x.strip() for x in l[5:].split(",") if x.strip()]
                elif l.startswith("EX:"):
                    q["ex"] = l[3:].strip()
                elif l.startswith("OTH:"):
                    for part in l[4:].split(" | "):
                        m = re.match(r"^\s*([A-D]):\s*(.+)$", part)
                        assert m, (f.name, part)
                        q["oth"]["ABCD".index(m.group(1))] = m.group(2).strip()
                elif l.startswith("PEARL:"):
                    q["pearl"] = l[6:].strip()
                else:
                    raise SystemExit(f"{f.name}: unparsed line: {l[:70]}")
            where = (f.name, q.get("q", lines[0])[:60])
            assert topic and "q" in q and len(q["o"]) == 4 and "a" in q and q["ex"], where
            assert q["a"] not in q["oth"], ("OTH explains the correct option", where)
            assert q["ex"].count("**") % 2 == 0 and q["pearl"].count("**") % 2 == 0, where
            shuffle(q)
            q["pq"] = "PQ" in q["tags"]
            q["tags"] = [t for t in q["tags"] if t != "PQ"]
            q["id"] = f"SQ{len(qs) + 1:04d}"
            qs.append(q)
    stems = collections.Counter(q["q"] for q in qs)
    dup = [s for s, n in stems.items() if n > 1]
    assert not dup, dup
    return qs


def plain(s):
    return s.replace("**", "")


def write_xlsx(qs):
    wb = Workbook()
    ws = wb.active
    ws.title = "MCQs"
    head = ["ID", "Topic", "PQ", "Type", "Question", "A", "B", "C", "D", "Answer", "Answer text",
            "Explanation", "Other options", "Pearl"]
    ws.append(head)
    for q in qs:
        oth = "\n".join(f"{'ABCD'[int(k)]}: {plain(v)}" for k, v in sorted(q["oth"].items()))
        ws.append([q["id"], q["t"], "PQ" if q["pq"] else "", ", ".join(q["tags"]), q["q"], *q["o"],
                   "ABCD"[q["a"]], q["o"][q["a"]], plain(q["ex"]), oth, plain(q["pearl"])])
    widths = [9, 24, 6, 16, 60, 28, 28, 28, 28, 8, 28, 80, 60, 60]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    fill = PatternFill("solid", fgColor="4F46D8")
    for c in ws[1]:
        c.font, c.fill = Font(bold=True, color="FFFFFF"), fill
        c.alignment = Alignment(vertical="center")
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical="top")
    ws.freeze_panes = "E2"
    ws.auto_filter.ref = ws.dimensions

    s = wb.create_sheet("Summary")
    s.append(["Topic", "Questions", "PQ"])
    by = collections.OrderedDict()
    for q in qs:
        n = by.setdefault(q["t"], [0, 0])
        n[0] += 1
        n[1] += q["pq"]
    for t, (n, p) in by.items():
        s.append([t, n, p])
    last = s.max_row
    s.append(["Total", f"=SUM(B2:B{last})", f"=SUM(C2:C{last})"])
    for c in list(s[1]) + list(s[s.max_row]):
        c.font = Font(bold=True)
    s.column_dimensions["A"].width = 30
    s.append([])
    s.append(["PQ = high-probability theme tested repeatedly in NEET PG / INI-CET. It is an editorial "
              "judgement, not a verbatim recalled question."])
    wb.save(OUT / "Surgery_QBank.xlsx")
    return by


def main():
    qs = parse()
    by = write_xlsx(qs)
    data = json.dumps(qs, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    frag = (ROOT / "build" / "surgery_app.html").read_text().replace("/*__DATA__*/[]", data)
    doc = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
           '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
           "<style>html,body{margin:0}[hidden]{display:none!important}</style></head><body>"
           + frag + "</body></html>")
    (OUT / "Surgery_QBank.html").write_text(doc)
    if len(sys.argv) > 1:
        pathlib.Path(sys.argv[1]).write_text(frag)
    print(f"{len(qs)} questions, {sum(q['pq'] for q in qs)} PQ, {len(by)} topics")
    print("answer key spread:", dict(sorted(collections.Counter("ABCD"[q["a"]] for q in qs).items())))
    for t, (n, p) in by.items():
        print(f"  {t:28s} {n:3d}  PQ {p}")


if __name__ == "__main__":
    main()
