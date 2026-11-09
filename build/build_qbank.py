#!/usr/bin/env python3
"""qbank/*.txt  ->  out/Pathology_MCQs.html, out/Pathology_Flashcards.html (self-contained, images inlined)."""
import re, json, base64, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
QB, IMG, OUT = ROOT / "qbank", ROOT / "img", ROOT / "out"
chapters = {c["id"][:2]: c["title"] for c in json.loads((OUT / "chapters.json").read_text()) if not c["front"]}

_img_cache = {}


def data_uri(rel):
    if rel in _img_cache:
        return _img_cache[rel]
    if rel.startswith("gen/") and rel.endswith(".svg"):
        rel_png = "gen-png/" + rel[4:-4] + ".png"
        p = IMG / rel_png
    else:
        p = IMG / rel
    if not p.exists():
        raise SystemExit(f"missing image {rel}")
    mime = "image/svg+xml" if p.suffix == ".svg" else "image/png" if p.suffix == ".png" else "image/jpeg"
    _img_cache[rel] = f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()
    return _img_cache[rel]


def parse_mcq():
    qs, ch = [], None
    for f in sorted(QB.glob("mcq-*.txt")):
        blocks = re.split(r"\n\s*\n", f.read_text())
        for b in blocks:
            lines = [l for l in b.strip().split("\n") if l.strip()]
            if lines and lines[0].startswith("@ch"):
                ch = lines[0].split()[1]
                lines = lines[1:]
            if not lines:
                continue
            q = {"ch": ch, "opts": [], "img": None}
            for l in lines:
                if l.startswith("Q:"):
                    q["q"] = l[2:].strip()
                elif re.match(r"^[A-D]\)", l):
                    q["opts"].append(l[2:].strip())
                elif l.startswith("ANS:"):
                    q["ans"] = "ABCD".index(l[4:].strip())
                elif l.startswith("EX:"):
                    q["ex"] = l[3:].strip()
                elif l.startswith("IMG:"):
                    q["img"] = data_uri(l[4:].strip())
            assert "q" in q and len(q["opts"]) == 4 and "ans" in q, (f.name, lines[:2])
            qs.append(q)
    return qs


def parse_cards():
    cards, ch = [], None
    for f in sorted(QB.glob("cards-*.txt")):
        for l in f.read_text().split("\n"):
            l = l.strip()
            if l.startswith("@ch"):
                ch = l.split()[1]
            elif "::" in l:
                a, b = [x.strip() for x in l.split("::", 1)]
                cards.append({"ch": ch, "f": a, "b": b})
    return cards


