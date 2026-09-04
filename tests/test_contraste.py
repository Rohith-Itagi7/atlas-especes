#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contrastes des deux thèmes (cf. #14).

Le site n'a plus aucune couleur en dur : tout passe par des jetons CSS, redéfinis pour le
thème sombre. Ce test lit ces jetons dans scripts/site_ui.py et vérifie les rapports de
contraste WCAG des paires réellement utilisées — clair ET sombre. Un thème sombre qui rend
le texte secondaire illisible serait pire que pas de thème sombre.

Seuils WCAG AA : 4.5 pour le texte courant, 3.0 pour le grand texte et les éléments
qui portent un état (focus, progression).
"""
import re

import pytest

from conftest import load_module

AA_TEXTE = 4.5
AA_GRAND = 3.0


def jetons():
    """({jeton: valeur} clair, {jeton: valeur} sombre) résolus (var(...) suivis)."""
    css = load_module("site_ui").CSS
    root = re.search(r":root\{(.*?)\n\}", css, re.S).group(1)
    sombre = re.search(r"@media \(prefers-color-scheme: dark\)\{\s*:root\{(.*?)\n \}", css, re.S)
    assert sombre, "aucun bloc de thème sombre dans le CSS"

    def lire(bloc):
        return dict(re.findall(r"(--[a-z0-9-]+)\s*:\s*([^;}\n]+?)\s*(?:;|$)", bloc, re.M))

    clair = lire(root)
    fonce = dict(clair)
    fonce.update(lire(sombre.group(1)))

    def resoudre(d):
        out = {}
        for cle in d:
            val, vu = d[cle], 0
            while val.startswith("var(") and vu < 10:
                val = d.get(val[4:].split(")")[0].strip(), val)
                vu += 1
            out[cle] = val.strip()
        return out

    return resoudre(clair), resoudre(fonce)


def canal(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def luminance(couleur):
    couleur = couleur.strip()
    m = re.match(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)", couleur)
    if m:
        r, g, b = (int(x) for x in m.groups())
    else:
        h = couleur.lstrip("#")
        if len(h) == 3:
            h = "".join(x * 2 for x in h)
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return 0.2126 * canal(r) + 0.7152 * canal(g) + 0.0722 * canal(b)


def contraste(a, b):
    la, lb = luminance(a), luminance(b)
    clair, fonce = max(la, lb), min(la, lb)
    return (clair + 0.05) / (fonce + 0.05)


# (texte, fond, seuil, à quoi ça sert)
PAIRES = [
    ("--fg-1", "--bg-canvas", AA_TEXTE, "texte principal sur la page"),
    ("--fg-1", "--bg-card", AA_TEXTE, "texte principal sur une carte"),
    ("--fg-2", "--bg-card", AA_TEXTE, "texte secondaire d'une carte"),
    ("--fg-3", "--bg-canvas", AA_TEXTE, "texte gris (légendes, compteurs)"),
    ("--fg-3", "--bg-card", AA_TEXTE, "texte gris sur carte"),
    ("--fg-3", "--bg-surface", AA_TEXTE, "texte gris sur le fond de l'app"),
    ("--fg-link", "--bg-card", AA_TEXTE, "lien"),
    ("--fg-accent", "--bg-card", AA_TEXTE, "accent (chiffres, libellés verts)"),
    ("--fg-on-accent", "--accent-bg", AA_TEXTE, "onglet actif, bouton principal"),
    ("--fg-on-accent", "--color-brand-red", AA_TEXTE, "bouton d'action"),
    ("--color-success", "--color-success-soft", AA_TEXTE, "bonne réponse"),
    ("--color-danger", "--color-danger-soft", AA_TEXTE, "mauvaise réponse"),
    ("--color-warning", "--color-warning-soft", AA_TEXTE, "« ne pas confondre », bandeau"),
    ("--panel-dark-fg", "--overlay-dark", AA_TEXTE, "pastille d'aspect sur la photo"),
    ("--panel-dark-fg", "--panel-dark-bg", AA_TEXTE, "bannière du quiz, pastille de série"),
    ("--panel-dark-fg", "--panel-dark-bg-hover", AA_TEXTE, "bouton sombre survolé"),
    ("--color-yellow", "--panel-dark-bg", AA_TEXTE, "surtitre de la bannière du quiz"),
    ("--color-partial", "--bg-card", AA_GRAND, "barre de progression partielle"),
    # WCAG 1.4.11 vise les éléments qui portent un état (focus, sélection), pas les
    # séparateurs décoratifs : --border / --border-strong n'y sont donc pas soumis.
    ("--focus", "--bg-canvas", AA_GRAND, "anneau de focus"),
    ("--focus", "--bg-card", AA_GRAND, "anneau de focus sur carte"),
]


@pytest.mark.parametrize("theme", ["clair", "sombre"])
def test_contrastes_wcag(theme):
    clair, fonce = jetons()
    palette = clair if theme == "clair" else fonce
    fautes = []
    for texte, fond, seuil, usage in PAIRES:
        assert texte in palette and fond in palette, (texte, fond)
        r = contraste(palette[texte], palette[fond])
        if r < seuil:
            fautes.append("%-28s %5.2f < %.1f  (%s sur %s)" % (usage, r, seuil, texte, fond))

    assert not fautes, "thème %s :\n  %s" % (theme, "\n  ".join(fautes))


def test_le_theme_sombre_redefinit_bien_les_fonds_et_les_textes():
    clair, fonce = jetons()

    # un thème sombre qui oublierait un fond laisserait du texte clair sur fond clair
    for jeton in ("--bg-canvas", "--bg-surface", "--bg-card", "--fg-1", "--fg-2", "--fg-3",
                  "--border", "--accent-bg", "--fg-on-accent"):
        assert clair[jeton] != fonce[jeton], jeton
    assert luminance(fonce["--bg-canvas"]) < luminance(clair["--bg-canvas"])
    assert luminance(fonce["--fg-1"]) > luminance(clair["--fg-1"])


def test_aucune_couleur_en_dur_hors_jetons():
    """Une couleur écrite en dur échappe au thème sombre : elle est interdite."""
    ui = load_module("site_ui")
    dur = []
    for source, nom in ((ui.CSS, "CSS"), (ui.JS, "JS"), (ui.BODY, "BODY")):
        for ligne in source.split("\n"):
            if ligne.strip().startswith("--"):
                continue        # la définition des jetons, seul endroit légitime
            for c in re.findall(r"#[0-9A-Fa-f]{3,6}\b|rgba?\([0-9 ,.]+\)", ligne):
                dur.append("%s : %s (%s)" % (nom, c, ligne.strip()[:70]))

    assert not dur, "couleurs en dur :\n  " + "\n  ".join(dur)
