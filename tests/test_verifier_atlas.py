#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contrôles de scripts/verifier_atlas.py sur le dossier img/quiz-extra/."""
import pytest

from conftest import load_module


@pytest.fixture
def va(repo, monkeypatch):
    """Le vérificateur, branché sur le faux dépôt de la fixture `repo`."""
    module = load_module("verifier_atlas")
    monkeypatch.setattr(module, "gq", repo.gq)
    return module


def test_photo_orpheline_signalee(va, repo):
    # Nommée hors convention : elle n'apparaîtrait nulle part dans le site.
    repo.extra_photo("chene_feuille_1.jpg")

    errs = va.verifier_photos_extra({"chene"})

    assert len(errs) == 1
    assert "chene_feuille_1.jpg" in errs[0]
    assert "aucune espèce" in errs[0]


def test_photo_dont_l_espece_n_existe_pas_signalee(va, repo):
    repo.extra_photo("especeinconnue-feuille-1.jpg")

    errs = va.verifier_photos_extra({"chene"})

    assert len(errs) == 1 and "especeinconnue-feuille-1.jpg" in errs[0]


def test_photo_ambigue_signalee(va, repo):
    # Deux stems dont l'un préfixe l'autre *avec un tiret* : le rattachement est ambigu.
    repo.extra_photo("ail-des-ours-1.jpg")

    errs = va.verifier_photos_extra({"ail", "ail-des-ours"})

    assert len(errs) == 1
    assert "réclamée par 2 espèces" in errs[0]


def test_photos_bien_nommees_ne_declenchent_rien(va, repo):
    repo.extra_photo("chene-feuille-1.jpg")
    repo.extra_photo("chene-2.jpg")
    repo.extra_photo("ail_des_ours-fleur-1.jpg")

    assert va.verifier_photos_extra({"chene", "ail_des_ours"}) == []


def test_fichiers_techniques_ignores(va, repo):
    repo.sidecar("chene-1.jpg\tfeuille\n")            # _aspects.tsv
    repo.write("img/quiz-extra/_COMMENT-NOMMER.txt", "aide au nommage\n")
    repo.extra_photo("chene-1.jpg")

    assert va.verifier_photos_extra({"chene"}) == []
