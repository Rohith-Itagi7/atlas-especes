#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Complète les atlas avec un 2e lot d'espèces manquantes (aromatiques, légumes, sauvages,
engrais verts, fruitiers ligneux) + télécharge les vignettes iNaturalist.
  python3 add_lot2.py rows    -> insère (ordre alpha) les fiches dans les 2 atlas
  python3 add_lot2.py fetch   -> télécharge img/especes/<stem>.jpg (iNat) pour les manquantes
"""
import sys, os, re, json, time, subprocess, urllib.request, urllib.parse, unicodedata

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(BASE, "img", "especes")
UA = "ForestryQuiz/1.0 (personal educational use)"
ATLAS_H = os.path.join(BASE, "Espèces herbacées - référence.md")
ATLAS_L = os.path.join(BASE, "Espèces - référence.md")

# HERBACÉES : stem, Plante, Latin, Famille, Cycle, Strate, Lum, Fix.N, Fonction, Comestible, Notes
HERB = [
("sauge","Sauge officinale","Salvia officinalis","Lamiacées","vivace (ss-arbriss.)","4","☀","non","com, att, méd","feuilles","mellifère ; tailler après floraison ; sol sec"),
("thym","Thym","Thymus vulgaris","Lamiacées","vivace (ss-arbriss.)","5","☀","non","com, att, cs","feuilles","sol sec drainé ; mellifère ; couvre-sol"),
("romarin","Romarin","Salvia rosmarinus","Lamiacées","vivace (arbriss.)","4","☀","non","com, att","feuilles","persistant ; mellifère précoce ; sec"),
("lavande","Lavande","Lavandula angustifolia","Lamiacées","vivace (ss-arbriss.)","4","☀","non","att, méd","(aromatique)","mellifère++ ; sol sec calcaire"),
("hysope","Hysope","Hyssopus officinalis","Lamiacées","vivace (ss-arbriss.)","4","☀","non","com, att, méd","feuilles, fleurs","mellifère ; sec"),
("marjolaine","Marjolaine","Origanum majorana","Lamiacées","vivace gélive","4","☀","non","com, att","feuilles","proche origan, plus douce"),
("fenouil","Fenouil","Foeniculum vulgare","Apiacées","vivace","4","☀","non","com, att","bulbe, feuilles, graines","ombellifère → auxiliaires ; se ressème"),
("camomille","Camomille (matricaire)","Matricaria chamomilla","Astéracées","annuel","4","☀","non","com (tisane), att, méd","fleurs","se ressème"),
("armoise","Armoise / Absinthe","Artemisia absinthium","Astéracées","vivace","4","☀","non","méd","(⚠ non comestible telle quelle)","amère ; répulsif insectes"),
("asperule","Aspérule odorante","Galium odoratum","Rubiacées","vivace","4","☾","non","cs, com","feuilles (aromatise)","couvre-sol de sous-bois"),
("verveine_citron","Verveine citronnelle","Aloysia citriodora","Verbénacées","vivace gélive (arbriss.)","4","☀","non","com, att","feuilles (tisane)","à rentrer l'hiver ; parfum citron"),
("poireau","Poireau","Allium porrum","Amaryllidacées","bisannuel","pot.","☀","non","com","fût, feuilles","(distinct du poireau perpétuel)"),
("ail","Ail","Allium sativum","Amaryllidacées","annuel (bulbe)","pot.","☀","non","com","bulbe","planté à l'automne ; anti-fongique"),
("echalote","Échalote","Allium cepa Aggregatum","Amaryllidacées","annuel (bulbe)","pot.","☀","non","com","bulbe","se plante, ne se sème pas"),
("courgette","Courgette","Cucurbita pepo","Cucurbitacées","annuel","pot.","☀","non","com","fruit, fleur","très productive ; gourmande"),
("mais","Maïs","Zea mays","Poacées","annuel","pot.","☀","non","com","grains","C4 ; « trois sœurs » ; gourmand en eau/N"),
("patate_douce","Patate douce","Ipomoea batatas","Convolvulacées","annuel gélif","6","☀","non","com","tubercules, feuilles","chaleur ; faux-ami de la pomme de terre"),
("cresson","Cresson de fontaine","Nasturtium officinale","Brassicacées","vivace","5","◐","non","com","feuilles","eau courante ; ⚠ douve (cuire si eau douteuse)"),
("stellaire","Stellaire (mouron blanc)","Stellaria media","Caryophyllacées","annuel","5","◐","non","com, cs","feuilles","couvre-sol comestible d'hiver ; indicatrice sol riche"),
("bardane","Bardane","Arctium lappa","Astéracées","bisannuel","4","☀","non","com, acc, méd","racine","racine comestible ; pivot = accumulateur"),
("paquerette","Pâquerette","Bellis perennis","Astéracées","vivace","5","☀","non","com, att","fleurs, feuilles","pelouse ; se ressème"),
("cardamine","Cardamine des prés","Cardamine pratensis","Brassicacées","vivace","4","◐","non","com","feuilles, fleurs","prairies humides ; goût cresson"),
("onagre","Onagre","Oenothera biennis","Onagracées","bisannuel","4","☀","non","com, att","racine, fleurs","sols pauvres ; mellifère nocturne"),
("millepertuis","Millepertuis","Hypericum perforatum","Hypéricacées","vivace","4","☀","non","méd, att","(⚠ photosensibilisant)","médicinal ; sol pauvre"),
("guimauve","Guimauve","Althaea officinalis","Malvacées","vivace","4","☀","non","com, méd","racine, feuilles, fleurs","zones humides ; mucilage"),
("valeriane","Valériane officinale","Valeriana officinalis","Caprifoliacées","vivace","4","☀◐","non","méd, att","racine","médicinal (sommeil) ; mellifère"),
("sarrasin","Sarrasin (blé noir)","Fagopyrum esculentum","Polygonacées","annuel","4","☀","non","com, EV, att","graines","engrais vert rapide, étouffe les adventices ; mellifère"),
("moutarde","Moutarde blanche","Sinapis alba","Brassicacées","annuel","4","☀","non","EV, com","graines, feuilles","engrais vert rapide ; ⚠ pas avant des crucifères (rotation)"),
("seigle","Seigle","Secale cereale","Poacées","annuel","4","☀","non","EV, com","grains","engrais vert d'hiver (avec vesce) ; structure le sol"),
("avoine","Avoine","Avena sativa","Poacées","annuel","4","☀","non","EV, com","grains","engrais vert ; gèle l'hiver (mulch)"),
("sainfoin","Sainfoin","Onobrychis viciifolia","Fabacées","vivace","4","☀","Rhizobium","fix, att, EV","(fourrage)","fixateur ; mellifère ; sol calcaire sec"),
("lotier","Lotier corniculé","Lotus corniculatus","Fabacées","vivace","5","☀","Rhizobium","fix, att, cs","(fourrage)","fixateur bas ; prairie"),
("melilot","Mélilot","Melilotus officinalis","Fabacées","bisannuel","4","☀","Rhizobium","fix, att","(fourrage)","fixateur ; mellifère++ ; sol pauvre"),
]

# LIGNEUX : stem, Espèce, Latin, Type, Famille, Fix.N, Mycorhize, Lum, Succ, Comestible, Notes
LIGN = [
("laurier_sauce","Laurier-sauce","Laurus nobilis","arbre/arbuste","Lauracées","non","AM","☀◐","post","feuilles (condiment)","persistant ; ⚠ ne pas confondre avec le laurier-rose (toxique)"),
("olivier","Olivier","Olea europaea","arbre","Oléacées","non","AM","☀","post","fruits (olives, à traiter)","méditerranéen ; sec ; longévif"),
("figuier","Figuier","Ficus carica","arbre/arbuste","Moracées","non","AM","☀","pion","figues","chaleur ; drageonne ; sec"),
("neflier","Néflier commun","Mespilus germanica","arbuste","Rosacées","non","AM","☀◐","post","nèfles (blettes)","fruit consommé blet, après gelées"),
("plaqueminier","Plaqueminier (kaki)","Diospyros kaki","arbre","Ébénacées","non","AM","☀","post","kakis","fruit d'automne ; rustique"),
("pecher","Pêcher","Prunus persica","arbre","Rosacées","non","AM","☀","pion","pêches","chaleur ; cloque ; vie courte"),
("abricotier","Abricotier","Prunus armeniaca","arbre","Rosacées","non","AM","☀","post","abricots","gel des fleurs = risque ; sec"),
("cerisier","Cerisier","Prunus avium (cultivé)","arbre","Rosacées","non","AM","☀","post","cerises","forme cultivée du merisier"),
("vigne","Vigne","Vitis vinifera","liane","Vitacées","non","AM","☀","post","raisin","liane ligneuse ; palissage ; sec"),
("feijoa","Feijoa (goyavier du Brésil)","Acca sellowiana","arbuste","Myrtacées","non","AM","☀","post","fruits + fleurs comestibles","persistant ; semi-rustique"),
("grenadier","Grenadier","Punica granatum","arbuste","Lythracées","non","AM","☀","post","grenades","méditerranéen ; sec ; ornemental"),
("jujubier","Jujubier","Ziziphus jujuba","arbre/arbuste","Rhamnacées","non","AM","☀","post","jujubes","très sec/chaud ; épineux ; rustique"),
("chevrefeuille_com","Chèvrefeuille comestible (camérisier)","Lonicera caerulea","arbuste","Caprifoliacées","non","AM","☀◐","post","baies (camerises)","très rustique ; fructifie tôt au printemps"),
("goji","Goji (lyciet)","Lycium barbarum","arbuste","Solanacées","non","AM","☀","pion","baies","rustique ; drageonne ; sol pauvre OK"),
]


def norm(s):
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")

def gsearch(latin):
    q = urllib.parse.quote_plus(re.sub(r"\s*\(.*?\)", "", latin).strip())
    return "[🔍](https://www.google.com/search?tbm=isch&q=%s)" % q

def row_herb(s):
    stem, plante, latin, fam, cycle, strate, lum, fixn, fonc, com, notes = s
    cells = ["![[%s.jpg\\|200]]" % stem, plante, latin, fam, cycle, strate, lum, fixn, fonc, com, notes, gsearch(latin)]
    return "| " + " | ".join(cells) + " |"

def row_lign(s):
    stem, esp, latin, typ, fam, fixn, myco, lum, succ, com, notes = s
    cells = ["![[%s.jpg\\|200]]" % stem, esp, latin, typ, fam, fixn, myco, lum, succ, com, notes, gsearch(latin)]
    return "| " + " | ".join(cells) + " |"

def name_of(line):
    parts = [c.strip().replace("\x01", "|") for c in line.replace("\\|", "\x01").split("|")][1:-1]
    return parts[1] if len(parts) > 1 else ""

def insert_rows(atlas_path, new_rows):
    lines = open(atlas_path, encoding="utf-8").read().split("\n")
    body_idx = [i for i, ln in enumerate(lines) if ln.lstrip().startswith("| ![[")]
    if not body_idx:
        print("  ⚠ pas de table trouvée dans", atlas_path); return 0
    existing = {norm(name_of(lines[i])) for i in body_idx}
    added = 0
    for nr in new_rows:
        nm = norm(name_of(nr))
        if nm in existing:
            print("  = déjà présent :", name_of(nr)); continue
        # position alpha parmi les lignes du corps (recalculé à chaque insertion)
        body_idx = [i for i, ln in enumerate(lines) if ln.lstrip().startswith("| ![[")]
        pos = None
        for i in body_idx:
            if nm < norm(name_of(lines[i])):
                pos = i; break
        if pos is None:
            pos = body_idx[-1] + 1
        lines.insert(pos, nr)
        existing.add(nm); added += 1
        print("  + inséré :", name_of(nr))
    open(atlas_path, "w", encoding="utf-8").write("\n".join(lines))
    return added

def fetch(all_specs):
    ok = skip = err = 0
    for i, s in enumerate(all_specs):
        stem, name, latin = s[0], s[1], s[2]
        dest = os.path.join(IMG, stem + ".jpg")
        if os.path.exists(dest):
            skip += 1; continue
        try:
            api = "https://api.inaturalist.org/v1/taxa?q=%s&per_page=1" % urllib.parse.quote(re.sub(r"\s*\(.*?\)", "", latin).strip())
            req = urllib.request.Request(api, headers={"User-Agent": UA})
            d = json.load(urllib.request.urlopen(req, timeout=30))
            res = d.get("results", [])
            src = None
            if res and res[0].get("default_photo"):
                src = res[0]["default_photo"].get("medium_url") or res[0]["default_photo"].get("url")
            if not src:
                print("  ∅ pas de photo :", name); err += 1; time.sleep(1.2); continue
            buf = urllib.request.urlopen(urllib.request.Request(src, headers={"User-Agent": UA}), timeout=30).read()
            open(dest + ".o", "wb").write(buf)
            subprocess.run(["sips", "-Z", "500", "-s", "format", "jpeg", "-s", "formatOptions", "80", dest + ".o", "--out", dest],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            os.remove(dest + ".o"); ok += 1
            print("  ✓ %s" % name)
        except Exception as e:
            print("  ✗ %s : %s" % (name, e)); err += 1
        time.sleep(1.2)
    print("=== fetch : %d OK / %d déjà / %d échec ===" % (ok, skip, err))

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "rows"
    if mode == "rows":
        a = insert_rows(ATLAS_H, [row_herb(s) for s in HERB])
        b = insert_rows(ATLAS_L, [row_lign(s) for s in LIGN])
        print("=== inséré : %d herbacées + %d ligneux ===" % (a, b))
    elif mode == "fetch":
        fetch(HERB + LIGN)
