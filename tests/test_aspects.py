#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Aspects d'une photo : dérivés du nom de fichier, ou forcés par img/quiz-extra/_aspects.tsv."""
import pytest


@pytest.mark.parametrize("fichier,attendu", [
    ("chene-feuille-1.jpg", ["feuille"]),
    ("chene-ecorce-1.jpg", ["ecorce"]),
    ("chene-fruit-1.jpg", ["fruit"]),
    ("chene-fleur-1.jpg", ["fleur"]),
    ("chene-port-1.jpg", ["port"]),
    ("chene-rameau-1.jpg", ["rameau"]),
    # pluriels et synonymes acceptés
    ("chene-feuilles-1.jpg", ["feuille"]),
    ("chene-fleurs-2.jpg", ["fleur"]),
    ("chene-fruits-1.jpg", ["fruit"]),
    ("chene-rameaux-1.jpg", ["rameau"]),
    ("chene-bourgeon-1.jpg", ["rameau"]),
    ("chene-hiver-1.jpg", ["rameau"]),
    ("chene-silhouette-1.jpg", ["port"]),
    # aspects multiples séparés par _
    ("chene-feuille_fleur-1.jpg", ["feuille", "fleur"]),
    # aucun aspect reconnaissable
    ("chene-1.jpg", ["divers"]),
    ("chene.jpg", ["divers"]),
    ("chene-bizarre-1.jpg", ["divers"]),
])
def test_aspect_depuis_le_nom_de_fichier(repo, fichier, attendu):
    assert repo.atlas_data.aspect_of(fichier, "chene") == attendu


def test_aspect_dedoublonne_et_garde_l_ordre_du_nom(repo):
    assert repo.atlas_data.aspect_of("chene-feuille_feuilles_fleur-1.jpg", "chene") == ["feuille", "fleur"]


def test_le_sidecar_ecrase_le_nom_de_fichier(repo):
    repo.sidecar("fichier\taspects\nchene-1.jpg\tfeuille,fleur\n")

    assert repo.atlas_data.aspect_of("chene-1.jpg", "chene") == ["feuille", "fleur"]


def test_le_sidecar_accepte_le_point_virgule(repo):
    repo.sidecar("chene-1.jpg\tfeuille;port\n")

    assert repo.atlas_data.aspect_of("chene-1.jpg", "chene") == ["feuille", "port"]


def test_le_sidecar_peut_tagger_une_vignette(repo):
    # Cas courant : la vignette img/especes/chene.jpg montre en fait une feuille.
    repo.sidecar("chene.jpg\tfeuille\n")

    assert repo.atlas_data.aspect_of("chene.jpg", "chene") == ["feuille"]


def test_sidecar_valeur_vide_retombe_sur_divers(repo):
    repo.sidecar("chene-1.jpg\t\n")

    # Ligne sans valeur exploitable : la photo reste « divers », elle n'est pas perdue.
    assert repo.atlas_data.aspect_of("chene-1.jpg", "chene") == ["divers"]


def test_sidecar_ignore_entete_et_commentaires(repo):
    repo.sidecar("fichier\taspects\n# chene-1.jpg\tfeuille\nchene-2.jpg\tport\n")

    assert "chene-1.jpg" not in repo.atlas_data.SIDE
    assert repo.atlas_data.SIDE["chene-2.jpg"] == ["port"]


def test_les_tags_de_contribution_ecrasent_le_sidecar(repo):
    repo.sidecar("chene-1.jpg\tfeuille\n")
    repo.contribution("app-test.tsv", "action\tfichier\tvaleur\ntag\tchene-1.jpg\tfleur,port\n")

    assert repo.atlas_data.aspect_of("chene-1.jpg", "chene") == ["fleur", "port"]
