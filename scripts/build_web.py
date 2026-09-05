#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build du site statique (GitHub Pages) — interface actuelle.
Lit les atlas via scripts/atlas_data.py, transforme les données au format attendu par
l'app (site_ui) et écrit un index.html autonome. Les photos sont copiées telles quelles,
plus une vignette légère par image pour les affichages petits (cf. scripts/derives.py,
Pillow optionnel). Pas de sips → tourne en CI Linux.

  python3 scripts/build_web.py [dossier_sortie]   (défaut : _site)
"""
import hashlib, json, os, shutil, sys

import atlas_data
import credits
import derives
import site_sw
import site_ui

BASE = atlas_data.BASE

OUTDIR = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BASE, "_site")

def enc_web(p):
    b = os.path.basename(p)
    return "img/especes/" + b if (os.sep + "especes" + os.sep) in p else "img/quiz-extra/" + b

def conf_groups(stem, id_par_stem):
    """Groupes de confusion de l'espèce : le critère qui tranche **et** ses sosies.

    Le quiz en a besoin des deux : le texte pour le feedback, les identifiants pour tirer
    des distracteurs qui sont de vraies confusions (souvent inter-familles).
    """
    out = []
    for g in atlas_data.CONF:
        if stem not in g["stems"]:
            continue
        ids = [id_par_stem[m] for m in g["stems"] if m != stem and m in id_par_stem]
        out.append({"tip": g["tip"], "ids": ids})
    return out

def to_web_data(species, deriveur=None):
    """Données injectées dans le site. Avec un `deriveur`, chaque photo reçoit sa vignette
    légère (« t ») et ses dimensions (« w », « h ») — cf. scripts/derives.py."""
    cred = credits.charger()
    id_par_stem = {}
    for s in species:
        id_par_stem.setdefault(s["stem"], s["id"])
    out = []
    for s in species:
        imgs = []
        for p in s["paths"]:
            rel = enc_web(p)
            im = {"u": rel, "a": atlas_data.aspect_of(p, s["stem"])}
            if deriveur is not None:
                thumb = deriveur.thumb(p, rel)
                if thumb != rel:
                    im["t"] = thumb
                wh = derives.dimensions(p)
                if wh:                      # dimensions connues = pas de saut de page
                    im["w"], im["h"] = wh
            # attribution affichée sous la photo ; absente tant que le crédit est inconnu
            attribution = credits.texte(cred.get(os.path.basename(p)))
            if attribution:
                im["c"] = attribution
                url = cred[os.path.basename(p)].get("url")
                if url and url != credits.INCONNU:
                    im["cu"] = url
            imgs.append(im)
        d = {
            "id": s["id"], "name": s["name"], "latin": s["latin"], "cat": s["cat"],
            "note": s["note"], "fields": s["fields"], "imgs": imgs,
            "conf": conf_groups(s["stem"], id_par_stem),
            # orthographes acceptées en mode saisie (cf. atlas_data.answer_variants)
            "alt": atlas_data.answer_variants(s["name"], s["latin"]),
        }
        if "comestible" in s["fields"]:  # verdict du mode Oui/Non, calculé ici (cf. atlas_data.is_edible)
            d["edible"] = atlas_data.is_edible(s["fields"]["comestible"])
        out.append(d)
    return out

def offline_web(data, outdir):
    """Poids des photos par catégorie, pour annoncer la taille d'un téléchargement hors ligne.

    Le client ne peut pas connaître la taille des fichiers sans les télécharger : c'est le
    build qui la mesure (original + vignette de chaque photo de la catégorie).
    """
    par_cat = {}
    for s in data:
        e = par_cat.setdefault(s["cat"], {"n": 0, "o": 0})
        for im in s["imgs"]:
            for rel, racine in ((im["u"], BASE), (im.get("t"), outdir)):
                if not rel:
                    continue
                chemin = os.path.join(racine, rel)
                if os.path.exists(chemin):
                    e["n"] += 1
                    e["o"] += os.path.getsize(chemin)
    return par_cat

def empreinte(data):
    """Version du build : change dès que la page ou les données changent (cf. service worker)."""
    brut = (json.dumps(data, ensure_ascii=False, sort_keys=True)
            + site_ui.CSS + site_ui.JS + site_ui.BODY)
    return hashlib.sha256(brut.encode("utf-8")).hexdigest()[:12]

def aspects_web():
    """Vocabulaire des aspects pour le site (l'app n'en garde aucune copie en dur)."""
    return [{"id": a.id, "label": a.label, "emoji": a.emoji, "cible": a.cible}
            for a in atlas_data.ASPECTS]

def assemble(data, offline=None):
    js = (site_ui.JS.replace("/*__DATA__*/", json.dumps(data, ensure_ascii=False))
                    .replace("/*__ASPECTS__*/", json.dumps(aspects_web(), ensure_ascii=False))
                    .replace("/*__OFFLINE__*/", json.dumps(offline or {}, ensure_ascii=False)))
    head = ('<meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">'
            '<meta name="theme-color" content="#16241C">'
            '<link rel="manifest" href="' + site_sw.MANIFESTE + '">'
            '<link rel="apple-touch-icon" href="apple-touch-icon.png">'
            '<title>Atlas des espèces</title><style>' + site_ui.CSS + '</style>')
    return ("<!doctype html><html lang=\"fr\"><head>" + head + "</head><body>"
            + site_ui.BODY + "<script>" + js + "</script></body></html>")

def main():
    species, seen = [], set()
    for path, cat in atlas_data.ATLASES:
        got = atlas_data.parse_atlas(path, cat, seen)
        print("%-38s : %d espèces" % (path, len(got)))
        species += got
    species = atlas_data.apply_corrections(species)
    os.makedirs(OUTDIR, exist_ok=True)
    deriveur = derives.Deriveur(OUTDIR)
    data = to_web_data(species, deriveur)
    offline = {"cats": offline_web(data, OUTDIR), "cache": site_sw.CACHE_IMAGES}
    with open(os.path.join(OUTDIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(assemble(data, offline))
    png = site_sw.ecrire(OUTDIR, empreinte(data))
    # copie uniquement les images réellement référencées
    refs = {im["u"] for s in data for im in s["imgs"]}
    copied = 0
    for rel in sorted(refs):
        srcp, dstp = os.path.join(BASE, rel), os.path.join(OUTDIR, rel)
        if os.path.exists(srcp):
            os.makedirs(os.path.dirname(dstp), exist_ok=True)
            shutil.copy2(srcp, dstp)
            copied += 1
        else:
            print("  ⚠ image absente :", rel)
    deriveur.cloturer()
    open(os.path.join(OUTDIR, ".nojekyll"), "w").close()
    sz = os.path.getsize(os.path.join(OUTDIR, "index.html")) / 1e6
    print("TOTAL : %d espèces, %d images -> %s (index.html %.1f Mo)"
          % (len(species), copied, OUTDIR, sz))
    print("       %s" % deriveur.resume())
    print("       hors ligne : service worker + manifeste%s, %.1f Mo de photos téléchargeables"
          % ("" if png else " (icônes PNG sautées : Pillow absent)",
             sum(c["o"] for c in offline["cats"].values()) / 1e6))

if __name__ == "__main__":
    main()
