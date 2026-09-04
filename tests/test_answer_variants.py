#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Orthographes acceptées comme réponse de quiz (atlas_data.answer_variants).

Régression : en mode « saisie », taper « Chalef » sur « Chalef / Olivier de Bohême » était
compté faux, comme toute espèce dont le nom porte une variante ou une précision (cf. #4).
"""
import pytest


@pytest.mark.parametrize("nom,latin,attendues", [
    ("Chalef / Olivier de Bohême", "Elaeagnus angustifolia", ["Chalef", "Olivier de Bohême"]),
    ("Cassissier / Groseillier", "Ribes sp.", ["Cassissier", "Groseillier"]),
    ("Caragana (arbre à pois)", "Caragana arborescens", ["Caragana", "arbre à pois"]),
    ("Usnée (barbe de Jupiter)", "Usnea barbata", ["Usnée", "barbe de Jupiter"]),
    ("Chèvrefeuille comestible (camérisier)", "Lonicera caerulea",
     ["Chèvrefeuille comestible", "camérisier"]),
    ("Betterave / Épinard", "Beta / Spinacia", ["Betterave", "Épinard", "Beta", "Spinacia"]),
])
def test_variantes_des_noms_composes(atlas_data, nom, latin, attendues):
    got = atlas_data.answer_variants(nom, latin)

    assert got[0] == nom, "le nom canonique reste en tête"
    for a in attendues:
        assert a in got


def test_le_latin_et_son_epithete_sont_acceptes(atlas_data):
    got = atlas_data.answer_variants("Ail des ours", "Allium ursinum")

    assert got == ["Ail des ours", "Allium ursinum", "ursinum"]


def test_l_hybride_perd_sa_croix_dans_l_epithete(atlas_data):
    got = atlas_data.answer_variants("Consoude", "Symphytum ×uplandicum")

    assert "uplandicum" in got


def test_pas_d_epithete_pour_une_abreviation(atlas_data):
    # « Ribes sp. » ne doit pas rendre « sp. » acceptable comme réponse.
    got = atlas_data.answer_variants("Groseillier", "Ribes sp.")

    assert "sp." not in got and "sp" not in got


def test_le_latin_entre_parentheses_est_une_note_pas_un_nom(atlas_data):
    got = atlas_data.answer_variants("Merisier", "Prunus avium (cultivé)")

    assert "Prunus avium" in got
    assert "cultivé" not in got and "(cultivé)" not in got


def test_nom_simple_sans_latin(atlas_data):
    assert atlas_data.answer_variants("Ortie", "") == ["Ortie"]


def test_pas_de_doublon_ni_de_vide(atlas_data):
    got = atlas_data.answer_variants("Ortie / Ortie", "Urtica dioica")

    assert got == ["Ortie / Ortie", "Ortie", "Urtica dioica", "dioica"]


def test_valeurs_absentes(atlas_data):
    assert atlas_data.answer_variants("", "") == []
    assert atlas_data.answer_variants(None, None) == []


def test_toutes_les_especes_reelles_ont_au_moins_leur_nom(atlas_data):
    especes, seen = [], set()
    for path, cat in atlas_data.ATLASES:
        especes += atlas_data.parse_atlas(path, cat, seen)

    for s in especes:
        variantes = atlas_data.answer_variants(s["name"], s["latin"])
        assert variantes and variantes[0] == s["name"], s["name"]
        assert all(v.strip() for v in variantes), s["name"]
