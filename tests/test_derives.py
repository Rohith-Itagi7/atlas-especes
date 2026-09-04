#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dérivés d'images du build (scripts/derives.py).

La grille de l'atlas affiche 251 cartes de ~227 px en servant les fichiers d'origine
(~18 Mo au total) : on y met des vignettes légères (cf. #13). Pillow est une dépendance du
build seulement — sans elle, le site doit se construire comme avant.
"""
import os

import pytest

from conftest import load_module

PIL = pytest.importorskip("PIL", reason="Pillow absent : dérivés non testés")
from PIL import Image  # noqa: E402  (après importorskip)


@pytest.fixture
def der():
    return load_module("derives")


def image(chemin, taille=(600, 400), couleur=(90, 140, 60)):
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    Image.new("RGB", taille, couleur).save(chemin, "JPEG", quality=90)
    return chemin


# ------------------------------------------------------------------- génération

def test_la_vignette_est_plus_petite_et_plus_legere(der, tmp_path):
    src = image(str(tmp_path / "src" / "chene.jpg"), (900, 600))
    out = str(tmp_path / "site")
    os.makedirs(out)

    d = der.Deriveur(out)
    rel = d.thumb(src, "img/especes/chene.jpg")
    d.cloturer()

    assert rel == "img/thumb/chene.jpg"
    produit = os.path.join(out, rel)
    with Image.open(produit) as im:
        assert max(im.size) == der.LARGEUR_THUMB
        assert im.size == (der.LARGEUR_THUMB, round(der.LARGEUR_THUMB * 600 / 900))
    assert os.path.getsize(produit) < os.path.getsize(src)


def test_une_petite_image_n_est_pas_agrandie(der, tmp_path):
    src = image(str(tmp_path / "src" / "petit.jpg"), (120, 80))
    out = str(tmp_path / "site")
    os.makedirs(out)

    rel = der.Deriveur(out).thumb(src, "img/quiz-extra/petit.jpg")

    with Image.open(os.path.join(out, rel)) as im:
        assert im.size == (120, 80), "thumbnail() ne fait que réduire"


def test_les_dimensions_sont_lues(der, tmp_path):
    src = image(str(tmp_path / "src" / "x.jpg"), (640, 480))

    assert der.dimensions(src) == (640, 480)
    assert der.dimensions(str(tmp_path / "absent.jpg")) is None


def test_un_fichier_illisible_retombe_sur_l_original(der, tmp_path, capsys):
    faux = tmp_path / "src" / "casse.jpg"
    faux.parent.mkdir(parents=True, exist_ok=True)
    faux.write_bytes(b"ceci n'est pas une image")
    out = str(tmp_path / "site")
    os.makedirs(out)

    d = der.Deriveur(out)
    rel = d.thumb(str(faux), "img/especes/casse.jpg")

    assert rel == "img/especes/casse.jpg", "on sert l'original plutôt que rien"
    assert d.echecs == 1
    assert "vignette impossible" in capsys.readouterr().out


# ------------------------------------------------------------------------ cache

def test_le_second_build_ne_regenere_rien(der, tmp_path):
    src = image(str(tmp_path / "src" / "chene.jpg"))
    out = str(tmp_path / "site")
    os.makedirs(out)

    d1 = der.Deriveur(out)
    d1.thumb(src, "img/especes/chene.jpg")
    d1.cloturer()
    d2 = der.Deriveur(out)
    d2.thumb(src, "img/especes/chene.jpg")
    d2.cloturer()

    assert (d1.generes, d1.reutilises) == (1, 0)
    assert (d2.generes, d2.reutilises) == (0, 1)


def test_une_source_modifiee_est_regeneree(der, tmp_path):
    src = image(str(tmp_path / "src" / "chene.jpg"))
    out = str(tmp_path / "site")
    os.makedirs(out)
    d1 = der.Deriveur(out)
    d1.thumb(src, "img/especes/chene.jpg")
    d1.cloturer()

    image(src, (700, 500), (200, 30, 30))          # la photo a changé
    d2 = der.Deriveur(out)
    d2.thumb(src, "img/especes/chene.jpg")
    d2.cloturer()

    assert (d2.generes, d2.reutilises) == (1, 0)


def test_une_vignette_devenue_inutile_est_supprimee(der, tmp_path):
    a = image(str(tmp_path / "src" / "a.jpg"))
    b = image(str(tmp_path / "src" / "b.jpg"))
    out = str(tmp_path / "site")
    os.makedirs(out)
    d1 = der.Deriveur(out)
    d1.thumb(a, "img/especes/a.jpg")
    d1.thumb(b, "img/especes/b.jpg")
    d1.cloturer()

    d2 = der.Deriveur(out)          # b n'est plus référencée (photo retirée d'un atlas)
    d2.thumb(a, "img/especes/a.jpg")
    d2.cloturer()

    assert sorted(os.listdir(os.path.join(out, der.DOSSIER_THUMB))) == ["a.jpg"]


def test_manifeste_illisible_regenere_tout(der, tmp_path):
    src = image(str(tmp_path / "src" / "chene.jpg"))
    out = str(tmp_path / "site")
    os.makedirs(out)
    open(os.path.join(out, der.MANIFESTE), "w").write("{ pas du json")

    d = der.Deriveur(out)
    d.thumb(src, "img/especes/chene.jpg")

    assert d.generes == 1


# ------------------------------------------------------------- repli sans Pillow

def test_sans_pillow_on_sert_les_originaux(der, tmp_path, monkeypatch):
    monkeypatch.setattr(der, "PILLOW", False)
    src = image(str(tmp_path / "src" / "chene.jpg"))
    out = str(tmp_path / "site")
    os.makedirs(out)

    d = der.Deriveur(out)
    rel = d.thumb(src, "img/especes/chene.jpg")
    d.cloturer()

    assert rel == "img/especes/chene.jpg"
    assert not os.path.exists(os.path.join(out, der.DOSSIER_THUMB))
    assert "Pillow absent" in d.resume()
    assert der.dimensions(src) is None


# --------------------------------------------------------------- intégration build

def test_le_build_annonce_la_vignette_et_les_dimensions(repo, monkeypatch, tmp_path):
    build_web = load_module("build_web")
    der = load_module("derives")
    monkeypatch.setattr(build_web, "atlas_data", repo.atlas_data)
    monkeypatch.setattr(build_web, "BASE", repo.root)
    image(os.path.join(repo.img, "chene.jpg"), (800, 600))
    out = str(tmp_path / "site")
    os.makedirs(out)
    especes = [{"id": "chene", "stem": "chene", "name": "Chêne", "latin": "Quercus robur",
                "cat": "ligneux", "note": "", "fields": {},
                "paths": [os.path.join(repo.img, "chene.jpg")]}]

    im = build_web.to_web_data(especes, der.Deriveur(out))[0]["imgs"][0]

    assert im["u"] == "img/especes/chene.jpg"
    assert im["t"] == "img/thumb/chene.jpg"
    assert (im["w"], im["h"]) == (800, 600), "dimensions déclarées côté HTML"


def test_sans_deriveur_les_donnees_restent_comme_avant(repo, monkeypatch):
    build_web = load_module("build_web")
    monkeypatch.setattr(build_web, "atlas_data", repo.atlas_data)
    image(os.path.join(repo.img, "chene.jpg"))
    especes = [{"id": "chene", "stem": "chene", "name": "Chêne", "latin": "Quercus robur",
                "cat": "ligneux", "note": "", "fields": {},
                "paths": [os.path.join(repo.img, "chene.jpg")]}]

    im = build_web.to_web_data(especes)[0]["imgs"][0]

    assert set(im) == {"u", "a"}
