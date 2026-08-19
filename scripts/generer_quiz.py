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

def load_sidecar():
    """Aspects annotés : img/quiz-extra/_aspects.tsv + toutes les contributions/*.tsv
    (ces dernières, plus récentes, écrasent). Format : « nom_fichier<TAB>aspect1,aspect2 »."""
    d = {}
    files = []
    p = os.path.join(EXTRA, "_aspects.tsv")
    if os.path.exists(p):
        files.append(p)
    cdir = os.path.join(BASE, "contributions")
    if os.path.isdir(cdir):
        files += sorted(glob.glob(os.path.join(cdir, "*.tsv")))
    for fp in files:
        for line in open(fp, encoding="utf-8"):
            line = line.rstrip("\n")
            if not line or line.startswith("#") or "\t" not in line:
                continue
            fn, asp = line.split("\t", 1)
            if fn.strip().lower() in ("fichier", "file"):  # ligne d'en-tête
                continue
            d[fn.strip()] = [a.strip() for a in re.split(r"[,;]", asp) if a.strip()]
    return d
SIDE = load_sidecar()

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
                   ("note", "notes")]:
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

def to_data(species, enc, cap=None):
    res = []
    for s in species:
        paths = s["paths"]
        if cap and len(paths) > cap:  # plafond version en ligne : vignette + extras (annotés d'abord)
            extras = sorted(paths[1:], key=lambda p: 0 if [a for a in aspect_of(p, s["stem"]) if a != "divers"] else 1)
            paths = paths[:1] + extras[:cap - 1]
        imgs = [{"u": enc(p), "a": aspect_of(p, s["stem"]), "f": os.path.basename(p)} for p in paths]
        res.append({"id": s["id"], "stem": s["stem"], "name": s["name"], "latin": s["latin"],
                    "note": s["note"], "cat": s["cat"], "fields": s["fields"], "imgs": imgs,
                    "indic": ("indic" in (s["note"] or "").lower())})
    return res

CSS = r"""
:root{--bg:#FBFAF7;--card:#fff;--ink:#2C2C2A;--soft:#5F5E5A;--line:#E4E1D8;--green:#6FA83C;--greenD:#4E8542;--amber:#C99A3B;--red:#C0392B;--blue:#5F84A8;}
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,'Helvetica Neue',Arial,sans-serif;background:var(--bg);color:var(--ink);}
.wrap{max-width:640px;margin:0 auto;padding:16px 14px 40px;}
h1{font-size:20px;margin:6px 0 2px;text-align:center}
h2{font-size:18px;margin:8px 0 0;text-align:center}
.sub{color:var(--soft);text-align:center;font-size:13px;margin-bottom:14px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px;margin:12px 0;}
.grouplab{font-size:12px;font-weight:700;color:var(--soft);text-transform:uppercase;letter-spacing:.03em;margin:2px 0 8px}
.hint{font-size:11px;color:var(--soft);margin-top:6px;font-style:italic}
.opts{display:flex;flex-wrap:wrap;gap:8px}
.opt{flex:1 1 45%;padding:11px 10px;border:1.5px solid var(--line);border-radius:10px;background:#fff;color:var(--ink);font-size:15px;cursor:pointer;text-align:center;}
.opt.sel{border-color:var(--green);background:#EEF5E1;font-weight:700}
.opt:focus-visible,button:focus-visible,input:focus-visible,.chip:focus-visible{outline:2px solid var(--greenD);outline-offset:2px}
button.go{width:100%;padding:14px;border:none;border-radius:12px;background:var(--greenD);color:#fff;font-size:17px;font-weight:700;cursor:pointer;margin-top:6px}
button.go.alt{background:var(--blue)}
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
.mini{font-size:13px;color:var(--soft);font-variant-numeric:tabular-nums}.pill{font-size:12px;color:var(--soft)}.hidden{display:none}
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
"""

