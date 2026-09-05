#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Génère COUVERTURE.md : pour chaque espèce, quels aspects ont au moins une photo et lesquels
manquent. Sert à repérer où contribuer. Le vocabulaire des aspects vient de
scripts/atlas_data.py (source unique) ; les colonnes sont celles de l'objectif de couverture,
plus tout aspect qu'au moins une photo utilise déjà.

  python3 scripts/couverture.py            # écrit COUVERTURE.md à la racine du dépôt
"""
import os

import atlas_data

BASE = atlas_data.BASE

OUT = os.path.join(BASE, "COUVERTURE.md")
# Colonnes du tableau : les aspects visés par l'objectif de couverture, plus tout aspect
# qu'au moins une photo utilise déjà (ainsi « rameau » apparaîtra dès la première photo).
def aspects_du_tableau(species):
    utilises = set()
    for sp in species:
        utilises |= aspects_present(sp)
    return [(a.id, a.label) for a in atlas_data.ASPECTS if a.cible or a.id in utilises]
CATLABEL = {"ligneux": "Ligneux", "herbace": "Herbacées", "champignon": "Champignons",
            "faune": "Faune", "divers": "Espèces diverses"}
PLANT_CATS = ("ligneux", "herbace")  # seules catégories où les aspects ont du sens

def aspects_present(sp):
    got = set()
    for p in sp["paths"]:
        for a in atlas_data.aspect_of(p, sp["stem"]):
            got.add(a)
    got.discard(atlas_data.DIVERS)
    return got

def main():
    seen = set()
    species = []
    for path, cat in atlas_data.ATLASES:
        species += atlas_data.parse_atlas(path, cat, seen)
    species = atlas_data.apply_corrections(species)
    by_cat = {}
    for sp in species:
        by_cat.setdefault(sp["cat"], []).append(sp)
    aspects = aspects_du_tableau(species)

    lines = ["# Couverture photo par espèce", "",
             "> Généré par `scripts/couverture.py` — **ne pas éditer à la main**.",
             "> ✓ = au moins une photo de cet aspect · ✗ = manquant. Pour ajouter une photo,",
             "> voir [CONTRIBUTING.md](CONTRIBUTING.md).", ""]

    # résumé rapide (plantes seulement)
    plants = [sp for c in PLANT_CATS for sp in by_cat.get(c, [])]
    full = sum(1 for sp in plants if len(aspects_present(sp) & {k for k, _ in aspects}) == len(aspects))
    none = sum(1 for sp in plants if not aspects_present(sp))
    lines += ["## En bref",
              "- Plantes (ligneux + herbacées) : **%d**" % len(plants),
              "- …dont **%d** avec les %d aspects, **%d** sans aucun aspect taggé."
              % (full, len(aspects), none),
              "- Manques par aspect : " + " · ".join(
                  "%s %d" % (lab, sum(1 for sp in plants if k not in aspects_present(sp)))
                  for k, lab in aspects),
              ""]

    for cat in ("ligneux", "herbace", "champignon", "faune", "divers"):
        sps = sorted(by_cat.get(cat, []), key=lambda s: s["name"].lower())
        if not sps:
            continue
        lines.append("## %s (%d)" % (CATLABEL.get(cat, cat), len(sps)))
        lines.append("")
        if cat in PLANT_CATS:
            lines.append("| Espèce | 📷 | " + " | ".join(lab for _, lab in aspects) + " | À compléter |")
            lines.append("|---|--:|" + "|".join([":-:"] * len(aspects)) + "|---|")
            for sp in sps:
                got = aspects_present(sp)
                cells = ["✓" if k in got else "✗" for k, _ in aspects]
                manque = ", ".join(lab for k, lab in aspects if k not in got) or "— (complet)"
                lines.append("| %s | %d | %s | %s |" % (sp["name"], len(sp["paths"]), " | ".join(cells), manque))
        else:
            lines.append("_Aspects non applicables (une photo « l'organisme »)._")
            lines.append("")
            lines.append("| Espèce | 📷 |")
            lines.append("|---|--:|")
            for sp in sps:
                lines.append("| %s | %d |" % (sp["name"], len(sp["paths"])))
        lines.append("")

    open(OUT, "w", encoding="utf-8").write("\n".join(lines))
    print("écrit :", OUT, "(%d espèces)" % sum(len(v) for v in by_cat.values()))

if __name__ == "__main__":
    main()
