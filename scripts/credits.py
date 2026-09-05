#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Crédits des images : qui a pris la photo, sous quelle licence, et où la retrouver.

La plupart des licences CC (CC-BY, CC-BY-SA) **exigent** de nommer l'auteur et la licence :
un crédit global « Wikimedia & iNaturalist » ne suffit pas. Ce fichier trace image par image.

  img/CREDITS.tsv    en-tête « fichier⇥source⇥auteur⇥licence⇥url »

  python3 scripts/credits.py            # rapport : connus, inconnus, manquants, morts
  python3 scripts/credits.py --init     # ajoute une ligne « inconnu » par image sans crédit

Les scripts de récupération (fetch_aspects.py, fetch_photos.py) appellent noter() au moment
du téléchargement : toute nouvelle image arrive donc créditée.
"""
import html
import os
import re
import sys

import atlas_data

BASE = atlas_data.BASE
CREDITS = os.path.join(BASE, "img", "CREDITS.tsv")
CHAMPS = ("fichier", "source", "auteur", "licence", "url")
INCONNU = "inconnu"
ENTETE = "\t".join(CHAMPS)
PREAMBULE = [
    "# Crédits des images — une ligne par fichier de img/especes/ et img/quiz-extra/.",
    "# Colonnes : fichier, source, auteur, licence, url (page d'origine).",
    "# « inconnu » = crédit à retrouver. Les images ont été récupérées par",
    "# scripts/fetch_aspects.py (Wikimedia Commons) et scripts/fetch_photos.py (iNaturalist),",
    "# qui ne notaient pas l'auteur à l'époque et ont recompressé les fichiers : la provenance",
    "# d'une image ancienne ne peut plus être retrouvée automatiquement, elle se complète à la",
    "# main. Toute nouvelle image est créditée automatiquement au téléchargement.",
]


def dossiers():
    return (("especes", atlas_data.IMG), ("quiz-extra", atlas_data.EXTRA))


def images_du_depot():
    """Noms de fichiers de toutes les images du dépôt (les deux dossiers)."""
    noms = set()
    for _nom, d in dossiers():
        if not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            if not f.startswith("_") and f.lower().endswith(atlas_data.PHOTO_EXT):
                noms.add(f)
    return noms


def charger():
    """{fichier: {source, auteur, licence, url}} tel qu'écrit dans img/CREDITS.tsv."""
    out = {}
    if not os.path.exists(CREDITS):
        return out
    for ln in open(CREDITS, encoding="utf-8"):
        ln = ln.rstrip("\n")
        if not ln or ln.startswith("#"):
            continue
        cells = ln.split("\t")
        if cells[0].strip().lower() == "fichier":
            continue
        cells += [""] * (len(CHAMPS) - len(cells))
        out[cells[0].strip()] = dict(zip(CHAMPS[1:], [c.strip() for c in cells[1:5]]))
    return out


def ecrire(entrees):
    """Réécrit img/CREDITS.tsv, trié, préambule compris."""
    with open(CREDITS, "w", encoding="utf-8") as fh:
        fh.write("\n".join(PREAMBULE) + "\n" + ENTETE + "\n")
        for f in sorted(entrees):
            e = entrees[f]
            fh.write("\t".join([f] + [(e.get(k) or INCONNU) for k in CHAMPS[1:]]) + "\n")


def noter(fichier, source, auteur=None, licence=None, url=None):
    """Enregistre (ou met à jour) le crédit d'une image. Appelé par les fetchers."""
    entrees = charger()
    entrees[os.path.basename(fichier)] = {
        "source": source or INCONNU, "auteur": auteur or INCONNU,
        "licence": licence or INCONNU, "url": url or INCONNU}
    ecrire(entrees)


def connu(entree):
    """Un crédit est exploitable si l'auteur ET la licence sont renseignés."""
    if not entree:
        return False
    return (entree.get("auteur", INCONNU) != INCONNU
            and entree.get("licence", INCONNU) != INCONNU)


