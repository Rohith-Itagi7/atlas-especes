#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contributions : lecture des TSV d'actions (tag / reassign / remove) et application."""
import os

from conftest import vignette_cell


def ligne(vignette, name, latin):
    return [vignette_cell(vignette), name, latin, "arbre", "Fagacées", "glands", ""]


def noms(paths):
    return [os.path.basename(p) for p in paths]


# ------------------------------------------------------------------ lecture des TSV

def test_lit_les_trois_actions(repo):
    repo.contribution("app-test.tsv",
                      "action\tfichier\tvaleur\n"
                      "tag\tchene-1.jpg\tfeuille,fleur\n"
                      "reassign\tchene-2.jpg\thetre\n"
                      "remove\tchene-3.jpg\t\n")

    tags, reassign, remove = repo.gq.CORR

    assert tags == {"chene-1.jpg": ["feuille", "fleur"]}
    assert reassign == {"chene-2.jpg": "hetre"}
    assert remove == {"chene-3.jpg"}


def test_ignore_entete_commentaires_et_lignes_sans_tabulation(repo):
    repo.contribution("app-test.tsv",
                      "action\tfichier\tvaleur\n"
                      "# manque une photo d'écorce pour le chêne\n"
                      "ligne sans tabulation\n"
                      "\n"
                      "tag\tchene-1.jpg\tport\n")

    tags, reassign, remove = repo.gq.CORR

    assert tags == {"chene-1.jpg": ["port"]}
    assert reassign == {} and remove == set()


def test_action_inconnue_ignoree(repo):
    repo.contribution("app-test.tsv", "action\tfichier\tvaleur\nrenomme\tchene-1.jpg\thetre\n")

    tags, reassign, remove = repo.gq.CORR

    assert (tags, reassign, remove) == ({}, {}, set())


def test_reassign_annule_un_remove_precedent(repo):
    # Ordre voulu : un fichier d'abord signalé à retirer, puis réattribué → il est déplacé.
    repo.contribution("a.tsv", "remove\tchene-1.jpg\t\n")
    repo.contribution("b.tsv", "reassign\tchene-1.jpg\thetre\n")

    _tags, reassign, remove = repo.gq.CORR

    assert reassign == {"chene-1.jpg": "hetre"}
    assert remove == set()


def test_les_fichiers_de_contribution_sont_lus_dans_l_ordre(repo):
    repo.contribution("a.tsv", "tag\tchene-1.jpg\tfeuille\n")
    repo.contribution("b.tsv", "tag\tchene-1.jpg\tport\n")

    # Ordre alphabétique des fichiers : le dernier gagne. Les noms produits par l'app étant
    # horodatés (app-AAAA-MM-JJ-…), cela revient à donner le dernier mot à la plus récente.
    assert repo.gq.CORR[0]["chene-1.jpg"] == ["port"]


# ------------------------------------------------------------ application aux espèces

def test_remove_retire_la_photo(repo):
    repo.vignette("chene.jpg")
    repo.extra_photo("chene-1.jpg")
    repo.extra_photo("chene-2.jpg")
    repo.atlas("Test.md", [ligne("chene.jpg", "Chêne test", "Quercus testus")])
    repo.contribution("app-test.tsv", "remove\tchene-1.jpg\t\n")

    got = repo.gq.apply_corrections(repo.parse("Test.md"))

    assert noms(got[0]["paths"]) == ["chene.jpg", "chene-2.jpg"]


def test_reassign_deplace_la_photo_vers_la_bonne_espece(repo):
    repo.vignette("chene.jpg")
    repo.vignette("hetre.jpg")
    repo.extra_photo("chene-1.jpg")
    repo.atlas("Test.md", [ligne("chene.jpg", "Chêne test", "Quercus testus"),
                           ligne("hetre.jpg", "Hêtre test", "Fagus testus")])
    repo.contribution("app-test.tsv", "reassign\tchene-1.jpg\thetre\n")

    got = repo.gq.apply_corrections(repo.parse("Test.md"))
    par_stem = {s["stem"]: noms(s["paths"]) for s in got}

    assert par_stem["chene"] == ["chene.jpg"]
    assert par_stem["hetre"] == ["hetre.jpg", "chene-1.jpg"]


def test_reassign_vers_un_stem_inconnu_perd_la_photo(repo):
    repo.vignette("chene.jpg")
    repo.extra_photo("chene-1.jpg")
    repo.atlas("Test.md", [ligne("chene.jpg", "Chêne test", "Quercus testus")])
    repo.contribution("app-test.tsv", "reassign\tchene-1.jpg\tespece_qui_nexiste_pas\n")

    got = repo.gq.apply_corrections(repo.parse("Test.md"))

    # La photo quitte le chêne sans arriver ailleurs : c'est le contrôle CI qui doit
    # rattraper ce cas (une cible inconnue est une erreur de contribution).
    assert noms(got[0]["paths"]) == ["chene.jpg"]


def test_une_espece_sans_photo_est_retiree(repo, capsys):
    repo.vignette("chene.jpg")
    repo.atlas("Test.md", [ligne("chene.jpg", "Chêne test", "Quercus testus")])
    repo.contribution("app-test.tsv", "remove\tchene.jpg\t\n")

    got = repo.gq.apply_corrections(repo.parse("Test.md"))

    assert got == []
    assert "sans photo après corrections" in capsys.readouterr().out


def test_sans_contribution_les_especes_sont_inchangees(repo):
    repo.vignette("chene.jpg")
    repo.extra_photo("chene-feuille-1.jpg")
    repo.atlas("Test.md", [ligne("chene.jpg", "Chêne test", "Quercus testus")])

    especes = repo.parse("Test.md")
    avant = noms(especes[0]["paths"])

    assert noms(repo.gq.apply_corrections(especes)[0]["paths"]) == avant
