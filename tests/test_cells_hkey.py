#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Découpage des lignes de tableau Markdown et normalisation des en-têtes."""
import pytest


def test_cells_of_decoupe_et_nettoie(gq):
    assert gq.cells_of("| a | b  |   c |") == ["a", "b", "c"]


def test_cells_of_restitue_les_pipes_echappes(gq):
    # Les vignettes s'écrivent ![[stem.jpg\|200]] : le pipe échappé ne doit pas couper la cellule.
    cells = gq.cells_of(r"| ![[chene.jpg\|200]] | Chêne | Quercus robur |")
    assert cells == ["![[chene.jpg|200]]", "Chêne", "Quercus robur"]


def test_cells_of_conserve_les_cellules_vides(gq):
    assert gq.cells_of("| a |  | c |") == ["a", "", "c"]


@pytest.mark.parametrize("entete,attendu", [
    ("Photo", "photo"),
    ("Espèce", "name"),
    ("Plante", "name"),
    ("Champignon", "name"),
    ("Animal", "name"),
    ("Nom latin", "latin"),
    ("Famille", "famille"),
    ("Fixation N", "fixn"),
    ("Mycorhize", "mycorhize"),
    ("Lumière", "lumiere"),
    ("Succession", "succession"),
    ("Cycle", "cycle"),
    ("Strate", "strate"),
    ("Fonction", "fonction"),
    ("Comestible", "comestible"),
    ("Écologie", "ecologie"),
    ("Arbre / substrat", "hote"),
    ("Substrat", "hote"),
    ("Saison", "saison"),
    ("Habitat", "habitat"),
    ("Rôle", "role"),
    ("Régime", "regime"),
    ("Répartition", "repartition"),
    ("Notes", "notes"),
])
def test_hkey_reconnait_les_colonnes_des_atlas(gq, entete, attendu):
    assert gq.hkey(entete) == attendu


def test_hkey_normalise_les_entetes_inconnues(gq):
    # Accents retirés, minuscules, points supprimés — mais la colonne reste exploitable.
    assert gq.hkey("  Densité max. ") == "densite max"


def test_hkey_prefixes_insensibles_a_la_casse_et_aux_accents(gq):
    assert gq.hkey("COMESTIBILITÉ") == "comestible"
    assert gq.hkey("Écologie fine") == "ecologie"
