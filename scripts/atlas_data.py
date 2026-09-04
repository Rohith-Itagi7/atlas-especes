#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Couche de données des atlas : lecture des fiches Markdown, des photos et des contributions.

Source unique pour tous les scripts du dépôt (build du site, vérification, couverture,
générateur local). Ne produit aucun HTML : voir scripts/build_web.py pour le site et
scripts/generer_quiz.py pour les versions locales autonome / Artifact.

Aspects des photos : nom de fichier <stem>-<aspect>-<n>.jpg (+ sidecar
img/quiz-extra/_aspects.tsv « fichier<TAB>aspect1,aspect2 » qui OVERRIDE, non destructif,
pour tagger les vignettes).
"""
import glob, os, re, unicodedata

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(BASE, "img", "especes")
EXTRA = os.path.join(BASE, "img", "quiz-extra")

ATLASES = [("Espèces - référence.md", "ligneux"), ("Espèces herbacées - référence.md", "herbace"),
           ("Champignons - référence.md", "champignon"), ("Faune - référence.md", "faune"),
           ("Espèces diverses - référence.md", "divers")]
IMG_RE = re.compile(r"!\[\[(?:[^\]\|]*/)?([^\]\|]+\.(?:jpg|jpeg|png))", re.I)
ASPECT_KW = {"feuille": "feuille", "feuilles": "feuille", "ecorce": "ecorce", "fruit": "fruit",
             "fruits": "fruit", "fleur": "fleur", "fleurs": "fleur", "rameau": "rameau",
             "rameaux": "rameau", "bourgeon": "rameau", "hiver": "rameau", "port": "port", "silhouette": "port"}

def load_corrections():
    """Actions de contribution (depuis l'app ou à la main) : img/quiz-extra/_corrections.tsv
    + contributions/*.tsv. Format : action<TAB>fichier<TAB>valeur, action ∈ tag|reassign|remove.
      tag      fichier  feuille,fleur   → force les aspects d'une photo
      reassign fichier  stem_correct    → la photo appartient à cette autre espèce
      remove   fichier                  → retire la photo (mauvaise attribution)"""
    tags, reassign, remove = {}, {}, set()
    files = []
    fp0 = os.path.join(EXTRA, "_corrections.tsv")
    if os.path.exists(fp0):
        files.append(fp0)
    cdir = os.path.join(BASE, "contributions")
    if os.path.isdir(cdir):
        files += sorted(glob.glob(os.path.join(cdir, "*.tsv")))
    for fp in files:
        for line in open(fp, encoding="utf-8"):
            line = line.rstrip("\n")
            if not line or line.startswith("#") or "\t" not in line:
                continue
            parts = line.split("\t")
            act = parts[0].strip().lower()
            if act in ("action", "type"):  # en-tête
                continue
            fn = parts[1].strip() if len(parts) > 1 else ""
            val = parts[2].strip() if len(parts) > 2 else ""
            if not fn:
                continue
            if act == "tag":
                tags[fn] = [a.strip() for a in re.split(r"[,;]", val) if a.strip()]
            elif act == "reassign" and val:
                reassign[fn] = val; remove.discard(fn)
            elif act == "remove":
                remove.add(fn)
    return tags, reassign, remove
CORR = load_corrections()

def load_sidecar():
    """Aspects : img/quiz-extra/_aspects.tsv (fichier<TAB>aspects) + tags des contributions."""
    d = {}
    p = os.path.join(EXTRA, "_aspects.tsv")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            line = line.rstrip("\n")
            if not line or line.startswith("#") or "\t" not in line:
                continue
            fn, asp = line.split("\t", 1)
            if fn.strip().lower() in ("fichier", "file"):  # ligne d'en-tête
                continue
            d[fn.strip()] = [a.strip() for a in re.split(r"[,;]", asp) if a.strip()]
    d.update(CORR[0])  # les tags de contribution écrasent
    return d
SIDE = load_sidecar()

def apply_corrections(species):
    """Applique reassign/remove : retire les photos signalées, déplace les reclassées."""
    _tags, reassign, remove = CORR
    if reassign or remove:
        by_stem = {}
        for s in species:
            by_stem.setdefault(s["stem"], s)
        moved = {}
        for s in species:
            keep = []
            for p in s["paths"]:
                b = os.path.basename(p)
                if b in remove:
                    continue
                if b in reassign:
                    moved.setdefault(reassign[b], []).append(p)
                    continue
                keep.append(p)
            s["paths"] = keep
        for tgt, ps in moved.items():
            if tgt in by_stem:
                for p in ps:
                    if p not in by_stem[tgt]["paths"]:
                        by_stem[tgt]["paths"].append(p)
    kept = []
    for s in species:
        if s["paths"]:
            kept.append(s)
        else:
            print("  ⚠ espèce sans photo après corrections, retirée du quiz :", s["name"])
    return kept

def cells_of(line):
    return [c.strip().replace("\x01", "|") for c in line.replace("\\|", "\x01").split("|")][1:-1]

def hkey(h):
    h = "".join(c for c in unicodedata.normalize("NFD", h.strip().lower()) if unicodedata.category(c) != "Mn").replace(".", "")
    for pre, k in [("photo", "photo"), ("esp", "name"), ("plante", "name"), ("champignon", "name"),
                   ("animal", "name"), ("groupe", "groupe"), ("type", "type"), ("fam", "famille"), ("fix", "fixn"),
                   ("mycor", "mycorhize"), ("lum", "lumiere"), ("succ", "succession"), ("cycle", "cycle"),
                   ("strate", "strate"), ("fonction", "fonction"), ("comest", "comestible"),
                   ("ecolog", "ecologie"), ("arbre", "hote"), ("substrat", "hote"), ("hote", "hote"),
                   ("saison", "saison"), ("habitat", "habitat"), ("role", "role"), ("regime", "regime"),
                   ("repart", "repartition"), ("note", "notes")]:
        if h.startswith(pre):
            return k
    if "latin" in h:
        return "latin"
    return h

def aspect_of(path, stem):
    base = os.path.basename(path)
    if base in SIDE:
        return SIDE[base] or ["divers"]
    fn = os.path.splitext(base.lower())[0]
    suffix = fn[len(stem):] if fn.startswith(stem) else fn
    found = []
    for tok in re.split(r"[-_ ]+", suffix):
        if tok in ASPECT_KW and ASPECT_KW[tok] not in found:
            found.append(ASPECT_KW[tok])
    return found or ["divers"]

PHOTO_EXT = (".jpg", ".jpeg", ".png")

def extra_photos(stem):
    """Photos supplémentaires d'une espèce dans img/quiz-extra/.

    La convention est <stem>-<aspects>-<n>.jpg : le **séparateur est exigé**, sinon un stem
    happe les photos de celui qu'il préfixe (« ail » prenait celles de l'ail des ours et de
    l'ail rocambole, « chou » celles du chou de Daubenton, « poireau » celles du perpétuel).
    Le stem nu (<stem>.jpg) est accepté : c'est une photo de l'espèce, sans aspect annoncé.
    """
    if not os.path.isdir(EXTRA):
        return []
    out = []
    for name in sorted(os.listdir(EXTRA)):
        if not name.startswith(stem) or not name.lower().endswith(PHOTO_EXT):
            continue
        rest = name[len(stem):]
        if not (rest.startswith("-") or rest.startswith(".")):
            continue  # « _des_ours-1.jpg » : appartient à une autre espèce
        p = os.path.join(EXTRA, name)
        if os.path.isfile(p):
            out.append(p)
    return out

def parse_atlas(path, cat, seen):
    lines = open(os.path.join(BASE, path), encoding="utf-8").read().split("\n")
    header = None
    for ln in lines:
        s = ln.lstrip()
        if s.startswith("|") and not s.startswith("| ![") and "latin" in ln.lower():
            header = [hkey(c) for c in cells_of(ln)]
            break
    out = []
    for ln in lines:
        if not ln.lstrip().startswith("| !["):
            continue
        m = IMG_RE.search(ln)
        if not m:
            continue
        cells = cells_of(ln)
        row = {}
        for i, val in enumerate(cells):
            k = header[i] if (header and i < len(header)) else None
            if k and k not in ("photo", "search", "🔍"):
                row[k] = val
        name = row.get("name", "")
        if not name:
            continue
        stem = os.path.splitext(m.group(1))[0]
        vpath = os.path.join(IMG, m.group(1))
        if not os.path.exists(vpath):
            print("  ⚠ vignette absente :", name, m.group(1)); continue
        paths = [vpath] + extra_photos(stem)
        fields = {k: v for k, v in row.items() if k not in ("name", "latin") and v and v not in ("—", "-", "")}
        sid = stem if stem not in seen else stem + "_" + cat
        seen.add(sid)
        out.append({"id": sid, "stem": stem, "name": name, "latin": row.get("latin", ""),
                    "note": row.get("notes", ""), "cat": cat, "fields": fields, "paths": paths})
    return out

def load_confusions():
    """Groupes de sosies depuis « Confusions - référence.md » : | Groupe | Espèces (stems) | Ce qui tranche |"""
    p = os.path.join(BASE, "Confusions - référence.md")
    groups = []
    if not os.path.exists(p):
        return groups
    for ln in open(p, encoding="utf-8"):
        if not ln.lstrip().startswith("|"):
            continue
        cells = cells_of(ln)
        if len(cells) < 3:
            continue
        if cells[1].strip().lower().startswith("esp"):  # en-tête
            continue
        if set(cells[0].strip()) <= set("-: "):  # séparateur
            continue
        stems = [x.strip() for x in re.split(r"[,;]", cells[1]) if x.strip()]
        tip = cells[2].strip()
        if stems and tip:
            groups.append({"stems": stems, "tip": tip})
    return groups
CONF = load_confusions()

# Verdict oui/non dérivé de la colonne « Comestible » des atlas. La règle vivait dans le JS du
# site ; elle est ici pour être testable, et le site consomme le champ « edible » produit au build.
_ED_LEAD = re.compile(r"^[☠⚠*\s]+")          # décorations de tête : ☠ ⚠ ** espaces
_ED_NO_HEAD = re.compile(r"^(non|toxique|mortel|immangeable)")
_ED_NO_ANY = re.compile(r"toxique|mortel|☠|immangeable")
_ED_NOT_FOOD = re.compile(r"^(fourrage|gazon|vannerie)")
_PARENS = re.compile(r"\([^)]*\)")   # note entre parenthèses, dans un nom ou un verdict

def is_edible(value):
    """La partie nommée est-elle comestible ?

    Le verdict de tête décide : « ☠ TOXIQUE (seul l'arille rouge…) » (if) → non.
    Un poison mis en garde entre parenthèses n'invalide pas un verdict positif :
    « Bon (⚠ crue TOXIQUE) » (morille) → oui, alors que « baies TOXIQUES » → non,
    parce que le poison y qualifie la partie nommée.
    Une valeur entièrement entre parenthèses est une note, pas un verdict : « (médicinal) » → non.
    """
    v = (value or "").strip()
    if not v:
        return False
    vl = v.lower()
    head = _ED_LEAD.sub("", vl)
    if _ED_NO_HEAD.match(head):
        return False
    if head.startswith("("):
        return False
    if _ED_NO_ANY.search(_PARENS.sub(" ", vl)):
        return False
    if _ED_NOT_FOOD.match(head):
        return False
    return True

def answer_variants(name, latin=""):
    """Orthographes acceptées comme réponse de quiz pour une espèce.

    Le nom canonique d'abord, puis ce qu'un apprenant tape légitimement — sans quoi le mode
    « saisie » compte faux une bonne réponse :
      « Chalef / Olivier de Bohême »            → « Chalef », « Olivier de Bohême »
      « Caragana (arbre à pois) »               → « Caragana », « arbre à pois »
      « Chèvrefeuille comestible (camérisier) » → …, « camérisier »
      latin « Allium ursinum »                  → « Allium ursinum », « ursinum »
    Dans les atlas, tout ce qui est entre parenthèses dans un nom d'espèce est un **autre
    nom commun** (gouet, poirée, lombric, faux-acacia…), donc une réponse valable.

    Les variantes sortent telles quelles : c'est le site qui les normalise (casse, accents,
    ponctuation) avec la même fonction que la saisie de l'utilisateur, pour n'avoir qu'une
    seule implémentation de la normalisation.
    """
    out = []

    def add(x):
        x = re.sub(r"\s+", " ", (x or "").strip()).strip(" -–—")
        if x and x not in out:
            out.append(x)

    add(name)
    for part in re.split(r"\s*/\s*", name or ""):
        add(part)
        add(_PARENS.sub(" ", part))                  # le nom sans sa parenthèse
        for note in re.findall(r"\(([^)]*)\)", part):
            add(note)                                # et le nom qui était dans la parenthèse
    for part in re.split(r"\s*/\s*", _PARENS.sub(" ", latin or "")):
        add(part)
        mots = part.split()
        if len(mots) >= 2:
            epithete = mots[1].lstrip("×x")          # « Allium ursinum » → « ursinum »
            if len(epithete) >= 4 and not epithete.endswith("."):
                add(epithete)
    return out
