#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vérifie l'intégrité des atlas (utilisé par la CI sur chaque Pull Request, et lançable en local).
Contrôle, pour chaque ligne d'espèce :
  - le bon nombre de colonnes (= en-tête du tableau),
  - présence d'une vignette ![[...]] ET que le fichier existe dans img/especes,
  - nom (2e colonne) et nom latin non vides.
Sort en erreur (code 1) si au moins un problème est trouvé.

  python3 scripts/verifier_atlas.py
"""
import os, sys, importlib.util

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("gq", os.path.join(BASE, "scripts", "generer_quiz.py"))
gq = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gq)

def main():
    errs = []
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
            row = {}
            for j, val in enumerate(cells):
                if j < len(header):
                    row[header[j]] = val
            if not row.get("name", "").strip():
                errs.append("%s:%d : nom (2e colonne) vide" % (path, i))
            if not row.get("latin", "").strip():
                errs.append("%s:%d : nom latin vide" % (path, i))
    if errs:
        print("❌ %d problème(s) détecté(s) :" % len(errs))
        for e in errs:
            print("  -", e)
        sys.exit(1)
    print("✅ Atlas valides.")

if __name__ == "__main__":
    main()
