#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tirage des distracteurs du QCM : le **JS réellement livré**, exécuté sous node.

Le bloc `// __SOSIES_DEBUT__ … // __SOSIES_FIN__` de scripts/site_ui.py est extrait et joué
sur les vraies données du site. Le tirage est rendu déterministe en injectant un `rand`
constant : le mélange devient l'ordre d'origine (le tri de V8 est stable).

Régression : le mode sosies tirait ses mauvaises réponses par genre latin ou famille
botanique, en ignorant « Confusions - référence.md » (cf. #5) — alors que les confusions
qui comptent sont souvent inter-familles (ail des ours / colchique / muguet).
"""
import json
import os
import re
import shutil
import subprocess

import pytest

from conftest import BASE, load_module

pytestmark = pytest.mark.skipif(shutil.which("node") is None,
                                reason="node absent : tirage JS non testé")

HARNESS = """
class Quiz {
  constructor(data){ this.data = data; }
  all(){ return this.data; }
__METHODES__
}
const app = new Quiz(__DATA__);
const trouve = n => app.all().find(s => s.name === n);
console.log(JSON.stringify(__CAS__.map(c => {
  const sp = trouve(c.sp);
  if (!sp) throw new Error('espèce absente des données : ' + c.sp);
  return app.distracteurs(sp, c.cfg, () => 0.5);   // rand constant = ordre d'origine
})));
"""


def bloc_js(nom):
    src = open(os.path.join(BASE, "scripts", "site_ui.py"), encoding="utf-8").read()
    m = re.search(r"// __%s_DEBUT__[^\n]*\n(.*?)// __%s_FIN__" % (nom, nom), src, re.S)
    assert m, "bloc %s introuvable dans scripts/site_ui.py" % nom
    return m.group(1)


def tirer(cas, data):
    js = (HARNESS.replace("__METHODES__", bloc_js("SOSIES"))
                 .replace("__DATA__", json.dumps(data, ensure_ascii=False))
                 .replace("__CAS__", json.dumps(cas, ensure_ascii=False)))
    r = subprocess.run(["node", "-e", js], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


@pytest.fixture(scope="module")
def site_data():
    """Les espèces telles que le build les injecte (conf porte les sosies)."""
    atlas_data = load_module("atlas_data")
    build_web = load_module("build_web")
    especes, seen = [], set()
    for path, cat in atlas_data.ATLASES:
        especes += atlas_data.parse_atlas(path, cat, seen)
    data = build_web.to_web_data(atlas_data.apply_corrections(especes))
    return [{"id": s["id"], "name": s["name"], "latin": s["latin"], "cat": s["cat"],
             "fields": {"famille": s["fields"].get("famille", "")}, "conf": s["conf"]}
            for s in data]


SOSIES = {"cat": "herbace", "diff": "sosies"}
LIGNEUX = {"cat": "ligneux", "diff": "sosies"}


def test_groupe_de_quatre_fournit_les_trois_distracteurs(site_data):
    """Ail des ours : le groupe compte muguet, arum et colchique — trois sosies mortels."""
    got = tirer([{"sp": "Ail des ours", "cfg": SOSIES}], site_data)[0]

    assert set(got["noms"]) == {"Muguet", "Arum tacheté (gouet)", "Colchique"}
    assert got["conf"] == 0


def test_les_apiacees_de_la_cigue(site_data):
    got = tirer([{"sp": "Grande ciguë", "cfg": SOSIES}], site_data)[0]

    # Le groupe en compte quatre : les trois retenus en viennent tous.
    assert set(got["noms"]) <= {"Cerfeuil", "Persil", "Carotte", "Égopode (herbe aux goutteux)"}
    assert len(got["noms"]) == 3


def test_un_groupe_de_deux_est_complete_sans_perdre_le_sosie(site_data):
    got = tirer([{"sp": "Chêne sessile", "cfg": LIGNEUX}], site_data)[0]

    assert "Chêne pédonculé" in got["noms"], "le sosie du groupe doit être proposé"
    assert len(got["noms"]) == 3 and len(set(got["noms"])) == 3
    assert got["conf"] == 0


def test_espece_sans_groupe_garde_le_repli_genre_famille(site_data):
    got = tirer([{"sp": "Basilic", "cfg": SOSIES}], site_data)[0]

    assert got["conf"] == -1
    assert len(got["noms"]) == 3 and "Basilic" not in got["noms"]


def test_le_mode_qcm_n_utilise_pas_les_groupes(site_data):
    got = tirer([{"sp": "Ail des ours", "cfg": {"cat": "herbace", "diff": "qcm"}}], site_data)[0]

    assert got["conf"] == -1, "hors mode sosies, aucun groupe n'est utilisé"
    assert len(got["noms"]) == 3


def test_jamais_l_espece_elle_meme_ni_de_doublon(site_data):
    cas = [{"sp": n, "cfg": SOSIES if n != "Chêne sessile" else LIGNEUX}
           for n in ["Ail des ours", "Grande ciguë", "Ortie", "Basilic", "Chêne sessile"]]

    for c, got in zip(cas, tirer(cas, site_data)):
        assert c["sp"] not in got["noms"], c["sp"]
        assert len(set(got["noms"])) == len(got["noms"]) == 3, c["sp"]


def test_categorie_respectee(site_data):
    """Un distracteur doit rester dans la catégorie jouée, même tiré d'un groupe."""
    cats = {s["name"]: s["cat"] for s in site_data}
    got = tirer([{"sp": "Ortie", "cfg": SOSIES}], site_data)[0]

    assert all(cats[n] == "herbace" for n in got["noms"]), got["noms"]


def test_mode_mixte_accepte_toutes_les_categories(site_data):
    got = tirer([{"sp": "Ail des ours", "cfg": {"cat": "mixte", "diff": "sosies"}}], site_data)[0]

    assert set(got["noms"]) == {"Muguet", "Arum tacheté (gouet)", "Colchique"}
