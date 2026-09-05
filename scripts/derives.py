#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dérivés d'images pour le site : des vignettes légères là où l'affichage est petit.

La grille de l'atlas montre les 251 espèces dans des cartes de ~160 px, mais servait les
fichiers d'origine (~420-500 px, 73 ko en moyenne) : ~18 Mo pour un mur de timbres-poste.
Un palier suffit ici, et un seul :

  thumb  320 px de large max, JPEG q75 progressif  → grille, bandeau de la fiche, cartes Oui/Non
  original                                          → photo du quiz, photo principale de la fiche

Pourquoi pas de palier intermédiaire : aucune source ne dépasse 1024 px (une seule), et la
médiane est à ~450 px. Un « medium 1200 px » serait un agrandissement, plus lourd et plus
flou que l'original. Pourquoi pas de WebP : mesuré à qualité équivalente sur les vignettes
du dépôt, le gain est de 1 % face au JPEG — pas de quoi ajouter un format.

Pillow est une dépendance **du build seulement** : sans elle, le site est construit avec les
originaux (avec un avertissement), comme avant.
"""
import json
import os

LARGEUR_THUMB = 320
QUALITE = 75
DOSSIER_THUMB = os.path.join("img", "thumb")
MANIFESTE = ".derives.json"

try:                                    # optionnel : le build reste possible sans
    from PIL import Image
    PILLOW = True
except ImportError:                     # pragma: no cover - dépend de l'environnement
    Image = None
    PILLOW = False


def chemin_thumb(rel):
    """Chemin relatif du dérivé pour une image du dépôt (img/especes/x.jpg → img/thumb/x.jpg).

    Les deux dossiers sources ont des noms de fichiers uniques (le vérificateur y veille),
    donc un seul dossier de dérivés suffit.
    """
    return os.path.join(DOSSIER_THUMB, os.path.basename(rel)).replace(os.sep, "/")


def dimensions(chemin):
    """(largeur, hauteur) de l'image, ou None si illisible / sans Pillow."""
    if not PILLOW:
        return None
    try:
        with Image.open(chemin) as im:
            return im.size
    except Exception:
        return None


def _empreinte(chemin):
    st = os.stat(chemin)
    return [int(st.st_mtime), st.st_size]


class Deriveur:
    """Génère les vignettes dans un dossier de sortie, en sautant ce qui est à jour."""

    def __init__(self, outdir):
        self.outdir = outdir
        self.manifeste = os.path.join(outdir, MANIFESTE)
        self.connu = {}
        self.faits = {}
        self.generes = 0
        self.reutilises = 0
        self.echecs = 0
        if os.path.exists(self.manifeste):
            try:
                self.connu = json.load(open(self.manifeste, encoding="utf-8"))
            except (ValueError, OSError):
                self.connu = {}

    def thumb(self, source, rel):
        """Fabrique (ou réutilise) la vignette de `source`. Renvoie son chemin relatif,
        ou celui de l'original si Pillow manque ou si la conversion échoue."""
        if not PILLOW:
            return rel
        cible_rel = chemin_thumb(rel)
        cible = os.path.join(self.outdir, cible_rel)
        emp = _empreinte(source)
        if self.connu.get(cible_rel) == emp and os.path.exists(cible):
            self.reutilises += 1
            self.faits[cible_rel] = emp
            return cible_rel
        os.makedirs(os.path.dirname(cible), exist_ok=True)
        try:
            with Image.open(source) as im:
                im = im.convert("RGB")
                im.thumbnail((LARGEUR_THUMB, LARGEUR_THUMB), Image.LANCZOS)
                im.save(cible, "JPEG", quality=QUALITE, optimize=True, progressive=True)
        except Exception as e:                     # image exotique ou corrompue
            print("  ⚠ vignette impossible pour %s (%s) : on sert l'original" % (rel, e))
            self.echecs += 1
            return rel
        self.generes += 1
        self.faits[cible_rel] = emp
        return cible_rel

    def cloturer(self):
        """Écrit le manifeste et supprime les vignettes devenues inutiles."""
        if not PILLOW:
            return
        dossier = os.path.join(self.outdir, DOSSIER_THUMB)
        if os.path.isdir(dossier):
            gardees = {os.path.basename(r) for r in self.faits}
            for f in os.listdir(dossier):
                if f not in gardees:
                    os.remove(os.path.join(dossier, f))
        with open(self.manifeste, "w", encoding="utf-8") as fh:
            json.dump(self.faits, fh, indent=0, sort_keys=True)

    def resume(self):
        if not PILLOW:
            return ("Pillow absent : site construit avec les images d'origine "
                    "(pip install Pillow pour des vignettes légères)")
        return ("vignettes : %d générée(s), %d réutilisée(s)%s"
                % (self.generes, self.reutilises,
                   ", %d échec(s)" % self.echecs if self.echecs else ""))
