#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vérifie l'intégrité des atlas et des photos (CI sur chaque Pull Request, et lançable en local).

Deux niveaux de signalement :
  ❌ erreur         → code de sortie 1 : donnée cassée, ou invisible dans le site
  ⚠  avertissement → code de sortie 0 : à corriger, sans bloquer

Contrôles :
  - tableaux : nombre de colonnes, vignette présente et existante, nom et nom latin non vides,
    forme du nom latin, deux espèces qui partagent une vignette ;
  - img/quiz-extra : photo rattachée à une espèce et à une seule (convention
    <stem>-<aspect>-<n>.jpg), mots-clés d'aspect reconnus ;
  - img/quiz-extra/_aspects.tsv : aspects connus, lignes qui visent un fichier existant ;
  - img/especes : vignette utilisée par au moins une espèce ;
  - contributions/*.tsv : actions connues, fichiers et stems cibles existants ;
  - Confusions - référence.md : stems connus, groupes qui tranchent vraiment ;
  - img/CREDITS.tsv : une ligne par image, pas de ligne orpheline, auteur et licence connus.

  python3 scripts/verifier_atlas.py
"""
import glob, os, re, sys

import atlas_data
import credits

BASE = atlas_data.BASE
# Vocabulaire des aspects : source unique dans scripts/atlas_data.py.
ASPECTS = atlas_data.ASPECTS_VALIDES              # ids + « divers » (sans aspect annoncé)
ASPECTS_NOMMES = ", ".join(atlas_data.ASPECT_IDS)  # pour les messages d'erreur

def verifier_latin(latin):
    """Message si le nom latin n'a pas la forme « Genre espèce », sinon None.

    Tolérances, toutes présentes dans les atlas :
      - « Genre sp. » / « Genre spp. »      espèce non précisée (Ribes sp.)
      - hybride « Genre ×epithete »         Symphytum ×uplandicum
      - sous-espèce ou cultivar en 3e mot   Brassica oleracea ramosa
      - groupe de cultivars en majuscule    Allium cepa Aggregatum
      - note entre parenthèses              Prunus avium (cultivé)
      - alternatives séparées par « / »     Beta / Spinacia (une ligne pour deux genres)
    """
    latin = (latin or "").strip()
    if not latin:
        return "nom latin vide"
    sans_note = re.sub(r"\([^)]*\)", " ", latin).strip()   # « (cultivé) » = commentaire
    if not sans_note:
        return "nom latin « %s » : seulement une note, pas de taxon" % latin
    parties = [p.strip() for p in sans_note.split("/")]
    for p in parties:
        mots = p.split()
        if not mots:
            return "nom latin mal formé : « %s »" % latin
        if not re.match(r"^[A-Z][A-Za-zà-ÿ\-]+$", mots[0]):
            return "nom latin « %s » : le genre doit commencer par une majuscule" % p
        if len(mots) == 1 and len(parties) == 1:
            return "nom latin « %s » incomplet : « Genre espèce » attendu" % latin
        for m in mots[1:]:
            # épithète (parfois hybride ×, parfois abrégée « sp. »), ou groupe de cultivars
            if not re.match(r"^(?:(?:×|x)?[a-zà-ÿ\-']+\.?|[A-Z][a-zà-ÿ\-']+)$", m):
                return "nom latin « %s » : épithète inattendue « %s »" % (latin, m)
    return None

def verifier_tableaux():
    """Contrôle les tableaux Markdown. Renvoie (erreurs, avertissements, stems)."""
    errs, warns = [], []
    vus = {}   # stem -> « fichier:ligne » de la première espèce qui l'utilise
    for path, _cat in atlas_data.ATLASES:
        full = os.path.join(BASE, path)
        if not os.path.exists(full):
            errs.append("%s : fichier introuvable" % path); continue
        lines = open(full, encoding="utf-8").read().split("\n")
        header = None
        for ln in lines:
            s = ln.lstrip()
            if s.startswith("|") and not s.startswith("| ![") and "latin" in ln.lower():
                header = [atlas_data.hkey(c) for c in atlas_data.cells_of(ln)]; break
        if not header:
            errs.append("%s : en-tête du tableau introuvable" % path); continue
        hlen = len(header)
        for i, ln in enumerate(lines, 1):
            if not ln.lstrip().startswith("| !["):
                continue
            ou = "%s:%d" % (path, i)
            cells = atlas_data.cells_of(ln)
            if len(cells) != hlen:
                errs.append("%s : %d colonnes au lieu de %d" % (ou, len(cells), hlen))
            m = atlas_data.IMG_RE.search(ln)
            if not m:
                errs.append("%s : vignette ![[...]] manquante" % ou); continue
            if not os.path.exists(os.path.join(atlas_data.IMG, m.group(1))):
                errs.append("%s : vignette absente → img/especes/%s" % (ou, m.group(1)))
            stem = os.path.splitext(m.group(1))[0]
            if stem in vus:
                errs.append("%s : vignette %s déjà utilisée par %s — deux espèces qui "
                            "partagent un stem partagent aussi toutes leurs photos, donc "
                            "la même question de quiz" % (ou, m.group(1), vus[stem]))
            else:
                vus[stem] = ou
            row = {}
            for j, val in enumerate(cells):
                if j < len(header):
                    row[header[j]] = val
            if not row.get("name", "").strip():
                errs.append("%s : nom (2e colonne) vide" % ou)
            pb = verifier_latin(row.get("latin", ""))
            if pb:
                errs.append("%s : %s" % (ou, pb))
    return errs, warns, set(vus)

def verifier_photos_extra(stems):
    """Chaque photo de img/quiz-extra/ va à une espèce, et à une seule.

    Le rattachement suit la convention <stem>-<aspects>-<n>.jpg (cf. atlas_data.extra_photos) :
    une photo qui n'y répond pas n'apparaît nulle part dans le site, et une photo réclamée
    par deux stems serait attribuée à une espèce qui n'est pas la sienne.
    """
    errs, warns = [], []
    if not os.path.isdir(atlas_data.EXTRA):
        return errs, warns
    proprietaires = {}
    for stem in stems:
        for p in atlas_data.extra_photos(stem):
            proprietaires.setdefault(os.path.basename(p), []).append(stem)
    for name in sorted(os.listdir(atlas_data.EXTRA)):
        if name.startswith("_") or not name.lower().endswith(atlas_data.PHOTO_EXT):
            continue  # _aspects.tsv, _COMMENT-NOMMER.txt
        owners = proprietaires.get(name, [])
        if not owners:
            errs.append("img/quiz-extra/%s : ne correspond à aucune espèce — attendu "
                        "<stem>-<aspect>-<n>.jpg, où <stem> est le nom de la vignette" % name)
            continue
        if len(owners) > 1:
            errs.append("img/quiz-extra/%s : réclamée par %d espèces (%s) — renommer pour "
                        "lever l'ambiguïté" % (name, len(owners), ", ".join(sorted(owners))))
        # Mots du nom de fichier qui ne sont ni un aspect connu ni un numéro : l'aspect
        # voulu est alors perdu (la photo retombe en « divers »).
        stem = max(owners, key=len)
        suffixe = os.path.splitext(name.lower())[0][len(stem):]
        inconnus = [t for t in re.split(r"[-_ ]+", suffixe)
                    if t and not t.isdigit() and t not in atlas_data.ASPECT_KW]
        if inconnus and name not in atlas_data.SIDE:
            warns.append("img/quiz-extra/%s : mot-clé d'aspect non reconnu (%s) — aspects "
                         "possibles : %s" % (name, ", ".join(inconnus), ASPECTS_NOMMES))
    return errs, warns

def verifier_sidecar():
    """img/quiz-extra/_aspects.tsv : aspects connus, lignes qui visent un fichier existant."""
    errs, warns = [], []
    p = os.path.join(atlas_data.EXTRA, "_aspects.tsv")
    if not os.path.exists(p):
        return errs, warns
    for i, ln in enumerate(open(p, encoding="utf-8"), 1):
        ln = ln.rstrip("\n")
        if not ln or ln.startswith("#"):
            continue
        ou = "img/quiz-extra/_aspects.tsv:%d" % i
        if "\t" not in ln:
            warns.append("%s : ligne ignorée, tabulation manquante (« fichier⇥aspects »)" % ou)
            continue
        fn, asp = ln.split("\t", 1)
        fn = fn.strip()
        if fn.lower() in ("fichier", "file"):
            continue
        if not (os.path.exists(os.path.join(atlas_data.EXTRA, fn))
                or os.path.exists(os.path.join(atlas_data.IMG, fn))):
            errs.append("%s : « %s » n'existe ni dans img/quiz-extra ni dans img/especes" % (ou, fn))
        for a in re.split(r"[,;]", asp):
            a = a.strip()
            if a and a not in ASPECTS:
                errs.append("%s : aspect inconnu « %s » — attendu : %s"
                            % (ou, a, ASPECTS_NOMMES))
    return errs, warns

def verifier_vignettes(stems):
    """Une vignette de img/especes/ que personne n'utilise n'apparaît pas dans le site."""
    errs, warns = [], []
    if not os.path.isdir(atlas_data.IMG):
        return errs, warns
    for name in sorted(os.listdir(atlas_data.IMG)):
        if name.startswith("_") or not name.lower().endswith(atlas_data.PHOTO_EXT):
            continue
        if os.path.splitext(name)[0] not in stems:
            warns.append("img/especes/%s : vignette utilisée par aucune espèce — ajouter "
                         "l'espèce à un atlas, ou supprimer le fichier" % name)
    return errs, warns

def verifier_contributions(stems):
    """contributions/*.tsv : actions connues, fichiers et stems cibles existants."""
    errs, warns = [], []
    cdir = os.path.join(BASE, "contributions")
    if not os.path.isdir(cdir):
        return errs, warns
    for fp in sorted(glob.glob(os.path.join(cdir, "*.tsv"))):
        rel = os.path.relpath(fp, BASE)
        for i, ln in enumerate(open(fp, encoding="utf-8"), 1):
            ln = ln.rstrip("\n")
            if not ln or ln.startswith("#"):
                continue
            ou = "%s:%d" % (rel, i)
            if "\t" not in ln:
                warns.append("%s : ligne ignorée, tabulation manquante "
                             "(« action⇥fichier⇥valeur »)" % ou)
                continue
            parts = ln.split("\t")
            act = parts[0].strip().lower()
            if act in ("action", "type"):
                continue
            fn = parts[1].strip() if len(parts) > 1 else ""
            val = parts[2].strip() if len(parts) > 2 else ""
            if act not in ("tag", "reassign", "remove"):
                errs.append("%s : action inconnue « %s » — attendu : tag, reassign, remove"
                            % (ou, act))
                continue
            if not fn:
                errs.append("%s : action « %s » sans nom de fichier" % (ou, act))
                continue
            if not (os.path.exists(os.path.join(atlas_data.EXTRA, fn))
                    or os.path.exists(os.path.join(atlas_data.IMG, fn))):
                errs.append("%s : « %s » n'existe ni dans img/quiz-extra ni dans img/especes"
                            % (ou, fn))
            if act == "reassign":
                if not val:
                    errs.append("%s : reassign sans espèce cible" % ou)
                elif val not in stems:
                    errs.append("%s : reassign vers « %s », qui n'est le stem d'aucune espèce "
                                "— la photo disparaîtrait du site" % (ou, val))
            if act == "tag":
                if not val:
                    warns.append("%s : tag sans aspect — la photo restera « divers »" % ou)
                for a in re.split(r"[,;]", val):
                    a = a.strip()
                    if a and a not in ASPECTS:
                        errs.append("%s : aspect inconnu « %s » — attendu : %s"
                                    % (ou, a, ASPECTS_NOMMES))
    return errs, warns

def verifier_confusions(stems):
    """« Confusions - référence.md » : stems connus, et un critère qui tranche par groupe."""
    errs, warns = [], []
    rel = "Confusions - référence.md"
    p = os.path.join(BASE, rel)
    if not os.path.exists(p):
        warns.append("%s : fichier absent — le mode sosies n'a aucun groupe" % rel)
        return errs, warns
    for i, ln in enumerate(open(p, encoding="utf-8"), 1):
        if not ln.lstrip().startswith("|"):
            continue
        cells = atlas_data.cells_of(ln)
        if len(cells) < 3 or cells[1].strip().lower().startswith("esp"):
            continue
        if set(cells[0].strip()) <= set("-: "):
            continue
        ou = "%s:%d" % (rel, i)
        groupe = [x.strip() for x in re.split(r"[,;]", cells[1]) if x.strip()]
        if not groupe:
            errs.append("%s : groupe « %s » sans espèce" % (ou, cells[0].strip()))
        if not cells[2].strip():
            errs.append("%s : groupe « %s » sans « ce qui tranche » — il est ignoré par le "
                        "quiz" % (ou, cells[0].strip()))
        for x in groupe:
            if x not in stems:
                errs.append("%s : « %s » n'est le stem d'aucune espèce" % (ou, x))
        if len(groupe) == 1:
            warns.append("%s : groupe « %s » à une seule espèce — sans sosie, il n'apprend "
                         "rien" % (ou, cells[0].strip()))
    return errs, warns

def verifier_credits():
    """img/CREDITS.tsv : une ligne par image, et pas de ligne orpheline.

    Avertissement et non erreur tant que le rattrapage n'est pas fait : les images anciennes
    ont été récupérées sans noter l'auteur (cf. scripts/credits.py). À passer en erreur quand
    le compte d'inconnus tombe à zéro.
    """
    errs, warns = [], []
    connus, inconnus, manquants, morts = credits.rapport()
    if manquants:
        warns.append("img/CREDITS.tsv : %d image(s) sans crédit (%s%s) — lancer "
                     "« python3 scripts/credits.py --init »"
                     % (len(manquants), ", ".join(manquants[:3]),
                        ", …" if len(manquants) > 3 else ""))
    for f in morts:
        warns.append("img/CREDITS.tsv : ligne « %s » sans image correspondante" % f)
    if inconnus:
        warns.append("img/CREDITS.tsv : %d image(s) sur %d sans auteur ni licence connus — "
                     "les licences CC-BY exigent l'attribution"
                     % (len(inconnus), len(connus) + len(inconnus)))
    return errs, warns

def main():
    errs, warns, stems = verifier_tableaux()
    for controle in (verifier_photos_extra, verifier_vignettes,
                     verifier_contributions, verifier_confusions):
        e, w = controle(stems)
        errs += e; warns += w
    for controle in (verifier_sidecar, verifier_credits):
        e, w = controle()
        errs += e; warns += w

    if warns:
        print("⚠ %d avertissement(s) :" % len(warns))
        for x in warns:
            print("  -", x)
    if errs:
        print("❌ %d problème(s) détecté(s) :" % len(errs))
        for x in errs:
            print("  -", x)
        sys.exit(1)
    print("✅ Atlas valides. (%d espèces)" % len(stems))

if __name__ == "__main__":
    main()
