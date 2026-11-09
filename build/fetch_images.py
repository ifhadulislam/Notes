#!/usr/bin/env python3
"""Fetch freely licensed images from Wikimedia Commons.

Input lines:  key | search query            (auto-pick first bitmap result)
          or  key | File:Exact_title.jpg    (exact file)
Writes img/web/<key>.jpg and records author/license in img/web/credits.json.
Skips keys that already exist.
"""
import sys, json, time, re, pathlib, urllib.parse, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "img/web"; OUT.mkdir(parents=True, exist_ok=True)
CRED = OUT / "credits.json"
UA = {"User-Agent": "PathologyNotesBuilder/1.0 (https://github.com/ifhadulislam/notes)"}
API = "https://commons.wikimedia.org/w/api.php?"


def get(url, raw=False):
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=40) as r:
                data = r.read()
            return data if raw else json.loads(data)
        except Exception as e:
            print("  retry", attempt, e, file=sys.stderr); time.sleep(45 * (attempt + 1))
    raise RuntimeError("failed " + url)


def strip(h):
    return re.sub(r"<[^>]+>", "", h or "").strip()


def main(lines):
    credits = json.loads(CRED.read_text()) if CRED.exists() else {}
    for ln in lines:
        if not ln.strip() or ln.startswith("#"):
            continue
        key, q = [x.strip() for x in ln.split("|", 1)]
        try:
            fetch_one(key, q, credits)
        except Exception as e:
            print("FAIL", key, e, flush=True)


def fetch_one(key, q, credits):
    if True:
        if (OUT / f"{key}.jpg").exists() and key in credits:
            return
        if q.startswith("File:"):
            title = q
        else:
            res = get(API + urllib.parse.urlencode({"action": "query", "list": "search", "srsearch": q,
                                                    "srnamespace": 6, "format": "json", "srlimit": 8}))
            hits = [h["title"] for h in res["query"]["search"] if re.search(r"\.(jpe?g|png)$", h["title"], re.I)]
            if not hits:
                print("NO HIT", key, q); return
            title = hits[0]
        time.sleep(2.5)
        info = get(API + urllib.parse.urlencode({"action": "query", "titles": title, "prop": "imageinfo",
                                                 "iiprop": "url|extmetadata", "iiurlwidth": 900, "format": "json"}))
        page = next(iter(info["query"]["pages"].values()))
        if "imageinfo" not in page:
            print("NO INFO", key, title); return
        ii = page["imageinfo"][0]
        url = ii["url"]
        time.sleep(2.5)
        img = get(url, raw=True)
        from PIL import Image
        import io
        im = Image.open(io.BytesIO(img)).convert("RGB")
        im.thumbnail((900, 900))
        im.save(OUT / f"{key}.jpg", quality=84)
        md = ii.get("extmetadata", {})
        credits[key] = {"title": title, "artist": strip(md.get("Artist", {}).get("value")),
                        "license": strip(md.get("LicenseShortName", {}).get("value")),
                        "url": "https://commons.wikimedia.org/wiki/" + urllib.parse.quote(title.replace(" ", "_"))}
        CRED.write_text(json.dumps(credits, indent=1))
        print("ok", key, "<-", title, "|", credits[key]["license"])
        time.sleep(3)


if __name__ == "__main__":
    main(open(sys.argv[1]).read().splitlines())
