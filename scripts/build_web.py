#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build du site statique (GitHub Pages) — nouvelle interface (refonte).
Réutilise le parseur de generer_quiz.py pour lire les atlas, transforme les données
au format attendu par l'app (site_ui), et écrit un index.html autonome (images en
chemins relatifs, pleine résolution). Pas de sips → tourne en CI Linux.

  python3 scripts/build_web.py [dossier_sortie]   (défaut : _site)
"""
import os, sys, json, shutil, importlib.util

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(BASE, "scripts", name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

gq = _load("generer_quiz")
ui = _load("site_ui")

OUTDIR = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BASE, "_site")

def enc_web(p):
    b = os.path.basename(p)
    return "img/especes/" + b if (os.sep + "especes" + os.sep) in p else "img/quiz-extra/" + b

def conf_tips(stem):
    """Liste de textes 'ce qui tranche' pour les groupes de confusion contenant l'espèce."""
    return [g["tip"] for g in gq.CONF if stem in g["stems"]]

def to_web_data(species):
    out = []
    for s in species:
        imgs = [{"u": enc_web(p), "a": gq.aspect_of(p, s["stem"])} for p in s["paths"]]
        d = {
            "id": s["id"], "name": s["name"], "latin": s["latin"], "cat": s["cat"],
            "note": s["note"], "fields": s["fields"], "imgs": imgs,
            "conf": conf_tips(s["stem"]),
        }
        if "comestible" in s["fields"]:  # verdict du mode Oui/Non, calculé ici (cf. gq.is_edible)
            d["edible"] = gq.is_edible(s["fields"]["comestible"])
        out.append(d)
    return out

def assemble(data):
    js = ui.JS.replace("/*__DATA__*/", json.dumps(data, ensure_ascii=False))
    head = ('<meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">'
            '<title>Atlas des espèces</title><style>' + ui.CSS + '</style>')
    return ("<!doctype html><html lang=\"fr\"><head>" + head + "</head><body>"
            + ui.BODY + "<script>" + js + "</script></body></html>")

def main():
    species, seen = [], set()
    for path, cat in gq.ATLASES:
        got = gq.parse_atlas(path, cat, seen)
        print("%-38s : %d espèces" % (path, len(got)))
        species += got
    species = gq.apply_corrections(species)
    data = to_web_data(species)
    os.makedirs(OUTDIR, exist_ok=True)
    with open(os.path.join(OUTDIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(assemble(data))
    # copie uniquement les images réellement référencées
    refs = {im["u"] for s in data for im in s["imgs"]}
    copied = 0
    for rel in sorted(refs):
        srcp, dstp = os.path.join(BASE, rel), os.path.join(OUTDIR, rel)
        if os.path.exists(srcp):
            os.makedirs(os.path.dirname(dstp), exist_ok=True)
            shutil.copy2(srcp, dstp)
            copied += 1
        else:
            print("  ⚠ image absente :", rel)
    open(os.path.join(OUTDIR, ".nojekyll"), "w").close()
    sz = os.path.getsize(os.path.join(OUTDIR, "index.html")) / 1e6
    print("TOTAL : %d espèces, %d images -> %s (index.html %.1f Mo)" % (len(species), copied, OUTDIR, sz))

if __name__ == "__main__":
    main()
