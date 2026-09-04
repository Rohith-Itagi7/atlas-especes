#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Révision espacée : le **JS réellement livré**, exécuté sous node (cf. #16).

Avant, la « maîtrise » était un seuil définitif (3 réponses dont 75 % de bonnes) et le
tirage était aléatoire : une espèce ratée hier avait la même chance de revenir qu'une
espèce sue depuis un mois. Le bloc `// __SRS_DEBUT__ … // __SRS_FIN__` de
scripts/site_ui.py planifie chaque carte ; il est joué ici tel quel, avec des dates
simulées (les échéances sont des **numéros de jour**, pas des timestamps).
"""
import json
import os
import re
import shutil
import subprocess

import pytest

from conftest import BASE

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node absent")

HARNESS = """
class App {
__METHODES__
  // seul ajout du harnais : jourDe reçoit un Date dans l'app, une date lisible ici
  jourDeTexte(s){ return this.jourDe(new Date(s)); }
  // mélange reproductible, pour tester l'ordre des neuves sans dépendre de Math.random
  fileGraine(entrees, jour, graine){
    let x = graine;
    return this.ordonnerFile(entrees, jour, () => (x = (x * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff);
  }
}
const app = new App();
console.log(JSON.stringify((__APPELS__).map(a => app[a[0]].apply(app, a.slice(1)))));
"""

J = 20400          # un jour de référence quelconque


def appeler(*appels, tz=None):
    """Joue des appels [methode, arg…]. `tz` force le fuseau du sous-processus node :
    en UTC il n'y a pas de changement d'heure, et les tests de numéro de jour ne
    prouveraient rien (le conteneur de CI est en UTC)."""
    src = open(os.path.join(BASE, "scripts", "site_ui.py"), encoding="utf-8").read()
    m = re.search(r"// __SRS_DEBUT__[^\n]*\n(.*?)// __SRS_FIN__", src, re.S)
    assert m, "bloc de révision introuvable dans site_ui.py"
    js = (HARNESS.replace("__METHODES__", m.group(1))
                 .replace("__APPELS__", json.dumps(list(appels), ensure_ascii=False)))
    env = dict(os.environ, TZ=tz) if tz else None
    r = subprocess.run(["node", "-e", js], capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def un(*appel):
    return appeler(list(appel))[0]


# ------------------------------------------------------------------ numéro de jour
# Fuseaux choisis pour ce qu'ils cassent : Paris passe à l'heure d'été, Kolkata a un
# décalage d'une demi-heure, Auckland est de l'autre côté et décale en octobre.
FUSEAUX = ["UTC", "Europe/Paris", "America/Los_Angeles", "Asia/Kolkata", "Pacific/Auckland"]


@pytest.mark.parametrize("tz", FUSEAUX)
def test_le_numero_de_jour_avance_d_un_par_jour(tz):
    a, b = appeler(["jourDeTexte", "2026-03-10T08:00:00"],
                   ["jourDeTexte", "2026-03-11T08:00:00"], tz=tz)

    assert b - a == 1


@pytest.mark.parametrize("tz", FUSEAUX)
def test_le_numero_de_jour_ne_bouge_pas_dans_la_journee(tz):
    """Deux réponses le même jour civil doivent tomber sur la même échéance."""
    matin, soir = appeler(["jourDeTexte", "2026-03-10T00:30:00"],
                          ["jourDeTexte", "2026-03-10T23:30:00"], tz=tz)

    assert matin == soir


@pytest.mark.parametrize("tz,bascule", [
    ("Europe/Paris", "2026-03-29"),          # heure d'été : la nuit ne fait que 23 h
    ("Europe/Paris", "2026-10-25"),          # heure d'hiver : 25 h
    ("America/Los_Angeles", "2026-03-08"),
    ("Pacific/Auckland", "2026-09-27"),
])
def test_le_changement_d_heure_ne_decale_pas_le_jour(tz, bascule):
    """La nuit du changement d'heure ne fait pas 24 h : un numéro de jour calculé par
    Date.now()/86400000 y perd ou double un jour, et une carte devient due la veille
    ou jamais. D'où le passage par Date.UTC(y, m, d)."""
    an, mois, jour = (int(x) for x in bascule.split("-"))
    veille = "%04d-%02d-%02dT12:00:00" % (an, mois, jour - 1)
    apres = "%04d-%02d-%02dT12:00:00" % (an, mois, jour + 1)

    a, b, c = appeler(["jourDeTexte", veille], ["jourDeTexte", bascule + "T12:00:00"],
                      ["jourDeTexte", apres], tz=tz)

    assert (b - a, c - b) == (1, 1), (tz, bascule)


# -------------------------------------------------------------------- intervalles

@pytest.mark.parametrize("box,attendu", [(0, 0), (1, 1), (2, 3), (3, 7), (4, 16), (5, 35)])
def test_les_intervalles_du_bareme(box, attendu):
    assert un("intervalle", box) == attendu


@pytest.mark.parametrize("box", [-3, 6, 99])
def test_une_boite_hors_bareme_est_ramenee_dans_les_bornes(box):
    assert un("intervalle", box) in (0, 35)


# ------------------------------------------------------------------ planification

def test_une_premiere_bonne_reponse_ouvre_la_carte_en_boite_1():
    c = un("planifier", None, True, J)

    assert c == {"s": 1, "c": 1, "box": 1, "due": J + 1, "last": J}


def test_une_premiere_mauvaise_reponse_laisse_la_carte_a_revoir_le_jour_meme():
    c = un("planifier", None, False, J)

    assert c["box"] == 0 and c["due"] == J, "boîte 0 = intervalle nul = encore aujourd'hui"
    assert un("estEchue", c, J) is True


def test_une_serie_de_bonnes_reponses_monte_les_boites():
    """Cinq réussites espacées : 1 → 3 → 7 → 16 → 35 jours."""
    carte, jour, echeances = None, J, []
    for _ in range(6):
        carte = un("planifier", carte, True, jour)
        echeances.append(carte["due"] - jour)
        jour = carte["due"]

    assert echeances == [1, 3, 7, 16, 35, 35], "la boîte 5 est le plafond"
    assert carte["box"] == 5 and carte["s"] == 6 and carte["c"] == 6


def test_une_erreur_ne_redescend_que_d_un_cran():
    """Choix mesuré : le retour à zéro affame la découverte de nouvelles espèces
    (~312 espèces introduites sur 502 contre ~437 en six mois de simulation)."""
    haut = {"s": 9, "c": 9, "box": 5, "due": J, "last": J - 35}

    rate = un("planifier", haut, False, J)

    assert rate["box"] == 4
    assert rate["due"] == J + 16, "à revoir bientôt, mais sans repartir de zéro"
    assert (rate["s"], rate["c"]) == (10, 9), "les compteurs historiques suivent"


def test_la_boite_0_ne_descend_pas_plus_bas():
    bas = {"s": 3, "c": 0, "box": 0, "due": J, "last": J}

    assert un("planifier", bas, False, J)["box"] == 0


def test_une_carte_ratee_revient_avant_une_carte_sue():
    ratee = un("planifier", {"s": 5, "c": 4, "box": 3, "due": J, "last": J - 7}, False, J)
    sue = un("planifier", {"s": 5, "c": 5, "box": 4, "due": J, "last": J - 16}, True, J)

    assert ratee["due"] < sue["due"]
    assert un("estEchue", ratee, J + 3) is True
    assert un("estEchue", sue, J + 3) is False


# ---------------------------------------------------------------------- échéances

@pytest.mark.parametrize("due,jour,echue", [
    (J, J, True), (J - 5, J, True), (J + 1, J, False), (J + 35, J, False),
])
def test_est_echue(due, jour, echue):
    assert un("estEchue", {"s": 1, "c": 1, "box": 2, "due": due, "last": due - 3}, jour) is echue


def test_une_carte_jamais_vue_n_est_pas_echue():
    """Elle n'a pas de retard : elle est neuve. C'est la file qui la sert, pas l'échéance."""
    assert un("estEchue", None, J) is False


# ----------------------------------------------------------------------- maîtrise

@pytest.mark.parametrize("box,due,maitrisee", [
    (5, J + 30, True), (4, J + 10, True),
    (3, J + 100, False),              # trop bas, même à jour
    (5, J, False),                    # haut mais échu : la maîtrise se périme
    (4, J - 1, False),
])
def test_la_maitrise_demande_une_boite_haute_et_une_carte_a_jour(box, due, maitrisee):
    c = {"s": 8, "c": 7, "box": box, "due": due, "last": due - 16}

    assert un("estMaitrisee", c, J) is maitrisee


def test_une_carte_inexistante_n_est_pas_maitrisee():
    assert un("estMaitrisee", None, J) is False


# --------------------------------------------------------------------- ordre de file

def entree(id_, box=None, due=None, last=None):
    if box is None:
        return {"id": id_, "carte": None}
    return {"id": id_, "carte": {"s": 3, "c": 2, "box": box, "due": due, "last": last}}


def test_les_echues_passent_avant_tout_le_reste():
    file = un("ordonnerFile", [
        entree("sue", 5, J + 30, J - 5),
        entree("neuve"),
        entree("echue", 2, J - 1, J - 4),
    ], J)

    assert file[0] == "echue", "aucune carte non échue avant une carte échue"


def test_les_plus_en_retard_d_abord():
    file = un("ordonnerFile", [
        entree("hier", 2, J - 1, J - 4),
        entree("il_y_a_20_jours", 1, J - 20, J - 21),
        entree("aujourdhui", 3, J, J - 7),
    ], J)

    assert file == ["il_y_a_20_jours", "hier", "aujourdhui"]


def test_les_neuves_viennent_apres_les_echues_et_avant_les_a_jour():
    file = un("ordonnerFile", [
        entree("a_jour", 4, J + 12, J - 4),
        entree("neuve"),
        entree("echue", 1, J - 2, J - 3),
    ], J)

    assert file == ["echue", "neuve", "a_jour"]


def test_a_jour_la_moins_recemment_vue_d_abord():
    file = un("ordonnerFile", [
        entree("vue_hier", 4, J + 15, J - 1),
        entree("vue_il_y_a_un_mois", 5, J + 5, J - 30),
    ], J)

    assert file == ["vue_il_y_a_un_mois", "vue_hier"]


def test_les_neuves_sont_melangees_pas_alphabetiques():
    """Servies dans l'ordre du tableau, le quiz parcourrait l'atlas de A à Z."""
    ids = [entree("e%02d" % i) for i in range(12)]
    ordre = [x["id"] for x in ids]

    file = un("fileGraine", ids, J, 42)

    assert sorted(file) == sorted(ordre), "aucune carte perdue par le mélange"
    assert file != ordre, "l'ordre d'entrée ressort tel quel : pas de mélange"


def test_le_melange_des_neuves_est_reproductible_a_graine_egale():
    """Le hasard est injecté, pas capté : c'est ce qui rend l'ordre testable."""
    ids = [entree("e%02d" % i) for i in range(10)]

    a, b, c = appeler(["fileGraine", ids, J, 7], ["fileGraine", ids, J, 7],
                      ["fileGraine", ids, J, 99])

    assert a == b and a != c


def test_le_melange_ne_touche_pas_l_ordre_des_echues():
    """Les échues sont classées par retard : le hasard ne doit pas s'y mêler."""
    entrees = [entree("e%02d" % i, 1, J - i, J - i - 1) for i in range(6)]

    a, b = appeler(["fileGraine", entrees, J, 1], ["fileGraine", entrees, J, 12345])

    assert a == b == ["e05", "e04", "e03", "e02", "e01", "e00"]


def test_la_file_ne_perd_ni_ne_duplique_aucune_carte():
    entrees = [entree("a", 0, J - 3, J - 3), entree("b"), entree("c", 5, J + 30, J - 5),
               entree("d"), entree("e", 2, J, J - 3)]

    file = un("ordonnerFile", entrees, J)

    assert sorted(file) == ["a", "b", "c", "d", "e"]


def test_une_file_vide_ne_casse_pas():
    assert un("ordonnerFile", [], J) == []


# ------------------------------------------------------- tête de file (tirage au sort)
# Le tirage pioche au hasard dans le haut de la file pour que deux sessions ne se
# ressemblent pas. Sans borne de palier, ce hasard servait une carte à jour alors qu'il
# restait des cartes en retard : 9 tirages sur 60 mesurés en navigateur.

def carte(box, due, last=None):
    return {"s": 3, "c": 2, "box": box, "due": due, "last": J - 5 if last is None else last}


def test_la_tete_s_arrete_a_la_derniere_echue():
    cartes = [carte(1, J - 3), carte(2, J - 1), carte(3, J), None, carte(5, J + 30)]

    assert un("tailleTete", cartes, J, 12) == 3, "les 3 échues, pas la neuve ni la carte à jour"


def test_la_tete_est_bornee_par_le_maximum():
    cartes = [carte(1, J - i) for i in range(30)]

    assert un("tailleTete", cartes, J, 12) == 12


def test_sans_echue_la_tete_couvre_les_neuves():
    cartes = [None, None, None, carte(5, J + 30)]

    assert un("tailleTete", cartes, J, 12) == 3


def test_sans_echue_ni_neuve_la_tete_couvre_tout_le_reste():
    """Tout est à jour : plus de palier à respecter, on peut varier sur toute la file."""
    cartes = [carte(4, J + 10), carte(5, J + 30), carte(4, J + 12)]

    assert un("tailleTete", cartes, J, 12) == 3


def test_la_tete_ne_vaut_jamais_zero():
    assert un("tailleTete", [], J, 12) == 1
    assert un("tailleTete", [carte(5, J + 30)], J, 0) == 1


# ----------------------------------------------------------------------- migration

def test_une_progression_maitrisee_sous_l_ancienne_regle_arrive_en_boite_4():
    """Sans ça, les espèces déjà acquises tomberaient toutes en retard le même jour et
    le compteur de maîtrise repartirait de zéro sous les yeux de l'utilisateur."""
    c = un("migrerCarte", {"s": 4, "c": 4}, J)

    assert c["box"] == 4 and c["due"] == J + 16 and c["last"] == J
    assert un("estMaitrisee", c, J) is True


@pytest.mark.parametrize("avant,box", [
    ({"s": 4, "c": 4}, 4),        # 100 % sur 4 réponses : maîtrisée sous l'ancienne règle
    ({"s": 3, "c": 3}, 4),
    ({"s": 4, "c": 3}, 4),        # 75 % : pile le seuil de l'ancienne règle
    ({"s": 4, "c": 2}, 1),        # 50 %
    ({"s": 2, "c": 2}, 1),        # bon mais trop peu de réponses pour la maîtrise
    ({"s": 3, "c": 1}, 0),        # 33 %
    ({"s": 1, "c": 0}, 0),
])
def test_la_boite_de_depart_se_deduit_de_la_reussite_passee(avant, box):
    assert un("migrerCarte", avant, J)["box"] == box


def test_les_compteurs_ne_sont_jamais_perdus_a_la_migration():
    avant = {"s": 7, "c": 5}

    apres = un("migrerCarte", avant, J)

    assert (apres["s"], apres["c"]) == (7, 5)


def test_une_carte_faible_est_a_revoir_des_le_jour_de_la_migration():
    c = un("migrerCarte", {"s": 3, "c": 1}, J)

    assert un("estEchue", c, J) is True, "boîte 0 : c'est justement ce qu'il faut revoir"


def test_une_carte_deja_planifiee_n_est_pas_retouchee():
    deja = {"s": 4, "c": 3, "box": 2, "due": J + 3, "last": J}

    assert un("migrerCarte", deja, J + 100) == deja


def test_la_migration_d_une_progression_complete():
    avant = {"chene|photo": {"s": 4, "c": 4}, "ortie|fiche": {"s": 3, "c": 1},
             "hetre|photo": {"s": 2, "c": 2, "box": 5, "due": J + 30, "last": J - 5}}

    res = un("migrerProg", avant, J)

    assert res["migrees"] == 2, "seules les deux entrées sans planification sont touchées"
    assert res["prog"]["chene|photo"]["box"] == 4
    assert res["prog"]["ortie|fiche"]["box"] == 0
    assert res["prog"]["hetre|photo"]["box"] == 5


def test_la_migration_est_idempotente():
    avant = {"chene|photo": {"s": 4, "c": 4}, "ortie|fiche": {"s": 3, "c": 1}}

    une_fois = un("migrerProg", avant, J)
    deux_fois = un("migrerProg", une_fois["prog"], J + 50)

    assert deux_fois["prog"] == une_fois["prog"] and deux_fois["migrees"] == 0


@pytest.mark.parametrize("mauvaise", [None, "3", 42, []])
def test_une_entree_qui_n_est_pas_une_carte_est_ecartee(mauvaise):
    res = un("migrerProg", {"chene|photo": mauvaise, "ortie|fiche": {"s": 1, "c": 1}}, J)

    assert "chene|photo" not in res["prog"] and "ortie|fiche" in res["prog"]


# -------------------------------------------------------------------- vue Progrès

def test_le_resume_compte_les_dues_et_repartit_par_boite():
    prog = {
        "a|photo": {"s": 1, "c": 0, "box": 0, "due": J, "last": J},
        "b|photo": {"s": 3, "c": 3, "box": 3, "due": J - 2, "last": J - 9},
        "c|fiche": {"s": 5, "c": 5, "box": 5, "due": J + 30, "last": J - 5},
        "d|fiche": {"s": 4, "c": 4, "box": 5, "due": J + 20, "last": J - 15},
    }

    r = un("resumeBoites", prog, J)

    assert r["dues"] == 2, "a échue aujourd'hui, b en retard de 2 jours"
    assert r["total"] == 4
    assert r["boites"] == [1, 0, 0, 1, 0, 2]


def test_le_resume_d_une_progression_vide():
    r = un("resumeBoites", {}, J)

    assert r["dues"] == 0 and r["total"] == 0 and sum(r["boites"]) == 0


def test_le_resume_ignore_une_entree_sans_planification():
    """Elle existe le temps d'un import, avant migrerProg : ne pas la compter en boîte 0."""
    r = un("resumeBoites", {"a|photo": {"s": 2, "c": 1}}, J)

    assert r["total"] == 0 and r["dues"] == 0
