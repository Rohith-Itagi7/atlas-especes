#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Vocabulaire des aspects : source unique dans atlas_data.ASPECTS (cf. #8).

La liste était recopiée dans couverture.py, site_ui.py, generer_quiz.py, fetch_aspects.py et
la documentation — avec des copies divergentes (« rameau » connu du site, ignoré de
COUVERTURE.md et absent de CONTRIBUTING.md).
"""
import json

import pytest

from conftest import load_module


# --------------------------------------------------------------- cohérence interne

def test_les_mots_cles_derivent_de_la_liste(atlas_data):
    for a in atlas_data.ASPECTS:
        assert atlas_data.ASPECT_KW[a.id] == a.id
        for syn in a.synonymes:
            assert atlas_data.ASPECT_KW[syn] == a.id, syn


def test_les_mots_cles_historiques_sont_tous_reconnus(atlas_data):
    # Ce que les noms de fichiers du dépôt utilisent déjà : rien ne doit disparaître.
    attendu = {"feuille": "feuille", "feuilles": "feuille", "ecorce": "ecorce",
               "fruit": "fruit", "fruits": "fruit", "fleur": "fleur", "fleurs": "fleur",
               "rameau": "rameau", "rameaux": "rameau", "bourgeon": "rameau",
               "hiver": "rameau", "port": "port", "silhouette": "port"}

    assert atlas_data.ASPECT_KW == attendu


def test_aucun_identifiant_ni_synonyme_en_double(atlas_data):
    mots = [kw for a in atlas_data.ASPECTS for kw in (a.id,) + a.synonymes]

    assert len(mots) == len(set(mots))


def test_le_vocabulaire_accepte_divers(atlas_data):
    assert atlas_data.ASPECTS_VALIDES == set(atlas_data.ASPECT_IDS) | {atlas_data.DIVERS}
    assert atlas_data.DIVERS not in atlas_data.ASPECT_IDS


def test_chaque_aspect_est_complet(atlas_data):
    for a in atlas_data.ASPECTS:
        assert a.id and a.id.islower() and a.id.isalpha(), a
        assert a.label and atlas_data.ASPECT_LABEL[a.id] == a.label
        assert a.emoji and a.terme_en, a
    assert atlas_data.ASPECT_LABEL[atlas_data.DIVERS]


def test_rameau_est_accepte_mais_hors_objectif_de_couverture(atlas_data):
    """Décision de #8 : aucune photo ne l'utilise (0 aujourd'hui), donc pas de colonne vide
    dans COUVERTURE.md — mais le mot-clé reste valable dans un nom de fichier."""
    rameau = [a for a in atlas_data.ASPECTS if a.id == "rameau"]

    assert rameau and rameau[0].cible is False
    assert "rameau" in atlas_data.ASPECTS_VALIDES
    assert atlas_data.ASPECT_KW["bourgeon"] == "rameau"


# ------------------------------------------------------- les consommateurs en dérivent

def test_couverture_liste_les_aspects_de_l_objectif(repo, monkeypatch):
    couverture = load_module("couverture")
    monkeypatch.setattr(couverture, "atlas_data", repo.atlas_data)
    repo.vignette("chene.jpg")
    repo.extra_photo("chene-feuille-1.jpg")

    colonnes = couverture.aspects_du_tableau(
        [{"stem": "chene", "paths": [repo.extra + "/chene-feuille-1.jpg"]}])

    assert [k for k, _ in colonnes] == [a.id for a in repo.atlas_data.ASPECTS if a.cible]


def test_couverture_ajoute_une_colonne_des_la_premiere_photo(repo, monkeypatch):
    """« rameau » n'a pas de colonne aujourd'hui, mais en aura dès qu'une photo l'utilisera."""
    couverture = load_module("couverture")
    monkeypatch.setattr(couverture, "atlas_data", repo.atlas_data)
    repo.extra_photo("chene-rameau-1.jpg")

    colonnes = couverture.aspects_du_tableau(
        [{"stem": "chene", "paths": [repo.extra + "/chene-rameau-1.jpg"]}])

    assert "rameau" in [k for k, _ in colonnes]


def test_le_site_recoit_le_vocabulaire_dans_ses_donnees():
    build_web = load_module("build_web")
    atlas_data = load_module("atlas_data")

    envoye = build_web.aspects_web()

    assert [a["id"] for a in envoye] == list(atlas_data.ASPECT_IDS)
    for a in envoye:
        assert set(a) == {"id", "label", "emoji", "cible"}
    json.dumps(envoye)   # doit être sérialisable pour l'injection


def test_ajouter_un_aspect_suffit_pour_le_site(monkeypatch):
    """Preuve que le site n'a pas de copie en dur : un aspect ajouté à la source apparaît
    dans l'index.html généré."""
    atlas_data = load_module("atlas_data")
    build_web = load_module("build_web")
    monkeypatch.setattr(build_web, "atlas_data", atlas_data)
    monkeypatch.setattr(atlas_data, "ASPECTS", list(atlas_data.ASPECTS) + [
        atlas_data.Aspect("racine", "Racine", ("racines",), "🥕", True, "root")])

    html = build_web.assemble([])

    assert '"id": "racine"' in html or '"id":"racine"' in html
    assert "Racine" in html
    assert "__ASPECTS__" not in html


def test_le_generateur_local_utilise_la_meme_source():
    generer_quiz = load_module("generer_quiz")
    atlas_data = load_module("atlas_data")

    assert [a["id"] for a in generer_quiz.aspects_js()] == list(atlas_data.ASPECT_IDS)


def test_les_termes_de_recherche_viennent_du_vocabulaire():
    fetch_aspects = load_module("fetch_aspects")
    atlas_data = load_module("atlas_data")
    termes = {a.id: a.terme_en for a in atlas_data.ASPECTS}

    for aspect, terme in fetch_aspects.ASP_LIG + fetch_aspects.ASP_HERB:
        assert termes[aspect] == terme
