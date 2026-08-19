#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Télécharge les vignettes de la faune (iNaturalist) -> img/especes/<stem>.jpg."""
import os, json, time, subprocess, urllib.request, urllib.parse
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(BASE, "img", "especes")
UA = "ForestryQuiz/1.0 (personal educational use)"
SP = [
("abeille","Apis mellifera"),("araignee","Araneus diadematus"),("bourdon","Bombus terrestris"),
("campagnol","Microtus arvalis"),("carabe","Carabus auratus"),("chauve_souris","Pipistrellus pipistrellus"),
("chrysope","Chrysoperla carnea"),("cloporte","Armadillidium vulgare"),("coccinelle","Coccinella septempunctata"),
("crapaud","Bufo bufo"),("doryphore","Leptinotarsa decemlineata"),("ecureuil","Sciurus vulgaris"),
("forficule","Forficula auricularia"),("geai","Garrulus glandarius"),("herisson","Erinaceus europaeus"),
("limace","Arion rufus"),("mesange","Parus major"),("osmie","Osmia bicornis"),
("papillon","Papilio machaon"),("processionnaire","Thaumetopoea pityocampa"),("puceron","Aphis fabae"),
("scolyte","Ips typographus"),("syrphe","Syrphus ribesii"),("ver_de_terre","Lumbricus terrestris"),
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
print("=== faune téléchargée :", ok, "===")