BODY = r"""
<div class="wrap">
<h1>🌳 Atlas & quiz des espèces</h1>
<div class="sub">identification — progression sauvegardée sur cet appareil</div>
<div id="home">
  <button class="go alt" id="showlist" style="margin-top:0">📋 Explorer l'atlas &amp; les photos</button>
  <div class="card">
    <div class="grouplab">Que réviser ?</div><div class="opts" id="scope"></div>
    <div class="grouplab" style="margin-top:14px">Mode</div><div class="opts" id="mode"></div>
    <div class="grouplab" style="margin-top:14px">Sur quoi ?</div><div class="opts" id="aspect"></div>
    <div class="hint" id="asphint">Tague des photos (écorce, feuille…) pour filtrer ici.</div>
    <div class="grouplab" style="margin-top:14px">Question</div><div class="opts" id="qtype"></div>
    <div class="grouplab" style="margin-top:14px">Difficulté</div><div class="opts" id="diff"></div>
    <button class="go" id="start">Commencer ▶</button>
  </div>
  <div class="card"><div class="grouplab">Tes statistiques</div><div id="stats"></div></div>
  <div class="card"><div class="grouplab">Sauvegarde de ma progression</div>
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
    <div class="qa" id="answerzone"></div><div id="feedback"></div></div>
</div>
<div id="list" class="hidden">
  <div class="topbar"><button class="ghost" id="backlist">← Accueil</button><div class="mini" id="listcount"></div></div>
  <div class="grouplab">Catégorie</div><div class="opts" id="listscope" style="margin-bottom:10px"></div>
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
    <div class="taghint">Clique un aspect pour (dé)tagger CETTE photo (effet immédiat). « Exporter mes tags » dans l'atlas → tu me l'envoies, je fige.</div>
    <div class="strip" id="detailstrip"></div>
    <div class="fields" id="detailfields"></div>
    <div class="chips" id="detailchips" style="justify-content:center;margin-top:6px"></div>
  </div>
</div>
<div class="credit">Photos : Wikimedia Commons &amp; iNaturalist (licences libres / CC).<br>
<a href="https://github.com/iribarnesy/atlas-especes" target="_blank" rel="noopener">Contribuer ou télécharger les atlas (Markdown) sur GitHub ↗</a></div>
</div>
"""

