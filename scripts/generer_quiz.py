#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Générateur du quiz / atlas connecté des espèces.
Sorties : « Quiz especes.html » (autonome pleine résolution) et « Quiz especes.artifact.html »
          (sans <html>/<head>/<body>, images recompressées, < 16 Mo).
Lit TOUTES les colonnes des atlas (via l'en-tête) → fiche complète affichée dans l'app.
Aspects des photos : nom de fichier <stem>-<aspect>-<n>.jpg  (+ sidecar img/quiz-extra/_aspects.tsv
                     « fichier<TAB>aspect1,aspect2 » qui OVERRIDE, non destructif, pour tagger les vignettes).
"""
import re, json, base64, glob, os, subprocess, tempfile, unicodedata

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(BASE, "img", "especes")
EXTRA = os.path.join(BASE, "img", "quiz-extra")
OUT = os.path.join(BASE, "Quiz especes.html")
OUT_ART = os.path.join(BASE, "Quiz especes.artifact.html")
OUT_SHARE = os.path.join(BASE, "Quiz especes - a partager.html")
TMP = tempfile.mktemp(suffix=".jpg")
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

def b64_asis(path):
    ext = path.rsplit(".", 1)[-1].lower()
    mime = "image/png" if ext == "png" else "image/jpeg"
    with open(path, "rb") as f:
        return "data:%s;base64,%s" % (mime, base64.b64encode(f.read()).decode())

def b64_small(path, maxpx=340, q=60):
    orig = open(path, "rb").read()
    r = subprocess.run(["sips", "-Z", str(maxpx), "-s", "format", "jpeg", "-s", "formatOptions", str(q),
                        path, "--out", TMP], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    comp = open(TMP, "rb").read() if (r.returncode == 0 and os.path.exists(TMP)) else b""
    if comp and len(comp) < len(orig):
        return "data:image/jpeg;base64," + base64.b64encode(comp).decode()
    ext = path.rsplit(".", 1)[-1].lower()
    mime = "image/png" if ext == "png" else "image/jpeg"
    return "data:%s;base64,%s" % (mime, base64.b64encode(orig).decode())

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
        paths = [vpath] + [ex for ex in sorted(glob.glob(os.path.join(EXTRA, stem + "*"))) if os.path.isfile(ex)]
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

def to_data(species, enc, cap=None):
    res = []
    for s in species:
        paths = s["paths"]
        if cap and len(paths) > cap:  # plafond version en ligne : vignette + extras (annotés d'abord)
            extras = sorted(paths[1:], key=lambda p: 0 if [a for a in aspect_of(p, s["stem"]) if a != "divers"] else 1)
            paths = paths[:1] + extras[:cap - 1]
        imgs = [{"u": enc(p), "a": aspect_of(p, s["stem"]), "f": os.path.basename(p)} for p in paths]
        conf = [{"tip": g["tip"], "mates": [m for m in g["stems"] if m != s["stem"]]}
                for g in CONF if s["stem"] in g["stems"]]
        res.append({"id": s["id"], "stem": s["stem"], "name": s["name"], "latin": s["latin"],
                    "note": s["note"], "cat": s["cat"], "fields": s["fields"], "imgs": imgs,
                    "indic": ("indic" in (s["note"] or "").lower()), "conf": conf})
    return res

CSS = r"""
:root{--bg:#F5F7EF;--bg2:#E7EEDA;--card:#FFFFFF;--ink:#232A20;--soft:#5E6656;--line:#E1E4D6;
  --green:#6FA83C;--greenD:#4E8542;--greenDD:#3A6A33;--amber:#C99A3B;--red:#C0392B;--blue:#4E7FA8;
  --shadow:0 1px 2px rgba(35,42,32,.05),0 6px 22px rgba(35,42,32,.07);--radius:14px;}
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,'Helvetica Neue',Arial,sans-serif;color:var(--ink);
  background:linear-gradient(180deg,var(--bg2),var(--bg) 300px) no-repeat,var(--bg);-webkit-text-size-adjust:100%;}
.wrap{max-width:640px;margin:0 auto;padding:16px 14px 40px;}
.hero{text-align:center;padding:24px 14px 16px;margin:-16px -14px 10px;
  background:radial-gradient(130% 110% at 50% -10%,rgba(78,133,66,.20),transparent 62%);}
