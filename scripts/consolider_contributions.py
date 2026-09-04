#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Consolide les contributions (contributions/*.tsv) dans les sources du dépôt.

Les contributions sont appliquées au build à chaque fois qu'on construit le site : tant
qu'elles restent là, la vérité est en deux endroits. Ce script les fait entrer dans les
sources, puis supprime le fichier traité.

  tag      → écrit la ligne dans img/quiz-extra/_aspects.tsv
  reassign → renomme la photo vers la bonne espèce (convention <stem>-<aspect>-<n>.jpg)
  remove   → supprime la photo et son entrée d'aspects
  # …      → recopié dans contributions/NOTES.md (ce sont les manques signalés)

Rien n'est modifié si une seule action est invalide : le rapport est complet, la
consolidation est tout ou rien.

  python3 scripts/consolider_contributions.py           # décrit le plan, ne touche à rien
  python3 scripts/consolider_contributions.py --apply   # exécute
"""
import collections
import glob
import os
import re
import sys

import atlas_data

BASE = atlas_data.BASE
CONTRIB = os.path.join(BASE, "contributions")
SIDECAR = os.path.join(atlas_data.EXTRA, "_aspects.tsv")
NOTES = os.path.join(CONTRIB, "NOTES.md")
ACTIONS = ("tag", "reassign", "remove")

Action = collections.namedtuple("Action", "source ligne action fichier valeur")


def lire_contributions():
    """Renvoie (actions, notes, erreurs) pour tous les contributions/*.tsv."""
    actions, notes, errs = [], [], []
    for fp in sorted(glob.glob(os.path.join(CONTRIB, "*.tsv"))):
        rel = os.path.relpath(fp, BASE)
        for i, ln in enumerate(open(fp, encoding="utf-8"), 1):
            ln = ln.rstrip("\n")
            if not ln.strip():
                continue
            if ln.startswith("#"):
                texte = ln.lstrip("# ").strip()
                if texte:
                    notes.append((rel, texte))
                continue
            ou = "%s:%d" % (rel, i)
            if "\t" not in ln:
                errs.append("%s : tabulation manquante (« action⇥fichier⇥valeur »)" % ou)
                continue
            parts = ln.split("\t")
            act = parts[0].strip().lower()
            if act in ("action", "type"):
                continue
            fichier = parts[1].strip() if len(parts) > 1 else ""
            valeur = parts[2].strip() if len(parts) > 2 else ""
            if act not in ACTIONS:
                errs.append("%s : action inconnue « %s » — attendu : %s"
                            % (ou, act, ", ".join(ACTIONS)))
                continue
            if not fichier:
                errs.append("%s : action « %s » sans nom de fichier" % (ou, act))
                continue
            actions.append(Action(rel, i, act, fichier, valeur))
    return actions, notes, errs


def emplacement(fichier):
    """« extra », « especes » ou None selon où vit le fichier."""
    if os.path.exists(os.path.join(atlas_data.EXTRA, fichier)):
        return "extra"
    if os.path.exists(os.path.join(atlas_data.IMG, fichier)):
        return "especes"
    return None


def lire_sidecar():
    """(en-tête, {fichier: [aspects]}) du sidecar, tel qu'il est sur le disque."""
    entrees = {}
    entete = "fichier\taspects"
    if not os.path.exists(SIDECAR):
        return entete, entrees
    for ln in open(SIDECAR, encoding="utf-8"):
        ln = ln.rstrip("\n")
        if not ln or ln.startswith("#") or "\t" not in ln:
            continue
        fn, asp = ln.split("\t", 1)
        if fn.strip().lower() in ("fichier", "file"):
            entete = ln
            continue
        entrees[fn.strip()] = [a.strip() for a in re.split(r"[,;]", asp) if a.strip()]
    return entete, entrees


def aspects_du_nom(nom, stem):
    """Aspects déduits du nom de fichier seul (sans passer par le sidecar)."""
    fn = os.path.splitext(nom.lower())[0]
    suffixe = fn[len(stem):] if fn.startswith(stem) else fn
    trouves = []
    for tok in re.split(r"[-_ ]+", suffixe):
        a = atlas_data.ASPECT_KW.get(tok)
        if a and a not in trouves:
            trouves.append(a)
    return trouves


def nom_libre(cible, aspects, ext, pris):
    """Premier nom disponible pour la photo réattribuée : <cible>-<aspects>-<n><ext>."""
    asp = "_".join(a for a in aspects if a != atlas_data.DIVERS)
    n = 1
    while True:
        nom = ("%s-%s-%d%s" % (cible, asp, n, ext)) if asp else ("%s-%d%s" % (cible, n, ext))
        if nom not in pris and not os.path.exists(os.path.join(atlas_data.EXTRA, nom)):
            return nom
        n += 1


def plan_de_consolidation(actions, notes, stems):
    """Construit le plan, ou la liste des raisons de ne rien faire."""
    errs = []
    _entete, sidecar = lire_sidecar()
    supprimes = {a.fichier for a in actions if a.action == "remove"}
    tags = {a.fichier: a for a in actions if a.action == "tag"}
    plan = {"tags": {}, "renommages": [], "suppressions": [], "entrees_a_retirer": [],
            "notes": notes, "fichiers_traites": sorted(
                os.path.relpath(p, BASE) for p in glob.glob(os.path.join(CONTRIB, "*.tsv")))}
    pris = set()

    for a in actions:
        ou = "%s:%d" % (a.source, a.ligne)
        ou_est = emplacement(a.fichier)
        if not ou_est:
            errs.append("%s : « %s » n'existe ni dans img/quiz-extra ni dans img/especes"
                        % (ou, a.fichier))
            continue

        if a.action == "tag":
            if a.fichier in supprimes:
                continue                      # le remove tranche : inutile de tagger
            aspects = [x.strip() for x in re.split(r"[,;]", a.valeur) if x.strip()]
            inconnus = [x for x in aspects if x not in atlas_data.ASPECTS_VALIDES]
            if inconnus:
                errs.append("%s : aspect inconnu %s — attendu : %s"
                            % (ou, ", ".join("« %s »" % x for x in inconnus),
                               ", ".join(atlas_data.ASPECT_IDS)))
                continue
            if not aspects:
                errs.append("%s : tag sans aspect (utiliser « divers » si la photo n'en "
                            "montre aucun)" % ou)
                continue
            if sidecar.get(a.fichier) != aspects:
                plan["tags"][a.fichier] = aspects

        elif a.action == "remove":
            if ou_est == "especes":
                errs.append("%s : « %s » est une vignette d'espèce — la retirer voudrait dire "
                            "supprimer l'espèce de son atlas, ce n'est pas le rôle d'un remove"
                            % (ou, a.fichier))
                continue
            plan["suppressions"].append(a.fichier)
            if a.fichier in sidecar:
                plan["entrees_a_retirer"].append(a.fichier)

        else:  # reassign
            if a.fichier in supprimes:
                continue
            if ou_est == "especes":
                errs.append("%s : « %s » est une vignette d'espèce — pour la réattribuer, "
                            "corriger la ligne de l'atlas" % (ou, a.fichier))
                continue
            if not a.valeur:
                errs.append("%s : reassign sans espèce cible" % ou)
                continue
            if a.valeur not in stems:
                errs.append("%s : reassign vers « %s », qui n'est le stem d'aucune espèce"
                            % (ou, a.valeur))
                continue
            aspects = (plan["tags"].get(a.fichier)
                       or (tags[a.fichier].valeur.split(",") if a.fichier in tags else None)
                       or sidecar.get(a.fichier)
                       or aspects_du_nom(a.fichier, a.valeur))
            aspects = [x.strip() for x in aspects if x.strip()]
            ext = os.path.splitext(a.fichier)[1].lower()
            nouveau = nom_libre(a.valeur, aspects, ext, pris)
            pris.add(nouveau)
            plan["renommages"].append((a.fichier, nouveau, aspects))
            plan["tags"].pop(a.fichier, None)
            if a.fichier in sidecar:
                plan["entrees_a_retirer"].append(a.fichier)
            # on ne garde une entrée que si le nom ne suffit pas à porter les aspects
            if aspects and aspects_du_nom(nouveau, a.valeur) != aspects:
                plan["tags"][nouveau] = aspects

    return plan, errs


def decrire(plan):
    lignes = []
    for f, aspects in sorted(plan["tags"].items()):
        lignes.append("  aspects   %-34s → %s" % (f, ",".join(aspects)))
    for src, dst, _asp in plan["renommages"]:
        lignes.append("  renomme   %-34s → %s" % (src, dst))
    for f in sorted(plan["suppressions"]):
        lignes.append("  supprime  %s" % f)
    for f in sorted(set(plan["entrees_a_retirer"]) - set(plan["tags"])):
        lignes.append("  oublie    entrée d'aspects de %s" % f)
    for source, texte in plan["notes"]:
        lignes.append("  note      %s (%s)" % (texte, source))
    for f in plan["fichiers_traites"]:
        lignes.append("  archive   %s (supprimé après traitement)" % f)
    return lignes


def ecrire_sidecar(plan):
    entete, entrees = lire_sidecar()
    for f in plan["entrees_a_retirer"]:
        entrees.pop(f, None)
    for f in plan["suppressions"]:
        entrees.pop(f, None)
    entrees.update(plan["tags"])
    with open(SIDECAR, "w", encoding="utf-8") as fh:
        fh.write(entete + "\n")
        for f in sorted(entrees):
            fh.write("%s\t%s\n" % (f, ",".join(entrees[f])))


def ecrire_notes(plan):
    if not plan["notes"]:
        return
    nouveau = not os.path.exists(NOTES)
    with open(NOTES, "a", encoding="utf-8") as fh:
        if nouveau:
            fh.write("# Notes des contributions\n\n"
                     "> Commentaires laissés dans les `contributions/*.tsv` et conservés ici "
                     "par `scripts/consolider_contributions.py` : ce sont surtout des manques "
                     "signalés par les utilisateurs.\n")
        for source, texte in plan["notes"]:
            fh.write("\n- %s — _%s_" % (texte, source))
        fh.write("\n")


def appliquer(plan):
    for src, dst, _asp in plan["renommages"]:
        os.rename(os.path.join(atlas_data.EXTRA, src), os.path.join(atlas_data.EXTRA, dst))
    for f in plan["suppressions"]:
        p = os.path.join(atlas_data.EXTRA, f)
        if os.path.exists(p):
            os.remove(p)
    ecrire_sidecar(plan)
    ecrire_notes(plan)
    for rel in plan["fichiers_traites"]:
        os.remove(os.path.join(BASE, rel))


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    inconnus = [a for a in argv if a not in ("--apply", "--dry-run")]
    if inconnus:
        print("option inconnue : %s" % ", ".join(inconnus))
        print(__doc__)
        return 2
    apply_ = "--apply" in argv

    actions, notes, errs_lecture = lire_contributions()
    if not actions and not notes:
        print("Rien à consolider (aucune action dans contributions/*.tsv).")
        return 0

    especes, seen = [], set()
    for path, cat in atlas_data.ATLASES:
        especes += atlas_data.parse_atlas(path, cat, seen)
    stems = {s["stem"] for s in especes}

    plan, errs = plan_de_consolidation(actions, notes, stems)
    errs = errs_lecture + errs
    if errs:
        print("❌ %d problème(s) : rien n'a été modifié." % len(errs))
        for e in errs:
            print("  -", e)
        return 1

    lignes = decrire(plan)
    print("Plan de consolidation (%d action%s) :" % (len(lignes), "s" if len(lignes) > 1 else ""))
    for l in lignes:
        print(l)
    if not apply_:
        print("\n--dry-run : rien n'a été modifié. Relancer avec --apply pour exécuter.")
        return 0
    appliquer(plan)
    print("\n✅ Consolidé. Penser à relancer :"
          "\n   python3 scripts/verifier_atlas.py"
          "\n   python3 scripts/couverture.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
