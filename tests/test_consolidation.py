#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Consolidation des contributions dans les sources (scripts/consolider_contributions.py).

Ce script renomme et supprime des fichiers : il doit être tout ou rien, et ne rien faire
tant qu'une action est douteuse (cf. #9).
"""
import os

import pytest

from conftest import load_module, vignette_cell


@pytest.fixture
def conso(repo, monkeypatch):
    """Le script, branché sur le faux dépôt."""
    module = load_module("consolider_contributions")
    monkeypatch.setattr(module, "atlas_data", repo.atlas_data)
    monkeypatch.setattr(module, "BASE", repo.root)
    monkeypatch.setattr(module, "CONTRIB", repo.contributions)
    monkeypatch.setattr(module, "SIDECAR", os.path.join(repo.extra, "_aspects.tsv"))
    monkeypatch.setattr(module, "NOTES", os.path.join(repo.contributions, "NOTES.md"))
    return module


def atlas_minimal(repo):
    """Deux espèces, pour avoir des stems valides."""
    repo.vignette("chene.jpg")
    repo.vignette("hetre.jpg")
    repo.write_atlas("Test.md", [
        [vignette_cell("chene.jpg"), "Chêne test", "Quercus testus", "arbre", "Fagacées", "glands", ""],
        [vignette_cell("hetre.jpg"), "Hêtre test", "Fagus testus", "arbre", "Fagacées", "faines", ""],
    ])
    repo.use_atlases("Test.md")


def sidecar(repo):
    p = os.path.join(repo.extra, "_aspects.tsv")
    if not os.path.exists(p):
        return {}
    out = {}
    for ln in open(p, encoding="utf-8"):
        ln = ln.rstrip("\n")
        if not ln or "\t" not in ln:
            continue
        fn, asp = ln.split("\t", 1)
        if fn.strip().lower() == "fichier":
            continue
        out[fn.strip()] = asp.strip()
    return out


def extras(repo):
    return sorted(f for f in os.listdir(repo.extra) if not f.startswith("_"))


# ------------------------------------------------------------------------ dry-run

def test_le_dry_run_ne_touche_a_rien(conso, repo, capsys):
    atlas_minimal(repo)
    repo.extra_photo("chene-1.jpg")
    repo.contribution("app.tsv", "tag\tchene-1.jpg\tfeuille\n")

    assert conso.main([]) == 0

    assert "rien n'a été modifié" in capsys.readouterr().out
    assert sidecar(repo) == {} and os.path.exists(repo.contributions + "/app.tsv")


def test_sans_contribution_il_n_y_a_rien_a_faire(conso, repo, capsys):
    atlas_minimal(repo)

    assert conso.main(["--apply"]) == 0
    assert "Rien à consolider" in capsys.readouterr().out


# --------------------------------------------------------------------------- tag

def test_tag_ecrit_l_entree_d_aspects(conso, repo):
    atlas_minimal(repo)
    repo.extra_photo("chene-1.jpg")
    repo.contribution("app.tsv", "action\tfichier\tvaleur\ntag\tchene-1.jpg\tfeuille,fleur\n")

    assert conso.main(["--apply"]) == 0

    assert sidecar(repo) == {"chene-1.jpg": "feuille,fleur"}


def test_tag_peut_annoter_une_vignette(conso, repo):
    atlas_minimal(repo)
    repo.contribution("app.tsv", "tag\tchene.jpg\tport\n")

    assert conso.main(["--apply"]) == 0

    assert sidecar(repo)["chene.jpg"] == "port"


def test_tag_deja_en_place_n_apparait_pas_dans_le_plan(conso, repo):
    atlas_minimal(repo)
    repo.extra_photo("chene-1.jpg")
    repo.sidecar("fichier\taspects\nchene-1.jpg\tfeuille\n")
    repo.contribution("app.tsv", "tag\tchene-1.jpg\tfeuille\n")

    actions, notes, errs = conso.lire_contributions()
    plan, errs2 = conso.plan_de_consolidation(actions, notes, {"chene", "hetre"})

    assert (errs, errs2) == ([], [])
    assert plan["tags"] == {}, "rien à réécrire si l'entrée est déjà la bonne"
    assert conso.main(["--apply"]) == 0
    assert sidecar(repo)["chene-1.jpg"] == "feuille"


def test_tag_avec_aspect_inconnu_bloque_tout(conso, repo, capsys):
    atlas_minimal(repo)
    repo.extra_photo("chene-1.jpg")
    repo.extra_photo("chene-2.jpg")
    repo.contribution("app.tsv", "tag\tchene-1.jpg\tfeuille\ntag\tchene-2.jpg\tecorse\n")

    assert conso.main(["--apply"]) == 1

    out = capsys.readouterr().out
    assert "ecorse" in out and "rien n'a été modifié" in out
    assert sidecar(repo) == {}, "aucune action ne doit passer"
    assert os.path.exists(repo.contributions + "/app.tsv")


def test_tag_sans_aspect_est_une_erreur(conso, repo):
    atlas_minimal(repo)
    repo.extra_photo("chene-1.jpg")
    repo.contribution("app.tsv", "tag\tchene-1.jpg\t\n")

    assert conso.main(["--apply"]) == 1


# ---------------------------------------------------------------------- reassign

def test_reassign_renomme_vers_la_bonne_espece(conso, repo):
    atlas_minimal(repo)
    repo.extra_photo("chene-feuille-1.jpg")
    repo.contribution("app.tsv", "reassign\tchene-feuille-1.jpg\thetre\n")

    assert conso.main(["--apply"]) == 0

    assert extras(repo) == ["hetre-feuille-1.jpg"]
    assert sidecar(repo) == {}, "le nom porte déjà l'aspect, pas besoin d'entrée"


def test_reassign_prend_le_premier_numero_libre(conso, repo):
    atlas_minimal(repo)
    repo.extra_photo("chene-feuille-9.jpg")
    repo.extra_photo("hetre-feuille-1.jpg")
    repo.extra_photo("hetre-feuille-2.jpg")
    repo.contribution("app.tsv", "reassign\tchene-feuille-9.jpg\thetre\n")

    assert conso.main(["--apply"]) == 0

    assert "hetre-feuille-3.jpg" in extras(repo)


def test_reassign_conserve_un_aspect_venu_du_sidecar(conso, repo):
    atlas_minimal(repo)
    repo.extra_photo("chene-1.jpg")
    repo.sidecar("fichier\taspects\nchene-1.jpg\tport\n")
    repo.contribution("app.tsv", "reassign\tchene-1.jpg\thetre\n")

    assert conso.main(["--apply"]) == 0

    assert extras(repo) == ["hetre-port-1.jpg"]
    assert "chene-1.jpg" not in sidecar(repo)


def test_reassign_d_une_photo_sans_aspect(conso, repo):
    atlas_minimal(repo)
    repo.extra_photo("chene-1.jpg")
    repo.contribution("app.tsv", "reassign\tchene-1.jpg\thetre\n")

    assert conso.main(["--apply"]) == 0

    assert extras(repo) == ["hetre-1.jpg"]


def test_reassign_vers_un_stem_inconnu_bloque(conso, repo, capsys):
    atlas_minimal(repo)
    repo.extra_photo("chene-1.jpg")
    repo.contribution("app.tsv", "reassign\tchene-1.jpg\tespece_fantome\n")

    assert conso.main(["--apply"]) == 1

    assert "espece_fantome" in capsys.readouterr().out
    assert extras(repo) == ["chene-1.jpg"]


def test_une_vignette_ne_se_reassigne_pas(conso, repo, capsys):
    atlas_minimal(repo)
    repo.contribution("app.tsv", "reassign\tchene.jpg\thetre\n")

    assert conso.main(["--apply"]) == 1
    assert "vignette" in capsys.readouterr().out


# ------------------------------------------------------------------------ remove

def test_remove_supprime_la_photo_et_son_entree(conso, repo):
    atlas_minimal(repo)
    repo.extra_photo("chene-1.jpg")
    repo.extra_photo("chene-2.jpg")
    repo.sidecar("fichier\taspects\nchene-1.jpg\tfeuille\nchene-2.jpg\tport\n")
    repo.contribution("app.tsv", "remove\tchene-1.jpg\t\n")

    assert conso.main(["--apply"]) == 0

    assert extras(repo) == ["chene-2.jpg"]
    assert sidecar(repo) == {"chene-2.jpg": "port"}


def test_une_vignette_ne_se_supprime_pas(conso, repo, capsys):
    atlas_minimal(repo)
    repo.contribution("app.tsv", "remove\tchene.jpg\t\n")

    assert conso.main(["--apply"]) == 1

    assert "vignette" in capsys.readouterr().out
    assert os.path.exists(os.path.join(repo.img, "chene.jpg"))


def test_remove_gagne_sur_un_tag_du_meme_fichier(conso, repo):
    """Cas réel du dépôt : une photo taggée « divers » puis signalée à retirer."""
    atlas_minimal(repo)
    repo.extra_photo("chene-1.jpg")
    repo.contribution("app.tsv", "tag\tchene-1.jpg\tdivers\nremove\tchene-1.jpg\t\n")

    assert conso.main(["--apply"]) == 0

    assert extras(repo) == []
    assert sidecar(repo) == {}, "pas d'entrée morte pour une photo supprimée"


# -------------------------------------------------------------- notes et nettoyage

def test_les_commentaires_partent_dans_les_notes(conso, repo):
    atlas_minimal(repo)
    repo.extra_photo("chene-1.jpg")
    repo.contribution("app.tsv",
                      "# il manque une écorce de chêne\n"
                      "action\tfichier\tvaleur\n"
                      "tag\tchene-1.jpg\tfeuille\n")

    assert conso.main(["--apply"]) == 0

    notes = open(os.path.join(repo.contributions, "NOTES.md"), encoding="utf-8").read()
    assert "il manque une écorce de chêne" in notes
    assert "app.tsv" in notes, "la note garde sa provenance"


def test_le_fichier_traite_est_supprime_et_l_operation_est_idempotente(conso, repo, capsys):
    atlas_minimal(repo)
    repo.extra_photo("chene-1.jpg")
    repo.contribution("app.tsv", "tag\tchene-1.jpg\tfeuille\n")

    assert conso.main(["--apply"]) == 0
    assert not os.path.exists(os.path.join(repo.contributions, "app.tsv"))

    capsys.readouterr()
    assert conso.main(["--apply"]) == 0
    assert "Rien à consolider" in capsys.readouterr().out


def test_fichier_cible_absent_bloque(conso, repo, capsys):
    atlas_minimal(repo)
    repo.contribution("app.tsv", "tag\tphoto-fantome.jpg\tfeuille\n")

    assert conso.main(["--apply"]) == 1
    assert "photo-fantome.jpg" in capsys.readouterr().out


def test_option_inconnue(conso, repo):
    atlas_minimal(repo)

    assert conso.main(["--force"]) == 2
