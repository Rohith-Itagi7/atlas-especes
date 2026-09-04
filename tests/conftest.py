#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Outillage commun aux tests.

Les tests de parsing travaillent sur un **faux dépôt** monté dans un dossier temporaire
(fixture `repo`) : le contenu réel des atlas bouge à chaque contribution, il ne peut pas
servir de référence. Seul `test_build_smoke.py` s'appuie sur les vrais atlas.
"""
import importlib.util
import os

import pytest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# En-tête par défaut des atlas de test : couvre les colonnes utiles au parseur.
HEADER = ["Photo", "Espèce", "Nom latin", "Type", "Famille", "Comestible", "Notes"]


def load_module(name):
    """Charge un script du dossier scripts/ comme module isolé (une instance par appel)."""
    spec = importlib.util.spec_from_file_location(name, os.path.join(BASE, "scripts", name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def gq():
    """Le module de données (parseur des atlas), rechargé pour chaque test.

    Le module lit le dépôt à l'import (CORR/SIDE/CONF) : une instance neuve par test évite
    que la fixture `repo` d'un test fuite dans le suivant.
    """
    return load_module("generer_quiz")


class FakeRepo:
    """Faux dépôt : atlas Markdown + images factices, avec les globales du module redirigées."""

    def __init__(self, root, module, monkeypatch):
        self.root = str(root)
        self.gq = module
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
        self.gq.CORR = self.gq.load_corrections()
        self.gq.SIDE = self.gq.load_sidecar()
        self.gq.CONF = self.gq.load_confusions()

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

    def atlas(self, name, rows, header=None):
        """Écrit un atlas Markdown. `rows` = listes de cellules (la 1re est la vignette)."""
        header = header or HEADER
        lines = ["# Atlas de test", "", "| " + " | ".join(header) + " |",
                 "|" + "|".join(["---"] * len(header)) + "|"]
        lines += ["| " + " | ".join(r) + " |" for r in rows]
        return self.write(name, "\n".join(lines) + "\n")

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
        return self.gq.parse_atlas(name, cat, set() if seen is None else seen)


@pytest.fixture
def repo(tmp_path, gq, monkeypatch):
    return FakeRepo(tmp_path, gq, monkeypatch)


def vignette_cell(filename):
    """Cellule photo au format Obsidian utilisé par les atlas : ![[fichier.jpg|200]]."""
    return "![[%s\\|200]]" % filename
