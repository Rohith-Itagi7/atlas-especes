#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lecture d'un atlas Markdown : lignes retenues, champs, vignettes, photos supplémentaires."""
from conftest import vignette_cell


def ligne(vignette, name, latin, type_="arbre", famille="Fagacées", comestible="glands", notes=""):
    return [vignette_cell(vignette), name, latin, type_, famille, comestible, notes]


def test_lit_les_especes_et_leurs_champs(repo):
    repo.vignette("chene.jpg")
    repo.write_atlas("Test.md", [ligne("chene.jpg", "Chêne test", "Quercus testus", notes="note libre")])

    got = repo.parse("Test.md", "ligneux")

    assert len(got) == 1
    s = got[0]
    assert (s["id"], s["stem"], s["name"], s["latin"], s["cat"]) == (
        "chene", "chene", "Chêne test", "Quercus testus", "ligneux")
    assert s["fields"]["type"] == "arbre"
    assert s["fields"]["famille"] == "Fagacées"
    assert s["fields"]["comestible"] == "glands"
    assert s["note"] == "note libre"


def test_exclut_le_nom_le_latin_et_la_photo_des_champs(repo):
    repo.vignette("chene.jpg")
    repo.write_atlas("Test.md", [ligne("chene.jpg", "Chêne test", "Quercus testus")])

    fields = repo.parse("Test.md")[0]["fields"]

    assert "name" not in fields and "latin" not in fields and "photo" not in fields


def test_ignore_les_cellules_vides_et_les_tirets(repo):
    repo.vignette("chene.jpg")
    repo.write_atlas("Test.md", [ligne("chene.jpg", "Chêne test", "Quercus testus",
                                 famille="", comestible="—", notes="-")])

    fields = repo.parse("Test.md")[0]["fields"]

    assert "famille" not in fields      # cellule vide
    assert "comestible" not in fields   # tiret cadratin = donnée absente
    assert "notes" not in fields        # tiret simple aussi


def test_saute_une_ligne_sans_nom(repo):
    repo.vignette("chene.jpg")
    repo.write_atlas("Test.md", [ligne("chene.jpg", "", "Quercus testus")])

    assert repo.parse("Test.md") == []


def test_saute_une_ligne_dont_la_vignette_est_absente(repo, capsys):
    # Pas de repo.vignette(...) : le fichier n'existe pas.
    repo.write_atlas("Test.md", [ligne("fantome.jpg", "Espèce fantôme", "Nihil nihil")])

    got = repo.parse("Test.md")

    assert got == []
    assert "vignette absente" in capsys.readouterr().out


def test_ignore_les_lignes_hors_tableau(repo):
    repo.vignette("chene.jpg")
    repo.write_atlas("Test.md", [ligne("chene.jpg", "Chêne test", "Quercus testus")])
    with open(repo.root + "/Test.md", "a", encoding="utf-8") as f:
        f.write("\n> [!note] Une callout Obsidian avec le mot latin dedans.\n\ntexte libre\n")

    assert len(repo.parse("Test.md")) == 1


def test_attache_les_photos_supplementaires(repo):
    repo.vignette("chene.jpg")
    repo.extra_photo("chene-feuille-1.jpg")
    repo.extra_photo("chene-ecorce-1.jpg")
    repo.extra_photo("autre-feuille-1.jpg")
    repo.write_atlas("Test.md", [ligne("chene.jpg", "Chêne test", "Quercus testus")])

    paths = [p.rsplit("/", 1)[-1] for p in repo.parse("Test.md")[0]["paths"]]

    assert paths[0] == "chene.jpg"                      # la vignette reste en tête
    assert sorted(paths[1:]) == ["chene-ecorce-1.jpg", "chene-feuille-1.jpg"]
    assert "autre-feuille-1.jpg" not in paths


def test_un_stem_deja_vu_est_suffixe_par_la_categorie(repo):
    repo.vignette("sureau.jpg")
    repo.write_atlas("Ligneux.md", [ligne("sureau.jpg", "Sureau noir", "Sambucus nigra")])
    repo.write_atlas("Herbacees.md", [ligne("sureau.jpg", "Sureau yèble", "Sambucus ebulus")])

    seen = set()
    a = repo.parse("Ligneux.md", "ligneux", seen)
    b = repo.parse("Herbacees.md", "herbace", seen)

    assert a[0]["id"] == "sureau"
    assert b[0]["id"] == "sureau_herbace"   # id unique, même vignette partagée
    assert b[0]["stem"] == "sureau"


def test_entete_absente_les_champs_ne_sont_pas_mappes(repo):
    # Un tableau sans colonne « latin » : le parseur ne trouve pas d'en-tête.
    repo.vignette("chene.jpg")
    repo.write("Test.md", "| Photo | Espèce |\n|---|---|\n| %s | Chêne test |\n"
               % vignette_cell("chene.jpg"))

    assert repo.parse("Test.md") == []
