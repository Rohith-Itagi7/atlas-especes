#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Télécharge les vignettes des champignons (iNaturalist) -> img/especes/<stem>.jpg."""
import os, json, time, subprocess, urllib.request, urllib.parse
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(BASE, "img", "especes")
UA = "ForestryQuiz/1.0 (personal educational use)"
SP = [
("amadouvier","Fomes fomentarius"),("amanite_panthere","Amanita pantherina"),
("amanite_phalloide","Amanita phalloides"),("amanite_tue_mouches","Amanita muscaria"),
("amanite_vireuse","Amanita virosa"),("bolet_bai","Imleria badia"),
("bolet_satan","Rubroboletus satanas"),("cepe","Boletus edulis"),
("clitocybe_blanc","Clitocybe rivulosa"),("cortinaire","Cortinarius orellanus"),
("coulemelle","Macrolepiota procera"),("entolome_livide","Entoloma sinuatum"),
("galere_marginee","Galerina marginata"),("girolle","Cantharellus cibarius"),
("lactaire_delicieux","Lactarius deliciosus"),("morille","Morchella esculenta"),
("pied_de_mouton","Hydnum repandum"),("pleurote","Pleurotus ostreatus"),
("polypore_soufre","Laetiporus sulphureus"),("rose_des_pres","Agaricus campestris"),
("russule_charbonniere","Russula cyanoxantha"),("trompette","Craterellus cornucopioides"),
("truffe","Tuber melanosporum"),("vesse_de_loup","Lycoperdon perlatum"),
]
ok = 0
for i, (stem, latin) in enumerate(SP):
    dest = os.path.join(IMG, stem + ".jpg")
    if os.path.exists(dest):
        print("[%d/%d] %s : déjà" % (i+1, len(SP), stem)); continue
    try:
        api = "https://api.inaturalist.org/v1/taxa?q=%s&per_page=1" % urllib.parse.quote(latin)
        req = urllib.request.Request(api, headers={"User-Agent": UA})
        d = json.load(urllib.request.urlopen(req, timeout=30))
        res = d.get("results", [])
        src = None
        if res and res[0].get("default_photo"):
            src = res[0]["default_photo"].get("medium_url") or res[0]["default_photo"].get("url")
        if not src:
            print("[%d/%d] %s : ∅" % (i+1, len(SP), stem)); time.sleep(1.3); continue
        buf = urllib.request.urlopen(urllib.request.Request(src, headers={"User-Agent": UA}), timeout=30).read()
        open(dest+".o","wb").write(buf)
        subprocess.run(["sips","-Z","500","-s","format","jpeg","-s","formatOptions","80",dest+".o","--out",dest],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.remove(dest+".o"); ok += 1
        print("[%d/%d] %s : OK" % (i+1, len(SP), stem))
    except Exception as e:
        print("[%d/%d] %s : err %s" % (i+1, len(SP), stem, e))
    time.sleep(1.3)
print("=== champignons téléchargés :", ok, "===")
