#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Comparateur de réponses du quiz : le **JS réellement livré**, exécuté sous node.

Le bloc `// __MATCH_DEBUT__ … // __MATCH_FIN__` de scripts/site_ui.py est extrait et joué
dans une classe minimale, avec les vraies données du site. C'est le seul moyen de tester
la logique de notation sans la réécrire en Python (une deuxième implémentation dériverait).

Les tests sont ignorés si node n'est pas installé ; les runners GitHub en ont un.
"""
import json
import os
import re
import shutil
import subprocess

import pytest

from conftest import BASE, load_module

pytestmark = pytest.mark.skipif(shutil.which("node") is None,
                                reason="node absent : comparateur JS non testé")

HARNESS = """
class Quiz {
  constructor(data){ this.data = data; }
  all(){ return this.data; }
__METHODES__
}
const app = new Quiz(__DATA__);
const trouve = n => app.all().find(s => s.name === n);
console.log(JSON.stringify(__CAS__.map(c => {
  const sp = trouve(c[1]);
  if (!sp) throw new Error('espèce absente des données : ' + c[1]);
  return app.answerOk(c[0], sp, c[2] || false);
})));
"""


def matcher_js():
    """Le bloc du comparateur, tel qu'il part dans index.html."""
    src = open(os.path.join(BASE, "scripts", "site_ui.py"), encoding="utf-8").read()
    # le reste de la ligne du marqueur est un commentaire : on part de la ligne suivante
    m = re.search(r"// __MATCH_DEBUT__[^\n]*\n(.*?)// __MATCH_FIN__", src, re.S)
    assert m, "bloc du comparateur introuvable dans scripts/site_ui.py"
    return m.group(1)


def answer_ok(cas, data):
    """Joue les cas (saisie, nom de l'espèce visée, exact ?) sous node."""
    js = (HARNESS.replace("__METHODES__", matcher_js())
                 .replace("__DATA__", json.dumps(data, ensure_ascii=False))
                 .replace("__CAS__", json.dumps(cas, ensure_ascii=False)))
    r = subprocess.run(["node", "-e", js], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


@pytest.fixture(scope="module")
def site_data():
    """Les espèces telles que le build les injecte (nom, id, orthographes acceptées)."""
    atlas_data = load_module("atlas_data")
    build_web = load_module("build_web")
    especes, seen = [], set()
    for path, cat in atlas_data.ATLASES:
        especes += atlas_data.parse_atlas(path, cat, seen)
    data = build_web.to_web_data(atlas_data.apply_corrections(especes))
    return [{"id": s["id"], "name": s["name"], "alt": s["alt"]} for s in data]


# ------------------------------------------------- les cas de l'issue, sur les vraies données

CAS_ACCEPTES = [
    ("Chalef", "Chalef / Olivier de Bohême"),
    ("Olivier de Bohême", "Chalef / Olivier de Bohême"),
    ("olivier de boheme", "Chalef / Olivier de Bohême"),      # sans accents ni casse
    ("Cassissier", "Cassissier / Groseillier"),
    ("Groseillier", "Cassissier / Groseillier"),
    ("Caragana", "Caragana (arbre à pois)"),
    ("arbre à pois", "Caragana (arbre à pois)"),
    ("Usnée", "Usnée (barbe de Jupiter)"),
    ("Camérisier", "Chèvrefeuille comestible (camérisier)"),
    ("Chèvrefeuille comestible", "Chèvrefeuille comestible (camérisier)"),
    ("Quercus petraea", "Chêne sessile"),                     # nom latin
    ("petraea", "Chêne sessile"),                             # épithète seule
    ("Aulne glutineu", "Aulne glutineux"),                    # une lettre manquante
    ("Aulne glutineux!", "Aulne glutineux"),                  # ponctuation ignorée
    ("Chêne sessil", "Chêne sessile"),                        # faute de frappe
]

CAS_REFUSES = [
    ("Chêne pédonculé", "Chêne sessile"),      # une autre espèce, bien orthographiée
    ("Pin maritime", "Pin sylvestre"),
    ("Chêne", "Chêne sessile"),                # trop vague : plusieurs chênes dans l'atlas
    ("", "Chêne sessile"),
    ("   ", "Chêne sessile"),
    ("Orti", "Ortie"),                         # nom court : pas de tolérance
    ("n'importe quoi", "Chêne sessile"),
]


def test_reponses_acceptees(site_data):
    got = answer_ok([[t, n] for t, n in CAS_ACCEPTES], site_data)

    refuses = [c for c, ok in zip(CAS_ACCEPTES, got) if not ok]
    assert not refuses, "comptées fausses à tort : %s" % refuses


def test_reponses_refusees(site_data):
    got = answer_ok([[t, n] for t, n in CAS_REFUSES], site_data)

    acceptees = [c for c, ok in zip(CAS_REFUSES, got) if ok]
    assert not acceptees, "comptées justes à tort : %s" % acceptees


def test_mode_qcm_sans_tolerance(site_data):
    # Les libellés du QCM viennent des données : une « presque » réponse n'est pas la réponse.
    exacte, presque = answer_ok([["Chêne sessile", "Chêne sessile", True],
                                 ["Chêne sessil", "Chêne sessile", True]], site_data)

    assert exacte is True
    assert presque is False


# ------------------------------------------- garde-fou d'ambiguïté (deux espèces proches)

VOISINES = [
    {"id": "a", "name": "Aubépine lisse", "alt": ["Aubépine lisse"]},
    {"id": "b", "name": "Aubépine lissa", "alt": ["Aubépine lissa"]},
]


def test_faute_ambigue_refusee_pour_les_deux_especes():
    # « lisss » est à une faute des deux noms : impossible de trancher, donc faux.
    got = answer_ok([["Aubépine lisss", "Aubépine lisse"],
                     ["Aubépine lisss", "Aubépine lissa"]], VOISINES)

    assert got == [False, False]


def test_le_nom_exact_d_une_voisine_reste_faux():
    got = answer_ok([["Aubépine lisse", "Aubépine lissa"]], VOISINES)

    assert got == [False]


def test_chaque_voisine_reste_acceptee_sur_son_propre_nom():
    got = answer_ok([["Aubépine lisse", "Aubépine lisse"],
                     ["Aubépine lissa", "Aubépine lissa"]], VOISINES)

    assert got == [True, True]
