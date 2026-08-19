#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build du site statique (GitHub Pages).
Réutilise le parseur + l'app de generer_quiz.py, mais encode les images en
CHEMINS RELATIFS (fichiers servis tels quels, pleine résolution) au lieu de base64.
=> aucune limite de taille, pas de sips, tourne sur Linux (CI GitHub Actions).

  python3 scripts/build_web.py [dossier_sortie]   (défaut : _site)
"""
import os, sys, shutil, importlib.util

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("gq", os.path.join(BASE, "scripts", "generer_quiz.py"))
gq = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gq)

OUTDIR = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BASE, "_site")

def enc_web(p):
    b = os.path.basename(p)
    return "img/especes/" + b if (os.sep + "especes" + os.sep) in p else "img/quiz-extra/" + b

def main():
    species, seen = [], set()
    for path, cat in gq.ATLASES:
        got = gq.parse_atlas(path, cat, seen)
        print("%-38s : %d espèces" % (path, len(got)))
        species += got
    data = gq.to_data(species, enc_web, cap=None)
    html = gq.assemble(data, True)
    os.makedirs(OUTDIR, exist_ok=True)
    with open(os.path.join(OUTDIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
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
    # petit fichier .nojekyll pour que GitHub Pages serve tout tel quel
    open(os.path.join(OUTDIR, ".nojekyll"), "w").close()
    print("TOTAL : %d espèces, %d images copiées -> %s" % (len(species), copied, OUTDIR))

if __name__ == "__main__":
    main()
