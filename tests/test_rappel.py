#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rappel quotidien de révision : le **JS réellement livré**, exécuté sous node.

Un site statique ne peut pas programmer une notification à une heure choisie — les
Notification Triggers ont été abandonnées, le Web Push demande un serveur qui pousse à
l'heure dite, et le Periodic Background Sync laisse le navigateur choisir le moment. On
délègue donc au calendrier de l'appareil : un fichier .ics avec un événement quotidien.

Ce fichier part dans une app tierce (Calendrier iOS, Google Agenda…) qui ne pardonne pas
les écarts au RFC 5545 : un mauvais repliage de ligne ou une virgule non échappée et
l'import échoue en silence. D'où ces tests.
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
}
const app = new App();
console.log(JSON.stringify((__APPELS__).map(a => app[a[0]].apply(app, a.slice(1)))));
"""

URL = "https://iribarnesy.github.io/atlas-especes/"
# vendredi 4 septembre 2026, 10 h 00 à Paris (vérifié : new Date(2026,8,4,10,0).getTime())
MATIN = 1788508800000


def appeler(*appels, tz="Europe/Paris"):
    src = open(os.path.join(BASE, "scripts", "site_ui.py"), encoding="utf-8").read()
    m = re.search(r"// __RAPPEL_DEBUT__[^\n]*\n(.*?)// __RAPPEL_FIN__", src, re.S)
    assert m, "bloc de rappel introuvable dans site_ui.py"
    js = (HARNESS.replace("__METHODES__", m.group(1))
                 .replace("__APPELS__", json.dumps(list(appels), ensure_ascii=False)))
    r = subprocess.run(["node", "-e", js], capture_output=True, text=True,
                       env=dict(os.environ, TZ=tz))
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def un(*appel):
    return appeler(list(appel))[0]


def ics(heure=19, minute=0, maintenant=MATIN, uid="test", tz="Europe/Paris"):
    return appeler(["icsRappel", heure, minute, URL, maintenant, uid], tz=tz)[0]


def deplie(texte):
    """Rend les lignes logiques : le repliage RFC 5545 est « CRLF + une espace »."""
    return texte.replace("\r\n ", "").split("\r\n")


# ------------------------------------------------------------------ structure du fichier

def test_l_enveloppe_icalendar_est_complete():
    lignes = deplie(ics())

    assert lignes[0] == "BEGIN:VCALENDAR" and "VERSION:2.0" in lignes
    assert lignes.count("BEGIN:VEVENT") == lignes.count("END:VEVENT") == 1
    assert lignes.count("BEGIN:VALARM") == lignes.count("END:VALARM") == 1
    assert lignes[-2] == "END:VCALENDAR", "le fichier se termine par la fin du calendrier"


def test_les_lignes_sont_terminees_par_crlf():
    """Le RFC impose CRLF ; un simple \\n fait échouer l'import chez certains clients."""
    texte = ics()

    assert texte.endswith("\r\n")
    assert "\n" not in texte.replace("\r\n", ""), "un \\n isolé traîne dans le fichier"


def test_l_evenement_se_repete_tous_les_jours():
    assert "RRULE:FREQ=DAILY" in deplie(ics())


def test_l_evenement_porte_une_alarme_a_son_debut():
    lignes = deplie(ics())

    assert "ACTION:DISPLAY" in lignes and "TRIGGER:PT0S" in lignes


def test_l_evenement_dure_un_quart_d_heure():
    assert "DURATION:PT15M" in deplie(ics())


def test_l_url_du_site_est_dans_l_evenement():
    lignes = deplie(ics())

    assert "URL:" + URL in lignes


def test_l_uid_et_l_horodatage_sont_presents():
    lignes = deplie(ics())
    uid = [l for l in lignes if l.startswith("UID:")][0]
    stamp = [l for l in lignes if l.startswith("DTSTAMP:")][0]

    assert uid.endswith("@atlas-especes")
    assert re.fullmatch(r"DTSTAMP:\d{8}T\d{6}Z", stamp), stamp


# --------------------------------------------------------------------- heure choisie

def dtstart(texte):
    return [l for l in deplie(texte) if l.startswith("DTSTART")][0]


def test_l_heure_choisie_se_retrouve_dans_l_evenement():
    assert dtstart(ics(heure=19, minute=0)).endswith("T190000")
    assert dtstart(ics(heure=7, minute=30)).endswith("T073000")


def test_l_heure_est_flottante_sans_fuseau():
    """Sans Z ni TZID : 19 h reste 19 h même en voyage, ce qu'on veut d'un rappel
    quotidien — contrairement à un rendez-vous, qui lui a un fuseau."""
    d = dtstart(ics())

    assert d.startswith("DTSTART:") and not d.endswith("Z") and "TZID" not in d


def test_si_l_heure_est_encore_a_venir_le_rappel_commence_aujourd_hui():
    # il est 10 h ; 19 h n'est pas passée
    assert dtstart(ics(heure=19)).startswith("DTSTART:20260904")


def test_si_l_heure_est_passee_le_rappel_commence_demain():
    """Sinon la première occurrence serait déjà échue, et certains clients la sautent."""
    assert dtstart(ics(heure=8)).startswith("DTSTART:20260905")


def test_le_basculement_au_lendemain_passe_les_fins_de_mois():
    # 30 septembre 2026 à 23 h 30 locales, rappel réglé à 8 h
    fin_de_mois = 1790803800000

    assert dtstart(ics(heure=8, maintenant=fin_de_mois)).startswith("DTSTART:20261001")


