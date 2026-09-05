#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Crédits des images (scripts/credits.py) — auteur, licence, page d'origine.

Les licences CC-BY / CC-BY-SA **exigent** de nommer l'auteur et la licence : un crédit
global ne suffit pas (cf. #10). Les fonctions de lecture des réponses d'API sont testées
sur des charges utiles enregistrées : les API ne sont pas appelées ici.
"""
import os

import pytest

from conftest import load_module


@pytest.fixture
def cr(repo, monkeypatch):
    """Le module, branché sur le faux dépôt."""
    module = load_module("credits")
    monkeypatch.setattr(module, "atlas_data", repo.atlas_data)
    monkeypatch.setattr(module, "BASE", repo.root)
    monkeypatch.setattr(module, "CREDITS", os.path.join(repo.root, "img", "CREDITS.tsv"))
    return module


# ------------------------------------------------------------------ lecture / écriture

def test_ecrire_puis_relire(cr):
    entrees = {"b.jpg": {"source": "wikimedia", "auteur": "Alice", "licence": "CC BY-SA 4.0",
                         "url": "https://commons.wikimedia.org/wiki/File:b.jpg"},
               "a.jpg": {"source": "inaturalist", "auteur": "Bob", "licence": "CC BY 4.0",
                         "url": "https://inaturalist.org/photos/1"}}

    cr.ecrire(entrees)

    assert cr.charger() == entrees
    lignes = [l for l in open(cr.CREDITS, encoding="utf-8").read().split("\n")
              if l and not l.startswith("#")]
    assert lignes[0] == cr.ENTETE
    assert lignes[1].startswith("a.jpg\t") and lignes[2].startswith("b.jpg\t"), "fichier trié"


def test_le_preambule_explique_les_inconnus(cr):
    cr.ecrire({})

    contenu = open(cr.CREDITS, encoding="utf-8").read()

    assert contenu.startswith("#") and "inconnu" in contenu


def test_champs_manquants_relus_comme_inconnus(cr):
    open(cr.CREDITS, "w", encoding="utf-8").write("fichier\tsource\nx.jpg\twikimedia\n")

    assert cr.charger()["x.jpg"] == {"source": "wikimedia", "auteur": "", "licence": "", "url": ""}


def test_noter_ajoute_puis_met_a_jour(cr, repo):
    cr.noter("chene-1.jpg", "wikimedia", "Alice", "CC BY 4.0", "https://exemple/1")
    assert cr.charger()["chene-1.jpg"]["auteur"] == "Alice"

    cr.noter(os.path.join(repo.extra, "chene-1.jpg"), "wikimedia", "Bob", "CC0", "https://x/2")

    entrees = cr.charger()
    assert len(entrees) == 1, "le chemin complet et le nom de fichier désignent la même image"
    assert entrees["chene-1.jpg"]["auteur"] == "Bob"


def test_noter_sans_auteur_ecrit_inconnu(cr):
    cr.noter("chene-1.jpg", "wikimedia")

    assert cr.charger()["chene-1.jpg"] == {"source": "wikimedia", "auteur": "inconnu",
                                           "licence": "inconnu", "url": "inconnu"}


# ------------------------------------------------------------------ crédit exploitable

@pytest.mark.parametrize("entree,attendu", [
    ({"auteur": "Alice", "licence": "CC BY 4.0", "source": "wikimedia"}, True),
    ({"auteur": "Alice", "licence": "inconnu", "source": "wikimedia"}, False),
    ({"auteur": "inconnu", "licence": "CC BY 4.0", "source": "wikimedia"}, False),
    ({}, False),
    (None, False),
])
def test_connu(cr, entree, attendu):
    assert cr.connu(entree) is attendu


def test_texte_d_attribution(cr):
    t = cr.texte({"auteur": "Alice Dupont", "licence": "CC BY-SA 4.0", "source": "wikimedia"})

    assert t == "© Alice Dupont — CC BY-SA 4.0 (wikimedia)"


def test_pas_de_texte_sans_credit(cr):
    assert cr.texte({"auteur": "inconnu", "licence": "inconnu"}) == ""


# ------------------------------------------------------- réponses d'API (enregistrées)

def test_auteur_commons_est_du_html(cr):
    assert cr.nettoyer_auteur('<a href="//commons.wikimedia.org/wiki/User:Foo" '
                              'title="User:Foo">Alice&nbsp;Dupont</a>') == "Alice Dupont"
    assert cr.nettoyer_auteur("") == "inconnu"


def test_credit_commons(cr):
    imageinfo = {
        "descriptionurl": "https://commons.wikimedia.org/wiki/File:Quercus.jpg",
        "extmetadata": {
            "Artist": {"value": '<a href="/wiki/User:Bob">Bob Martin</a>'},
            "LicenseShortName": {"value": "CC BY-SA 4.0"},
            "License": {"value": "cc-by-sa-4.0"},
        },
    }

    assert cr.credit_commons(imageinfo) == {
        "source": "wikimedia", "auteur": "Bob Martin", "licence": "CC BY-SA 4.0",
        "url": "https://commons.wikimedia.org/wiki/File:Quercus.jpg"}


def test_credit_commons_sans_metadonnees(cr):
    got = cr.credit_commons({"descriptionurl": "https://commons.wikimedia.org/wiki/File:X.jpg"})

    assert got["auteur"] == "inconnu" and got["licence"] == "inconnu"
    assert got["url"].endswith("File:X.jpg")


def test_credit_inaturalist(cr):
    photo = {"attribution": "(c) Camille Roux, some rights reserved (CC BY-NC)",
             "license_code": "cc-by-nc", "url": "https://inaturalist.org/photos/42"}

    assert cr.credit_inaturalist(photo) == {
        "source": "inaturalist", "auteur": "Camille Roux", "licence": "CC BY NC",
        "url": "https://inaturalist.org/photos/42"}


def test_credit_inaturalist_vide(cr):
    got = cr.credit_inaturalist({})

    assert got["source"] == "inaturalist" and got["auteur"] == "inconnu"


# ------------------------------------------------------------------------- rapport

def test_rapport(cr, repo):
    repo.vignette("chene.jpg")
    repo.extra_photo("chene-1.jpg")
    repo.extra_photo("chene-2.jpg")
    cr.ecrire({
        "chene.jpg": {"source": "wikimedia", "auteur": "Alice", "licence": "CC BY 4.0",
                      "url": "https://exemple/1"},
        "chene-1.jpg": {"source": "inconnu", "auteur": "inconnu", "licence": "inconnu",
                        "url": "inconnu"},
        "disparue.jpg": {"source": "wikimedia", "auteur": "Bob", "licence": "CC0",
                         "url": "https://exemple/2"},
    })

    connus, inconnus, manquants, morts = cr.rapport()

    assert connus == ["chene.jpg"]
    assert inconnus == ["chene-1.jpg"]
    assert manquants == ["chene-2.jpg"], "image sans aucune ligne"
    assert morts == ["disparue.jpg"], "ligne sans image"


def test_init_complete_et_est_idempotent(cr, repo, capsys):
    repo.vignette("chene.jpg")
    repo.extra_photo("chene-1.jpg")

    assert cr.main(["--init"]) == 0
    assert sorted(cr.charger()) == ["chene-1.jpg", "chene.jpg"]

    capsys.readouterr()
    assert cr.main(["--init"]) == 0
    assert "0 entrée(s) ajoutée(s)" in capsys.readouterr().out


def test_init_ne_touche_pas_aux_credits_connus(cr, repo):
    repo.vignette("chene.jpg")
    repo.extra_photo("chene-1.jpg")
    cr.noter("chene.jpg", "wikimedia", "Alice", "CC BY 4.0", "https://exemple/1")

    cr.main(["--init"])

    assert cr.charger()["chene.jpg"]["auteur"] == "Alice"


def test_option_inconnue(cr):
    assert cr.main(["--backfill"]) == 2


# --------------------------------------------------- affichage dans le site et la CI

def test_le_site_ne_montre_que_les_credits_exploitables(repo, monkeypatch):
    build_web = load_module("build_web")
    cr = load_module("credits")
    monkeypatch.setattr(cr, "CREDITS", os.path.join(repo.root, "img", "CREDITS.tsv"))
    monkeypatch.setattr(cr, "atlas_data", repo.atlas_data)
    monkeypatch.setattr(build_web, "credits", cr)
    monkeypatch.setattr(build_web, "atlas_data", repo.atlas_data)
    repo.vignette("chene.jpg")
    repo.extra_photo("chene-1.jpg")
    cr.ecrire({"chene.jpg": {"source": "wikimedia", "auteur": "Alice", "licence": "CC BY 4.0",
                             "url": "https://exemple/1"},
               "chene-1.jpg": {"source": "inconnu", "auteur": "inconnu", "licence": "inconnu",
                               "url": "inconnu"}})
    especes = [{"id": "chene", "stem": "chene", "name": "Chêne", "latin": "Quercus robur",
                "cat": "ligneux", "note": "", "fields": {},
                "paths": [os.path.join(repo.img, "chene.jpg"),
                          os.path.join(repo.extra, "chene-1.jpg")]}]

    imgs = build_web.to_web_data(especes)[0]["imgs"]

    assert imgs[0]["c"] == "© Alice — CC BY 4.0 (wikimedia)"
    assert imgs[0]["cu"] == "https://exemple/1"
    assert "c" not in imgs[1], "pas d'attribution inventée quand le crédit est inconnu"


def test_la_ci_avertit_sur_les_credits_manquants(repo, monkeypatch):
    va = load_module("verifier_atlas")
    cr = load_module("credits")
    monkeypatch.setattr(cr, "CREDITS", os.path.join(repo.root, "img", "CREDITS.tsv"))
    monkeypatch.setattr(cr, "atlas_data", repo.atlas_data)
    monkeypatch.setattr(va, "credits", cr)
    repo.vignette("chene.jpg")
    cr.ecrire({"disparue.jpg": {"source": "wikimedia", "auteur": "Bob", "licence": "CC0",
                                "url": "https://exemple/2"}})

    errs, warns = va.verifier_credits()

    assert errs == [], "avertissement seulement, tant que le rattrapage n'est pas fait"
    assert any("chene.jpg" in w for w in warns)
    assert any("disparue.jpg" in w for w in warns)
