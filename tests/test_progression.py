#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Export / import de la progression : le **JS réellement livré**, exécuté sous node.

Le bloc `// __PROG_DEBUT__ … // __PROG_FIN__` de scripts/site_ui.py est extrait et joué tel
quel. La progression est la seule donnée personnelle de l'app : un import qui la corrompt
ou l'efface est une perte sèche pour l'utilisateur (cf. #6).
"""
import json
import os
import re
import shutil
import subprocess

import pytest

from conftest import BASE

pytestmark = pytest.mark.skipif(shutil.which("node") is None,
                                reason="node absent : import/export JS non testé")

HARNESS = """
class Prog {
__METHODES__
}
const app = new Prog();
console.log(JSON.stringify((__APPELS__).map(a => app[a[0]].apply(app, a.slice(1)))));
"""


def bloc_js(nom="PROG"):
    src = open(os.path.join(BASE, "scripts", "site_ui.py"), encoding="utf-8").read()
    m = re.search(r"// __%s_DEBUT__[^\n]*\n(.*?)// __%s_FIN__" % (nom, nom), src, re.S)
    assert m, "bloc %s introuvable dans scripts/site_ui.py" % nom
    return m.group(1)


def appeler(*appels):
    """Joue des appels [nom_de_methode, arg…] et renvoie leurs résultats.

    Depuis #16, progParse et progFusion s'appuient sur la planification (BOITE_MAX,
    intervalle, migrerProg…) : le bloc SRS est chargé avec le bloc PROG.
    """
    js = (HARNESS.replace("__METHODES__", bloc_js("SRS") + "\n" + bloc_js())
                 .replace("__APPELS__", json.dumps(list(appels), ensure_ascii=False)))
    r = subprocess.run(["node", "-e", js], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


PROG = {"chene|photo": {"s": 4, "c": 3}, "chene|photo:feuille": {"s": 2, "c": 2},
        "chene|fiche": {"s": 3, "c": 1}, "crit|comest": {"s": 6, "c": 5}}


# ------------------------------------------------------------------------- export

def test_l_export_est_enveloppe_et_versionne():
    txt, = appeler(["progExport", PROG])

    # v2 depuis #16 : les entrées portent en plus box/due/last
    assert json.loads(txt) == {"v": 2, "app": "atlas-especes", "prog": PROG}


def test_la_planification_survit_a_l_aller_retour():
    planifie = {"chene|photo": {"s": 4, "c": 3, "box": 3, "due": 20400, "last": 20393}}

    txt, = appeler(["progExport", planifie])
    lu, = appeler(["progParse", txt])

    assert lu["prog"] == planifie


@pytest.mark.parametrize("carte,garde", [
    ({"s": 2, "c": 2, "box": 3, "due": 20400, "last": 20393}, True),
    ({"s": 2, "c": 2, "box": 3, "due": 20400}, True),          # last déduit de l'intervalle
    ({"s": 2, "c": 2, "box": 99, "due": 20400}, False),        # boîte hors barème
    ({"s": 2, "c": 2, "box": -1, "due": 20400}, False),
    ({"s": 2, "c": 2, "box": 3}, False),                       # boîte sans échéance
    ({"s": 2, "c": 2, "box": "3", "due": 20400}, False),
])
def test_une_planification_incoherente_est_ignoree_pas_l_entree(carte, garde):
    """Une planification douteuse ne doit pas faire perdre les compteurs : la carte
    repart d'une boîte déduite de sa réussite (migrerProg), elle n'est pas jetée."""
    lu, = appeler(["progParse", json.dumps({"chene|photo": carte})])

    e = lu["prog"]["chene|photo"]
    assert (e["s"], e["c"]) == (2, 2)
    assert ("box" in e) is garde, e


def test_aller_retour_export_import():
    txt, = appeler(["progExport", PROG])
    lu, = appeler(["progParse", txt])

    assert lu["prog"] == PROG and lu["ignores"] == 0


def test_l_ancien_format_plat_reste_lisible():
    # Les fichiers déjà exportés par la version précédente étaient un objet plat.
    lu, = appeler(["progParse", json.dumps(PROG)])

    assert lu["prog"] == PROG


def test_export_d_une_progression_vide():
    txt, = appeler(["progExport", None])

    assert json.loads(txt)["prog"] == {}


# -------------------------------------------------------------------- fichiers refusés

@pytest.mark.parametrize("contenu,extrait", [
    ("ceci n'est pas du json", "pas du JSON"),
    ("[1,2,3]", "aucune progression"),
    ('"une chaîne"', "aucune progression"),
    ("null", "aucune progression"),
    ('{"v":1,"prog":[1,2]}', "aucune progression"),
    ('{"nimportequoi":1}', "Aucune entrée exploitable"),
])
def test_fichiers_refuses(contenu, extrait):
    lu, = appeler(["progParse", contenu])

    assert "erreur" in lu and extrait in lu["erreur"], lu


def test_le_message_de_refus_compte_les_entrees_ignorees():
    lu, = appeler(["progParse", json.dumps({"a": 1, "b": 2, "c": 3})])

    assert "3 ignorées" in lu["erreur"]


# ------------------------------------------------------------- entrées non conformes

def test_les_entrees_douteuses_sont_ignorees_pas_le_fichier():
    fichier = {
        "chene|photo": {"s": 3, "c": 2},          # bonne
        "crit|comest": {"s": 1, "c": 0},          # bonne
        "sans_barre_verticale": {"s": 1, "c": 1},
        "chene|autrechose": {"s": 1, "c": 1},
        "chene|fiche": {"s": 2, "c": 5},          # plus de correctes que de réponses
        "hetre|photo": {"s": -1, "c": 0},
        "orme|photo": {"s": 1.5, "c": 1},
        "aulne|photo": "3",
        "tilleul|photo": None,
    }

    lu, = appeler(["progParse", json.dumps(fichier)])

    assert lu["prog"] == {"chene|photo": {"s": 3, "c": 2}, "crit|comest": {"s": 1, "c": 0}}
    assert lu["ignores"] == 7


@pytest.mark.parametrize("cle", [
    "chene|photo", "chene|photo:feuille", "chene|fiche", "crit|comest",
    "chou_daubenton|photo:ecorce", "sureau_herbace|fiche",
])
def test_formes_de_cles_acceptees(cle):
    lu, = appeler(["progParse", json.dumps({cle: {"s": 1, "c": 1}})])

    assert cle in lu.get("prog", {}), lu


def test_une_espece_inconnue_n_est_pas_rejetee():
    # Un stem renommé depuis l'export ne doit pas faire perdre l'entrée : la forme suffit.
    lu, = appeler(["progParse", json.dumps({"especeinconnue|photo": {"s": 2, "c": 1}})])

    assert lu["prog"] == {"especeinconnue|photo": {"s": 2, "c": 1}}


# ------------------------------------------------------------------------- fusion

def test_la_fusion_additionne_les_compteurs():
    actuel = {"chene|photo": {"s": 4, "c": 3}}
    entrant = {"chene|photo": {"s": 2, "c": 1}, "hetre|fiche": {"s": 5, "c": 5}}

    res, = appeler(["progFusion", actuel, entrant])

    assert res["prog"] == {"chene|photo": {"s": 6, "c": 4}, "hetre|fiche": {"s": 5, "c": 5}}
    assert (res["ajoutes"], res["fusionnes"]) == (1, 1)


def test_la_fusion_ne_touche_pas_l_original():
    actuel = {"chene|photo": {"s": 4, "c": 3}}

    res, = appeler(["progFusion", actuel, {"chene|photo": {"s": 1, "c": 1}}])

    assert res["prog"]["chene|photo"] == {"s": 5, "c": 4}
    assert actuel == {"chene|photo": {"s": 4, "c": 3}}, "l'appelant garde son objet intact"


def test_fusion_sur_progression_vide():
    res, = appeler(["progFusion", {}, PROG])

    assert res["prog"] == PROG and res["fusionnes"] == 0 and res["ajoutes"] == len(PROG)


def test_la_fusion_garde_la_planification_la_plus_recente():
    """Deux appareils : c'est la révision la plus récente qui dit où en est la mémoire.

    Additionner les échéances n'aurait aucun sens, et prendre la plus haute boîte
    ferait passer un vieux « je le savais » devant un échec d'hier.
    """
    vieux = {"chene|photo": {"s": 10, "c": 9, "box": 5, "due": 20430, "last": 20395}}
    recent = {"chene|photo": {"s": 2, "c": 0, "box": 0, "due": 20410, "last": 20410}}

    res, = appeler(["progFusion", vieux, recent])

    e = res["prog"]["chene|photo"]
    assert (e["s"], e["c"]) == (12, 9), "les compteurs, eux, s'additionnent"
    assert (e["box"], e["due"], e["last"]) == (0, 20410, 20410)


def test_a_egalite_de_date_la_boite_la_plus_haute_gagne():
    a = {"chene|photo": {"s": 3, "c": 3, "box": 4, "due": 20420, "last": 20404}}
    b = {"chene|photo": {"s": 3, "c": 2, "box": 2, "due": 20407, "last": 20404}}

    res, = appeler(["progFusion", a, b])

    assert res["prog"]["chene|photo"]["box"] == 4


def test_la_fusion_avec_une_entree_non_planifiee_garde_la_planification_connue():
    planifie = {"chene|photo": {"s": 3, "c": 3, "box": 4, "due": 20420, "last": 20404}}
    ancien = {"chene|photo": {"s": 2, "c": 1}}

    res, = appeler(["progFusion", planifie, ancien])

    e = res["prog"]["chene|photo"]
    assert (e["s"], e["c"]) == (5, 4)
    assert e["box"] == 4, "un fichier d'avant #16 ne doit pas effacer la planification"


# ------------------------------------------------------------------------- résumé

def test_le_resume_dit_ce_qui_s_est_passe():
    msg, = appeler(["progResume", {"ajoutes": 3, "fusionnes": 1, "ignores": 2}, False])

    # 3 + 1 = les 4 entrées lues dans le fichier (et non le total après fusion)
    assert "4 entrées" in msg and "3 ajoutées" in msg and "1 fusionnée" in msg
    assert "2 ignorées" in msg


def test_le_resume_du_remplacement_ne_parle_pas_de_fusion():
    msg, = appeler(["progResume", {"ajoutes": 4, "fusionnes": 0, "ignores": 0}, True])

    assert "remplacée" in msg and "fusionnée" not in msg
