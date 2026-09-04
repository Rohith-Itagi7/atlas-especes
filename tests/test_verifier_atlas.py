#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contrôles de scripts/verifier_atlas.py.

Chaque contrôle renvoie (erreurs, avertissements) : une erreur fait échouer la CI, un
avertissement non. Les tests vérifient aussi qu'une donnée correcte ne déclenche rien —
un linter qui crie au loup est un linter qu'on désactive.
"""
import os
import subprocess
import sys

import pytest

from conftest import BASE, load_module, vignette_cell


@pytest.fixture
def va(repo, monkeypatch):
    """Le vérificateur, branché sur le faux dépôt de la fixture `repo`."""
    module = load_module("verifier_atlas")
    monkeypatch.setattr(module, "atlas_data", repo.atlas_data)
    monkeypatch.setattr(module, "BASE", repo.root)
    return module


def ligne(vignette, name, latin, comestible="glands"):
    return [vignette_cell(vignette), name, latin, "arbre", "Fagacées", comestible, ""]


# --------------------------------------------------------------------- noms latins

@pytest.mark.parametrize("latin", [
    "Quercus robur",
    "Ribes sp.",                    # espèce non précisée
    "Symphytum ×uplandicum",        # hybride
    "Brassica oleracea ramosa",     # sous-espèce
    "Allium cepa Aggregatum",       # groupe de cultivars (majuscule attendue)
    "Prunus avium (cultivé)",       # note entre parenthèses
    "Beta / Spinacia",              # une ligne pour deux genres
])
def test_latins_valides(va, latin):
    assert va.verifier_latin(latin) is None


@pytest.mark.parametrize("latin,attendu", [
    ("", "vide"),
    ("   ", "vide"),
    ("quercus robur", "majuscule"),
    ("Quercus", "incomplet"),
    ("Quercus robur 123", "épithète inattendue"),
    ("(cultivé)", "pas de taxon"),
])
def test_latins_invalides(va, latin, attendu):
    pb = va.verifier_latin(latin)
    assert pb and attendu in pb


# ------------------------------------------------------------------------ tableaux

def test_deux_especes_qui_partagent_une_vignette(va, repo):
    repo.vignette("sureau.jpg")
    repo.write_atlas("Test.md", [ligne("sureau.jpg", "Sureau noir", "Sambucus nigra"),
                                 ligne("sureau.jpg", "Sureau yèble", "Sambucus ebulus")])
    repo.use_atlases("Test.md")

    errs, warns, stems = va.verifier_tableaux()

    assert len(errs) == 1 and "déjà utilisée" in errs[0]
    assert stems == {"sureau"}


def test_tableau_correct_ne_declenche_rien(va, repo):
    repo.vignette("chene.jpg")
    repo.vignette("hetre.jpg")
    repo.write_atlas("Test.md", [ligne("chene.jpg", "Chêne sessile", "Quercus petraea"),
                                 ligne("hetre.jpg", "Hêtre", "Fagus sylvatica")])
    repo.use_atlases("Test.md")

    errs, warns, stems = va.verifier_tableaux()

    assert (errs, warns) == ([], [])
    assert stems == {"chene", "hetre"}


def test_latin_fautif_signale_avec_sa_ligne(va, repo):
    repo.vignette("chene.jpg")
    repo.write_atlas("Test.md", [ligne("chene.jpg", "Chêne test", "quercus")])
    repo.use_atlases("Test.md")

    errs, _warns, _stems = va.verifier_tableaux()

    assert len(errs) == 1 and errs[0].startswith("Test.md:5")


# ------------------------------------------------------------- photos supplémentaires

def test_photo_orpheline_signalee(va, repo):
    # Nommée hors convention : elle n'apparaîtrait nulle part dans le site.
    repo.extra_photo("chene_feuille_1.jpg")

    errs, _warns = va.verifier_photos_extra({"chene"})

    assert len(errs) == 1
    assert "chene_feuille_1.jpg" in errs[0] and "aucune espèce" in errs[0]


def test_photo_dont_l_espece_n_existe_pas_signalee(va, repo):
    repo.extra_photo("especeinconnue-feuille-1.jpg")

    errs, _warns = va.verifier_photos_extra({"chene"})

    assert len(errs) == 1 and "especeinconnue-feuille-1.jpg" in errs[0]


def test_photo_ambigue_signalee(va, repo):
    # Deux stems dont l'un préfixe l'autre *avec un tiret* : le rattachement est ambigu.
    repo.extra_photo("ail-des-ours-1.jpg")

    errs, _warns = va.verifier_photos_extra({"ail", "ail-des-ours"})

    assert len(errs) == 1 and "réclamée par 2 espèces" in errs[0]


def test_mot_cle_d_aspect_non_reconnu_averti(va, repo):
    repo.extra_photo("chene-ecorse-1.jpg")   # faute de frappe : l'aspect est perdu

    errs, warns = va.verifier_photos_extra({"chene"})

    assert errs == []
    assert len(warns) == 1 and "ecorse" in warns[0]


def test_pas_d_avertissement_si_le_sidecar_annote_la_photo(va, repo):
    repo.extra_photo("chene-vueaerienne-1.jpg")
    repo.sidecar("chene-vueaerienne-1.jpg\tport\n")

    errs, warns = va.verifier_photos_extra({"chene"})

    assert (errs, warns) == ([], [])


def test_photos_bien_nommees_ne_declenchent_rien(va, repo):
    repo.extra_photo("chene-feuille-1.jpg")
    repo.extra_photo("chene-2.jpg")
    repo.extra_photo("ail_des_ours-fleur-1.jpg")

    assert va.verifier_photos_extra({"chene", "ail_des_ours"}) == ([], [])


def test_fichiers_techniques_ignores(va, repo):
    repo.sidecar("chene-1.jpg\tfeuille\n")            # _aspects.tsv
    repo.write("img/quiz-extra/_COMMENT-NOMMER.txt", "aide au nommage\n")
    repo.extra_photo("chene-1.jpg")

    assert va.verifier_photos_extra({"chene"}) == ([], [])


# --------------------------------------------------------------- sidecar _aspects.tsv

def test_sidecar_aspect_inconnu(va, repo):
    repo.extra_photo("chene-1.jpg")
    repo.sidecar("chene-1.jpg\tfeuille,ecorse\n")

    errs, _warns = va.verifier_sidecar()

    assert len(errs) == 1 and "ecorse" in errs[0]


def test_sidecar_ligne_morte(va, repo):
    repo.sidecar("photo-supprimee-1.jpg\tfeuille\n")

    errs, _warns = va.verifier_sidecar()

    assert len(errs) == 1 and "n'existe ni dans" in errs[0]


def test_sidecar_tabulation_manquante(va, repo):
    repo.sidecar("chene-1.jpg feuille\n")

    errs, warns = va.verifier_sidecar()

    assert errs == [] and len(warns) == 1 and "tabulation" in warns[0]


def test_sidecar_valide_ne_declenche_rien(va, repo):
    repo.vignette("chene.jpg")
    repo.extra_photo("chene-1.jpg")
    repo.sidecar("fichier\taspects\n# un commentaire\nchene-1.jpg\tfeuille;fleur\n"
                 "chene.jpg\tport\n")   # une vignette peut aussi être annotée

    assert va.verifier_sidecar() == ([], [])


# ------------------------------------------------------------------------ vignettes

def test_vignette_orpheline_avertie(va, repo):
    repo.vignette("bruyere-cendree.jpg")

    errs, warns = va.verifier_vignettes({"chene"})

    assert errs == []
    assert len(warns) == 1 and "bruyere-cendree.jpg" in warns[0]


def test_vignette_utilisee_ne_declenche_rien(va, repo):
    repo.vignette("chene.jpg")

    assert va.verifier_vignettes({"chene"}) == ([], [])


# --------------------------------------------------------------------- contributions

def test_contribution_action_inconnue(va, repo):
    repo.contribution("app.tsv", "action\tfichier\tvaleur\nrenomme\tchene-1.jpg\thetre\n")

    errs, _warns = va.verifier_contributions({"chene"})

    assert any("action inconnue" in e for e in errs)


def test_contribution_reassign_vers_stem_inconnu(va, repo):
    repo.extra_photo("chene-1.jpg")
    repo.contribution("app.tsv", "reassign\tchene-1.jpg\tespece_fantome\n")

    errs, _warns = va.verifier_contributions({"chene"})

    assert len(errs) == 1 and "espece_fantome" in errs[0]


def test_contribution_fichier_absent(va, repo):
    repo.contribution("app.tsv", "remove\tphoto-inexistante.jpg\t\n")

    errs, _warns = va.verifier_contributions({"chene"})

    assert len(errs) == 1 and "photo-inexistante.jpg" in errs[0]


def test_contribution_tag_aspect_inconnu(va, repo):
    repo.extra_photo("chene-1.jpg")
    repo.contribution("app.tsv", "tag\tchene-1.jpg\tfeuille,ecorse\n")

    errs, _warns = va.verifier_contributions({"chene"})

    assert len(errs) == 1 and "ecorse" in errs[0]


def test_contribution_tag_sans_aspect_averti(va, repo):
    repo.extra_photo("chene-1.jpg")
    repo.contribution("app.tsv", "tag\tchene-1.jpg\t\n")

    errs, warns = va.verifier_contributions({"chene"})

    assert errs == [] and len(warns) == 1 and "restera « divers »" in warns[0]


def test_contribution_valide_ne_declenche_rien(va, repo):
    repo.vignette("chene.jpg")
    repo.extra_photo("chene-1.jpg")
    repo.vignette("hetre.jpg")
    repo.contribution("app.tsv",
                      "# manque une écorce de chêne\n"
                      "action\tfichier\tvaleur\n"
                      "tag\tchene-1.jpg\tfeuille,fleur\n"
                      "tag\tchene.jpg\tport\n"
                      "reassign\tchene-1.jpg\thetre\n"
                      "remove\tchene-1.jpg\t\n")

    assert va.verifier_contributions({"chene", "hetre"}) == ([], [])


# ------------------------------------------------------------------------ confusions

def test_confusion_stem_inconnu(va, repo):
    repo.confusions([["Chênes", "chene_sessile,chene_fantome", "Pétiole long"]])

    errs, _warns = va.verifier_confusions({"chene_sessile"})

    assert len(errs) == 1 and "chene_fantome" in errs[0]


def test_confusion_sans_critere(va, repo):
    repo.confusions([["Chênes", "chene_sessile,chene_pedoncule", ""]])

    errs, _warns = va.verifier_confusions({"chene_sessile", "chene_pedoncule"})

    assert len(errs) == 1 and "ce qui tranche" in errs[0]


def test_confusion_a_une_seule_espece_avertie(va, repo):
    repo.confusions([["Chêne seul", "chene_sessile", "Pétiole long"]])

    errs, warns = va.verifier_confusions({"chene_sessile"})

    assert errs == [] and len(warns) == 1 and "une seule espèce" in warns[0]


def test_confusions_absentes_averti(va, repo):
    errs, warns = va.verifier_confusions({"chene"})

    assert errs == [] and len(warns) == 1 and "mode sosies" in warns[0]


def test_confusions_valides_ne_declenchent_rien(va, repo):
    repo.confusions([["Ail des ours & sosies", "ail_des_ours,colchique",
                      "Froisser la feuille : odeur d'ail"]])

    assert va.verifier_confusions({"ail_des_ours", "colchique"}) == ([], [])


# ------------------------------------------------------------------- dépôt réel (CI)

def test_le_verificateur_passe_sur_le_depot_reel():
    """Ce que lance la CI : le dépôt doit rester sans erreur (les avertissements passent)."""
    r = subprocess.run([sys.executable, os.path.join("scripts", "verifier_atlas.py")],
                       cwd=BASE, capture_output=True, text=True)

    assert r.returncode == 0, r.stdout + r.stderr
    assert "Atlas valides" in r.stdout
