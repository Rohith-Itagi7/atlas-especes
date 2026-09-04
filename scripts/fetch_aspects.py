#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Télécharge des photos par ASPECT depuis Wikimedia Commons pour LIGNEUX et HERBACÉES.
  ligneux   : écorce(bark), feuille(leaf), fruit(fruit)
  herbacées : feuille(leaf), fleur(flower), fruit(fruit)   (pas d'écorce)
Fichiers : img/quiz-extra/<stem>-<aspect>-1.jpg (réduits sips 420px q70).
Idempotent (saute un aspect déjà présent). Relancer generer_quiz.py ensuite.
"""
import re, os, json, time, glob, subprocess, urllib.request, urllib.parse, urllib.error

import atlas_data

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXTRA = os.path.join(BASE, "img", "quiz-extra")
os.makedirs(EXTRA, exist_ok=True)
IMG_RE = re.compile(r"!\[\[(?:[^\]\|]*/)?([^\]\|]+\.(?:jpg|jpeg|png))", re.I)
UA = "ForestryQuiz/1.0 (personal educational use)"
ATLASES = [("Espèces - référence.md", "ligneux"), ("Espèces herbacées - référence.md", "herbace")]
# Quels aspects chercher, et sous quel mot-clé anglais : les identifiants et les termes
# viennent du vocabulaire partagé (scripts/atlas_data.py). Renommer un aspect là-bas fait
# échouer ce script à l'import plutôt que de le laisser télécharger n'importe quoi.
_TERME = {a.id: a.terme_en for a in atlas_data.ASPECTS}
ASP_LIG = [(i, _TERME[i]) for i in ("ecorce", "feuille", "fruit")]
ASP_HERB = [(i, _TERME[i]) for i in ("feuille", "fleur", "fruit")]
BAD = ("map", "range", "distribution", "locator", "icon", "logo", "diagram", "chart", "signature", "illustration")

def species_all():
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
            out.append((os.path.splitext(m.group(1))[0], cells[2], cat))
    return out

def clean_latin(l):
    l = l.split("/")[0].strip()
    l = re.sub(r"\bsp\.?$", "", l).strip()
    return " ".join(l.split()[:2])

def commons_photo(latin, kw):
    q = urllib.parse.urlencode({"action": "query", "generator": "search",
        "gsrsearch": '%s %s' % (latin, kw), "gsrnamespace": "6", "gsrlimit": "8",
        "prop": "imageinfo", "iiprop": "url|mime", "iiurlwidth": "700", "format": "json"})
    req = urllib.request.Request("https://commons.wikimedia.org/w/api.php?" + q, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.load(r)
    pages = list(d.get("query", {}).get("pages", {}).values())
    pages.sort(key=lambda p: p.get("index", 99))
    for p in pages:
        title = p.get("title", "").lower()
        if any(b in title for b in BAD) or title.endswith(".svg"):
            continue
        ii = p.get("imageinfo", [{}])[0]
        if ii.get("mime") in ("image/jpeg", "image/png") and ii.get("thumburl"):
            return ii["thumburl"]
    return None

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

def with_retry(fn, *a):
    for attempt in range(5):
        try:
            return fn(*a)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(8 + attempt * 8); continue
            raise
    return None

def main():
    sp = species_all()
    print("%d espèces (ligneux + herbacées)" % len(sp))
    ok = 0
    for i, (stem, latin, cat) in enumerate(sp):
        cl = clean_latin(latin)
        aspects = ASP_LIG if cat == "ligneux" else ASP_HERB
        got = []
        for asp, kw in aspects:
            if glob.glob(os.path.join(EXTRA, "%s-%s*" % (stem, asp))):
                got.append(asp + "=déjà"); continue
            dest = os.path.join(EXTRA, "%s-%s-1.jpg" % (stem, asp))
            try:
                src = with_retry(commons_photo, cl, kw)
                if not src:
                    got.append(asp + "=∅"); time.sleep(2.5); continue
                dl(src, dest); got.append(asp + "=OK"); ok += 1
            except Exception:
                got.append(asp + "=err")
            time.sleep(2.5)
        print("[%d/%d] %-22s (%s) : %s" % (i + 1, len(sp), stem, cl, "  ".join(got)))
    print("=== terminé : %d nouvelles photos d'aspect ===" % ok)

if __name__ == "__main__":
    main()
