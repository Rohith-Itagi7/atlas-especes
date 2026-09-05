#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sélection d'un lot d'espèces pour les fetchers de photos (cf. #17).

Combler les manques photo se fait par lots d'une vingtaine d'espèces. Sans sélection,
compléter 20 espèces obligeait à reparcourir les 253 de l'atlas et à marteler les API
pour rien : les deux fetchers acceptent maintenant `--lot` / `--especes`.

Le téléchargement lui-même n'est pas testable ici (il sort sur le réseau) ; ce qui se
teste, et ce qui casse en silence, c'est le choix des espèces.
"""
import os

import pytest

from conftest import BASE, load_module

LOT1 = os.path.join(BASE, "lots", "lot-1-confusions.txt")


# ------------------------------------------------------------------- lecture d'un lot

def test_une_liste_en_ligne(atlas_data):
    assert atlas_data.lire_lot("cigue,arum,colchique") == ["cigue", "arum", "colchique"]


def test_les_espaces_et_les_doublons_sont_absorbes(atlas_data):
    assert atlas_data.lire_lot(" cigue , arum ,cigue ") == ["cigue", "arum"]


def test_un_argument_vide_ne_selectionne_rien(atlas_data):
    assert atlas_data.lire_lot("") == [] and atlas_data.lire_lot(None) == []


def test_un_fichier_avec_commentaires(atlas_data, tmp_path):
    f = tmp_path / "lot.txt"
    f.write_text("# un lot\n\ncigue   # mortelle\narum\n\n# fin\n", encoding="utf-8")

    assert atlas_data.lire_lot(str(f)) == ["cigue", "arum"]


def test_l_ordre_du_lot_est_conserve(atlas_data):
    """Les espèces dangereuses sont en tête du fichier : on les traite d'abord."""
    assert atlas_data.lire_lot("zzz,aaa,mmm") == ["zzz", "aaa", "mmm"]


# ---------------------------------------------------------------------- sélection

def test_la_selection_suit_l_ordre_du_lot_pas_celui_de_l_atlas(atlas_data):
    retenus, inconnus = atlas_data.selection(["arum", "cigue", "hetre"], ["cigue", "arum"])

    assert retenus == ["cigue", "arum"] and inconnus == []


def test_un_stem_inconnu_est_rendu_a_l_appelant(atlas_data):
    """Une faute de frappe doit arrêter le téléchargement, pas le laisser ne rien faire."""
    retenus, inconnus = atlas_data.selection(["cigue"], ["cigue", "cigüe", "nawak"])

    assert retenus == ["cigue"] and inconnus == ["cigüe", "nawak"]


# ------------------------------------------------------------ branchement des fetchers

@pytest.fixture(params=["fetch_aspects", "fetch_photos"])
def fetcher(request):
    return load_module(request.param)


def especes(fetcher):
    return fetcher.species_all() if hasattr(fetcher, "species_all") else fetcher.species_list()


def test_sans_argument_tout_l_atlas_est_traite(fetcher):
    sp = especes(fetcher)

    assert fetcher.choisir(sp, []) == sp
    assert fetcher.choisir(sp, ["--autre-chose"]) == sp


def test_un_lot_restreint_bien_la_liste(fetcher):
    sp = especes(fetcher)

    lot = fetcher.choisir(sp, ["--especes", "cigue,arum,berce"])

    assert [x[0] for x in lot] == ["cigue", "arum", "berce"]
    assert len(sp) > len(lot), "le filtre ne filtre rien"


def test_le_lot_est_servi_dans_son_ordre_pas_dans_celui_de_l_atlas(fetcher):
    sp = especes(fetcher)

    lot = fetcher.choisir(sp, ["--especes", "ortie,alliaire,arum"])

    assert [x[0] for x in lot] == ["ortie", "alliaire", "arum"]


def test_un_stem_inconnu_arrete_le_fetcher(fetcher):
    sp = especes(fetcher)

    with pytest.raises(SystemExit) as e:
        fetcher.choisir(sp, ["--especes", "cigue,pasunestem"])

    assert "pasunestem" in str(e.value)


def test_le_lot_1_du_depot_est_valide(fetcher):
    """Le fichier livré doit rester exécutable : un stem renommé le casserait."""
    sp = especes(fetcher)

    lot = fetcher.choisir(sp, ["--lot", LOT1])

    assert len(lot) >= 20, "le lot 1 devait couvrir une vingtaine d'espèces"
    # les quatre mortelles / toxiques sont en tête du fichier, donc du traitement
    assert [x[0] for x in lot][:4] == ["cigue", "arum", "colchique", "digitale"]


def test_chaque_espece_du_lot_1_est_bien_dans_un_groupe_de_confusion(atlas_data):
    """Le lot vise les espèces confondables : une espèce sans groupe n'apprend rien du
    critère qui tranche, même avec trois photos de plus."""
    groupes = {s for g in atlas_data.CONF for s in g["stems"]}
    lot = atlas_data.lire_lot(LOT1)

    # basilic et aspérule n'ont pas de sosie dangereux : elles ne veulent que des photos
    orphelines = [s for s in lot if s not in groupes and s not in ("basilic", "asperule")]

    assert not orphelines, "sans groupe de confusion : %s" % ", ".join(orphelines)
