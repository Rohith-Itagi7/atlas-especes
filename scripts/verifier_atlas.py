#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vérifie l'intégrité des atlas (utilisé par la CI sur chaque Pull Request, et lançable en local).
Contrôle, pour chaque ligne d'espèce :
  - le bon nombre de colonnes (= en-tête du tableau),
  - présence d'une vignette ![[...]] ET que le fichier existe dans img/especes,
  - nom (2e colonne) et nom latin non vides.
Contrôle aussi img/quiz-extra : chaque photo doit se rattacher à une espèce (et une seule)
par la convention <stem>-<aspect>-<n>.jpg.
Sort en erreur (code 1) si au moins un problème est trouvé.

  python3 scripts/verifier_atlas.py
"""
import os, sys, importlib.util

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("gq", os.path.join(BASE, "scripts", "generer_quiz.py"))
gq = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gq)

def verifier_photos_extra(stems):
    """Chaque photo de img/quiz-extra/ doit se rattacher à une espèce, et à une seule.

    Le rattachement suit la convention <stem>-<aspects>-<n>.jpg (cf. gq.extra_photos) :
    une photo qui n'y répond pas n'apparaît nulle part dans le site, et une photo
    réclamée par deux stems serait attribuée à une espèce qui n'est pas la sienne.
    """
    errs = []
    if not os.path.isdir(gq.EXTRA):
        return errs
    proprietaires = {}
    for stem in stems:
        for p in gq.extra_photos(stem):
            proprietaires.setdefault(os.path.basename(p), []).append(stem)
    for name in sorted(os.listdir(gq.EXTRA)):
        if name.startswith("_") or not name.lower().endswith(gq.PHOTO_EXT):
            continue  # _aspects.tsv, _COMMENT-NOMMER.txt
        owners = proprietaires.get(name, [])
        if not owners:
            errs.append("img/quiz-extra/%s : ne correspond à aucune espèce — attendu "
                        "<stem>-<aspect>-<n>.jpg, où <stem> est le nom de la vignette" % name)
        elif len(owners) > 1:
            errs.append("img/quiz-extra/%s : réclamée par %d espèces (%s) — renommer pour "
                        "lever l'ambiguïté" % (name, len(owners), ", ".join(sorted(owners))))
    return errs

def main():
    errs = []
    stems = set()
    for path, _cat in gq.ATLASES:
        full = os.path.join(BASE, path)
        if not os.path.exists(full):
            errs.append("%s : fichier introuvable" % path); continue
        lines = open(full, encoding="utf-8").read().split("\n")
        header = None
        for ln in lines:
            s = ln.lstrip()
            if s.startswith("|") and not s.startswith("| ![") and "latin" in ln.lower():
                header = [gq.hkey(c) for c in gq.cells_of(ln)]; break
        if not header:
            errs.append("%s : en-tête du tableau introuvable" % path); continue
        hlen = len(header)
        for i, ln in enumerate(lines, 1):
            if not ln.lstrip().startswith("| !["):
                continue
            cells = gq.cells_of(ln)
            if len(cells) != hlen:
                errs.append("%s:%d : %d colonnes au lieu de %d" % (path, i, len(cells), hlen))
            m = gq.IMG_RE.search(ln)
            if not m:
                errs.append("%s:%d : vignette ![[...]] manquante" % (path, i)); continue
            if not os.path.exists(os.path.join(gq.IMG, m.group(1))):
                errs.append("%s:%d : vignette absente → img/especes/%s" % (path, i, m.group(1)))
            stems.add(os.path.splitext(m.group(1))[0])
            row = {}
            for j, val in enumerate(cells):
                if j < len(header):
                    row[header[j]] = val
            if not row.get("name", "").strip():
                errs.append("%s:%d : nom (2e colonne) vide" % (path, i))
            if not row.get("latin", "").strip():
                errs.append("%s:%d : nom latin vide" % (path, i))
    errs += verifier_photos_extra(stems)
    if errs:
        print("❌ %d problème(s) détecté(s) :" % len(errs))
        for e in errs:
            print("  -", e)
        sys.exit(1)
    print("✅ Atlas valides.")

if __name__ == "__main__":
    main()
