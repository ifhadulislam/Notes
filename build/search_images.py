#!/usr/bin/env python3
"""List top Commons file hits per query:  python3 search_images.py "query1" "query2" ..."""
import sys, json, time, urllib.parse, urllib.request, re
UA = {"User-Agent": "PathologyNotesBuilder/1.0 (https://github.com/ifhadulislam/notes)"}
for q in sys.argv[1:]:
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(
        {"action": "query", "list": "search", "srsearch": q, "srnamespace": 6, "format": "json", "srlimit": 7})
    r = None
    for a in range(5):
        try:
            r = json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read()); break
        except Exception as e:
            time.sleep(10 * (a + 1))
    if r is None:
        print("## FAIL", q); continue
    hits = [h["title"] for h in r["query"]["search"] if re.search(r"\.(jpe?g|png)$", h["title"], re.I)]
    print("##", q); [print("  ", h) for h in hits[:6]]
    time.sleep(3)
