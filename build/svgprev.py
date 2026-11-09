#!/usr/bin/env python3
"""Render SVG(s) to PNG with the handwriting font for visual checking: svgprev.py out.png a.svg b.svg"""
import sys, pathlib, subprocess, json
out, files = sys.argv[1], sys.argv[2:]
html = '<html><head><link href="https://fonts.googleapis.com/css2?family=Coming+Soon&display=block" rel="stylesheet"></head><body style="background:#FFFEF2;margin:10px;width:760px">'
for f in files:
    html += f'<div style="border:1px solid #ccc;margin:6px 0">{pathlib.Path(f).read_text()}</div>'
html += '</body></html>'
p = pathlib.Path('/tmp/claude-0/-home-user-Notes/b5d11bb7-3ed0-5dae-89e7-19b8720d1be6/scratchpad/svgprev.html'); p.write_text(html)
js = f"""const {{chromium}}=require('playwright');(async()=>{{const b=await chromium.launch();const pg=await b.newPage({{viewport:{{width:790,height:600}}}});
await pg.goto('file://{p}');await pg.evaluate(()=>document.fonts.ready);await pg.waitForTimeout(500);await pg.screenshot({{path:'{out}',fullPage:true}});await b.close()}})()"""
subprocess.run(["node", "-e", js], check=True)
