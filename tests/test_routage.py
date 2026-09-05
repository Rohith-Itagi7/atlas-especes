#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Routage par fragment : le **JS réellement livré**, exécuté sous node (cf. #15).

L'URL ne portait pas l'état : impossible de partager une fiche, et F5 ramenait à l'accueil.
Le bloc `// __ROUTE_DEBUT__ … // __ROUTE_FIN__` de scripts/site_ui.py écrit et relit le
fragment ; il est joué ici tel quel.
"""
import json
import os
import re
import shutil
import subprocess

import pytest

from conftest import BASE, load_module

HARNESS = """
class App {
__METHODES__
}
const app = new App();
console.log(JSON.stringify(__APPELS__.map(a => app[a[0]].apply(app, a.slice(1)))));
"""


def appeler(*appels):
    if shutil.which("node") is None:
        pytest.skip("node absent")
    src = open(os.path.join(BASE, "scripts", "site_ui.py"), encoding="utf-8").read()
    m = re.search(r"// __ROUTE_DEBUT__[^\n]*\n(.*?)// __ROUTE_FIN__", src, re.S)
    assert m, "bloc de routage introuvable dans site_ui.py"
    js = (HARNESS.replace("__METHODES__", m.group(1))
                 .replace("__APPELS__", json.dumps(list(appels), ensure_ascii=False)))
    r = subprocess.run(["node", "-e", js], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def url(etat):
    return appeler(["urlDeVue", etat])[0]


def vue(hash_):
    return appeler(["vueDeUrl", hash_])[0]


# --------------------------------------------------------------- état → URL

@pytest.mark.parametrize("etat,attendu", [
    ({"v": "home"}, "#/"),
    ({"v": "progres"}, "#/progres"),
    ({"v": "atlas", "cat": "mixte", "query": ""}, "#/atlas"),
    ({"v": "atlas", "cat": "ligneux", "query": "chene"}, "#/atlas?cat=ligneux&q=chene"),
    ({"v": "fiche", "fiche": "alisier"}, "#/espece/alisier"),
    ({"v": "trierPick"}, "#/trier"),
    ({"v": "trierPlay", "crit": "comest"}, "#/trier/comest"),
])
def test_url_de_vue(etat, attendu):
    assert url(etat) == attendu


def test_les_valeurs_par_defaut_n_encombrent_pas_l_url():
    # « tout » et « mixte » sont les valeurs par défaut : inutile de les écrire
    assert url({"v": "quiz", "cfgCat": "mixte", "qtype": "photo", "aspect": "tout",
                "diff": "qcm"}) == "#/quiz?type=photo&diff=qcm"


def test_url_de_quiz_complete():
    assert url({"v": "quiz", "cfgCat": "ligneux", "qtype": "photo", "aspect": "feuille",
                "diff": "qcm"}) == "#/quiz?cat=ligneux&type=photo&aspect=feuille&diff=qcm"


def test_une_fiche_sans_espece_retombe_sur_l_atlas():
    assert url({"v": "fiche", "fiche": None}) == "#/atlas"


def test_les_valeurs_sont_encodees():
    assert url({"v": "atlas", "cat": "mixte", "query": "chêne à glands"}) \
        == "#/atlas?q=ch%C3%AAne%20%C3%A0%20glands"


# --------------------------------------------------------------- URL → état

@pytest.mark.parametrize("hash_,attendu", [
    ("", {"v": "home", "tab": "reviser"}),
    ("#/", {"v": "home", "tab": "reviser"}),
    ("#/progres", {"v": "progres", "tab": "progres"}),
    ("#/espece/alisier", {"v": "fiche", "tab": "atlas", "fiche": "alisier",
                          "ficheFrom": "atlas"}),
    ("#/trier", {"v": "trierPick", "tab": "trier"}),
    ("#/trier/comest", {"v": "trierPlay", "tab": "trier", "crit": "comest"}),
])
def test_vue_de_url(hash_, attendu):
    assert vue(hash_) == attendu


def test_atlas_avec_parametres():
    assert vue("#/atlas?cat=faune&q=abeille") == {"v": "atlas", "tab": "atlas",
                                                  "cat": "faune", "query": "abeille"}


def test_atlas_sans_parametre_revient_aux_defauts():
    assert vue("#/atlas") == {"v": "atlas", "tab": "atlas", "cat": "mixte", "query": ""}


def test_quiz_avec_parametres():
    assert vue("#/quiz?cat=ligneux&type=fiche&diff=saisie") == {
        "v": "quiz", "tab": "reviser", "cfgCat": "ligneux", "qtype": "fiche",
        "aspect": "", "diff": "saisie"}


@pytest.mark.parametrize("hash_", ["#/nimportequoi", "#/espece", "#/espece/", "#/toto/tata"])
def test_routes_inconnues(hash_):
    assert vue(hash_) is None or vue(hash_)["v"] in ("home", "atlas"), hash_


def test_une_espece_inconnue_reste_une_route_valide():
    """C'est l'app qui décide quoi faire d'un stem absent (atlas + message), pas le parseur."""
    assert vue("#/espece/nexistepas")["fiche"] == "nexistepas"