def texte(entree):
    """Ligne d'attribution affichable, ou '' si le crédit n'est pas exploitable."""
    if not connu(entree):
        return ""
    t = "© %s — %s" % (entree["auteur"], entree["licence"])
    src = entree.get("source", INCONNU)
    return t + (" (%s)" % src if src and src != INCONNU else "")


# ------------------------------------------------------ lecture des réponses d'API

_BALISES = re.compile(r"<[^>]+>")


def nettoyer_auteur(valeur):
    """L'« Artist » de Commons est du HTML : « <a href="…">Prénom Nom</a> »."""
    txt = html.unescape(_BALISES.sub(" ", valeur or ""))
    txt = re.sub(r"\s+", " ", txt).strip(" ·,;")
    return txt or INCONNU


def credit_commons(imageinfo):
    """Crédit depuis un imageinfo de l'API Commons (iiprop=url|extmetadata)."""
    em = (imageinfo or {}).get("extmetadata") or {}

    def val(cle):
        v = em.get(cle) or {}
        return v.get("value") if isinstance(v, dict) else None

    licence = val("LicenseShortName") or val("License") or INCONNU
    return {"source": "wikimedia",
            "auteur": nettoyer_auteur(val("Artist") or val("Credit")),
            "licence": nettoyer_auteur(licence),
            "url": (imageinfo or {}).get("descriptionurl") or val("DescriptionUrl") or INCONNU}


def credit_inaturalist(photo):
    """Crédit depuis un objet photo de l'API iNaturalist.

    « attribution » est une phrase toute faite (« (c) Nom, some rights reserved (CC BY) ») :
    on en extrait le nom, et la licence vient de license_code.
    """
    photo = photo or {}
    att = photo.get("attribution") or ""
    m = re.match(r"\s*(?:\(c\)|©)?\s*([^,]+)", att)
    auteur = nettoyer_auteur(m.group(1) if m else "")
    code = (photo.get("license_code") or "").upper().replace("-", " ")
    return {"source": "inaturalist", "auteur": auteur,
            "licence": code or INCONNU,
            "url": photo.get("url") or photo.get("native_page_url") or INCONNU}


# ------------------------------------------------------------------------ rapport

def rapport():
    """(connus, inconnus, manquants, morts) : manquants = images sans ligne du tout."""
    entrees = charger()
    images = images_du_depot()
    manquants = sorted(images - set(entrees))
    morts = sorted(set(entrees) - images)
    connus = sorted(f for f, e in entrees.items() if f in images and connu(e))
    inconnus = sorted(f for f, e in entrees.items() if f in images and not connu(e))
    return connus, inconnus, manquants, morts


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    inconnus_opts = [a for a in argv if a not in ("--init",)]
    if inconnus_opts:
        print("option inconnue : %s" % ", ".join(inconnus_opts))
        print(__doc__)
        return 2

    if "--init" in argv:
        entrees = charger()
        ajoutes = 0
        for f in sorted(images_du_depot()):
            if f not in entrees:
                entrees[f] = {k: INCONNU for k in CHAMPS[1:]}
                ajoutes += 1
        ecrire(entrees)
        print("img/CREDITS.tsv : %d entrée(s) ajoutée(s), %d au total." % (ajoutes, len(entrees)))

    connus, inconnus, manquants, morts = rapport()
    total = len(connus) + len(inconnus)
    print("Crédits : %d/%d image(s) avec auteur et licence (%.0f %%)."
          % (len(connus), total, (100.0 * len(connus) / total) if total else 0))
    if manquants:
        print("  %d image(s) sans aucune ligne (lancer --init) :" % len(manquants))
        for f in manquants[:10]:
            print("    -", f)
        if len(manquants) > 10:
            print("    … et %d autre(s)" % (len(manquants) - 10))
    if morts:
        print("  %d ligne(s) sans image correspondante :" % len(morts))
        for f in morts[:10]:
            print("    -", f)
    return 0


if __name__ == "__main__":
    sys.exit(main())
