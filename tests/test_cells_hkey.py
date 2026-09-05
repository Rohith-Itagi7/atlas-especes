#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Découpage des lignes de tableau Markdown et normalisation des en-têtes."""
import pytest


def test_cells_of_decoupe_et_nettoie(atlas_data):
    assert atlas_data.cells_of("| a | b  |   c |") == ["a", "b", "c"]


def test_cells_of_restitue_les_pipes_echappes(atlas_data):
    # Les vignettes s'écrivent ![[stem.jpg\|200]] : le pipe échappé ne doit pas couper la cellule.
    cells = atlas_data.cells_of(r"| ![[chene.jpg\|200]] | Chêne | Quercus robur |")
    assert cells == ["![[chene.jpg|200]]", "Chêne", "Quercus robur"]


def test_cells_of_conserve_les_cellules_vides(atlas_data):
    assert atlas_data.cells_of("| a |  | c |") == ["a", "", "c"]


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
def test_hkey_reconnait_les_colonnes_des_atlas(atlas_data, entete, attendu):
    assert atlas_data.hkey(entete) == attendu


def test_hkey_normalise_les_entetes_inconnues(atlas_data):
    # Accents retirés, minuscules, points supprimés — mais la colonne reste exploitable.
    assert atlas_data.hkey("  Densité max. ") == "densite max"


def test_hkey_prefixes_insensibles_a_la_casse_et_aux_accents(atlas_data):
    assert atlas_data.hkey("COMESTIBILITÉ") == "comestible"
    assert atlas_data.hkey("Écologie fine") == "ecologie"
