#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rattachement des photos supplémentaires à leur espèce (img/quiz-extra/).

Régression : un stem qui préfixe un autre happait ses photos — « Ail » recevait celles de
l'ail des ours et de l'ail rocambole, « Chou » celles du chou de Daubenton (cf. #18).
"""
import os

from conftest import vignette_cell


def ligne(vignette, name, latin):
    return [vignette_cell(vignette), name, latin, "vivace", "Amaryllidacées", "bulbe", ""]


def noms(paths):
    return [os.path.basename(p) for p in paths]


def test_photo_avec_aspect_et_numero(repo):
    repo.extra_photo("chene-feuille-1.jpg")
    repo.extra_photo("chene-2.jpg")

    assert noms(repo.atlas_data.extra_photos("chene")) == ["chene-2.jpg", "chene-feuille-1.jpg"]


def test_stem_nu_accepte(repo):
    # Une photo « l'organisme », sans aspect annoncé, déposée dans quiz-extra.
    repo.extra_photo("chene.jpg")

    assert noms(repo.atlas_data.extra_photos("chene")) == ["chene.jpg"]


def test_un_stem_ne_prend_pas_les_photos_de_celui_qu_il_prefixe(repo):
    repo.extra_photo("ail-1.jpg")
    repo.extra_photo("ail_des_ours-1.jpg")
    repo.extra_photo("ail_rocambole-fleur-1.jpg")

    assert noms(repo.atlas_data.extra_photos("ail")) == ["ail-1.jpg"]


def test_l_espece_prefixee_garde_toutes_ses_photos(repo):
    repo.extra_photo("ail-1.jpg")
    repo.extra_photo("ail_des_ours-1.jpg")
    repo.extra_photo("ail_des_ours-feuille-1.jpg")

    assert noms(repo.atlas_data.extra_photos("ail_des_ours")) == ["ail_des_ours-1.jpg",
                                                          "ail_des_ours-feuille-1.jpg"]


def test_ignore_les_fichiers_non_images(repo):
    repo.extra_photo("chene-notes.txt")
    repo.extra_photo("chene-feuille-1.jpg")

    assert noms(repo.atlas_data.extra_photos("chene")) == ["chene-feuille-1.jpg"]


def test_accepte_jpeg_et_png(repo):
    repo.extra_photo("chene-1.jpeg")
    repo.extra_photo("chene-2.PNG")

    assert noms(repo.atlas_data.extra_photos("chene")) == ["chene-1.jpeg", "chene-2.PNG"]


def test_dossier_quiz_extra_absent(repo):
    import shutil
    shutil.rmtree(repo.extra)

    assert repo.atlas_data.extra_photos("chene") == []


def test_le_parseur_n_attribue_que_les_bonnes_photos(repo):
    """Vérification de bout en bout : les deux espèces coexistent dans un atlas."""
    repo.vignette("ail.jpg")
    repo.vignette("ail_des_ours.jpg")
    repo.extra_photo("ail-1.jpg")
    repo.extra_photo("ail_des_ours-1.jpg")
    repo.extra_photo("ail_des_ours-2.jpg")
    repo.write_atlas("Test.md", [ligne("ail.jpg", "Ail", "Allium sativum"),
                           ligne("ail_des_ours.jpg", "Ail des ours", "Allium ursinum")])

    par_stem = {s["stem"]: noms(s["paths"]) for s in repo.parse("Test.md", "herbace")}

    assert par_stem["ail"] == ["ail.jpg", "ail-1.jpg"]
    assert par_stem["ail_des_ours"] == ["ail_des_ours.jpg", "ail_des_ours-1.jpg",
                                        "ail_des_ours-2.jpg"]
