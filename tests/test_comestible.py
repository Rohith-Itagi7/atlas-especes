#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Règle « Est-ce comestible ? » du mode Oui/Non (colonne Comestible des atlas).

Cette règle décide de la bonne réponse d'un quiz portant sur des espèces dont certaines
sont mortelles : chaque cas ci-dessous vient d'une valeur réellement présente dans un atlas.
"""
import pytest


# --------------------------------------------------------------- cas nommés (régressions)

def test_morille_est_comestible(atlas_data):
    # Champignons - référence.md : le poison est une **mise en garde** entre parenthèses,
    # le verdict de tête (« Bon ») reste positif.
    assert atlas_data.is_edible("Bon (⚠ crue TOXIQUE)") is True


def test_if_n_est_pas_comestible(atlas_data):
    # Espèces - référence.md : verdict de tête négatif, malgré une exception entre parenthèses.
    assert atlas_data.is_edible("☠ TOXIQUE (seul l'arille rouge est sans danger)") is False


# ------------------------------------------------------------------- verdicts négatifs

@pytest.mark.parametrize("valeur", [
    "non",
    "Non comestible",
    "toxique",
    "TOXIQUE",
    "**Toxique**",
    "☠ TOXIQUE",
    "⚠ toxique",
    "mortel",
    "☠ MORTEL",
    "immangeable",
    "baies TOXIQUES",          # le poison qualifie la partie nommée
    "feuilles toxiques crues et cuites",
    "(médicinal)",             # note, pas un verdict
    "(fourrage)",
    "(non)",
    "(toxique à dose)",
    "fourrage",                # consommable, mais pas par nous
    "gazon",
    "vannerie",
    "",
    "   ",
    None,
])
def test_valeurs_non_comestibles(atlas_data, valeur):
    assert atlas_data.is_edible(valeur) is False


# ------------------------------------------------------------------- verdicts positifs

@pytest.mark.parametrize("valeur", [
    "glands",
    "fruits",
    "feuilles, fleurs",
    "Bon",
    "Excellent",
    "oui",
    "tubercule",
    "chapeau (bien cuire)",
    "jeunes feuilles (⚠ crue TOXIQUE)",    # mise en garde entre parenthèses
    "fruits mûrs (amandes toxiques)",      # idem : le verdict de tête tranche
    "jeunes pousses (⚠ racine toxique)",   # idem
    "**fruits**",
    "⚠ fruits (bien mûrs)",
])
def test_valeurs_comestibles(atlas_data, valeur):
    assert atlas_data.is_edible(valeur) is True


# ------------------------------------------------------------------------- cohérence

def test_toutes_les_valeurs_reelles_donnent_un_booleen(atlas_data):
    especes, seen = [], set()
    for path, cat in atlas_data.ATLASES:
        especes += atlas_data.parse_atlas(path, cat, seen)
    valeurs = {s["fields"]["comestible"] for s in especes if "comestible" in s["fields"]}

    assert valeurs, "aucune valeur « Comestible » lue dans les atlas"
    assert all(isinstance(atlas_data.is_edible(v), bool) for v in valeurs)
