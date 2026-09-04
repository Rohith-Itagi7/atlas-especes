#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Groupes de sosies lus dans « Confusions - référence.md »."""


def test_lit_les_groupes(repo):
    repo.confusions([
        ["Ail des ours & sosies mortels", "ail_des_ours, colchique, muguet",
         "Froisser la feuille : **odeur d'ail** chez l'ail des ours uniquement"],
        ["Chênes", "chene_sessile,chene_pedoncule", "Pétiole long chez le sessile"],
    ])

    groups = repo.gq.load_confusions()

    assert len(groups) == 2
    assert groups[0]["stems"] == ["ail_des_ours", "colchique", "muguet"]
    assert "odeur d'ail" in groups[0]["tip"]
    assert groups[1]["stems"] == ["chene_sessile", "chene_pedoncule"]


def test_ignore_entete_et_separateur(repo):
    repo.confusions([["Chênes", "chene_sessile,chene_pedoncule", "Pétiole long chez le sessile"]])

    assert len(repo.gq.load_confusions()) == 1   # ni la ligne d'en-tête ni le |---| ne comptent


def test_accepte_le_point_virgule_comme_separateur(repo):
    repo.confusions([["Chênes", "chene_sessile; chene_pedoncule", "Pétiole long"]])

    assert repo.gq.load_confusions()[0]["stems"] == ["chene_sessile", "chene_pedoncule"]


def test_groupe_sans_critere_ignore(repo):
    # Un groupe sans « ce qui tranche » n'apprend rien : il est écarté.
    repo.confusions([["Chênes", "chene_sessile,chene_pedoncule", ""]])

    assert repo.gq.load_confusions() == []


def test_groupe_sans_espece_ignore(repo):
    repo.confusions([["Chênes", "", "Pétiole long chez le sessile"]])

    assert repo.gq.load_confusions() == []


def test_fichier_absent_pas_de_groupe(repo):
    # Le dépôt de test n'a pas d'atlas Confusions : la fonction doit rester silencieuse.
    assert repo.gq.load_confusions() == []