def test_le_fragment_supporte_les_slashes_en_trop():
    assert vue("#//atlas//") == {"v": "atlas", "tab": "atlas", "cat": "mixte", "query": ""}


def test_les_valeurs_sont_decodees():
    assert vue("#/atlas?q=ch%C3%AAne+%C3%A0+glands")["query"] == "chêne à glands"
    assert vue("#/espece/ch%C3%AAne")["fiche"] == "chêne"


# ------------------------------------------------------------ aller-retour

@pytest.mark.parametrize("etat", [
    {"v": "home"},
    {"v": "progres"},
    {"v": "atlas", "cat": "champignon", "query": "amanite"},
    {"v": "fiche", "fiche": "chou_daubenton"},
    {"v": "trierPlay", "crit": "fixn"},
])
def test_aller_retour(etat):
    relu = vue(url(etat))

    assert relu["v"] == etat["v"]
    for cle in ("fiche", "crit", "cat", "query"):
        if cle in etat:
            assert relu.get(cle) == etat[cle], cle


# ------------------------------------------------------------------ titre

def test_l_app_prend_la_main_sur_le_defilement():
    """Sans « manual », le navigateur réapplique sa position mémorisée après notre restore().

    Vérifié en navigateur : le retour d'une fiche revenait en haut de grille au lieu des
    1800 px d'origine. Node ne peut pas rejouer ça, d'où ce garde-fou sur le JS livré.
    """
    js = load_module("site_ui").JS

    assert "history.scrollRestoration='manual'" in js
    assert "'scrollRestoration' in history" in js, "navigateur ancien : à tester avant d'écrire"


def test_le_titre_suit_toute_route_ouverte_depuis_l_url():
    """Vu en navigateur : le titre restait celui de la fiche précédente.

    Sur un changement de fragment, Chromium émet popstate AVANT hashchange : popstate
    ouvre la route, puis hashchange se tait (l'URL colle déjà à l'état) — et lui seul
    appelait ecrireHistorique, donc majTitre. Le titre se met donc à jour dans
    ouvrirRoute, qui est le passage obligé des deux gestionnaires.
    """
    js = load_module("site_ui").JS

    assert re.search(r"ouvrirRoute\(r\)\{[^\n]*majTitre\(\)", js), \
        "ouvrirRoute doit remettre le titre à jour"


def test_les_evenements_d_historique_sont_ecoutes():
    """Boutons Précédent/Suivant et fragment édité à la main."""
    js = load_module("site_ui").JS

    assert "'popstate'" in js and "'hashchange'" in js


def test_le_titre_reflete_la_vue():
    titres = appeler(["titreDeVue", "atlas", ""], ["titreDeVue", "fiche", "Alisier torminal"],
                     ["titreDeVue", "home", ""])

    assert titres[0].startswith("Atlas des espèces · ")
    assert titres[1].startswith("Alisier torminal · ")
    assert titres[2].startswith("Ma session · ")
    assert all(t.endswith("Atlas & quiz des espèces") for t in titres)


# ------------------------------------------ un lien partagé doit ouvrir CE quiz-là (revue)

def test_les_defauts_omis_de_l_url_sont_bien_les_defauts_pas_les_reglages_du_lecteur():
    """urlDeVue omet « mixte » et « tout » pour garder les liens lisibles. Si la relecture
    traite un paramètre absent comme « inchangé », celui qui clique ouvre le quiz avec SES
    propres réglages — un lien de quiz mixte devient un quiz champignons chez le voisin."""
    js = load_module("site_ui").JS

    assert re.search(r"DEFAUTS\s*=\s*\{[^}]*cat:'mixte'[^}]*aspect:'tout'", js), \
        "appliquerRoute doit repartir des valeurs par défaut"
    assert re.search(r"Object\.assign\(\{\},this\.state\.cfg,DEFAUTS\)", js)
