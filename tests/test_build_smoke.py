#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test de bout en bout du build du site, sur les **vrais** atlas.

Contrairement aux autres tests, celui-ci dépend du contenu du dépôt : il vérifie que le
pipeline complet tourne et que ses invariants tiennent, pas des valeurs figées (le nombre
d'espèces est lu, pas codé en dur — il augmente à chaque contribution).
"""
import json
import os
import re
import subprocess
import sys

from conftest import BASE, load_module


def species_data(html):
    """Extrait le tableau de données injecté dans la page."""
    m = re.search(r"SPECIES_DATA\s*=\s*(\[.*?\])\s*;", html, re.S)
    assert m, "SPECIES_DATA introuvable dans index.html"
    return json.loads(m.group(1))


def test_le_build_produit_un_site_complet(tmp_path):
    out = tmp_path / "_site"
    r = subprocess.run([sys.executable, os.path.join("scripts", "build_web.py"), str(out)],
                       cwd=BASE, capture_output=True, text=True)

    assert r.returncode == 0, r.stderr
    assert "image absente" not in r.stdout, r.stdout      # toute image référencée existe
    assert "vignette absente" not in r.stdout, r.stdout   # toute espèce a sa vignette

    m = re.search(r"TOTAL : (\d+) espèces, (\d+) images", r.stdout)
    assert m, r.stdout
    n_especes, n_images = int(m.group(1)), int(m.group(2))
    assert n_especes > 200 and n_images > n_especes

    index = out / "index.html"
    assert index.exists() and index.stat().st_size > 50_000
    assert (out / ".nojekyll").exists()

    html = index.read_text(encoding="utf-8")
    data = species_data(html)
    assert len(data) == n_especes


def test_chaque_espece_du_site_a_le_minimum_vital(tmp_path):
    out = tmp_path / "_site"
    subprocess.run([sys.executable, os.path.join("scripts", "build_web.py"), str(out)],
                   cwd=BASE, capture_output=True, text=True, check=True)
    data = species_data((out / "index.html").read_text(encoding="utf-8"))

    ids = [s["id"] for s in data]
    assert len(ids) == len(set(ids)), "identifiants d'espèces dupliqués"
    for s in data:
        assert s["name"], s
        assert s["imgs"], "espèce sans photo : %s" % s["name"]
        for im in s["imgs"]:
            assert im["u"].startswith(("img/especes/", "img/quiz-extra/"))
            assert im["a"], "photo sans aspect : %s" % im["u"]
            assert (out / im["u"]).exists(), "image non copiée : %s" % im["u"]


def test_le_verdict_comestible_est_calcule_au_build():
    """Le mode Oui/Non lit le champ « edible » : il doit exister exactement pour les espèces
    dont l'atlas renseigne « Comestible » (côté JS, c'est le test `has` du critère)."""
    atlas_data = load_module("atlas_data")
    bw = load_module("build_web")

    especes, seen = [], set()
    for path, cat in atlas_data.ATLASES:
        especes += atlas_data.parse_atlas(path, cat, seen)
    data = bw.to_web_data(atlas_data.apply_corrections(especes))

    avec_colonne = [s for s in data if "comestible" in s["fields"]]
    assert avec_colonne, "aucune espèce avec une colonne « Comestible »"
    for s in data:
        assert ("edible" in s) == ("comestible" in s["fields"]), s["name"]
        if "edible" in s:
            assert s["edible"] == atlas_data.is_edible(s["fields"]["comestible"])
    # Le quiz Oui/Non n'a d'intérêt que si les deux réponses existent.
    verdicts = {s["edible"] for s in avec_colonne}
    assert verdicts == {True, False}


def test_les_astuces_de_confusion_sont_injectees():
    atlas_data = load_module("atlas_data")
    bw = load_module("build_web")

    especes, seen = [], set()
    for path, cat in atlas_data.ATLASES:
        especes += atlas_data.parse_atlas(path, cat, seen)
    data = bw.to_web_data(atlas_data.apply_corrections(especes))

    assert atlas_data.CONF, "aucun groupe de confusion lu"
    avec_conf = [s for s in data if s["conf"]]
    assert avec_conf, "aucune espèce ne porte d'astuce « Ne pas confondre »"
