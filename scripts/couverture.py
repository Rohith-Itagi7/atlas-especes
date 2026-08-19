#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Génère COUVERTURE.md : pour chaque espèce, quels aspects (feuille/écorce/fruit/fleur/port)
ont au moins une photo, et lesquels manquent. Sert à repérer où contribuer.

  python3 scripts/couverture.py            # écrit COUVERTURE.md à la racine du dépôt
"""
import os, importlib.util

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("gq", os.path.join(BASE, "scripts", "generer_quiz.py"))
gq = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gq)

OUT = os.path.join(BASE, "COUVERTURE.md")
ASPECTS = [("feuille", "Feuille"), ("ecorce", "Écorce"), ("fruit", "Fruit"), ("fleur", "Fleur"), ("port", "Port")]
CATLABEL = {"ligneux": "Ligneux", "herbace": "Herbacées", "champignon": "Champignons",
            "faune": "Faune", "divers": "Espèces diverses"}
PLANT_CATS = ("ligneux", "herbace")  # seules catégories où les aspects ont du sens

def aspects_present(sp):
    got = set()
    for p in sp["paths"]:
        for a in gq.aspect_of(p, sp["stem"]):
            got.add(a)
    got.discard("divers")
    return got

def main():
    seen = set()
    species = []
    for path, cat in gq.ATLASES:
        species += gq.parse_atlas(path, cat, seen)
    species = gq.apply_corrections(species)
    by_cat = {}
    for sp in species:
        by_cat.setdefault(sp["cat"], []).append(sp)

    lines = ["# Couverture photo par espèce", "",
             "> Généré par `scripts/couverture.py` — **ne pas éditer à la main**.",
             "> ✓ = au moins une photo de cet aspect · ✗ = manquant. Pour ajouter une photo,",
             "> voir [CONTRIBUTING.md](CONTRIBUTING.md).", ""]

    # résumé rapide (plantes seulement)
    plants = [sp for c in PLANT_CATS for sp in by_cat.get(c, [])]
    full = sum(1 for sp in plants if len(aspects_present(sp)) == len(ASPECTS))
    none = sum(1 for sp in plants if not aspects_present(sp))
    lines += ["## En bref",
              "- Plantes (ligneux + herbacées) : **%d**" % len(plants),
              "- …dont **%d** avec les 5 aspects, **%d** sans aucun aspect taggé." % (full, none),
              "- Manques par aspect : " + " · ".join(
                  "%s %d" % (lab, sum(1 for sp in plants if k not in aspects_present(sp)))
                  for k, lab in ASPECTS),
              ""]

    for cat in ("ligneux", "herbace", "champignon", "faune", "divers"):
        sps = sorted(by_cat.get(cat, []), key=lambda s: s["name"].lower())
        if not sps:
            continue
        lines.append("## %s (%d)" % (CATLABEL.get(cat, cat), len(sps)))
        lines.append("")
        if cat in PLANT_CATS:
            lines.append("| Espèce | 📷 | " + " | ".join(lab for _, lab in ASPECTS) + " | À compléter |")
            lines.append("|---|--:|" + "|".join([":-:"] * len(ASPECTS)) + "|---|")
            for sp in sps:
                got = aspects_present(sp)
                cells = ["✓" if k in got else "✗" for k, _ in ASPECTS]
                manque = ", ".join(lab for k, lab in ASPECTS if k not in got) or "— (complet)"
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
