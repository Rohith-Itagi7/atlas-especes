#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Hors ligne : manifeste, service worker, poids par catégorie (cf. #12).

L'atlas sert en forêt, là où il n'y a pas de réseau. Ce qui se teste ici est le **build**
(fichiers produits, tailles annoncées) et les deux fonctions pures du client ; le comportement
du service worker lui-même se vérifie en navigateur, serveur arrêté.
"""
import json
import os
import re
import shutil
import subprocess

import pytest

from conftest import BASE, load_module


@pytest.fixture
def sw():
    return load_module("site_sw")


# ------------------------------------------------------------------------ manifeste

def test_le_manifeste_a_ce_qu_il_faut_pour_etre_installable(sw):
    m = sw.manifeste()

    assert m["name"] and m["short_name"]
    assert m["display"] == "standalone"
    assert m["start_url"] == "./" and m["scope"] == "./"
    assert m["lang"] == "fr" and m["theme_color"].startswith("#")
    tailles = {i.get("sizes") for i in m["icons"]}
    assert "192x192" in tailles and "512x512" in tailles, "Android exige 192 et 512"
    assert any(i.get("purpose") == "maskable" for i in m["icons"])
    json.dumps(m)


# ------------------------------------------------------------------ service worker

def test_le_sw_est_versionne_et_sans_placeholder(sw):
    js = sw.sw_js("abc123def456")

    assert "abc123def456" in js
    assert "__VERSION__" not in js and "__COQUILLE__" not in js and "__CACHE_IMAGES__" not in js
    assert sw.CACHE_IMAGES in js


def test_la_coquille_ne_contient_pas_les_photos(sw):
    fichiers = sw.coquille()

    assert "index.html" in fichiers and sw.MANIFESTE in fichiers
    assert not [f for f in fichiers if f.startswith("img/")], \
        "les 33 Mo de photos ne sont pas précachés : l'utilisateur choisit"


def test_les_deux_strategies_sont_en_place(sw):
    js = sw.sw_js("v")

    assert "cacheDabord" in js and "reseauDabord" in js
    assert "/img/" in js, "les images passent par le cache d'abord"
    # le cache des photos survit aux mises à jour, celui de la coquille non
    assert "coquille-' + VERSION" in js
    assert "startsWith('coquille-')" in js and "startsWith('images-')" in js


def test_ecrire_produit_les_fichiers(sw, tmp_path):
    out = str(tmp_path)

    png = sw.ecrire(out, "v1")

    produits = set(os.listdir(out))
    assert {sw.FICHIER_SW, sw.MANIFESTE, sw.ICONE_SVG} <= produits
    if png:
        assert {n for _px, n in sw.ICONES_PNG} <= produits
    json.load(open(os.path.join(out, sw.MANIFESTE), encoding="utf-8"))


def test_sans_pillow_l_icone_svg_suffit(sw, tmp_path, monkeypatch):
    monkeypatch.setitem(__import__("sys").modules, "PIL", None)   # import → TypeError/ImportError
    out = str(tmp_path)

    try:
        png = sw.ecrire_icones(out)
    except Exception:
        pytest.skip("simulation d'absence de Pillow non concluante dans cet environnement")

    assert os.path.exists(os.path.join(out, sw.ICONE_SVG))
    if not png:
        assert not [f for f in os.listdir(out) if f.endswith(".png")]


# -------------------------------------------------------- poids annoncés par catégorie

def test_le_poids_par_categorie_compte_original_et_vignette(repo, monkeypatch, tmp_path):
    build_web = load_module("build_web")
    monkeypatch.setattr(build_web, "BASE", repo.root)
    from PIL import Image
    Image.new("RGB", (600, 400), (80, 120, 60)).save(os.path.join(repo.img, "chene.jpg"))
    out = str(tmp_path / "site")
    os.makedirs(os.path.join(out, "img", "thumb"))
    shutil.copy(os.path.join(repo.img, "chene.jpg"), os.path.join(out, "img/thumb/chene.jpg"))
    data = [{"cat": "ligneux", "imgs": [{"u": "img/especes/chene.jpg", "t": "img/thumb/chene.jpg"}]},
            {"cat": "herbace", "imgs": [{"u": "img/especes/absente.jpg"}]}]

    par_cat = build_web.offline_web(data, out)

    assert par_cat["ligneux"]["n"] == 2, "l'original et sa vignette"
    assert par_cat["ligneux"]["o"] > 0
    assert par_cat["herbace"] == {"n": 0, "o": 0}, "un fichier absent ne compte pas"


def test_l_empreinte_change_avec_les_donnees():
    build_web = load_module("build_web")
    a = [{"id": "chene", "name": "Chêne"}]
    b = [{"id": "chene", "name": "Chêne sessile"}]

    assert build_web.empreinte(a) == build_web.empreinte(a)
    assert build_web.empreinte(a) != build_web.empreinte(b)
    assert len(build_web.empreinte(a)) == 12


def test_la_page_declare_le_manifeste_et_le_theme():
    build_web = load_module("build_web")
    site_sw = load_module("site_sw")

    html = build_web.assemble([], {"cats": {}, "cache": site_sw.CACHE_IMAGES})

    assert 'rel="manifest"' in html and site_sw.MANIFESTE in html
    assert 'name="theme-color"' in html
    assert 'rel="apple-touch-icon"' in html, "iOS a besoin de son icône"
    assert "__OFFLINE__" not in html


# ------------------------------------------------- fonctions pures du client (node)

HARNESS = """
class App {
  constructor(data){ this.data = data; }
  all(){ return this.data; }
__METHODES__
}
const app = new App(__DATA__);
console.log(JSON.stringify(__APPELS__.map(a => app[a[0]].apply(app, a.slice(1)))));
"""

ESPECES = [
    {"id": "chene", "cat": "ligneux",
     "imgs": [{"u": "img/especes/chene.jpg", "t": "img/thumb/chene.jpg"},
              {"u": "img/quiz-extra/chene-1.jpg", "t": "img/thumb/chene-1.jpg"}]},
    {"id": "ortie", "cat": "herbace", "imgs": [{"u": "img/especes/ortie.jpg"}]},
]


def _appeler(appels, data=ESPECES):
    src = open(os.path.join(BASE, "scripts", "site_ui.py"), encoding="utf-8").read()
    m = re.search(r"// __HORSLIGNE_DEBUT__[^\n]*\n(.*?)// __HORSLIGNE_FIN__", src, re.S)
    assert m, "bloc hors ligne introuvable dans site_ui.py"
    js = (HARNESS.replace("__METHODES__", m.group(1))
                 .replace("__DATA__", json.dumps(data, ensure_ascii=False))
                 .replace("__APPELS__", json.dumps(appels, ensure_ascii=False)))
    r = subprocess.run(["node", "-e", js], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


@pytest.mark.skipif(shutil.which("node") is None, reason="node absent")
@pytest.mark.parametrize("octets,attendu", [
    (0, "1 ko"), (2048, "2 ko"), (900 * 1024, "0,9 Mo"),
    (5 * 1048576, "5,0 Mo"), (19_200_000, "18 Mo"),
])
def test_tailles_lisibles(octets, attendu):
    assert _appeler([["octetsLisibles", octets]]) == [attendu]


@pytest.mark.skipif(shutil.which("node") is None, reason="node absent")
def test_les_urls_d_une_categorie_couvrent_originaux_et_vignettes():
    got, = _appeler([["urlsCategorie", "ligneux"]])

    assert got == ["img/especes/chene.jpg", "img/thumb/chene.jpg",
                   "img/quiz-extra/chene-1.jpg", "img/thumb/chene-1.jpg"]


@pytest.mark.skipif(shutil.which("node") is None, reason="node absent")
def test_une_espece_sans_vignette_n_ajoute_rien_de_vide():
    got, = _appeler([["urlsCategorie", "herbace"]])

    assert got == ["img/especes/ortie.jpg"]


@pytest.mark.skipif(shutil.which("node") is None, reason="node absent")
def test_mixte_prend_tout_sans_doublon():
    got, = _appeler([["urlsCategorie", "mixte"]])

    assert len(got) == len(set(got)) == 5


# ------------------------------------------- la coquille sans Pillow (trouvé à la revue)

def test_la_coquille_ne_liste_que_les_icones_produites(sw):
    """Sans Pillow, les PNG ne sont pas écrits. Les précacher quand même cassait TOUT le
    mode hors ligne : addAll est atomique, et son échec est avalé par .catch(() => {}).
    Mesuré en navigateur : 0 fichier en cache, et ERR_FAILED serveur coupé."""
    assert set(n for _px, n in sw.ICONES_PNG) <= set(sw.coquille(True))
    assert not [f for f in sw.coquille(False) if f.endswith(".png")]
    assert "index.html" in sw.coquille(False), "l'essentiel reste précaché"


def test_l_installation_ne_perd_pas_tout_pour_un_fichier(sw):
    """Un seul 404 (icône absente, déploiement partiel) ne doit pas coûter le hors ligne."""
    code = "\n".join(l for l in sw.sw_js("v").split("\n") if not l.strip().startswith("//"))

    assert "addAll" not in code, "addAll est atomique : un échec emporte toute la coquille"
    assert "c.add(f).catch" in code


def test_ecrire_n_annonce_que_des_fichiers_qu_il_a_ecrits(sw, tmp_path):
    """Le contrat qui compte : tout fichier annoncé au précache existe vraiment.

    « ./ » et index.html sont produits par build_web.py, pas par ce module : le reste de
    la coquille est à la charge de site_sw, et c'est là qu'était le trou (les PNG).
    """
    out = str(tmp_path)

    sw.ecrire(out, "v1")

    js = open(os.path.join(out, sw.FICHIER_SW), encoding="utf-8").read()
    fichiers = json.loads(re.search(r"const FICHIERS = (\[.*?\]);", js, re.S).group(1))
    assert "./" in fichiers and "index.html" in fichiers, "la page elle-même doit être précachée"
    a_nous = [f for f in fichiers if f not in ("./", "index.html")]
    absents = [f for f in a_nous if not os.path.exists(os.path.join(out, f))]

    assert not absents, "annoncés au précache mais absents : %s" % absents