h1{font-size:26px;line-height:1.12;margin:0;text-align:center;font-weight:800;letter-spacing:-.02em;text-wrap:balance}
h2{font-size:18px;margin:8px 0 0;text-align:center}
.sub{color:var(--soft);text-align:center;font-size:13px;margin:7px 0 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:15px;margin:12px 0;box-shadow:var(--shadow);}
.grouplab{font-size:12px;font-weight:800;color:var(--soft);text-transform:uppercase;letter-spacing:.05em;margin:2px 0 9px}
.hint{font-size:11px;color:var(--soft);margin-top:6px;font-style:italic}
.opts{display:flex;flex-wrap:wrap;gap:8px}
.opt{flex:1 1 45%;padding:12px 10px;border:1.5px solid var(--line);border-radius:11px;background-color:var(--card);background-repeat:no-repeat;color:var(--ink);font-size:15px;cursor:pointer;text-align:center;transition:border-color .12s,background-color .12s,transform .06s;}
.opt:hover{border-color:var(--green)}
.opt:active{transform:scale(.98)}
.opt.sel{border-color:var(--greenD);background-color:#EAF3D9;font-weight:700;box-shadow:0 1px 0 rgba(78,133,66,.18)}
.opt:focus-visible,button:focus-visible,input:focus-visible,.chip:focus-visible{outline:2px solid var(--greenD);outline-offset:2px}
button.go{width:100%;padding:15px;border:none;border-radius:var(--radius);background:linear-gradient(180deg,var(--green),var(--greenD));color:#fff;font-size:17px;font-weight:700;cursor:pointer;margin-top:6px;box-shadow:0 2px 9px rgba(78,133,66,.32);transition:transform .06s,box-shadow .12s}
button.go:hover{box-shadow:0 5px 16px rgba(78,133,66,.42)}
button.go:active{transform:translateY(1px)}
button.go.alt{background:linear-gradient(180deg,#6a97c0,var(--blue));box-shadow:0 2px 9px rgba(78,127,168,.32)}
button.ghost{width:100%;background:none;border:1px solid var(--line);color:var(--soft);border-radius:10px;padding:11px 12px;font-size:14px;cursor:pointer;margin-top:8px}
button:disabled{opacity:.4;cursor:default}
.topbar{display:flex;justify-content:space-between;align-items:center;gap:8px}
.topbar button.ghost{width:auto;margin:0}
.stat{display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px dashed var(--line);font-size:14px}
.stat:last-child{border-bottom:none}.stat b{font-variant-numeric:tabular-nums}
.imgbox{width:100%;aspect-ratio:1/1;border-radius:12px;overflow:hidden;background:#eee;display:flex;align-items:center;justify-content:center}
.imgbox img{width:100%;height:100%;object-fit:cover}
.qa{margin-top:12px}.ans{width:100%;padding:12px;border:1.5px solid var(--line);border-radius:10px;font-size:16px}
.fb{margin-top:10px;padding:12px;border-radius:10px;font-size:15px}
.fb.ok{background:#EAF3DD;border:1px solid var(--green)}.fb.no{background:#F7E4E0;border:1px solid var(--red)}
.fb .nm{font-weight:700;font-size:17px}.fb .lt{font-style:italic;color:var(--soft)}.fb .nt{margin-top:4px;font-size:13px;color:var(--soft)}
.badge{display:inline-block;font-size:11px;font-weight:700;padding:2px 8px;border-radius:20px;background:#EEF5E1;color:var(--greenD);margin-left:6px}
.mini{font-size:13px;color:var(--soft);font-variant-numeric:tabular-nums}.pill{font-size:12px;color:var(--soft)}.hidden{display:none!important}
a.reset{display:block;text-align:center;color:var(--soft);font-size:12px;margin-top:14px;text-decoration:underline;cursor:pointer}
.credit{text-align:center;color:var(--soft);font-size:11px;margin-top:18px}
.glist{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;margin-top:12px}
.gcard{border:1px solid var(--line);border-radius:10px;overflow:hidden;background:#fff}
.gthumb{position:relative;width:100%;aspect-ratio:1/1;overflow:hidden;background:#eee;cursor:pointer}
.gthumb img{width:100%;height:100%;object-fit:cover}
.gcount{position:absolute;top:6px;right:6px;background:rgba(0,0,0,.6);color:#fff;font-size:11px;font-weight:700;padding:2px 7px;border-radius:20px}
.gmeta{padding:8px}.gname{font-size:13px;font-weight:700;line-height:1.2}.glat{font-size:11px;font-style:italic;color:var(--soft)}
.gstat{font-size:11px;margin-top:4px;font-weight:700}.gstat.k{color:var(--greenD)}.gstat.p{color:var(--amber)}.gstat.n{color:var(--soft);font-weight:400}
.chips{display:flex;flex-wrap:wrap;gap:4px;margin-top:7px}
.chip{font-size:10px;padding:2px 7px;border-radius:20px;border:1px solid var(--line);cursor:pointer;user-select:none;background:#fff;color:var(--soft)}
.chip.ok{background:#EEF5E1;border-color:var(--green);color:var(--greenD);font-weight:700}.chip.missing{opacity:.55}.chip.want{background:#FBE6C9;border-color:var(--amber);color:#8a6a1f;font-weight:700}
.tools{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0}
.tools button{flex:1 1 30%;padding:9px;border:1px solid var(--line);background:#fff;border-radius:9px;font-size:12px;cursor:pointer}
.expout{width:100%;height:130px;margin-top:8px;font-family:monospace;font-size:12px;padding:8px;border:1px solid var(--line);border-radius:8px}
.legend{font-size:11px;color:var(--soft);margin:4px 0 8px}.legend b.ok{color:var(--greenD)}.legend b.want{color:#8a6a1f}
.big{width:100%;aspect-ratio:1/1;border-radius:12px;overflow:hidden;background:#fff;border:1px solid var(--line)}.big img{width:100%;height:100%;object-fit:contain}
.strip{display:flex;gap:8px;overflow-x:auto;padding:10px 0}
.strip img{width:72px;height:72px;object-fit:cover;border-radius:8px;border:2px solid transparent;cursor:pointer;flex:0 0 auto}.strip img.sel{border-color:var(--greenD)}
.asplabel{text-align:center;font-size:12px;color:var(--soft);margin-top:4px}
.tagger{display:flex;flex-wrap:wrap;gap:6px;justify-content:center;margin-top:8px}
.tagbtn{font-size:12px;padding:5px 10px;border:1.5px solid var(--line);border-radius:8px;background:#fff;color:var(--soft);cursor:pointer}
.tagbtn.active{border-color:var(--greenD);background:#EEF5E1;color:var(--greenD);font-weight:700}
.taghint{font-size:11px;color:var(--soft);text-align:center;margin-top:6px;font-style:italic}
.fields{margin:12px 0 2px}
.frow{display:flex;gap:8px;padding:5px 0;border-bottom:1px dashed var(--line);font-size:13px}
.frow .fl{flex:0 0 34%;color:var(--soft);font-weight:600}.frow .fv{flex:1}
.fichecard{border:1px solid var(--line);border-radius:12px;padding:12px;background:#fff}
.qtag{font-weight:700;margin-bottom:8px}
.fv.blur{filter:blur(5px);cursor:pointer;user-select:none;border-radius:4px;background:#F3F1EA;transition:filter .12s}
.fv.blur::after{content:' 👁';filter:none;opacity:.6;font-size:11px}
.fv.blur.reveal{filter:none;background:none;cursor:default}
.fv.blur.reveal::after{content:''}
.fichehint{font-size:11px;color:var(--soft);font-style:italic;margin-top:8px}
.indic{color:#B07C24;font-weight:700;font-size:12px}
#critplay{display:flex;flex-direction:column}
#critstack{position:relative;height:56dvh;min-height:210px;margin-bottom:2px}
.critstackcard{position:absolute;inset:0;display:flex;flex-direction:column;justify-content:center;margin:0;will-change:transform,opacity}
#critback{transform:scale(.96);opacity:.7;pointer-events:none}
.critimg{width:100%;flex:1 1 auto;min-height:110px;border-radius:12px;overflow:hidden;background:#eef0e8;display:flex;align-items:center;justify-content:center}
.critimg img{width:100%;height:100%;object-fit:contain}
.critname{text-align:center;font-weight:700;font-size:17px;margin-top:8px}
#critbtns{margin-top:10px}
.critbanner{padding:9px 12px;border-radius:10px;font-size:14px;margin-top:8px;text-align:center}
.critbanner.ok{background:#EAF3DD;border:1px solid var(--green)}
.critbanner.no{background:#F7E4E0;border:1px solid var(--red)}
"""

BODY = r"""
<div class="wrap">
<header class="hero"><h1>🌿 Atlas &amp; quiz des espèces</h1>
<div class="sub">identification — progression sauvegardée sur cet appareil</div></header>
<div id="home">
  <button class="go alt" id="showlist" style="margin-top:0">📋 Explorer l'atlas &amp; les photos</button>
  <button class="go alt" id="showcrit" style="margin-top:8px;background:linear-gradient(180deg,#c9a24b,#b0862f)">🃏 Trier par critère (swipe)</button>
  <div class="card">
    <div class="grouplab">🗂 Que réviser ?</div><div class="opts" id="scope"></div>
    <div class="grouplab" style="margin-top:14px">🎓 Mode</div><div class="opts" id="mode"></div>
    <div class="grouplab" style="margin-top:14px">🔍 Sur quoi ?</div><div class="opts" id="aspect"></div>
    <div class="hint" id="asphint">Tague des photos (écorce, feuille…) pour filtrer ici.</div>
    <div class="grouplab" style="margin-top:14px">❓ Type de question</div><div class="opts" id="qtype"></div>
    <div class="grouplab" style="margin-top:14px">🎚 Difficulté</div><div class="opts" id="diff"></div>
    <button class="go" id="start">Commencer ▶</button>
  </div>
  <div class="card"><div class="grouplab">📊 Tes statistiques</div><div id="stats"></div></div>
  <div class="card"><div class="grouplab">💾 Sauvegarde de ma progression</div>
    <div class="hint" style="margin-top:0">Exporte pour garder une copie ou changer d'appareil ; importe pour restaurer.</div>
    <div class="tools">
      <button id="expprog">💾 Exporter</button>
      <button id="impfilebtn">📂 Importer un fichier</button>
      <button id="restorebtn">↩︎ Restaurer le texte</button>
    </div>
    <input type="file" id="impfile" accept="application/json,.json" class="hidden">
    <textarea class="expout hidden" id="backupbox" placeholder="Sauvegarde (copiée automatiquement à l'export) — ou colle-la ici puis « Restaurer le texte »…"></textarea>
  </div>
  <a class="reset" id="reset">réinitialiser ma progression</a>
</div>
<div id="quiz" class="hidden">
  <div class="topbar"><button class="ghost" id="back">← Accueil</button><div class="mini" id="score">0 / 0</div></div>
  <div class="pill" id="ctx" style="margin:8px 2px"></div>
  <div class="card"><div class="imgbox" id="imgbox"><img id="pic" alt="espèce à identifier"></div>
    <div id="fichebox" class="hidden"></div>
    <div class="qa" id="answerzone"></div><div id="feedback"></div>
    <button class="ghost" id="reportbtn" style="margin-top:8px">⚠️ Signaler un problème sur cette photo</button>
    <div id="reportpanel" class="hidden"></div></div>
</div>
<div id="list" class="hidden">
  <div class="topbar"><button class="ghost" id="backlist">← Accueil</button><div class="mini" id="listcount"></div></div>
  <div class="grouplab">🗂 Catégorie</div><div class="opts" id="listscope" style="margin-bottom:10px"></div>
  <div class="legend">Puces : <b class="ok">vertes = photos présentes</b> · grises = manquantes · <b class="want">orange = demandées</b>.</div>
  <div class="tools">
    <button id="markgaps">Marquer les manques</button>
    <button id="clearmarks">Effacer</button>
    <button id="doexport">📋 Copier les manques</button>
    <button id="exporttags">🏷 Exporter mes tags</button>
  </div>
  <textarea class="expout hidden" id="expout" readonly></textarea>
  <button class="go" id="publishpr" style="margin-top:10px">🚀 Publier mes changements sur GitHub (PR)</button>
  <div class="hint">Envoie tes re-tags de photos (🏷) et tes manques signalés (oranges) sous forme de Pull Request. Une page GitHub s'ouvre : clique « Propose changes ».</div>
  <div class="glist" id="glist"></div>
</div>
<div id="detail" class="hidden">
  <div class="topbar"><button class="ghost" id="backdetail">← Atlas</button><div class="mini" id="detailcount"></div></div>
  <h2 id="detailname"></h2><div class="glat" id="detaillat" style="text-align:center"></div>
  <div class="topbar" style="margin:8px 0"><button class="ghost" id="prevsp">‹ Précédente</button><button class="ghost" id="nextsp">Suivante ›</button></div>
  <div class="card"><div class="big"><img id="detailpic" alt=""></div>
    <div class="asplabel" id="detailasp"></div>
    <div class="tagger" id="tagger"></div>
    <div class="taghint">Clique un aspect pour (dé)tagger CETTE photo (effet immédiat).</div>
    <div id="detailmis"></div>
    <div class="strip" id="detailstrip"></div>
    <div class="fields" id="detailfields"></div>
    <div class="chips" id="detailchips" style="justify-content:center;margin-top:6px"></div>
  </div>
</div>
<div id="crit" class="hidden">
  <div class="topbar"><button class="ghost" id="backcrit">← Accueil</button><div class="mini" id="critscore"></div></div>
  <div id="critchoose">
    <div class="card"><div class="grouplab">🃏 Sur quelle catégorie ?</div><div class="opts" id="critscope"></div>
      <div class="grouplab" style="margin-top:14px">Critère à trier</div><div class="opts" id="critlist"></div>
      <div class="hint">Réponds pour chaque espèce : appartient-elle au critère ? Swipe (ou boutons / flèches ←→).</div>
    </div>
  </div>
  <div id="critplay" class="hidden">
    <div class="pill" id="critq" style="text-align:center;font-weight:800;font-size:17px;margin:4px 0 8px"></div>
    <div id="critstack">
      <div class="card critstackcard" id="critback"><div class="critimg"><img id="critpicB" alt=""></div><div class="critname" id="critnameB"></div></div>
      <div class="card critstackcard" id="critcard" style="touch-action:pan-y"><div class="critimg"><img id="critpic" alt="espèce à trier"></div><div class="critname" id="critname"></div></div>
    </div>
    <div id="critfb"></div>
    <div class="opts" id="critbtns"><button class="opt" id="critno">👎 Non</button><button class="opt" id="crityes">👍 Oui</button></div>
  </div>
</div>
<div class="credit">Photos : Wikimedia Commons &amp; iNaturalist (licences libres / CC).<br>
<a href="https://github.com/iribarnesy/atlas-especes" target="_blank" rel="noopener">Contribuer ou télécharger les atlas (Markdown) sur GitHub ↗</a></div>
</div>
"""

JS = r"""
const SPECIES = /*__DATA__*/;
const KEY='quizEspeces_v1', FLAGKEY='photoFlags_v1', TAGKEY='tagOverrides_v1', CORRKEY='photoCorr_v1';
const REPO='iribarnesy/atlas-especes';
const ASPECTS={tout:'✨ Tout',divers:'Divers',feuille:'🍃 Feuille',ecorce:'🪵 Écorce',fruit:'🍒 Fruit',fleur:'🌸 Fleur',rameau:"❄️ Rameau",port:'🌲 Port'};
const CHIP_ASPECTS=['feuille','ecorce','fruit','fleur','port'];
const FIELD_ORDER=[['groupe','Groupe'],['type','Type'],['cycle','Cycle'],['famille','Famille'],['ecologie','Écologie'],['hote','Arbre / substrat'],['habitat','Habitat'],['role','Rôle'],['regime','Régime'],['saison','Saison'],['lumiere','Lumière'],['fixn','Fixation N'],['mycorhize','Mycorhize'],['succession','Succession'],['strate','Strate'],['fonction','Fonction'],['comestible','Comestible'],['repartition','Où on la trouve'],['notes','Notes']];
const CATLABEL={ligneux:'🌳 Ligneux',herbace:'🌿 Herbacées',champignon:'🍄 Champignons',faune:'🦋 Faune',divers:'🌾 Diverses'};
const CATSHORT={ligneux:'ligneux',herbace:'herbacée',champignon:'champignon',faune:'animal',divers:'flore'};
function catsAvail(){const s=[];SPECIES.forEach(sp=>{if(!s.includes(sp.cat))s.push(sp.cat);});return ['ligneux','herbace','champignon','faune','divers'].filter(c=>s.includes(c));}
const BYID={}; SPECIES.forEach(s=>BYID[s.id]=s);
const STEMBYNAME={}; SPECIES.forEach(s=>{STEMBYNAME[s.name]=s.stem;});
let stats=JSON.parse(localStorage.getItem(KEY)||'{}');
let flags=JSON.parse(localStorage.getItem(FLAGKEY)||'{}');
let tags=JSON.parse(localStorage.getItem(TAGKEY)||'{}');
let corr=JSON.parse(localStorage.getItem(CORRKEY)||'{}');
let cfg={scope:'ligneux',mode:'apprendre',aspect:'tout',qtype:'photo',diff:'facile'};
let current=null, session={s:0,c:0}, answered=false, detailSp=null, detailIdx=0, detailArr=[], detailPos=0, curImg=null;
const sortedScope=()=>scopeAll().slice().sort((a,b)=>a.name.localeCompare(b.name,'fr'));
const norm=s=>(s||'').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g,'').replace(/[^a-z0-9]/g,'');
const md=s=>(s||'').replace(/\*\*(.+?)\*\*/g,'<b>$1</b>');
const save=()=>localStorage.setItem(KEY,JSON.stringify(stats));
const savef=()=>localStorage.setItem(FLAGKEY,JSON.stringify(flags));
const savet=()=>localStorage.setItem(TAGKEY,JSON.stringify(tags));
const savec=()=>localStorage.setItem(CORRKEY,JSON.stringify(corr));
const stkey=(id,qt,asp)=>{qt=qt||cfg.qtype;if(qt==='fiche')return id+'::fiche';asp=asp||cfg.aspect;return (asp&&asp!=='tout')?id+'::'+asp:id;}; // photo+tout = clé nue (compat)
const st=(id,qt,asp)=>stats[stkey(id,qt,asp)]||{s:0,c:0,ko:false};
const known=(id,qt,asp)=>{const x=st(id,qt,asp);return x.s>3&&(x.c/x.s)>=0.75&&!x.ko;};
const effA=im=>{const o=tags[im.f];return o?(o.length?o:['divers']):im.a;};
const inScope=sp=>cfg.scope==='mixte'||sp.cat===cfg.scope;
const scopeAll=()=>SPECIES.filter(inScope);
const aspPresent=(sp,a)=>sp.imgs.some(im=>effA(im).includes(a));
const hasAspect=(sp,a)=>a==='tout'||aspPresent(sp,a);
const pool=()=>SPECIES.filter(sp=>inScope(sp)&&(cfg.mode==='apprendre'?!known(sp.id):known(sp.id))&&(cfg.qtype==='fiche'||hasAspect(sp,cfg.aspect)));
const shuffle=a=>{for(let i=a.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]];}return a;};
const row=(l,v)=>`<div class="stat"><span>${l}</span><b>${v}</b></div>`;
function aspectsAvail(){const set=new Set();scopeAll().forEach(sp=>sp.imgs.forEach(im=>effA(im).forEach(x=>set.add(x))));
  const order=['divers','feuille','ecorce','fruit','fleur','rameau','port'];const present=order.filter(a=>set.has(a));
  return present.filter(a=>a!=='divers').length?['tout',...present]:['tout'];}
function radios(key,items){const host=document.getElementById(key);host.innerHTML='';
  items.forEach(([val,lab])=>{const d=document.createElement('div');d.className='opt'+(cfg[key]===val?' sel':'');d.tabIndex=0;d.textContent=lab;d.dataset.val=val;
    d.onclick=()=>{cfg[key]=val;renderConfig();};d.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();d.onclick();}};host.appendChild(d);});}
function renderConfig(){radios('scope',catsAvail().map(c=>[c,CATLABEL[c]||c]).concat([['mixte','🎲 Tout']]));
  radios('mode',[['apprendre','📚 Apprendre'],['reviser','🔁 Réviser']]);
  const asp=aspectsAvail();if(!asp.includes(cfg.aspect))cfg.aspect='tout';
  radios('aspect',asp.map(a=>[a,ASPECTS[a]]));document.getElementById('asphint').style.display=asp.length>1?'none':'block';
  radios('qtype',[['photo','📷 Photo'],['fiche','📋 Fiche → devine']]);
  radios('diff',[['facile','🟢 QCM'],['sosies','🎭 Sosies'],['difficile','🎯 Saisie']]);renderStats();applyAspectFills();}
function aspectPct(asp){const inS=scopeAll().filter(sp=>asp==='tout'||aspPresent(sp,asp));if(!inS.length)return 0;
  return Math.round(100*inS.filter(sp=>known(sp.id,'photo',asp)).length/inS.length);}
function applyAspectFills(){document.querySelectorAll('#aspect .opt').forEach(el=>{const val=el.dataset.val;if(!val)return;
  const pct=aspectPct(val);el.style.backgroundImage='linear-gradient(to right,rgba(111,168,60,.30) '+pct+'%,transparent '+pct+'%)';
  el.textContent=(ASPECTS[val]||val)+(pct?'  '+pct+'%':'');el.title=pct+'% appris en photo';});}
function renderStats(){const inS=scopeAll(),qt=cfg.qtype,ql=qt==='fiche'?'fiche':('photo · '+(ASPECTS[cfg.aspect]||cfg.aspect));
  const seen=inS.filter(sp=>st(sp.id,qt).s>0);
  const reps=inS.reduce((a,sp)=>a+st(sp.id,qt).s,0),cor=inS.reduce((a,sp)=>a+st(sp.id,qt).c,0);
  const knCur=inS.filter(sp=>known(sp.id,qt)).length;
  const pct=reps?Math.round(100*cor/reps):0;
  document.getElementById('stats').innerHTML=row('Espèces du périmètre',inS.length)+
    row('Rencontrées ('+ql+')',seen.length)+row('Répétitions ('+ql+')',reps)+row('% correct ('+ql+')',pct+' %')+
    row('Connues ★ ('+ql+')',knCur+' / '+inS.length);}
function startQuiz(){if(pool().length===0){alert("Aucune espèce avec ces réglages (essaie « Tout » / change mode/aspect).");return;}
  session={s:0,c:0};show('quiz');navPush({v:'quiz'});document.getElementById('score').textContent='0 / 0';next();}
function next(){answered=false;window.scrollTo(0,0);document.getElementById('feedback').innerHTML='';
  const p=pool();if(p.length===0){navBack('home');return;}
  let pick;do{pick=p[Math.floor(Math.random()*p.length)];}while(p.length>1&&pick===current);current=pick;
  const imgbox=document.getElementById('imgbox'),fbox=document.getElementById('fichebox');
  if(cfg.qtype==='fiche'){imgbox.classList.add('hidden');fbox.classList.remove('hidden');fbox.innerHTML=ficheHTML(current);curImg=null;
    fbox.querySelectorAll('.fv.blur').forEach(el=>el.onclick=()=>el.classList.add('reveal'));}
  else{fbox.classList.add('hidden');imgbox.classList.remove('hidden');
    const imgs=cfg.aspect==='tout'?current.imgs:current.imgs.filter(im=>effA(im).includes(cfg.aspect));
    const chosen=imgs[Math.floor(Math.random()*imgs.length)];document.getElementById('pic').src=chosen.u;curImg=chosen;}
  const rb=document.getElementById('reportbtn');rb.style.display=cfg.qtype==='photo'?'block':'none';
  const rp=document.getElementById('reportpanel');rp.classList.add('hidden');rp.innerHTML='';
  document.getElementById('ctx').textContent=(cfg.mode==='apprendre'?'Apprendre':'Réviser')+' · '+(CATSHORT[current.cat]||current.cat)+(cfg.qtype==='photo'&&cfg.aspect!=='tout'?' · '+ASPECTS[cfg.aspect].toLowerCase():'')+(cfg.qtype==='fiche'?' · fiche':'')+' · reste '+p.length;
  const zone=document.getElementById('answerzone');
  if(cfg.diff!=='difficile'){let src;
    if(cfg.diff==='sosies'){const mates=new Set();(current.conf||[]).forEach(c=>c.mates.forEach(m=>mates.add(m)));
      const inScopeMates=scopeAll().filter(s=>s.id!==current.id&&mates.has(s.stem));
      const filler=scopeAll().filter(s=>s.cat===current.cat&&s.id!==current.id&&!mates.has(s.stem));
      src=shuffle(inScopeMates.slice()).concat(shuffle(filler.slice()));
    }else{const same=scopeAll().filter(s=>s.cat===current.cat&&s.id!==current.id);
      src=shuffle((same.length>=3?same:scopeAll().filter(s=>s.id!==current.id)).slice());}
    const opts=src.slice(0,3).map(s=>s.name);opts.push(current.name);shuffle(opts);
    zone.innerHTML='<div class="opts">'+opts.map(o=>`<button class="opt">${o}</button>`).join('')+'</div>';
    zone.querySelectorAll('.opt').forEach(b=>b.onclick=()=>answer(b.textContent===current.name,b));
  }else{const names=[...new Set(scopeAll().map(s=>s.name))].sort((a,b)=>a.localeCompare(b,'fr'));
    zone.innerHTML='<input class="ans" id="typed" list="names" placeholder="Tape le nom de l\'espèce…" autocomplete="off"><datalist id="names">'+names.map(n=>`<option value="${n}"></option>`).join('')+'</datalist><button class="go" id="valider" style="margin-top:8px">Valider</button>';
    document.getElementById('valider').onclick=()=>answer(norm(document.getElementById('typed').value)===norm(current.name));document.getElementById('typed').focus();}}
function answer(ok,btn){if(answered)return;answered=true;
  const k=stkey(current.id);const s=stats[k]||{s:0,c:0,ko:false};s.s++;if(ok)s.c++;if(!ok&&cfg.mode==='reviser')s.ko=true;if(ok)s.ko=false;
  stats[k]=s;save();session.s++;if(ok)session.c++;document.getElementById('score').textContent=session.c+' / '+session.s;if(btn)btn.classList.add('sel');
  const nk=known(current.id);
  document.getElementById('feedback').innerHTML=`<div class="fb ${ok?'ok':'no'}">${ok?'✅ Correct':'❌ Faux'}<div class="nm">${current.name}${nk?'<span class="badge">connue ★</span>':''}</div><div class="lt">${current.latin||''}</div>`+(current.note?`<div class="nt">${current.note}</div>`:'')+(current.conf&&current.conf.length?`<div class="nt">🔎 ${current.conf.map(c=>md(c.tip)).join('<br>')}</div>`:'')+`<button class="go" id="suiv" style="margin-top:10px">Espèce suivante →</button></div>`;
  document.getElementById('suiv').onclick=next;document.getElementById('suiv').focus();}
function chipState(id,a){if(flags[id]&&flags[id][a])return 'want';return aspPresent(BYID[id],a)?'ok':'missing';}
function toggleFlag(id,a){flags[id]=flags[id]||{};if(flags[id][a])delete flags[id][a];else flags[id][a]=1;if(!Object.keys(flags[id]).length)delete flags[id];savef();}
function chipsHTML(id){return CHIP_ASPECTS.map(a=>`<span class="chip ${chipState(id,a)}" data-id="${id}" data-a="${a}" tabindex="0">${ASPECTS[a]}</span>`).join('');}
function bindChips(root){root.querySelectorAll('.chip').forEach(c=>{const f=()=>{toggleFlag(c.dataset.id,c.dataset.a);c.className='chip '+chipState(c.dataset.id,c.dataset.a);};
  c.onclick=f;c.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();f();}};});}
function renderListScope(){const host=document.getElementById('listscope');
  const items=catsAvail().map(c=>[c,CATLABEL[c]||c]).concat([['mixte','Tout']]);host.innerHTML='';
  items.forEach(([val,lab])=>{const d=document.createElement('div');d.className='opt'+(cfg.scope===val?' sel':'');d.tabIndex=0;d.textContent=lab;
    d.onclick=()=>{cfg.scope=val;renderList();};d.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();d.onclick();}};host.appendChild(d);});}
function renderList(){renderListScope();const arr=sortedScope();
  document.getElementById('listcount').textContent=arr.length+' espèces';
  const statTxt=(id,qt,asp)=>{if(known(id,qt,asp))return '★';const x=st(id,qt,asp);return x.s>0?Math.round(100*x.c/x.s)+'%':'–';};
  document.getElementById('glist').innerHTML=arr.map(sp=>{
    const cls=(known(sp.id,'photo','tout')||known(sp.id,'fiche'))?'k':(st(sp.id,'photo','tout').s>0||st(sp.id,'fiche').s>0)?'p':'n';
    const txt='📷 '+statTxt(sp.id,'photo','tout')+' · 📋 '+statTxt(sp.id,'fiche');
    return `<div class="gcard"><div class="gthumb" data-id="${sp.id}" role="button" tabindex="0"><img loading="lazy" src="${sp.imgs[0].u}" alt=""><span class="gcount">${sp.imgs.length} 📷</span></div><div class="gmeta"><div class="gname">${sp.name}${sp.indic?' 🚩':''}</div><div class="glat">${sp.latin||''}</div><div class="gstat ${cls}">${txt}</div><div class="chips">${chipsHTML(sp.id)}</div></div></div>`;}).join('');
  const g=document.getElementById('glist');
  g.querySelectorAll('.gthumb').forEach(t=>{const o=()=>{openDetail(t.dataset.id);navPush({v:'detail',id:t.dataset.id});};t.onclick=o;t.onkeydown=e=>{if(e.key==='Enter')o();};});bindChips(g);}
function renderFields(sp){const f=sp.fields||{};document.getElementById('detailfields').innerHTML=
  FIELD_ORDER.filter(([k])=>f[k]).map(([k,lab])=>`<div class="frow"><div class="fl">${lab}</div><div class="fv">${f[k]}</div></div>`).join('');}
const FICHE_BLUR=['comestible','notes'];
function ficheHTML(sp){const f=sp.fields||{};const rows=FIELD_ORDER.filter(([k])=>f[k]).map(([k,lab])=>`<div class="frow"><div class="fl">${lab}</div><div class="fv${FICHE_BLUR.includes(k)?' blur':''}">${f[k]}</div></div>`).join('');
  const anyBlur=FIELD_ORDER.some(([k])=>FICHE_BLUR.includes(k)&&f[k]);
  return `<div class="fichecard"><div class="qtag">D'après ces caractères (${CATSHORT[sp.cat]||sp.cat}), quelle espèce ?</div>${rows||'<div class="fv">(fiche peu détaillée)</div>'}${anyBlur?'<div class="fichehint">Comestible &amp; Notes sont floutés (indices) — clique pour révéler.</div>':''}</div>`;}
function openDetail(id){detailSp=BYID[id];show('detail');window.scrollTo(0,0);
  detailArr=sortedScope();detailPos=detailArr.findIndex(s=>s.id===id);
  document.getElementById('prevsp').disabled=detailPos<=0;
  document.getElementById('nextsp').disabled=detailPos<0||detailPos>=detailArr.length-1;
  document.getElementById('detailname').innerHTML=detailSp.name+(detailSp.indic?' <span class="indic">🚩 indicatrice</span>':'');
  document.getElementById('detaillat').textContent=detailSp.latin||'';
  document.getElementById('detailcount').textContent=detailSp.imgs.length+' photo(s)';
  const strip=document.getElementById('detailstrip');
  strip.innerHTML=detailSp.imgs.map((im,i)=>`<img src="${im.u}" data-i="${i}" alt="">`).join('');
  strip.querySelectorAll('img').forEach(im=>im.onclick=()=>setMain(+im.dataset.i));
  renderFields(detailSp);document.getElementById('detailchips').innerHTML=chipsHTML(id);bindChips(document.getElementById('detailchips'));
  setMain(0);}
function setMain(i){detailIdx=i;const im=detailSp.imgs[i];document.getElementById('detailpic').src=im.u;
  document.getElementById('detailasp').textContent='Aspect : '+effA(im).map(a=>ASPECTS[a]||a).join(', ')+'  ('+(i+1)+'/'+detailSp.imgs.length+')';
  document.getElementById('detailstrip').querySelectorAll('img').forEach((x,j)=>x.classList.toggle('sel',j===i));
  renderTagger(im);renderDetailMis(im);}
function renderTagger(im){const eff=new Set(effA(im));
  const t=document.getElementById('tagger');t.innerHTML=CHIP_ASPECTS.map(a=>`<button class="tagbtn ${eff.has(a)?'active':''}" data-a="${a}">${ASPECTS[a]}</button>`).join('');
  t.querySelectorAll('.tagbtn').forEach(b=>b.onclick=()=>{const cur=new Set(tags[im.f]||im.a);cur.has(b.dataset.a)?cur.delete(b.dataset.a):cur.add(b.dataset.a);cur.delete('divers');tags[im.f]=[...cur];savet();setMain(detailIdx);
    document.getElementById('detailchips').innerHTML=chipsHTML(detailSp.id);bindChips(document.getElementById('detailchips'));});}
function misattribHTML(im){const c=corr[im.f]||{};
  let extra='';
  if(c.reassign)extra='<div class="taghint">→ reclassée vers <b>'+c.reassign+'</b> · <a href="#" data-cancel style="color:var(--red)">annuler</a></div>';
  return '<div style="margin-top:8px"><div class="taghint">Cette photo ne correspond pas à l\'espèce ?</div>'
    +'<div class="tagger"><button class="tagbtn '+(c.remove?'active':'')+'" data-act="remove">🗑 Photo à retirer</button></div>'
    +'<input class="ans" list="allnames" placeholder="…ou reclasser vers une autre espèce" data-reassign style="margin-top:6px">'+extra+'</div>';}
function bindMisattrib(root,im,after){
  const rm=root.querySelector('[data-act="remove"]');
  if(rm)rm.onclick=()=>{corr[im.f]=corr[im.f]||{};if(corr[im.f].remove){delete corr[im.f].remove;}else{corr[im.f]={remove:1};}if(!Object.keys(corr[im.f]).length)delete corr[im.f];savec();after();};
  const ri=root.querySelector('[data-reassign]');
  if(ri)ri.onchange=()=>{const st=STEMBYNAME[ri.value.trim()];if(st){corr[im.f]={reassign:st};savec();after();}else if(ri.value.trim()){alert('Espèce inconnue : '+ri.value);}};
  const cx=root.querySelector('[data-cancel]');
  if(cx)cx.onclick=e=>{e.preventDefault();delete corr[im.f];savec();after();};}
function renderReport(im){const host=document.getElementById('reportpanel');if(!im){host.innerHTML='';return;}
  const eff=new Set(effA(im));
  host.innerHTML='<div class="fichecard"><div class="taghint">Aspect(s) de cette photo (corrige si c\'est faux) :</div>'
   +'<div class="tagger" id="rtag">'+CHIP_ASPECTS.map(a=>'<button class="tagbtn '+(eff.has(a)?'active':'')+'" data-a="'+a+'">'+ASPECTS[a]+'</button>').join('')+'</div>'
   +misattribHTML(im)+'<div class="taghint" style="margin-top:6px">Tes signalements partent dans la même Pull Request (bouton « Publier » de l\'atlas).</div></div>';
  host.querySelectorAll('#rtag .tagbtn').forEach(b=>b.onclick=()=>{const cur=new Set(tags[im.f]||im.a);cur.has(b.dataset.a)?cur.delete(b.dataset.a):cur.add(b.dataset.a);cur.delete('divers');tags[im.f]=[...cur];savet();renderReport(im);});
  bindMisattrib(host,im,()=>renderReport(im));}
function renderDetailMis(im){const host=document.getElementById('detailmis');if(!host)return;host.innerHTML=misattribHTML(im);bindMisattrib(host,im,()=>renderDetailMis(im));}
function showExport(txt){const ta=document.getElementById('expout');ta.classList.remove('hidden');ta.value=txt;ta.focus();ta.select();
  try{document.execCommand('copy');}catch(e){}try{if(navigator.clipboard)navigator.clipboard.writeText(txt);}catch(e){}}
function exportGaps(){const lines=[];scopeAll().forEach(sp=>{const g=CHIP_ASPECTS.filter(a=>chipState(sp.id,a)==='want');
  if(g.length)lines.push(sp.stem+' ('+sp.name+') : '+g.map(a=>ASPECTS[a]).join(', '));});
  showExport(lines.length?lines.join('\n'):'(aucune demande — clique des puces ou « Marquer les manques »)');}
function exportTags(){const lines=Object.keys(tags).map(f=>f+'\t'+(tags[f].length?tags[f].join(','):'divers'));
  showExport(lines.length?lines.join('\n'):'(aucun tag modifié — tague des photos dans le détail)');}
function publishToGitHub(){
  const actions=[];
  Object.keys(tags).forEach(f=>actions.push('tag\t'+f+'\t'+(tags[f].length?tags[f].join(','):'divers')));
  Object.keys(corr).forEach(f=>{const c=corr[f]||{};if(c.remove)actions.push('remove\t'+f+'\t');else if(c.reassign)actions.push('reassign\t'+f+'\t'+c.reassign);});
  const gapLines=[];
  Object.keys(flags).forEach(id=>{const sp=BYID[id];if(!sp)return;const a=Object.keys(flags[id]||{});
    if(a.length)gapLines.push('# '+sp.name+' ('+sp.stem+') : '+a.map(x=>ASPECTS[x]||x).join(', '));});
  if(!actions.length&&!gapLines.length){alert('Rien à publier — corrige un aspect, signale une photo, ou coche des manques (oranges).');return;}
  const stamp=new Date().toISOString().slice(0,19).replace(/[:T]/g,'-');
  const rnd=Math.random().toString(36).slice(2,7);
  let body="# Contribution depuis l'app ("+stamp+")\n";
  if(gapLines.length)body+='#\n# Manques signales (photos a ajouter) :\n'+gapLines.join('\n')+'\n';
  body+='#\naction\tfichier\tvaleur\n'+(actions.length?actions.join('\n'):'# (aucune action)')+'\n';
  const fn='contributions/app-'+stamp+'-'+rnd+'.tsv';
  const url='https://github.com/'+REPO+'/new/main?filename='+encodeURIComponent(fn)+'&value='+encodeURIComponent(body);
  const a=document.createElement('a');a.href=url;a.target='_blank';a.rel='noopener';document.body.appendChild(a);a.click();a.remove();}
function markGaps(){scopeAll().forEach(sp=>CHIP_ASPECTS.forEach(a=>{if(!aspPresent(sp,a)){flags[sp.id]=flags[sp.id]||{};flags[sp.id][a]=1;}}));savef();renderList();}
function clearMarks(){flags={};savef();renderList();document.getElementById('expout').classList.add('hidden');}
const CRITERIA=[
 {id:'fixn',q:"Fixe l'azote ?",field:'fixn',has:sp=>('fixn' in sp.fields),ok:sp=>/rhizobium|frankia/i.test(sp.fields.fixn||'')},
 {id:'soleil',q:'Aime le plein soleil ?',field:'lumiere',has:sp=>('lumiere' in sp.fields),ok:sp=>/☀/.test(sp.fields.lumiere||'')},
 {id:'ombre',q:"Supporte l'ombre ?",field:'lumiere',has:sp=>('lumiere' in sp.fields),ok:sp=>/☾/.test(sp.fields.lumiere||'')},
 {id:'vivace',q:'Est-ce une vivace ?',field:'cycle',has:sp=>('cycle' in sp.fields),ok:sp=>/vivace/i.test(sp.fields.cycle||'')},
 {id:'fixateur',q:'A un rôle fixateur ?',field:'fonction',has:sp=>('fonction' in sp.fields),ok:sp=>/(^|[^a-z])fix/i.test(sp.fields.fonction||'')},
 {id:'cs',q:'Est-ce un couvre-sol ?',field:'fonction',has:sp=>('fonction' in sp.fields),ok:sp=>/(^|[^a-z])cs([^a-z]|$)/i.test(sp.fields.fonction||'')},
 {id:'pionnier',q:'Espèce pionnière ?',field:'succession',has:sp=>('succession' in sp.fields),ok:sp=>/pion/i.test(sp.fields.succession||'')},
 {id:'ligneux',q:'Est-ce un ligneux (arbre/arbuste) ?',field:null,only:'mixte',has:sp=>true,ok:sp=>sp.cat==='ligneux'},
];
let critC=null,critQueue=[],critPos=0,critSess={s:0,c:0},critScope='ligneux',critAnim=false;
function critScopes(){return ['ligneux','herbace','champignon','faune','divers'].filter(c=>SPECIES.some(s=>s.cat===c)).concat(['mixte']);}
function renderCritScope(){const host=document.getElementById('critscope');host.innerHTML='';
  critScopes().forEach(v=>{const d=document.createElement('div');d.className='opt'+(critScope===v?' sel':'');d.tabIndex=0;d.textContent=v==='mixte'?'🎲 Tout':(CATLABEL[v]||v);d.onclick=()=>{critScope=v;renderCritScope();renderCritList();};host.appendChild(d);});}
function critAvail(cr){return SPECIES.filter(sp=>(critScope==='mixte'||sp.cat===critScope)&&cr.has(sp));}
function renderCritList(){const host=document.getElementById('critlist');host.innerHTML='';
  CRITERIA.forEach(cr=>{if(cr.only&&cr.only!==critScope)return;const n=critAvail(cr).length;if(n<4)return;
    const d=document.createElement('div');d.className='opt';d.tabIndex=0;d.textContent=cr.q+' ('+n+')';d.onclick=()=>startCrit(cr);host.appendChild(d);});
  if(!host.children.length)host.innerHTML='<div class="hint">Aucun critère objectif pour cette catégorie — essaie Ligneux, Herbacées ou Tout.</div>';}
function openCrit(){show('crit');document.getElementById('critchoose').classList.remove('hidden');document.getElementById('critplay').classList.add('hidden');document.getElementById('critscore').textContent='';renderCritScope();renderCritList();window.scrollTo(0,0);}
function startCrit(cr){critC=cr;critQueue=shuffle(critAvail(cr).slice());critPos=0;critSess={s:0,c:0};
  document.getElementById('critchoose').classList.add('hidden');document.getElementById('critplay').classList.remove('hidden');
  document.getElementById('critq').textContent=cr.q;document.getElementById('critscore').textContent='0 / 0';
  document.getElementById('critfb').innerHTML='';document.getElementById('critbtns').style.display='';critFace();}
function critReset(){const c=document.getElementById('critcard');c.style.transition='transform .15s,opacity .15s';c.style.transform='';c.style.opacity=1;}
function critFace(){const card=document.getElementById('critcard'),back=document.getElementById('critback');
  if(critPos>=critQueue.length){card.style.display='none';back.style.display='none';document.getElementById('critbtns').style.display='none';
    document.getElementById('critfb').innerHTML='<div class="fb ok">Terminé ! <b>'+critSess.c+' / '+critSess.s+'</b> bonnes réponses.<button class="go" id="critagain" style="margin-top:10px">Choisir un autre critère</button></div>';
    document.getElementById('critagain').onclick=openCrit;return;}
  const cur=critQueue[critPos],nxt=critQueue[critPos+1];
  card.style.display='';card.style.transition='none';card.style.transform='';card.style.opacity=1;
  document.getElementById('critpic').src=cur.imgs[0].u;document.getElementById('critname').textContent=cur.name;
  if(nxt){back.style.display='';document.getElementById('critpicB').src=nxt.imgs[0].u;document.getElementById('critnameB').textContent=nxt.name;}else{back.style.display='none';}
  void card.offsetWidth;}
function critCommit(yes){const sp=critQueue[critPos],truth=critC.ok(sp),ok=(yes===truth);
  critSess.s++;if(ok)critSess.c++;document.getElementById('critscore').textContent=critSess.c+' / '+critSess.s;
  const val=critC.field?(sp.fields[critC.field]||'—'):(CATSHORT[sp.cat]||sp.cat);
  document.getElementById('critfb').innerHTML='<div class="critbanner '+(ok?'ok':'no')+'">'+(ok?'✅':'❌')+' '+sp.name+' : <b>'+(truth?'oui':'non')+'</b> <span class="lt">('+val+')</span></div>';
  critPos++;critFace();}
function critSwipeOut(yes){if(critAnim||!critC||critPos>=critQueue.length)return;critAnim=true;
  const c=document.getElementById('critcard');c.style.transition='transform .2s,opacity .2s';c.style.transform='translateX('+(yes?560:-560)+'px) rotate('+(yes?14:-14)+'deg)';c.style.opacity=0;
  setTimeout(()=>{critCommit(yes);critAnim=false;},190);}
function show(id){['home','quiz','list','detail','crit'].forEach(s=>document.getElementById(s).classList.toggle('hidden',s!==id));
  const h=document.querySelector('.hero');if(h)h.style.display=(id==='home')?'':'none';}
function toHome(){show('home');renderConfig();window.scrollTo(0,0);}
// Historique navigateur : bouton Retour = vue précédente (fonctionne là où l'History API est dispo,
// ex. GitHub Pages ; repli sur navigation directe si bloquée, ex. iframe d'artifact à origine opaque).
const HISTOK=(function(){try{history.replaceState({v:'home'},'');return true;}catch(e){return false;}})();
function navPush(st){if(HISTOK){try{history.pushState(st,'');}catch(e){}}}
function navRepl(st){if(HISTOK){try{history.replaceState(st,'');}catch(e){}}}
function navBack(fallbackView){if(HISTOK){history.back();}else{renderView(fallbackView);}}
function renderView(v,id){
  if(v==='list'){show('list');renderList();
    const key=id||(detailSp&&detailSp.id);const el=key&&document.querySelector('.gthumb[data-id="'+key+'"]');
    if(el){el.scrollIntoView({block:'center'});}else{window.scrollTo(0,0);}}
  else if(v==='detail'){openDetail(id||(detailSp&&detailSp.id));}
  else if(v==='quiz'){show('quiz');window.scrollTo(0,0);}
  else if(v==='crit'){openCrit();}
  else{show('home');renderConfig();window.scrollTo(0,0);}}
if(HISTOK)window.addEventListener('popstate',function(e){const st=(e.state&&e.state.v)?e.state:{v:'home'};renderView(st.v,st.id);});
function makeBackup(){return JSON.stringify({v:1,app:'atlas-quiz',stats:stats,tags:tags,flags:flags});}
function showBackupBox(txt){const ta=document.getElementById('backupbox');ta.classList.remove('hidden');ta.value=txt;ta.focus();ta.select();
  try{document.execCommand('copy');}catch(e){}try{if(navigator.clipboard)navigator.clipboard.writeText(txt);}catch(e){}}
function doBackup(){const txt=makeBackup();showBackupBox(txt);
  try{const blob=new Blob([txt],{type:'application/json'});const url=URL.createObjectURL(blob);const a=document.createElement('a');
    a.href=url;a.download='progression-atlas.json';document.body.appendChild(a);a.click();setTimeout(()=>{a.remove();URL.revokeObjectURL(url);},0);}catch(e){}}
function restore(txt){let o;try{o=JSON.parse(txt);}catch(e){alert('Sauvegarde illisible ❌');return;}
  if(o&&o.stats){stats=o.stats;save();}if(o&&o.tags){tags=o.tags;savet();}if(o&&o.flags){flags=o.flags;savef();}
  alert('Progression restaurée ✅');renderConfig();}
document.getElementById('start').onclick=startQuiz;
document.getElementById('back').onclick=()=>navBack('home');
document.getElementById('showlist').onclick=()=>{detailSp=null;renderView('list');navPush({v:'list'});};
document.getElementById('backlist').onclick=()=>navBack('home');
document.getElementById('backdetail').onclick=()=>navBack('list');
document.getElementById('prevsp').onclick=()=>{if(detailPos>0){const id=detailArr[detailPos-1].id;openDetail(id);navRepl({v:'detail',id:id});}};
document.getElementById('nextsp').onclick=()=>{if(detailPos>=0&&detailPos<detailArr.length-1){const id=detailArr[detailPos+1].id;openDetail(id);navRepl({v:'detail',id:id});}};
document.getElementById('markgaps').onclick=markGaps;
document.getElementById('clearmarks').onclick=clearMarks;
document.getElementById('doexport').onclick=exportGaps;
document.getElementById('exporttags').onclick=exportTags;
document.getElementById('publishpr').onclick=publishToGitHub;
document.getElementById('expprog').onclick=doBackup;
document.getElementById('impfilebtn').onclick=()=>document.getElementById('impfile').click();
document.getElementById('impfile').onchange=e=>{const f=e.target.files[0];if(!f)return;const r=new FileReader();r.onload=()=>restore(String(r.result));r.readAsText(f);e.target.value='';};
document.getElementById('restorebtn').onclick=()=>{const t=document.getElementById('backupbox').value.trim();if(t)restore(t);else{document.getElementById('backupbox').classList.remove('hidden');alert('Colle d\'abord une sauvegarde dans le cadre.');}};
document.getElementById('reportbtn').onclick=()=>{const p=document.getElementById('reportpanel');
  if(p.classList.contains('hidden')){p.classList.remove('hidden');renderReport(curImg);}else{p.classList.add('hidden');}};
document.getElementById('reset').onclick=()=>{if(confirm('Effacer toute la progression (pas les tags/corrections) ?')){stats={};save();renderConfig();}};
document.getElementById('showcrit').onclick=()=>{openCrit();navPush({v:'crit'});};
document.getElementById('backcrit').onclick=()=>navBack('home');
document.getElementById('crityes').onclick=()=>critSwipeOut(true);
document.getElementById('critno').onclick=()=>critSwipeOut(false);
(function(){const card=document.getElementById('critcard');let x0=0,dx=0,drag=false;
  card.addEventListener('pointerdown',e=>{if(critAnim)return;drag=true;x0=e.clientX;dx=0;try{card.setPointerCapture(e.pointerId);}catch(_){}});
  card.addEventListener('pointermove',e=>{if(!drag)return;dx=e.clientX-x0;card.style.transform='translateX('+dx+'px) rotate('+(dx/25)+'deg)';card.style.opacity=(1-Math.min(Math.abs(dx)/500,.35));});
  card.addEventListener('pointerup',()=>{if(!drag)return;drag=false;if(Math.abs(dx)>90){critSwipeOut(dx>0);}else{critReset();}dx=0;});})();
window.addEventListener('keydown',e=>{if(document.getElementById('crit').classList.contains('hidden'))return;
  if(document.getElementById('critplay').classList.contains('hidden'))return;
  if(e.key==='ArrowRight'){e.preventDefault();critSwipeOut(true);}else if(e.key==='ArrowLeft'){e.preventDefault();critSwipeOut(false);}});
(function(){const dl=document.createElement('datalist');dl.id='allnames';
  SPECIES.forEach(s=>{const o=document.createElement('option');o.value=s.name;dl.appendChild(o);});document.body.appendChild(dl);})();
renderConfig();
"""

def assemble(data, standalone):
    js = JS.replace("/*__DATA__*/", json.dumps(data, ensure_ascii=False))
    if standalone:
        head = ('<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">'
                '<title>Atlas &amp; quiz des espèces</title><style>' + CSS + '</style>')
        return "<!doctype html><html lang=\"fr\"><head>" + head + "</head><body>" + BODY + "<script>" + js + "</script></body></html>"
    return '<title>Atlas &amp; quiz des espèces</title><style>' + CSS + '</style>' + BODY + "<script>" + js + "</script>"

def main():
    species, seen = [], set()
    for path, cat in ATLASES:
        got = parse_atlas(path, cat, seen)
        print("%-38s : %d espèces" % (path, len(got)))
        species += got
    species = apply_corrections(species)
    print("TOTAL : %d espèces, %d images, sidecar=%d" % (len(species), sum(len(s["paths"]) for s in species), len(SIDE)))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(assemble(to_data(species, b64_asis), True))
    # Artifact = version COMPLÈTE (toutes les photos, aucun plafond) ; on baisse la
    # résolution/qualité juste assez pour rester sous la limite 16 Mo d'Artifact.
    TARGET = 15_500_000
    ladder = [(320, 60), (300, 58), (280, 55), (260, 52), (240, 50), (220, 48), (200, 45)]
    art_html, chosen, chosen_data = None, ladder[-1], None
    for px, q in ladder:
        data_c = to_data(species, lambda p: b64_small(p, px, q), cap=None)
        html = assemble(data_c, False)
        n = len(html.encode("utf-8"))
        print("  artifact complet @ %dpx q%d : %.1f Mo" % (px, q, n / 1e6))
        art_html, chosen, chosen_data = html, (px, q), data_c
        if n <= TARGET:
            break
    with open(OUT_ART, "w", encoding="utf-8") as f:
        f.write(art_html)
    # Fichier « à partager » = standalone (wrappers HTML complets) avec les mêmes images compressées.
    with open(OUT_SHARE, "w", encoding="utf-8") as f:
        f.write(assemble(chosen_data, True))
    if os.path.exists(TMP):
        os.remove(TMP)
    print("Standalone pleine réso : %.1f Mo   Artifact (%dpx q%d) : %.1f Mo   À partager : %.1f Mo" %
          (os.path.getsize(OUT)/1e6, chosen[0], chosen[1], os.path.getsize(OUT_ART)/1e6, os.path.getsize(OUT_SHARE)/1e6))

if __name__ == "__main__":
    main()
