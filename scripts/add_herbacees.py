#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ajoute un lot d'espèces HERBACÉES à l'atlas + télécharge leurs vignettes.
  python3 add_herbacees.py rows    -> insère (fusion triée) les fiches dans « Espèces herbacées - référence.md »
  python3 add_herbacees.py fetch   -> télécharge img/especes/<stem>.jpg (iNaturalist) pour les manquantes
"""
import sys, os, re, json, time, subprocess, urllib.request, urllib.parse, unicodedata

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(BASE, "img", "especes")
ATLAS = os.path.join(BASE, "Espèces herbacées - référence.md")
UA = "ForestryQuiz/1.0 (personal educational use)"

# stem, Plante, Latin, Famille, Cycle, Strate, Lum, Fix.N, Fonction, Comestible, Notes
SP = [
("persil","Persil","Petroselinum crispum","Apiacées","bisannuel","4","☀◐","non","com, att","feuilles","ombellifère → auxiliaires"),
("basilic","Basilic","Ocimum basilicum","Lamiacées","annuel","4","☀","non","com, att","feuilles","gélif, aime la chaleur ; éloigne pucerons"),
("aneth","Aneth","Anethum graveolens","Apiacées","annuel","4","☀","non","com, att","feuilles, graines","ombellifère"),
("coriandre","Coriandre","Coriandrum sativum","Apiacées","annuel","4","☀","non","com, att","feuilles, graines","monte vite à la chaleur"),
("cerfeuil","Cerfeuil","Anthriscus cerefolium","Apiacées","annuel","4","◐","non","com","feuilles","mi-ombre ; ⚠ ne pas confondre avec la ciguë"),
("estragon","Estragon","Artemisia dracunculus","Astéracées","vivace","4","☀","non","com","feuilles","aromate ; peu de graines viables"),
("melisse","Mélisse","Melissa officinalis","Lamiacées","vivace","4","☀◐","non","com, att","feuilles (tisane)","mellifère, se ressème"),
("sarriette","Sarriette","Satureja hortensis","Lamiacées","annuel","4","☀","non","com","feuilles","aromate des légumineuses"),
("epinard","Épinard","Spinacia oleracea","Amaranthacées","annuel","pot.","☀◐","non","com","feuilles","non mycorhizable ; monte à la chaleur"),
("blette","Blette (poirée)","Beta vulgaris","Amaranthacées","bisannuel","pot.","☀","non","com","feuilles, côtes","non mycorhizable"),
("mache","Mâche","Valerianella locusta","Caprifoliacées","annuel","5","☀◐","non","com, cs","feuilles","rosette d'hiver, se ressème"),
("roquette","Roquette","Eruca sativa","Brassicacées","annuel","4","☀◐","non","com","feuilles","non mycorhizable ; monte vite"),
("radis","Radis","Raphanus sativus","Brassicacées","annuel","pot.","☀","non","com","racine, fanes","rapide ; non mycorhizable"),
("navet","Navet","Brassica rapa","Brassicacées","bisannuel","pot.","☀","non","com","racine, fanes","non mycorhizable"),
("panais","Panais","Pastinaca sativa","Apiacées","bisannuel","pot.","☀◐","non","com","racine","rustique, se conserve en terre"),
("celeri","Céleri","Apium graveolens","Apiacées","bisannuel","pot.","☀","non","com","côtes, racine, feuilles","gourmand en eau"),
("chicoree","Chicorée / Endive","Cichorium intybus","Astéracées","vivace","4","☀","non","com","feuilles, racine","amère ; racine torréfiée = « café »"),
("concombre","Concombre / Cornichon","Cucumis sativus","Cucurbitacées","annuel","pot.","☀","non","com","fruit","aime chaleur + eau"),
("aubergine","Aubergine","Solanum melongena","Solanacées","annuel","pot.","☀","non","com","fruit","Solanacée (rotation, mildiou) ; chaleur"),
("poivron","Poivron / Piment","Capsicum annuum","Solanacées","annuel","pot.","☀","non","com","fruit","Solanacée ; chaleur"),
("asperge","Asperge","Asparagus officinalis","Asparagacées","vivace","4","☀","non","com","turions (jeunes pousses)","plantation longue durée (griffes)"),
("crosne","Crosne du Japon","Stachys affinis","Lamiacées","vivace","6","☀◐","non","com","tubercules","petit tubercule nacré"),
("plantain","Plantain","Plantago lanceolata","Plantaginacées","vivace","4","☀","non","com, méd","jeunes feuilles","sauvage ; médicinal (piqûres)"),
("pourpier","Pourpier","Portulaca oleracea","Portulacacées","annuel","5","☀","non","com, cs","feuilles charnues","riche en oméga-3 ; couvre-sol, se ressème"),
("mauve","Mauve","Malva sylvestris","Malvacées","bisannuel","4","☀◐","non","com, att","feuilles, fleurs","mucilage ; mellifère"),
("chenopode","Chénopode blanc","Chenopodium album","Amaranthacées","annuel","pot.","☀","non","com","feuilles (cuites)","« épinard sauvage » ; non mycorhizable"),
("amarante","Amarante","Amaranthus retroflexus","Amaranthacées","annuel","pot.","☀","non","com","feuilles, graines","pseudo-céréale ; non mycorhizable"),
("egopode","Égopode (herbe aux goutteux)","Aegopodium podagraria","Apiacées","vivace","5","◐☾","non","com","jeunes feuilles","⚠ très envahissant (traçant) ; d'ombre"),
("lamier","Lamier blanc","Lamium album","Lamiacées","vivace","4","◐","non","com, att","jeunes pousses, fleurs","« ortie blanche » non urticante ; mellifère"),
("berce","Berce commune","Heracleum sphondylium","Apiacées","bisannuel","4","☀◐","non","com","jeunes pousses","⚠ NE PAS confondre avec la berce du Caucase (brûlures)"),
("alliaire","Alliaire","Alliaria petiolata","Brassicacées","bisannuel","4","◐","non","com","feuilles (goût d'ail)","sous-bois ; non mycorhizable"),
("primevere","Primevère","Primula veris","Primulacées","vivace","5","◐","non","com, att","fleurs, feuilles","prairie ; floraison précoce mellifère"),
("violette","Violette odorante","Viola odorata","Violacées","vivace","5","◐☾","non","com, att","fleurs, feuilles","couvre-sol d'ombre"),
("souci","Souci (calendula)","Calendula officinalis","Astéracées","annuel","4","☀","non","att, com","pétales","auxiliaires ; se ressème"),
("digitale","Digitale pourpre","Digitalis purpurea","Plantaginacées","bisannuel","◐","◐","non","☠ TOXIQUE","☠ MORTELLE (cardiotoxique)","NE JAMAIS consommer ; bio-indic. sol acide"),
("arum","Arum tacheté (gouet)","Arum maculatum","Aracées","vivace","5","☾","non","☠ TOXIQUE","☠ toxique (oxalates)","sous-bois ; baies rouges attirantes"),
("colchique","Colchique","Colchicum autumnale","Colchicacées","vivace","4","☀","non","☠ TOXIQUE","☠ MORTELLE (colchicine)","« safran des prés » ; ⚠ confusion mortelle"),
("cigue","Grande ciguë","Conium maculatum","Apiacées","bisannuel","4","☀◐","non","☠ TOXIQUE","☠ MORTELLE","tige tachée de pourpre, odeur fétide ; ⚠ confusion ombellifères"),
("muguet","Muguet","Convallaria majalis","Asparagacées","vivace","5","☾","non","☠ TOXIQUE","☠ toxique (cardiotoxique)","sous-bois ; ⚠ confusion avec l'ail des ours !"),
]

def stg(latin):
    return "https://www.google.com/search?tbm=isch&q=" + latin.replace(" ", "+")

def row(s):
    stem, name, latin, fam, cyc, strate, lum, fixn, fonc, com, notes = s
    return "| ![[%s.jpg\\|200]] | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | [🔍](%s) |" % (
        stem, name, latin, fam, cyc, strate, lum, fixn, fonc, com, notes, stg(latin))

def keyname(n):
    n = "".join(c for c in unicodedata.normalize("NFD", n) if unicodedata.category(c) != "Mn")
    return n.lower()

def do_rows():
    lines = open(ATLAS, encoding="utf-8").read().split("\n")
    idx = [i for i, l in enumerate(lines) if l.lstrip().startswith("| ![[")]
    first, last = idx[0], idx[-1]
    existing = lines[first:last + 1]
    def rowname(r):
        c = [x.strip() for x in r.replace("\\|", "\x01").split("|")]
        return c[2].replace("\x01", "|") if len(c) > 2 else ""
    have = {keyname(rowname(r)) for r in existing}
    added = 0
    allrows = list(existing)
    for s in SP:
        if keyname(s[1]) in have:
            continue
        allrows.append(row(s)); added += 1
    allrows.sort(key=rowname_key)
    lines = lines[:first] + allrows + lines[last + 1:]
    open(ATLAS, "w", encoding="utf-8").write("\n".join(lines))
    print("Fiches ajoutées :", added, "/ total table :", len(allrows))

def rowname_key(r):
    c = [x.strip() for x in r.replace("\\|", "\x01").split("|")]
    return keyname(c[2].replace("\x01", "|")) if len(c) > 2 else ""

def do_fetch():
    ok = 0
    for i, s in enumerate(SP):
        stem, latin = s[0], s[2]
        dest = os.path.join(IMG, stem + ".jpg")
        if os.path.exists(dest):
            print("[%d/%d] %s : déjà" % (i + 1, len(SP), stem)); continue
        try:
            q = urllib.parse.quote(latin)
            api = "https://api.inaturalist.org/v1/taxa?q=%s&per_page=1" % q
            req = urllib.request.Request(api, headers={"User-Agent": UA})
            d = json.load(urllib.request.urlopen(req, timeout=30))
            res = d.get("results", [])
            src = None
            if res and res[0].get("default_photo"):
                src = res[0]["default_photo"].get("medium_url") or res[0]["default_photo"].get("url")
            if not src:
                print("[%d/%d] %s : ∅" % (i + 1, len(SP), stem)); time.sleep(1.3); continue
            req2 = urllib.request.Request(src, headers={"User-Agent": UA})
            buf = urllib.request.urlopen(req2, timeout=30).read()
            open(dest + ".o", "wb").write(buf)
            subprocess.run(["sips", "-Z", "500", "-s", "format", "jpeg", "-s", "formatOptions", "80",
                            dest + ".o", "--out", dest], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            os.remove(dest + ".o"); ok += 1
            print("[%d/%d] %s : OK" % (i + 1, len(SP), stem))
        except Exception as e:
            print("[%d/%d] %s : err %s" % (i + 1, len(SP), stem, e))
        time.sleep(1.3)
    print("=== vignettes téléchargées :", ok, "===")

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "rows"
    (do_fetch if mode == "fetch" else do_rows)()
