#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Télécharge des photos supplémentaires (iNaturalist) pour chaque espèce des atlas,
les réduit (≤420 px, JPEG q70) et les range dans img/quiz-extra/<stem>-N.jpg.
Chaque image téléchargée est créditée dans img/CREDITS.tsv (auteur, licence, page).
Idempotent : saute les espèces qui ont déjà des extras. Relancer le générateur ensuite.

  python3 scripts/fetch_photos.py                        tout l'atlas
  python3 scripts/fetch_photos.py --lot lots/lot-1.txt   un lot (cf. #17)
  python3 scripts/fetch_photos.py --especes cigue,arum   quelques espèces
"""
import re, os, sys, json, time, glob, subprocess, urllib.request, urllib.parse

import atlas_data
import credits

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(BASE, "img", "especes")
EXTRA = os.path.join(BASE, "img", "quiz-extra")
os.makedirs(EXTRA, exist_ok=True)
ATLASES = [("Espèces - référence.md", "ligneux"), ("Espèces herbacées - référence.md", "herbace")]
IMG_RE = re.compile(r"!\[\[(?:[^\]\|]*/)?([^\]\|]+\.(?:jpg|jpeg|png))", re.I)
UA = "ForestryQuiz/1.0 (personal educational use)"
N_EXTRA = 2

def species_list():
    out = []
    for path, cat in ATLASES:
        for line in open(os.path.join(BASE, path), encoding="utf-8"):
            if not line.lstrip().startswith("| !["):
                continue
            m = IMG_RE.search(line)
            if not m:
                continue
            cells = [c.strip().replace("\x01", "|") for c in line.replace("\\|", "\x01").split("|")][1:-1]
            if len(cells) < 3:
                continue
            stem = os.path.splitext(m.group(1))[0]
            latin = cells[2]
            out.append((stem, latin))
    return out

def clean_latin(l):
    l = l.split("/")[0].strip()
    l = re.sub(r"\bsp\.?$", "", l).strip()
    return " ".join(l.split()[:2])

def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def taxon_photos(latin):
    q = urllib.parse.quote(clean_latin(latin))
    d = get_json("https://api.inaturalist.org/v1/taxa?q=%s&per_page=1" % q)
    res = d.get("results", [])
    if not res:
        return []
    tid = res[0]["id"]
    time.sleep(1.0)
    d2 = get_json("https://api.inaturalist.org/v1/taxa/%d" % tid)
    r2 = d2.get("results", [])
    if not r2:
        return []
    urls = []
    for tp in r2[0].get("taxon_photos", []):
        p = tp.get("photo", {})
        u = p.get("medium_url") or p.get("url")
        if u:
            # le crédit accompagne l'URL : iNaturalist est surtout du CC-BY / CC-BY-NC
            urls.append((u, credits.credit_inaturalist(p)))
    return urls

def dl(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        buf = r.read()
    if len(buf) < 1500:
        raise IOError("too small")
    open(dest + ".orig", "wb").write(buf)
    subprocess.run(["sips", "-Z", "420", "-s", "format", "jpeg", "-s", "formatOptions", "70",
                    dest + ".orig", "--out", dest], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.remove(dest + ".orig")

def choisir(sp, argv):
    """Restreint la liste au lot demandé par --lot / --especes (cf. atlas_data)."""
    arg = None
    for i, a in enumerate(argv):
        if a in ("--lot", "--especes") and i + 1 < len(argv):
            arg = argv[i + 1]
    if not arg:
        return sp
    demandes = atlas_data.lire_lot(arg)
    retenus, inconnus = atlas_data.selection([x[0] for x in sp], demandes)
    if inconnus:
        raise SystemExit("stem(s) inconnu(s) dans le lot : %s" % ", ".join(inconnus))
    ordre = {s: i for i, s in enumerate(retenus)}
    return sorted([x for x in sp if x[0] in ordre], key=lambda x: ordre[x[0]])

def main():
    sp = choisir(species_list(), sys.argv[1:])
    ok = skip = fail = 0
    for i, (stem, latin) in enumerate(sp):
        if glob.glob(os.path.join(EXTRA, stem + "-*")):
            skip += 1; continue
        try:
            urls = taxon_photos(latin)[:N_EXTRA]
            n = 0
            for j, (u, credit) in enumerate(urls, 1):
                try:
                    dest = os.path.join(EXTRA, "%s-%d.jpg" % (stem, j))
                    dl(u, dest); credits.noter(dest, **credit); n += 1
                    time.sleep(0.5)
                except Exception as e:
                    print("   img fail %s-%d: %s" % (stem, j, e))
            print("[%d/%d] %-22s (%s) : %d photo(s)" % (i + 1, len(sp), stem, clean_latin(latin), n))
            ok += 1 if n else 0
            if not n:
                fail += 1
        except Exception as e:
            print("[%d/%d] %-22s : ÉCHEC %s" % (i + 1, len(sp), stem, e)); fail += 1
        time.sleep(1.3)
    print("=== fait : %d espèces avec extras, %d sautées, %d sans photo ===" % (ok, skip, fail))

if __name__ == "__main__":
    main()
