#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hors ligne : manifeste d'application, icônes et service worker du site.

L'atlas sert sur le terrain — en forêt, en jardin-forêt, là où il n'y a pas de réseau. Toutes
les données sont déjà dans la page ; il ne manquait qu'un service worker pour que la page
elle-même reste disponible.

Stratégies :
  page          réseau d'abord, cache en repli → une version publiée est prise au lancement
                suivant, et l'app démarre quand même sans réseau
  images        cache d'abord → toute photo consultée une fois reste consultable hors ligne
  précache      la coquille seulement (index.html, manifeste, icônes) : les 33 Mo de photos
                ne sont PAS téléchargés d'office, l'utilisateur choisit ses catégories

Le cache des images est délibérément séparé de celui de la coquille et survit aux mises à
jour : les noms de fichiers des photos ne changent pas, et re-télécharger 11 Mo à chaque
publication serait absurde.
"""
import json
import os

FICHIER_SW = "sw.js"
CACHE_IMAGES = "images-v1"   # séparé de la coquille : les photos survivent aux mises à jour
MANIFESTE = "manifest.webmanifest"
ICONE_SVG = "icon.svg"
ICONES_PNG = ((192, "icon-192.png"), (512, "icon-512.png"), (180, "apple-touch-icon.png"))
FOND = (22, 36, 28)        # var(--color-navy-900) du site
FEUILLE = (166, 199, 138)  # vert clair, lisible sur le fond

# La coquille : ce qui est mis en cache à l'installation (quelques centaines de ko).
def coquille(avec_png=True):
    """Ne liste que ce qui a vraiment été écrit : sans Pillow, les PNG n'existent pas, et
    un fichier absent dans la coquille suffisait à laisser le site sans mode hors ligne."""
    base = ["./", "index.html", MANIFESTE, ICONE_SVG]
    return base + ([n for _px, n in ICONES_PNG] if avec_png else [])


def manifeste():
    return {
        "name": "Atlas & quiz des espèces",
        "short_name": "Atlas espèces",
        "description": "Atlas et quiz d'identification d'espèces, utilisable hors ligne.",
        "start_url": "./",
        "scope": "./",
        "display": "standalone",
        "orientation": "any",
        "background_color": "#F7F7F5",
        "theme_color": "#16241C",
        "lang": "fr",
        "icons": [
            {"src": ICONE_SVG, "sizes": "any", "type": "image/svg+xml"},
            {"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"},
            {"src": "icon-512.png", "sizes": "512x512", "type": "image/png",
             "purpose": "maskable"},
        ],
    }


SVG_ICONE = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
<rect width="512" height="512" rx="96" fill="#16241C"/>
<path d="M256 96c-88 0-152 62-152 148 0 62 40 112 100 132-4-58 22-108 76-140-38 34-58 78-56 132
 8 2 20 4 32 4 88 0 152-62 152-148 0-70-58-128-152-128z" fill="#A6C78A"/>
<path d="M256 416V292" stroke="#A6C78A" stroke-width="18" stroke-linecap="round"/>
</svg>
"""


def ecrire_icones(outdir):
    """Écrit l'icône SVG et, si Pillow est là, les PNG attendus par Android et iOS."""
    with open(os.path.join(outdir, ICONE_SVG), "w", encoding="utf-8") as fh:
        fh.write(SVG_ICONE)
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return False
    for px, nom in ICONES_PNG:
        im = Image.new("RGB", (px, px), FOND)
        d = ImageDraw.Draw(im)
        u = px / 512.0
        # feuille stylisée : une ellipse inclinée + la nervure, dessinée à la main faute de
        # rendu SVG dans Pillow (l'icône reste simple, c'est un logo de 192 px)
        feuille = Image.new("RGBA", (px, px), (0, 0, 0, 0))
        df = ImageDraw.Draw(feuille)
        df.ellipse([120 * u, 90 * u, 392 * u, 330 * u], fill=FEUILLE + (255,))
        feuille = feuille.rotate(-30, resample=Image.BICUBIC, center=(px / 2, px * 0.41))
        im.paste(feuille, (0, 0), feuille)
        d.line([(px / 2, 420 * u), (px / 2, 250 * u)], fill=FEUILLE, width=max(2, int(18 * u)))
        im.save(os.path.join(outdir, nom), "PNG", optimize=True)
    return True


JS_SW = r"""// Service worker de l'atlas — généré par scripts/site_sw.py, ne pas éditer à la main.
const VERSION = '__VERSION__';
const COQUILLE = 'coquille-' + VERSION;   // renommé à chaque publication
const IMAGES = '__CACHE_IMAGES__';        // durable : les noms de photos ne changent pas
const FICHIERS = __COQUILLE__;

self.addEventListener('install', ev => {
  // On n'active pas de force : la page proposera « Recharger » quand la version sera prête.
  // Fichier par fichier, et non addAll : celui-ci est atomique, si bien qu'un seul 404
  // (une icône absente, un déploiement partiel) laissait le site SANS mode hors ligne.
  ev.waitUntil(caches.open(COQUILLE)
    .then(c => Promise.all(FICHIERS.map(f => c.add(f).catch(() => {}))))
    .catch(() => {}));
});

self.addEventListener('activate', ev => {
  ev.waitUntil((async () => {
    const noms = await caches.keys();
    await Promise.all(noms.filter(n => (n.startsWith('coquille-') && n !== COQUILLE)
                                    || (n.startsWith('images-') && n !== IMAGES))
                          .map(n => caches.delete(n)));
    await self.clients.claim();
  })());
});

self.addEventListener('message', ev => {
  const type = ev.data && ev.data.type;
  if (type === 'ACTIVER') self.skipWaiting();
  if (type === 'VERSION' && ev.source) ev.source.postMessage({type: 'VERSION', version: VERSION});
});

async function cacheDabord(req) {
  const cache = await caches.open(IMAGES);
  const vu = await cache.match(req);
  if (vu) return vu;
  const rep = await fetch(req);
  if (rep && rep.ok) cache.put(req, rep.clone());
  return rep;
}

async function reseauDabord(req) {
  const cache = await caches.open(COQUILLE);
  try {
    const rep = await fetch(req);
    if (rep && rep.ok) cache.put(req, rep.clone());
    return rep;
  } catch (e) {
    const vu = await cache.match(req) || await cache.match('index.html') || await cache.match('./');
    if (vu) return vu;
    throw e;
  }
}

self.addEventListener('fetch', ev => {
  const req = ev.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== location.origin) return;
  if (url.pathname.indexOf('/img/') >= 0) { ev.respondWith(cacheDabord(req)); return; }
  ev.respondWith(reseauDabord(req));
});
"""


def sw_js(version, avec_png=True):
    return (JS_SW.replace("__VERSION__", version)
                 .replace("__CACHE_IMAGES__", CACHE_IMAGES)
                 .replace("__COQUILLE__", json.dumps(coquille(avec_png))))


def ecrire(outdir, version):
    """Écrit sw.js, le manifeste et les icônes. Renvoie True si les PNG ont pu être produits.

    Les icônes d'abord : le service worker ne doit précacher que des fichiers qui existent.
    """
    png = ecrire_icones(outdir)
    with open(os.path.join(outdir, FICHIER_SW), "w", encoding="utf-8") as fh:
        fh.write(sw_js(version, png))
    with open(os.path.join(outdir, MANIFESTE), "w", encoding="utf-8") as fh:
        json.dump(manifeste(), fh, ensure_ascii=False, indent=2)
    return png