@pytest.mark.parametrize("tz", ["Europe/Paris", "UTC", "Pacific/Auckland", "America/Los_Angeles"])
def test_l_heure_ecrite_est_l_heure_locale_de_l_utilisateur(tz):
    """L'heure vient du réglage, pas du fuseau : elle sort telle quelle partout."""
    assert dtstart(ics(heure=19, minute=45, tz=tz)).endswith("T194500")


# ---------------------------------------------------------- repliage et échappement

def test_aucune_ligne_ne_depasse_75_octets():
    """Limite du RFC, en octets : « é » en compte deux, et le texte est accentué."""
    trop = [l for l in ics().split("\r\n") if len(l.encode("utf-8")) > 75]

    assert not trop, trop


def test_le_repliage_ne_coupe_pas_un_caractere_accentue():
    """Une ligne pliée au milieu d'un « é » donnerait deux octets invalides."""
    texte = ics()

    for ligne in texte.split("\r\n"):
        ligne.encode("utf-8").decode("utf-8")     # lève si la découpe a cassé un caractère
    assert "’" in texte.replace("\r\n ", ""), "le texte accentué a survécu au repliage"


def test_une_ligne_courte_n_est_pas_pliee():
    assert un("plierLigne", "VERSION:2.0") == "VERSION:2.0"


def test_une_ligne_longue_est_pliee_avec_une_espace():
    plie = un("plierLigne", "DESCRIPTION:" + "a" * 200)

    morceaux = plie.split("\r\n")
    assert len(morceaux) > 1
    assert all(m.startswith(" ") for m in morceaux[1:]), "la suite doit commencer par une espace"
    assert plie.replace("\r\n ", "") == "DESCRIPTION:" + "a" * 200, "aucun caractère perdu"


@pytest.mark.parametrize("brut,attendu", [
    ("a,b", "a\\,b"),
    ("a;b", "a\\;b"),
    ("a\\b", "a\\\\b"),
    ("a\nb", "a\\nb"),
    ("rien", "rien"),
])
def test_les_caracteres_speciaux_sont_echappes(brut, attendu):
    """Une virgule non échappée coupe la valeur en deux et casse l'import."""
    assert un("echapperIcs", brut) == attendu


def test_le_titre_du_rappel_est_echappe_dans_le_fichier():
    lignes = deplie(ics())
    somm = [l for l in lignes if l.startswith("SUMMARY:")][0]

    assert "Réviser" in somm
    assert re.search(r"(?<!\\)[,;]", somm[len("SUMMARY:"):]) is None, somm


# ------------------------------------------------------------------ relance à l'ouverture

J = 20400


def carte(last):
    return {"s": 3, "c": 2, "box": 2, "due": last + 3, "last": last}


def test_sans_carte_due_aucune_relance():
    """Ne rien dire quand il n'y a rien à faire : une relance permanente ne se lit plus."""
    assert un("phraseRelance", {"a|photo": carte(J)}, J, 0) == ""


def test_la_relance_compte_les_cartes_et_les_jours():
    prog = {"a|photo": carte(J - 3), "b|photo": carte(J - 5)}

    p = un("phraseRelance", prog, J, 4)

    assert "3 jours" in p and "4 cartes" in p and p.endswith(".")


def test_la_relance_dit_hier_plutot_qu_un_jour():
    p = un("phraseRelance", {"a|photo": carte(J - 1)}, J, 2)

    assert p.startswith("Depuis hier,") and "1 jour" not in p


def test_une_seule_carte_reste_au_singulier():
    p = un("phraseRelance", {"a|photo": carte(J - 2)}, J, 1)

    assert "1 carte attend d’être revue." in p and "cartes" not in p


def test_une_session_du_jour_ne_parle_pas_de_delai():
    p = un("phraseRelance", {"a|photo": carte(J)}, J, 3)

    assert "aujourd’hui" in p and "Depuis 0 jours" not in p


def test_une_progression_sans_date_ne_casse_pas_la_phrase():
    """Entrées d'avant la planification (#16), le temps d'une migration."""
    p = un("phraseRelance", {"a|photo": {"s": 2, "c": 1}}, J, 5)

    assert "5 cartes" in p and "Depuis" not in p


def test_la_derniere_session_est_la_plus_recente():
    prog = {"a|photo": carte(J - 9), "b|fiche": carte(J - 2), "c|photo": carte(J - 30)}

    assert un("derniereSession", prog) == J - 2


def test_la_derniere_session_d_une_progression_vide():
    assert un("derniereSession", {}) is None


# ------------------------------------------------- relu par une vraie bibliothèque

def test_le_fichier_est_accepte_par_une_bibliotheque_icalendar():
    """Mes assertions ne valent que ce que vaut ma lecture du RFC : un parseur tiers
    tranche. C'est lui qui joue le rôle du Calendrier iOS ou de Google Agenda."""
    ical = pytest.importorskip("icalendar", reason="pip install -r requirements-dev.txt")

    cal = ical.Calendar.from_ical(ics(heure=19, minute=30).encode("utf-8"))
    evts = list(cal.walk("VEVENT"))

    assert len(evts) == 1
    ev = evts[0]
    debut = ev.decoded("dtstart")
    assert debut.hour == 19 and debut.minute == 30
    assert debut.tzinfo is None, "heure flottante : aucun fuseau ne doit être attaché"
    assert dict(ev.get("rrule")) == {"FREQ": ["DAILY"]}
    assert ev.decoded("duration").total_seconds() == 900
    assert "Réviser" in str(ev.get("summary")), "les accents ont survécu au repliage"
    assert len(list(ev.walk("VALARM"))) == 1
