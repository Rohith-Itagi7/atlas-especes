#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Insère (une seule fois) une colonne « Répartition » (info « où on la trouve »)
dans chaque atlas, juste avant la colonne 🔍. Idempotent."""
import os, re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ATLASES = ["Espèces - référence.md", "Espèces herbacées - référence.md",
           "Champignons - référence.md", "Faune - référence.md", "Espèces diverses - référence.md"]
IMG_RE = re.compile(r"!\[\[(?:[^\]\|]*/)?([^\]\|]+)\.(?:jpg|jpeg|png)", re.I)

REP = {
# --- ligneux ---
"abricotier":"origine Asie centrale ; cultivé en zones tempérées chaudes","ajonc":"façade atlantique de l'Europe de l'Ouest",
"alisier":"Europe, bois surtout calcaires","amandier":"origine Asie ; cultivé en région méditerranéenne",
"amelanchier":"montagnes d'Europe ; espèces nord-américaines cultivées","arbousier":"pourtour méditerranéen et façade atlantique",
"arbre_de_judee":"méditerranée orientale ; planté en Europe du Sud","argousier":"Eurasie ; littoraux et montagnes",
"aronia":"origine Amérique du Nord ; cultivé en Europe","aubepine":"Europe, Afrique du Nord, Asie occidentale ; très commune",
"aulne_glutineux":"Europe et Asie occidentale ; bords d'eau","bouleau":"Europe et Asie tempérée à boréale",
"buis":"Europe de l'Ouest et du Sud, sur calcaire","callune":"Europe ; landes acides ; très commune",
"caragana":"origine Sibérie/Mongolie ; planté","groseillier":"Europe tempérée ; cultivé",
"cerisier":"origine Europe/Asie occidentale ; cultivé en zone tempérée","chalef":"origine Asie ; planté (haies, littoral)",
"charme":"Europe tempérée ; commun dans les bois","chataignier":"Europe du Sud ; largement planté (sols acides)",
"chene_liege":"ouest méditerranéen, sols siliceux","chene_pedoncule":"Europe jusqu'en Russie ; très commun",
"chene_pubescent":"sud de l'Europe et régions tempérées chaudes","chene_sessile":"Europe tempérée ; commun",
"chene_vert":"pourtour méditerranéen","chevrefeuille_com":"Sibérie/Asie du NE ; cultivé (camerise)",
"cognassier":"origine Caucase/Asie ; cultivé en zone tempérée","cormier":"Europe du Sud et centrale",
"cornouiller_male":"Europe centrale et méridionale","epicea":"montagnes d'Europe ; planté en plaine",
"erable_champetre":"Europe, Afrique du Nord, Asie occidentale","erable_sycomore":"montagnes d'Europe ; planté largement",
"feijoa":"origine Amérique du Sud ; cultivé en climat doux","fevier":"origine Amérique du Nord ; planté",
"figuier":"pourtour méditerranéen ; cultivé en climat doux","framboisier":"Europe et Asie tempérée ; montagnes",
"frene":"Europe ; très commun","genet":"Europe de l'Ouest, sols acides","genevrier":"hémisphère nord tempéré ; très large",
"goji":"origine Chine ; cultivé","grenadier":"origine Asie du SO ; cultivé en région méditerranéenne",
"hetre":"Europe ; forêts fraîches","houx":"Europe de l'Ouest et du Sud","if":"Europe, Afrique du Nord, Asie occidentale",
"jujubier":"origine Asie ; cultivé en méditerranée","kiwai":"origine Asie de l'Est ; cultivé",
"laurier_sauce":"pourtour méditerranéen ; cultivé","meleze":"Alpes et montagnes d'Europe centrale",
"merisier":"Europe, Afrique du Nord, Asie occidentale","micocoulier":"sud de l'Europe (méditerranée)",
"murier":"origine Asie ; planté","myrtille":"Europe et Asie ; montagnes et landes acides",
"neflier":"origine Asie mineure ; naturalisé/cultivé en Europe","noisetier":"Europe et Asie occidentale ; commun",
"noyer":"origine Asie/SE Europe ; cultivé en zone tempérée","olivier":"pourtour méditerranéen",
"pecher":"origine Chine ; cultivé en zone tempérée chaude","pin_maritime":"sud-ouest de l'Europe ; littoraux atlantique et méditerranéen",
"pin_sylvestre":"Eurasie, très vaste (Europe à Sibérie)","plaqueminier":"origine Asie de l'Est ; cultivé (kaki)",
"poirier":"origine Europe/Asie ; cultivé en zone tempérée","pommier":"origine Asie centrale ; cultivé en zone tempérée",
"prunellier":"Europe, Afrique du Nord, Asie occidentale ; haies","prunier":"cultivé en zone tempérée (origine eurasiatique)",
"robinier":"origine Amérique du Nord ; naturalisé en Europe","ronce":"cosmopolite tempéré ; très commune",
"sapin":"montagnes d'Europe (sapin pectiné)","saule":"hémisphère nord ; bords d'eau",
"sorbier":"Europe et Asie ; jusqu'en altitude","sureau":"Europe, Afrique du Nord, Asie occidentale ; très commun",
"tilleul":"Europe ; commun et planté","tremble":"Europe, Afrique du Nord, Asie ; très vaste",
"vigne":"origine Caucase/méditerranée ; cultivée en zone tempérée",
# --- herbacées ---
"achillee":"Europe, Asie, Amérique du Nord ; prairies","ail":"origine Asie centrale ; cultivé partout",
"ail_des_ours":"Europe et Asie ; sous-bois frais","ail_rocambole":"Europe ; cultivé/naturalisé",
"alliaire":"Europe, Asie occidentale ; lisières et haies","amarante":"origine Amériques ; cultivée et naturalisée",
"aneth":"origine Asie du SO ; cultivé","armoise":"Europe, Asie ; friches (absinthe)","artichaut":"origine méditerranée ; cultivé",
"arum":"Europe de l'Ouest et du Sud ; sous-bois","asperge":"Europe, Afrique du Nord, Asie ; cultivée",
"asperule":"Europe, Asie occidentale ; forêts","aubergine":"origine Asie ; cultivée en climat chaud",
"avoine":"cultivée en zone tempérée (origine Proche-Orient)","bardane":"Europe et Asie ; friches",
"basilic":"origine Asie tropicale ; cultivé","berce":"Europe, Asie ; prairies et lisières",
"betterave":"origine littoraux d'Europe ; cultivée","blette":"origine méditerranée ; cultivée",
"bourrache":"origine méditerranée ; cultivée et naturalisée","camomille":"Europe, Asie ; cultivée (matricaire)",
"capucine":"origine Andes ; cultivée","cardamine":"Europe, Asie ; prairies humides",
"carotte":"Europe, Asie, Afrique du Nord (sauvage) ; cultivée partout","celeri":"Europe (littoraux) ; cultivé",
"cerfeuil":"origine Caucase/Asie occidentale ; cultivé","chenopode":"cosmopolite ; friches et cultures",
"chicoree":"Europe, Asie, Afrique du Nord ; bords de chemins","chou":"origine littoraux d'Europe ; cultivé partout",
"chou_daubenton":"cultivar pérenne (Europe de l'Ouest)","ciboulette":"hémisphère nord tempéré ; cultivée",
"claytone":"origine Amérique du Nord ; cultivée/naturalisée","colchique":"Europe ; prairies humides",
"concombre":"origine Inde ; cultivé","consoude":"Europe, Asie occidentale ; bords d'eau",
"coriandre":"origine méditerranée/Proche-Orient ; cultivée","courge":"origine Amériques ; cultivée",
"courgette":"origine Amériques ; cultivée","cresson":"Europe, Asie ; eaux courantes","crosne":"origine Asie de l'Est ; cultivé",
"digitale":"Europe de l'Ouest ; clairières acides","echalote":"cultivée en zone tempérée (origine Asie)",
"egopode":"Europe, Asie ; lieux frais ombragés","epinard":"origine Asie du SO ; cultivé",
"estragon":"origine Asie centrale/Sibérie ; cultivé","fenouil":"pourtour méditerranéen ; naturalisé/cultivé",
"feverole":"cultivée en zone tempérée (origine Proche-Orient)","fraisier_des_bois":"Europe, Asie ; bois et lisières",
"cigue":"Europe, Afrique du Nord, Asie ; friches","guimauve":"Europe, Asie ; sols humides et salés",
"haricot":"origine Amériques ; cultivé","hysope":"origine sud de l'Europe/Asie ; cultivée",
"laitue":"cultivée partout (origine méditerranée/Asie)","lamier":"Europe, Asie ; haies et jardins",
"lavande":"pourtour méditerranéen ; cultivée","liveche":"origine Asie du SO ; cultivée",
"lotier":"Europe, Asie, Afrique du Nord ; prairies","lupin":"origine Amérique/méditerranée ; cultivé",
"luzerne":"origine Asie/méditerranée ; cultivée","mache":"Europe, Afrique du Nord ; cultivée",
"mais":"origine Amérique centrale (Mexique) ; cultivé partout","marjolaine":"origine méditerranée orientale ; cultivée",
"mauve":"Europe, Asie, Afrique du Nord ; friches","melilot":"Europe, Asie ; friches et bords de route",
"melisse":"origine méditerranée orientale ; cultivée/naturalisée","menthe":"Europe, Asie ; lieux humides ; cultivée",
"millepertuis":"Europe, Asie occidentale, Afrique du Nord ; friches","moutarde":"origine méditerranée ; cultivée et naturalisée",
"muguet":"Europe, Asie tempérée ; sous-bois","navet":"cultivé en zone tempérée (origine Europe/Asie)",
"oca":"origine Andes ; cultivé","oignon":"origine Asie centrale ; cultivé partout",
"onagre":"origine Amérique du Nord ; naturalisée en Europe","origan":"Europe, Asie ; coteaux secs",
"ortie":"cosmopolite tempéré ; très commune","oseille":"Europe, Asie ; prairies","panais":"Europe, Asie ; cultivé et sauvage",
"paquerette":"Europe ; pelouses ; très commune","patate_douce":"origine Amérique tropicale ; cultivée en climat chaud",
"persil":"origine méditerranée ; cultivé","phacelie":"origine Amérique du Nord ; cultivée (engrais vert)",
"pissenlit":"hémisphère nord ; très commun","plantain":"cosmopolite ; pelouses et chemins",
"poire_de_terre":"origine Andes ; cultivé (yacon)","poireau":"cultivé en zone tempérée (origine méditerranée)",
"poireau_perpetuel":"Europe ; cultivé/naturalisé","pois":"cultivé en zone tempérée (origine Proche-Orient)",
"poivron":"origine Amérique centrale/du Sud ; cultivé","pomme_de_terre":"origine Andes ; cultivée en zone tempérée",
"pourpier":"cosmopolite des régions chaudes ; cultivé/sauvage","primevere":"Europe, Asie occidentale ; prairies et bois",
"radis":"cultivé partout (origine Asie/méditerranée)","raifort":"origine Europe du SE/Asie ; cultivé et naturalisé",
"rhubarbe":"origine Asie ; cultivée","romarin":"pourtour méditerranéen ; cultivé","roquette":"origine méditerranée ; cultivée",
"sainfoin":"Europe, Asie ; coteaux calcaires","sarrasin":"origine Asie centrale ; cultivé","sarriette":"origine méditerranée ; cultivée",
"sauge":"pourtour méditerranéen ; cultivée","scorsonere":"Europe du Sud/centrale ; cultivée",
"seigle":"cultivé en zone tempérée (origine Anatolie)","souci":"origine sud de l'Europe ; cultivé",
"stellaire":"cosmopolite ; cultures et jardins (mouron)","tanaisie":"Europe, Asie ; friches et bords de route",
"thym":"pourtour méditerranéen ; coteaux secs","tomate":"origine Andes ; cultivée partout",
"topinambour":"origine Amérique du Nord ; cultivé/naturalisé","trefle_blanc":"Europe, Asie ; prairies ; très commun",
"trefle_violet":"Europe, Asie ; prairies ; cultivé","valeriane":"Europe, Asie ; lieux frais",
"verveine_citron":"origine Amérique du Sud ; cultivée","vesce":"Europe, Asie, Afrique du Nord ; prairies et cultures",
"violette":"Europe, Asie ; bois et haies",
# --- champignons ---
"amadouvier":"hémisphère nord tempéré ; sur troncs (hêtre, bouleau)","amanite_panthere":"Europe, Asie ; forêts",
"amanite_phalloide":"Europe (introduite ailleurs) ; sous feuillus","amanite_tue_mouches":"hémisphère nord ; sous bouleaux/conifères",
"amanite_vireuse":"Europe ; forêts (mortelle)","bolet_bai":"hémisphère nord ; conifères et feuillus",
"bolet_satan":"Europe tempérée/du Sud ; feuillus sur calcaire","cepe":"hémisphère nord tempéré ; feuillus et conifères",
"clitocybe_blanc":"Europe ; prairies et pelouses","cortinaire":"hémisphère nord ; forêts",
"coulemelle":"cosmopolite tempéré ; prairies et lisières","entolome_livide":"Europe ; feuillus sur calcaire",
"galere_marginee":"hémisphère nord ; sur bois mort de conifères","girolle":"hémisphère nord tempéré ; forêts",
"lactaire_delicieux":"Europe ; sous pins","morille":"hémisphère nord tempéré ; au printemps",
"pied_de_mouton":"hémisphère nord ; forêts","pleurote":"cosmopolite ; sur troncs de feuillus",
"polypore_soufre":"hémisphère nord tempéré ; sur troncs","rose_des_pres":"zones tempérées ; prairies pâturées",
"russule_charbonniere":"Europe ; feuillus","trompette":"hémisphère nord tempéré ; sous feuillus",
"truffe":"sud de l'Europe ; sous chênes calcaires","vesse_de_loup":"cosmopolite ; prairies et bois",
# --- faune ---
"abeille":"quasi cosmopolite (élevée)","araignee":"cosmopolite","bourdon":"hémisphère nord tempéré ; commun en Europe",
"campagnol":"Europe, Asie ; prairies et cultures","carabe":"zones tempérées ; sols et litière","chauve_souris":"cosmopolite (sauf pôles)",
"chrysope":"cosmopolite tempéré ; jardins","cloporte":"cosmopolite ; lieux humides","coccinelle":"cosmopolite ; très commune",
"crapaud":"Europe, Asie, Afrique du Nord","doryphore":"origine Amérique du Nord ; envahissant en Europe",
"ecureuil":"Eurasie (écureuil roux) ; forêts","forficule":"cosmopolite tempéré ; jardins (perce-oreille)",
"geai":"Europe, Asie, Afrique du Nord ; forêts","herisson":"Europe de l'Ouest ; jardins et haies",
"limace":"cosmopolite ; lieux humides","mesange":"Europe, Asie, Afrique du Nord ; jardins et bois",
"osmie":"toute l'Europe (sauf pays nordiques) et Asie tempérée","papillon":"cosmopolite",
"processionnaire":"sud de l'Europe, en expansion vers le nord ; sur pins","puceron":"cosmopolite ; sur plantes",
"scolyte":"hémisphère nord ; sous écorce des conifères","syrphe":"cosmopolite ; jardins et prairies",
"ver_de_terre":"cosmopolite ; sols",
# --- divers ---
"cladonie":"hémisphère nord ; landes et sols pauvres","dactyle":"Europe, Asie, Afrique du Nord ; prairies",
"fetuque":"hémisphère nord tempéré ; pelouses","fougere-aigle":"cosmopolite ; landes et sous-bois acides",
"jonc":"cosmopolite tempéré ; sols humides","molinie":"Europe, Asie ; landes humides","mousse_hypne":"cosmopolite ; troncs et sols",
"osmonde":"Europe, Amérique, Asie ; bas-fonds humides acides","parmelie":"cosmopolite ; écorces et rochers",
"polypode":"hémisphère nord tempéré ; troncs, murs, rochers","polytric":"cosmopolite ; sols acides humides",
"roseau":"cosmopolite ; zones humides","scolopendre":"hémisphère nord tempéré ; rochers ombragés, murs",
"sphaigne":"hémisphère nord ; tourbières","usnee":"hémisphère nord ; branches en air pur",
"xanthorie":"cosmopolite ; murs et écorces",
}

def split_cells(line):
    return line.replace("\\|", "\x01").split("|")

def join_cells(parts):
    return "|".join(parts).replace("\x01", "\\|")

def insert_before_last(line, value):
    parts = split_cells(line)
    parts.insert(len(parts) - 2, " " + value + " ")
    return join_cells(parts)

def main():
    for atlas in ATLASES:
        p = os.path.join(BASE, atlas)
        lines = open(p, encoding="utf-8").read().split("\n")
        # repère l'en-tête
        hi = next((i for i, ln in enumerate(lines)
                   if ln.lstrip().startswith("|") and not ln.lstrip().startswith("| ![") and "latin" in ln.lower()), None)
        if hi is None:
            print("  ⚠ en-tête introuvable :", atlas); continue
        if "épartition" in lines[hi] or "epartition" in lines[hi].lower():
            print("  = déjà fait :", atlas); continue
        miss = []
        for i in range(hi, len(lines)):
            ln = lines[i]
            s = ln.lstrip()
            if not s.startswith("|"):
                if s == "" and i > hi + 1:
                    break
                continue
            if i == hi:
                lines[i] = insert_before_last(ln, "Répartition")
            elif set(s.replace("|", "").replace("-", "").replace(":", "").strip()) == set() and "-" in s:
                lines[i] = insert_before_last(ln, "---")
            elif s.startswith("| !["):
                m = IMG_RE.search(ln)
                stem = m.group(1) if m else ""
                val = REP.get(stem, "—")
                if stem and stem not in REP:
                    miss.append(stem)
                lines[i] = insert_before_last(ln, val)
        open(p, "w", encoding="utf-8").write("\n".join(lines))
        print("  + colonne ajoutée :", atlas, ("(manquants: %s)" % ", ".join(miss) if miss else ""))

if __name__ == "__main__":
    main()