HEAD = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Coming+Soon&family=Crimson+Pro:wght@500;600&display=swap" rel="stylesheet">
<style>
:root{{--navy:#28377C;--pink:#C62E7C;--black:#1A1919;--green:#1B6E3C;--rule:#9E9F9E;--paper:#FFFEF2;--card:#FFFFFF;--bad:#B3261E;--okbg:#EEF6EE;--badbg:#FBECEC;--hand:"Coming Soon","Patrick Hand","Comic Neue",cursive;--serif:"Crimson Pro",Georgia,serif}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--navy:#AEB9F2;--pink:#F07AB6;--black:#F2F0E8;--green:#7BD69C;--rule:#6E6F6E;--paper:#1B1C22;--card:#24252D;--bad:#FF8A80;--okbg:#1F3326;--badbg:#3A2224}}}}
:root[data-theme="dark"]{{--navy:#AEB9F2;--pink:#F07AB6;--black:#F2F0E8;--green:#7BD69C;--rule:#6E6F6E;--paper:#1B1C22;--card:#24252D;--bad:#FF8A80;--okbg:#1F3326;--badbg:#3A2224}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--paper);color:var(--navy);font-family:var(--hand);font-size:17px;line-height:1.55}}
.wrap{{max-width:820px;margin:0 auto;padding:20px 16px 60px}}
h1{{font-family:var(--serif);font-weight:600;color:var(--black);font-size:26px;letter-spacing:.03em;margin:6px 0 2px;text-transform:uppercase}}
.sub{{color:var(--rule);margin-bottom:14px}}
.bar{{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:10px 0 16px;padding-bottom:10px;border-bottom:1.5px solid var(--rule)}}
select,button{{font-family:var(--hand);font-size:15px;color:var(--navy);background:var(--card);border:1.4px solid var(--navy);border-radius:8px;padding:6px 12px;cursor:pointer}}
button.primary{{background:var(--navy);color:var(--paper)}}
button:disabled{{opacity:.45;cursor:default}}
.pill{{border:1.2px solid var(--rule);border-radius:999px;padding:2px 10px;color:var(--black);font-size:14px}}
.k{{color:var(--pink)}}
img.q{{display:block;max-width:100%;max-height:340px;margin:10px auto;border-radius:6px;background:#FFFEF2}}
</style></head><body><div class="wrap">"""


def mcq_html(qs):
    data = json.dumps({"qs": qs, "ch": chapters}, ensure_ascii=False)
    return HEAD.format(title="Pathology MCQs") + """
<h1>Pathology — Question Bank</h1>
<div class="sub">NEET PG / INI-CET style · <span id="total"></span> questions · tap an option to check</div>
<div class="bar">
  <select id="chap"></select>
  <select id="mode"><option value="seq">In order</option><option value="rand">Shuffled</option></select>
  <button id="start" class="primary">Start</button>
  <span class="pill" id="score">Score 0/0</span>
  <button id="wrongOnly">Review wrong</button>
  <button id="theme" title="Toggle theme">◐</button>
</div>
<div id="qbox"></div>
<style>
.card{background:var(--card);border:1.4px solid var(--rule);border-radius:12px;padding:16px 18px;box-shadow:0 1px 4px rgba(0,0,0,.06)}
.meta{display:flex;justify-content:space-between;color:var(--rule);font-size:14px;margin-bottom:6px;gap:8px;flex-wrap:wrap}
.stem{color:var(--black);font-size:18px;margin-bottom:10px}
.opt{display:block;width:100%;text-align:left;margin:7px 0;padding:9px 12px;border-radius:9px;border:1.4px solid var(--rule);background:var(--paper);color:var(--navy);font-size:16px}
.opt:hover:not(:disabled){border-color:var(--navy)}
.opt:disabled{opacity:1;cursor:default}
.opt.ok{border-color:var(--green);background:var(--okbg);color:var(--green)}
.opt.bad{border-color:var(--bad);background:var(--badbg);color:var(--bad)}
.ex{margin-top:12px;padding:10px 12px;border-left:3px solid var(--green);background:var(--okbg);color:var(--green);border-radius:6px;display:none}
.ex b{color:var(--black);font-weight:400}
.nav{display:flex;justify-content:space-between;margin-top:14px;gap:8px}
.done{text-align:center;padding:30px 10px}
.done .big{font-family:var(--serif);font-size:42px;color:var(--black)}
</style>
<script>
const D=""" + data + """;
const $=s=>document.querySelector(s);
let list=[],i=0,answered={},wrongOnly=false;
function store(k,v){try{localStorage.setItem(k,JSON.stringify(v))}catch(e){}}
function load(k,d){try{const v=localStorage.getItem(k);return v?JSON.parse(v):d}catch(e){return d}}
let theme=load('mcq-theme',null); if(theme) document.documentElement.dataset.theme=theme;
$('#theme').onclick=()=>{const t=document.documentElement.dataset.theme==='dark'?'light':'dark';document.documentElement.dataset.theme=t;store('mcq-theme',t)};
$('#total').textContent=D.qs.length;
const sel=$('#chap');
sel.innerHTML='<option value="all">All chapters ('+D.qs.length+')</option>'+Object.keys(D.ch).map(c=>{const n=D.qs.filter(q=>q.ch===c).length;return n?`<option value="${c}">${c} · ${D.ch[c]} (${n})</option>`:''}).join('');
sel.value=load('mcq-chap','all');
function build(){
  const c=sel.value; store('mcq-chap',c);
  list=D.qs.map((q,k)=>({...q,k})).filter(q=>c==='all'||q.ch===c);
  if(wrongOnly) list=list.filter(q=>answered[q.k]!==undefined&&answered[q.k]!==q.ans);
  if($('#mode').value==='rand') for(let a=list.length-1;a>0;a--){const b=Math.floor(Math.random()*(a+1));[list[a],list[b]]=[list[b],list[a]]}
  i=0; render();
}
function score(){const ks=list.map(q=>q.k).filter(k=>answered[k]!==undefined);const ok=ks.filter(k=>answered[k]===D.qs[k].ans).length;$('#score').textContent=`Score ${ok}/${ks.length}`;return [ok,ks.length]}
function render(){
  const box=$('#qbox'); score();
  if(!list.length){box.innerHTML='<div class="card done">No questions here yet. '+(wrongOnly?'You have no wrong answers in this set.':'')+'</div>';return}
  if(i>=list.length){const [ok,n]=score();box.innerHTML=`<div class="card done"><div class="big">${ok} / ${n}</div><p>${n?Math.round(100*ok/n):0}% correct in this set.</p><button class="primary" onclick="build()">Restart</button></div>`;return}
  const q=list[i];const a=answered[q.k];
  box.innerHTML=`<div class="card"><div class="meta"><span>Q ${i+1} of ${list.length}</span><span>${q.ch} · ${D.ch[q.ch]||''}</span></div>
  <div class="stem">${q.q}</div>${q.img?`<img class="q" src="${q.img}" alt="Question image">`:''}
  ${q.opts.map((o,j)=>`<button class="opt" data-j="${j}">${'ABCD'[j]}. ${o}</button>`).join('')}
  <div class="ex" id="ex"><b>Answer : ${'ABCD'[q.ans]}.</b> ${q.ex||''}</div>
  <div class="nav"><button id="prev" ${i?'':'disabled'}>← Previous</button><button id="next" class="primary">${i===list.length-1?'Finish':'Next →'}</button></div></div>`;
  box.querySelectorAll('.opt').forEach(b=>b.onclick=()=>{if(answered[q.k]!==undefined)return;answered[q.k]=+b.dataset.j;store('mcq-ans',answered);show(q)});
  $('#prev').onclick=()=>{i--;render()}; $('#next').onclick=()=>{i++;render();window.scrollTo(0,0)};
  if(a!==undefined) show(q);
}
function show(q){const a=answered[q.k];document.querySelectorAll('.opt').forEach(b=>{const j=+b.dataset.j;b.disabled=true;if(j===q.ans)b.classList.add('ok');else if(j===a)b.classList.add('bad')});$('#ex').style.display='block';score()}
answered=load('mcq-ans',{});
$('#start').onclick=()=>{wrongOnly=false;$('#wrongOnly').textContent='Review wrong';build()};
$('#wrongOnly').onclick=()=>{wrongOnly=!wrongOnly;$('#wrongOnly').textContent=wrongOnly?'Show all':'Review wrong';build()};
sel.onchange=build; $('#mode').onchange=build;
document.addEventListener('keydown',e=>{if(!list[i])return;const k=e.key.toUpperCase();if('ABCD'.includes(k)&&k.length===1){const b=document.querySelector(`.opt[data-j="${'ABCD'.indexOf(k)}"]`);b&&b.click()}if(e.key==='ArrowRight')$('#next')?.click();if(e.key==='ArrowLeft')$('#prev')?.click()});
build();
</script></div></body></html>"""


def cards_html(cards):
    data = json.dumps({"cards": cards, "ch": chapters}, ensure_ascii=False)
    return HEAD.format(title="Pathology Flashcards") + """
<h1>Pathology — Flashcards</h1>
<div class="sub"><span id="total"></span> cards · tap the card (or press Space) to flip</div>
<div class="bar">
  <select id="chap"></select>
  <button id="shuffle">Shuffle</button>
  <button id="due">Only "again" cards</button>
  <span class="pill" id="prog"></span>
  <button id="theme" title="Toggle theme">◐</button>
</div>
<style>
.flash{perspective:1200px;margin:8px 0 14px;cursor:pointer;user-select:none}
.inner{position:relative;min-height:260px;transition:transform .45s;transform-style:preserve-3d}
.flash.flipped .inner{transform:rotateY(180deg)}
.face{position:absolute;inset:0;backface-visibility:hidden;-webkit-backface-visibility:hidden;border-radius:14px;border:1.4px solid var(--rule);background:var(--card);display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;padding:22px;box-shadow:0 1px 5px rgba(0,0,0,.07)}
.face .tag{position:absolute;top:10px;left:14px;font-size:13px;color:var(--rule)}
.front .t{font-size:22px;color:var(--black)}
.back{transform:rotateY(180deg);border-color:var(--green)}
.back .t{font-size:20px;color:var(--pink)}
.row{display:flex;gap:8px;justify-content:center;flex-wrap:wrap}
.row button{min-width:120px}
button.again{border-color:var(--bad);color:var(--bad)}
button.know{border-color:var(--green);color:var(--green)}
@media (prefers-reduced-motion:reduce){.inner{transition:none}}
</style>
<div class="flash" id="flash"><div class="inner"><div class="face front"><span class="tag" id="tagF"></span><div class="t" id="front"></div></div><div class="face back"><span class="tag" id="tagB"></span><div class="t" id="back"></div></div></div></div>
<div class="row"><button id="prev">← Prev</button><button class="again" id="again">Again</button><button class="know" id="know">Know it</button><button id="next">Next →</button></div>
<script>
const D=""" + data + """;
const $=s=>document.querySelector(s);
function store(k,v){try{localStorage.setItem(k,JSON.stringify(v))}catch(e){}}
function load(k,d){try{const v=localStorage.getItem(k);return v?JSON.parse(v):d}catch(e){return d}}
let theme=load('fc-theme',null); if(theme) document.documentElement.dataset.theme=theme;
$('#theme').onclick=()=>{const t=document.documentElement.dataset.theme==='dark'?'light':'dark';document.documentElement.dataset.theme=t;store('fc-theme',t)};
let marks=load('fc-marks',{}),list=[],i=0,dueOnly=false;
$('#total').textContent=D.cards.length;
const sel=$('#chap');
sel.innerHTML='<option value="all">All chapters ('+D.cards.length+')</option>'+Object.keys(D.ch).map(c=>{const n=D.cards.filter(x=>x.ch===c).length;return n?`<option value="${c}">${c} · ${D.ch[c]} (${n})</option>`:''}).join('');
sel.value=load('fc-chap','all');
function build(shuffle){store('fc-chap',sel.value);list=D.cards.map((c,k)=>({...c,k})).filter(c=>(sel.value==='all'||c.ch===sel.value)&&(!dueOnly||marks[c.k]==='again'));
 if(shuffle)for(let a=list.length-1;a>0;a--){const b=Math.floor(Math.random()*(a+1));[list[a],list[b]]=[list[b],list[a]]}i=0;render()}
function render(){$('#flash').classList.remove('flipped');const known=list.filter(c=>marks[c.k]==='know').length;
 $('#prog').textContent=list.length?`${i+1}/${list.length} · known ${known}`:'0 cards';
 if(!list.length){$('#front').textContent=dueOnly?'No "again" cards — well done!':'No cards';$('#back').textContent='';return}
 const c=list[i];$('#front').textContent=c.f;$('#back').textContent=c.b;$('#tagF').textContent=$('#tagB').textContent=c.ch+' · '+(D.ch[c.ch]||'')+(marks[c.k]?'  ['+marks[c.k]+']':'')}
function go(d){if(!list.length)return;i=(i+d+list.length)%list.length;render()}
function mark(m){if(!list.length)return;marks[list[i].k]=m;store('fc-marks',marks);go(1)}
$('#flash').onclick=()=>$('#flash').classList.toggle('flipped');
$('#prev').onclick=()=>go(-1);$('#next').onclick=()=>go(1);$('#again').onclick=()=>mark('again');$('#know').onclick=()=>mark('know');
$('#shuffle').onclick=()=>build(true);$('#due').onclick=()=>{dueOnly=!dueOnly;$('#due').textContent=dueOnly?'All cards':'Only "again" cards';build(false)};
sel.onchange=()=>build(false);
document.addEventListener('keydown',e=>{if(e.key===' '){e.preventDefault();$('#flash').click()}if(e.key==='ArrowRight')go(1);if(e.key==='ArrowLeft')go(-1);if(e.key==='1')mark('again');if(e.key==='2')mark('know')});
build(false);
</script></div></body></html>"""


if __name__ == "__main__":
    qs, cards = parse_mcq(), parse_cards()
    (OUT / "Pathology_MCQs.html").write_text(mcq_html(qs))
    (OUT / "Pathology_Flashcards.html").write_text(cards_html(cards))
    from collections import Counter
    print("MCQs", len(qs), dict(sorted(Counter(q["ch"] for q in qs).items())))
    print("Cards", len(cards), dict(sorted(Counter(c["ch"] for c in cards).items())))
    print("images inlined", len(_img_cache))
