#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Outillage commun aux tests.

Les tests de parsing travaillent sur un **faux dépôt** monté dans un dossier temporaire
(fixture `repo`) : le contenu réel des atlas bouge à chaque contribution, il ne peut pas
servir de référence. Seul `test_build_smoke.py` s'appuie sur les vrais atlas.
"""
import importlib.util
import os
import sys

import pytest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)   # les scripts s'importent entre eux par leur nom

# En-tête par défaut des atlas de test : couvre les colonnes utiles au parseur.
HEADER = ["Photo", "Espèce", "Nom latin", "Type", "Famille", "Comestible", "Notes"]


def load_module(name):
    """Charge un script du dossier scripts/ comme module isolé (une instance par appel)."""
    spec = importlib.util.spec_from_file_location(name, os.path.join(BASE, "scripts", name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def atlas_data():
    """La couche de données (scripts/atlas_data.py), rechargée pour chaque test.

    Le module lit le dépôt à l'import (CORR/SIDE/CONF) : une instance neuve par test évite
    que la fixture `repo` d'un test fuite dans le suivant.
    """
    return load_module("atlas_data")


class FakeRepo:
    """Faux dépôt : atlas Markdown + images factices, avec les globales du module redirigées."""

    def __init__(self, root, module, monkeypatch):
        self.root = str(root)
        self.atlas_data = module
        self.monkeypatch = monkeypatch
        self.img = os.path.join(self.root, "img", "especes")
        self.extra = os.path.join(self.root, "img", "quiz-extra")
        self.contributions = os.path.join(self.root, "contributions")
        for d in (self.img, self.extra, self.contributions):
            os.makedirs(d, exist_ok=True)
        monkeypatch.setattr(module, "BASE", self.root)
        monkeypatch.setattr(module, "IMG", self.img)
        monkeypatch.setattr(module, "EXTRA", self.extra)
        self.reload()

    def reload(self):
        """Recharge les données annexes après écriture d'un sidecar / d'une contribution."""
        self.atlas_data.CORR = self.atlas_data.load_corrections()
        self.atlas_data.SIDE = self.atlas_data.load_sidecar()
        self.atlas_data.CONF = self.atlas_data.load_confusions()

    def write(self, rel, text):
        p = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)
        return p

    def photo(self, rel):
        """Crée une image factice : le parseur ne teste que l'existence du fichier."""
        p = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "wb") as f:
            f.write(b"\xff\xd8\xff\xd9")
        return p

    def vignette(self, filename):
        return self.photo(os.path.join("img", "especes", filename))

    def extra_photo(self, filename):
        return self.photo(os.path.join("img", "quiz-extra", filename))

    def write_atlas(self, name, rows, header=None):
        """Écrit un atlas Markdown. `rows` = listes de cellules (la 1re est la vignette)."""
        header = header or HEADER
        lines = ["# Atlas de test", "", "| " + " | ".join(header) + " |",
                 "|" + "|".join(["---"] * len(header)) + "|"]
        lines += ["| " + " | ".join(r) + " |" for r in rows]
        return self.write(name, "\n".join(lines) + "\n")

    def use_atlases(self, *names, cat="test"):
        """Déclare les atlas du faux dépôt comme seuls atlas connus (pour les outils qui
        parcourent ATLASES, comme le vérificateur)."""
        self.monkeypatch.setattr(self.atlas_data, "ATLASES", [(n, cat) for n in names])

    def sidecar(self, text):
        p = self.write(os.path.join("img", "quiz-extra", "_aspects.tsv"), text)
        self.reload()
        return p

    def contribution(self, name, text):
        p = self.write(os.path.join("contributions", name), text)
        self.reload()
        return p

    def confusions(self, rows):
        lines = ["# Confusions", "", "| Groupe | Espèces | Ce qui tranche |", "|---|---|---|"]
        lines += ["| " + " | ".join(r) + " |" for r in rows]
        p = self.write("Confusions - référence.md", "\n".join(lines) + "\n")
        self.reload()
        return p

    def parse(self, name, cat="test", seen=None):
        return self.atlas_data.parse_atlas(name, cat, set() if seen is None else seen)


@pytest.fixture
def repo(tmp_path, atlas_data, monkeypatch):
    return FakeRepo(tmp_path, atlas_data, monkeypatch)


def vignette_cell(filename):
    """Cellule photo au format Obsidian utilisé par les atlas : ![[fichier.jpg|200]]."""
    return "![[%s\\|200]]" % filename