JS = r"""
const SPECIES = /*__DATA__*/;
const KEY='quizEspeces_v1', FLAGKEY='photoFlags_v1', TAGKEY='tagOverrides_v1';
const REPO='iribarnesy/atlas-especes';
const ASPECTS={tout:'Tout',divers:'Divers',feuille:'Feuille',ecorce:'Écorce',fruit:'Fruit',fleur:'Fleur',rameau:"Rameau d'hiver",port:'Port'};
const CHIP_ASPECTS=['feuille','ecorce','fruit','fleur','port'];
const FIELD_ORDER=[['groupe','Groupe'],['type','Type'],['cycle','Cycle'],['famille','Famille'],['ecologie','Écologie'],['hote','Arbre / substrat'],['habitat','Habitat'],['role','Rôle'],['regime','Régime'],['saison','Saison'],['lumiere','Lumière'],['fixn','Fixation N'],['mycorhize','Mycorhize'],['succession','Succession'],['strate','Strate'],['fonction','Fonction'],['comestible','Comestible'],['notes','Notes']];
const CATLABEL={ligneux:'Ligneux',herbace:'Herbacées',champignon:'Champignons',faune:'Faune',divers:'Diverses'};
const CATSHORT={ligneux:'ligneux',herbace:'herbacée',champignon:'champignon',faune:'animal',divers:'flore'};
function catsAvail(){const s=[];SPECIES.forEach(sp=>{if(!s.includes(sp.cat))s.push(sp.cat);});return ['ligneux','herbace','champignon','faune','divers'].filter(c=>s.includes(c));}
const BYID={}; SPECIES.forEach(s=>BYID[s.id]=s);
let stats=JSON.parse(localStorage.getItem(KEY)||'{}');
let flags=JSON.parse(localStorage.getItem(FLAGKEY)||'{}');
let tags=JSON.parse(localStorage.getItem(TAGKEY)||'{}');
let cfg={scope:'ligneux',mode:'apprendre',aspect:'tout',qtype:'photo',diff:'facile'};
let current=null, session={s:0,c:0}, answered=false, detailSp=null, detailIdx=0, detailArr=[], detailPos=0;
const sortedScope=()=>scopeAll().slice().sort((a,b)=>a.name.localeCompare(b.name,'fr'));
const norm=s=>(s||'').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g,'').replace(/[^a-z0-9]/g,'');
const save=()=>localStorage.setItem(KEY,JSON.stringify(stats));
const savef=()=>localStorage.setItem(FLAGKEY,JSON.stringify(flags));
const savet=()=>localStorage.setItem(TAGKEY,JSON.stringify(tags));
const stkey=(id,qt)=>((qt||cfg.qtype)==='fiche')?id+'::fiche':id; // photo = clé nue (compat progression existante)
const st=(id,qt)=>stats[stkey(id,qt)]||{s:0,c:0,ko:false};
const known=(id,qt)=>{const x=st(id,qt);return x.s>3&&(x.c/x.s)>=0.75&&!x.ko;};
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
  items.forEach(([val,lab])=>{const d=document.createElement('div');d.className='opt'+(cfg[key]===val?' sel':'');d.tabIndex=0;d.textContent=lab;
    d.onclick=()=>{cfg[key]=val;renderConfig();};d.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();d.onclick();}};host.appendChild(d);});}
function renderConfig(){radios('scope',catsAvail().map(c=>[c,CATLABEL[c]||c]).concat([['mixte','Tout']]));
  radios('mode',[['apprendre','Apprendre'],['reviser','Réviser']]);
  const asp=aspectsAvail();if(!asp.includes(cfg.aspect))cfg.aspect='tout';
  radios('aspect',asp.map(a=>[a,ASPECTS[a]]));document.getElementById('asphint').style.display=asp.length>1?'none':'block';
  radios('qtype',[['photo','Photo'],['fiche','Fiche → devine']]);
  radios('diff',[['facile','Facile (4 choix)'],['difficile','Difficile (liste)']]);renderStats();}
function renderStats(){const inS=scopeAll(),qt=cfg.qtype,ql=qt==='fiche'?'fiche':'photo';
  const seen=inS.filter(sp=>st(sp.id,qt).s>0);
  const reps=inS.reduce((a,sp)=>a+st(sp.id,qt).s,0),cor=inS.reduce((a,sp)=>a+st(sp.id,qt).c,0);
  const knP=inS.filter(sp=>known(sp.id,'photo')).length,knF=inS.filter(sp=>known(sp.id,'fiche')).length;
  const pct=reps?Math.round(100*cor/reps):0;
  document.getElementById('stats').innerHTML=row('Espèces du périmètre',inS.length)+
    row('Rencontrées ('+ql+')',seen.length)+row('Répétitions ('+ql+')',reps)+row('% correct ('+ql+')',pct+' %')+
    row('Connues en photo 📷★',knP+' / '+inS.length)+row('Connues en fiche 📋★',knF+' / '+inS.length);}
function startQuiz(){if(pool().length===0){alert("Aucune espèce avec ces réglages (essaie « Tout » / change mode/aspect).");return;}
  session={s:0,c:0};show('quiz');document.getElementById('score').textContent='0 / 0';next();}
function next(){answered=false;window.scrollTo(0,0);document.getElementById('feedback').innerHTML='';
  const p=pool();if(p.length===0){toHome();return;}
  let pick;do{pick=p[Math.floor(Math.random()*p.length)];}while(p.length>1&&pick===current);current=pick;
  const imgbox=document.getElementById('imgbox'),fbox=document.getElementById('fichebox');
  if(cfg.qtype==='fiche'){imgbox.classList.add('hidden');fbox.classList.remove('hidden');fbox.innerHTML=ficheHTML(current);
    fbox.querySelectorAll('.fv.blur').forEach(el=>el.onclick=()=>el.classList.add('reveal'));}
  else{fbox.classList.add('hidden');imgbox.classList.remove('hidden');
    const imgs=cfg.aspect==='tout'?current.imgs:current.imgs.filter(im=>effA(im).includes(cfg.aspect));
    document.getElementById('pic').src=imgs[Math.floor(Math.random()*imgs.length)].u;}
  document.getElementById('ctx').textContent=(cfg.mode==='apprendre'?'Apprendre':'Réviser')+' · '+(CATSHORT[current.cat]||current.cat)+(cfg.qtype==='photo'&&cfg.aspect!=='tout'?' · '+ASPECTS[cfg.aspect].toLowerCase():'')+(cfg.qtype==='fiche'?' · fiche':'')+' · reste '+p.length;
  const zone=document.getElementById('answerzone');
  if(cfg.diff==='facile'){const same=scopeAll().filter(s=>s.cat===current.cat&&s.id!==current.id);
    const src=same.length>=3?same:scopeAll().filter(s=>s.id!==current.id);
    const opts=shuffle(src.slice()).slice(0,3).map(s=>s.name);opts.push(current.name);shuffle(opts);
    zone.innerHTML='<div class="opts">'+opts.map(o=>`<button class="opt">${o}</button>`).join('')+'</div>';
    zone.querySelectorAll('.opt').forEach(b=>b.onclick=()=>answer(b.textContent===current.name,b));
  }else{const names=[...new Set(scopeAll().map(s=>s.name))].sort((a,b)=>a.localeCompare(b,'fr'));
    zone.innerHTML='<input class="ans" id="typed" list="names" placeholder="Tape le nom de l\'espèce…" autocomplete="off"><datalist id="names">'+names.map(n=>`<option value="${n}"></option>`).join('')+'</datalist><button class="go" id="valider" style="margin-top:8px">Valider</button>';
    document.getElementById('valider').onclick=()=>answer(norm(document.getElementById('typed').value)===norm(current.name));document.getElementById('typed').focus();}}
function answer(ok,btn){if(answered)return;answered=true;
  const k=stkey(current.id);const s=stats[k]||{s:0,c:0,ko:false};s.s++;if(ok)s.c++;if(!ok&&cfg.mode==='reviser')s.ko=true;if(ok)s.ko=false;
  stats[k]=s;save();session.s++;if(ok)session.c++;document.getElementById('score').textContent=session.c+' / '+session.s;if(btn)btn.classList.add('sel');
  const nk=known(current.id);
  document.getElementById('feedback').innerHTML=`<div class="fb ${ok?'ok':'no'}">${ok?'✅ Correct':'❌ Faux'}<div class="nm">${current.name}${nk?'<span class="badge">connue ★</span>':''}</div><div class="lt">${current.latin||''}</div>`+(current.note?`<div class="nt">${current.note}</div>`:'')+`<button class="go" id="suiv" style="margin-top:10px">Espèce suivante →</button></div>`;
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
  const statTxt=(id,qt)=>{if(known(id,qt))return '★';const x=st(id,qt);return x.s>0?Math.round(100*x.c/x.s)+'%':'–';};
  document.getElementById('glist').innerHTML=arr.map(sp=>{
    const cls=(known(sp.id,'photo')||known(sp.id,'fiche'))?'k':(st(sp.id,'photo').s>0||st(sp.id,'fiche').s>0)?'p':'n';
    const txt='📷 '+statTxt(sp.id,'photo')+' · 📋 '+statTxt(sp.id,'fiche');
    return `<div class="gcard"><div class="gthumb" data-id="${sp.id}" role="button" tabindex="0"><img loading="lazy" src="${sp.imgs[0].u}" alt=""><span class="gcount">${sp.imgs.length} 📷</span></div><div class="gmeta"><div class="gname">${sp.name}${sp.indic?' 🚩':''}</div><div class="glat">${sp.latin||''}</div><div class="gstat ${cls}">${txt}</div><div class="chips">${chipsHTML(sp.id)}</div></div></div>`;}).join('');
  const g=document.getElementById('glist');
  g.querySelectorAll('.gthumb').forEach(t=>{const o=()=>openDetail(t.dataset.id);t.onclick=o;t.onkeydown=e=>{if(e.key==='Enter')o();};});bindChips(g);}
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
  renderTagger(im);}
function renderTagger(im){const eff=new Set(effA(im));
  const t=document.getElementById('tagger');t.innerHTML=CHIP_ASPECTS.map(a=>`<button class="tagbtn ${eff.has(a)?'active':''}" data-a="${a}">${ASPECTS[a]}</button>`).join('');
  t.querySelectorAll('.tagbtn').forEach(b=>b.onclick=()=>{const cur=new Set(tags[im.f]||im.a);cur.has(b.dataset.a)?cur.delete(b.dataset.a):cur.add(b.dataset.a);cur.delete('divers');tags[im.f]=[...cur];savet();setMain(detailIdx);
    document.getElementById('detailchips').innerHTML=chipsHTML(detailSp.id);bindChips(document.getElementById('detailchips'));});}
function showExport(txt){const ta=document.getElementById('expout');ta.classList.remove('hidden');ta.value=txt;ta.focus();ta.select();
  try{document.execCommand('copy');}catch(e){}try{if(navigator.clipboard)navigator.clipboard.writeText(txt);}catch(e){}}
function exportGaps(){const lines=[];scopeAll().forEach(sp=>{const g=CHIP_ASPECTS.filter(a=>chipState(sp.id,a)==='want');
  if(g.length)lines.push(sp.stem+' ('+sp.name+') : '+g.map(a=>ASPECTS[a]).join(', '));});
  showExport(lines.length?lines.join('\n'):'(aucune demande — clique des puces ou « Marquer les manques »)');}
function exportTags(){const lines=Object.keys(tags).map(f=>f+'\t'+(tags[f].length?tags[f].join(','):'divers'));
  showExport(lines.length?lines.join('\n'):'(aucun tag modifié — tague des photos dans le détail)');}
function publishToGitHub(){
  const tagLines=Object.keys(tags).map(f=>f+'\t'+(tags[f].length?tags[f].join(','):'divers'));
  const gapLines=[];
  Object.keys(flags).forEach(id=>{const sp=BYID[id];if(!sp)return;const a=Object.keys(flags[id]||{});
    if(a.length)gapLines.push('# '+sp.name+' ('+sp.stem+') : '+a.map(x=>ASPECTS[x]||x).join(', '));});
  if(!tagLines.length&&!gapLines.length){alert('Rien à publier — coche des manques (oranges) ou retague des photos.');return;}
  const stamp=new Date().toISOString().slice(0,19).replace(/[:T]/g,'-');
  const rnd=Math.random().toString(36).slice(2,7);
  let body="# Contribution depuis l'app ("+stamp+")\n#\n";
  if(gapLines.length)body+='# --- Manques signales (photos a ajouter) ---\n'+gapLines.join('\n')+'\n#\n';
  body+='# --- Re-tags de photos (pris en compte au build) ---\n'+(tagLines.length?tagLines.join('\n'):'# (aucun)')+'\n';
  const fn='contributions/app-'+stamp+'-'+rnd+'.tsv';
  const url='https://github.com/'+REPO+'/new/main?filename='+encodeURIComponent(fn)+'&value='+encodeURIComponent(body);
  const a=document.createElement('a');a.href=url;a.target='_blank';a.rel='noopener';document.body.appendChild(a);a.click();a.remove();}
function markGaps(){scopeAll().forEach(sp=>CHIP_ASPECTS.forEach(a=>{if(!aspPresent(sp,a)){flags[sp.id]=flags[sp.id]||{};flags[sp.id][a]=1;}}));savef();renderList();}
function clearMarks(){flags={};savef();renderList();document.getElementById('expout').classList.add('hidden');}
function show(id){['home','quiz','list','detail'].forEach(s=>document.getElementById(s).classList.toggle('hidden',s!==id));}
function toHome(){show('home');renderConfig();window.scrollTo(0,0);}
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
document.getElementById('back').onclick=toHome;
document.getElementById('showlist').onclick=()=>{show('list');renderList();window.scrollTo(0,0);};
document.getElementById('backlist').onclick=toHome;
document.getElementById('backdetail').onclick=()=>{const id=detailSp&&detailSp.id;show('list');renderList();
  const el=id&&document.querySelector('.gthumb[data-id="'+id+'"]');if(el){el.scrollIntoView({block:'center'});}else{window.scrollTo(0,0);}};
document.getElementById('prevsp').onclick=()=>{if(detailPos>0)openDetail(detailArr[detailPos-1].id);};
document.getElementById('nextsp').onclick=()=>{if(detailPos>=0&&detailPos<detailArr.length-1)openDetail(detailArr[detailPos+1].id);};
document.getElementById('markgaps').onclick=markGaps;
document.getElementById('clearmarks').onclick=clearMarks;
document.getElementById('doexport').onclick=exportGaps;
document.getElementById('exporttags').onclick=exportTags;
document.getElementById('publishpr').onclick=publishToGitHub;
document.getElementById('expprog').onclick=doBackup;
document.getElementById('impfilebtn').onclick=()=>document.getElementById('impfile').click();
document.getElementById('impfile').onchange=e=>{const f=e.target.files[0];if(!f)return;const r=new FileReader();r.onload=()=>restore(String(r.result));r.readAsText(f);e.target.value='';};
document.getElementById('restorebtn').onclick=()=>{const t=document.getElementById('backupbox').value.trim();if(t)restore(t);else{document.getElementById('backupbox').classList.remove('hidden');alert('Colle d\'abord une sauvegarde dans le cadre.');}};
document.getElementById('reset').onclick=()=>{if(confirm('Effacer toute la progression (pas les tags) ?')){stats={};save();renderConfig();}};
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
