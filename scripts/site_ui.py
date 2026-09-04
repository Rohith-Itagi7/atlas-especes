# -*- coding: utf-8 -*-
"""Nouvelle interface du site (refonte d'après la maquette Claude Design).
CSS = design system repeint en palette forêt ; app = portage vanilla du composant.
Les données sont injectées via window.SPECIES_DATA (généré depuis les atlas)."""

CSS = r"""
:root{
 --color-navy-900:#16241C;--color-navy-800:#22362A;--color-navy-700:#31463A;--color-navy-500:#606F63;
 --color-navy-300:#A9B6AC;--color-navy-200:#C8D2C6;--color-navy-100:#E2E6DD;--color-navy-50:#F1F3EC;
 --color-brand-red:#2F6B3A;--color-brand-red-deep:#245430;--color-brand-red-soft:#E4EFDF;
 --color-line:#E2E6DD;--color-line-strong:#C8D2C6;--color-off:#F6F6F1;--color-white:#fff;
 --color-yellow:#E3B45C;--color-success:#2F6B3A;--color-success-soft:#E4EFDF;
 --color-danger:#A33A2B;--color-danger-soft:#F6E2DD;--color-warning:#80590F;--color-warning-soft:#F4EAD3;
 --bg-canvas:var(--color-white);--bg-surface:var(--color-off);
 --fg-1:#16241C;--fg-2:#31463A;--fg-3:#606F63;--fg-4:#A9B6AC;--fg-accent:#2F6B3A;--fg-link:#2F6B3A;
 --border:var(--color-line);--border-strong:var(--color-line-strong);
 --bg-card:var(--color-white);          /* surfaces : cartes, menus, champs */
 --accent-bg:var(--color-navy-900);     /* fond des éléments actifs (nav, chips) */
 --fg-on-accent:#fff;                   /* texte posé sur --accent-bg ou sur l'accent */
 --color-partial:#A87B3C;               /* progression partielle */
 --focus:#2F6B3A;                       /* anneau de focus, visible sur les deux thèmes */
 --overlay-dark:rgba(14,23,48,.82);     /* pastille posée sur une photo */
 --overlay-light:rgba(255,255,255,.94);
 --panel-dark-bg:var(--color-navy-900);  /* panneaux sombres dans les DEUX thèmes */
 --panel-dark-bg-hover:var(--color-navy-800);
 --panel-dark-fg:#fff;
 --shadow-2:0 4px 12px rgba(22,36,28,.08),0 1px 2px rgba(22,36,28,.06);
 --shadow-3:0 12px 32px rgba(22,36,28,.14),0 2px 6px rgba(22,36,28,.07);
 --font-brand:"Betclic","Helvetica Neue",Arial,sans-serif;
 --font-condensed:"Arial Narrow","Helvetica Neue",Arial,sans-serif;
 --font-body:"Aptos","Segoe UI","Helvetica Neue",Arial,sans-serif;
 --font-headline-data:"Aptos Display","Segoe UI",Arial,sans-serif;
 --font-mono:"Aptos Mono","JetBrains Mono","Consolas",monospace;
}
@media (prefers-color-scheme: dark){
 :root{
  --bg-canvas:#131A15;--bg-surface:#0E140F;--bg-card:#1B241D;
  --fg-1:#E9EEE7;--fg-2:#CDD8CB;--fg-3:#A7B8A9;--fg-4:#87978A;
  --color-line:#2C382E;--color-line-strong:#3E4D40;
  --color-navy-50:#1B241D;--color-navy-100:#2C382E;--color-navy-200:#3E4D40;--color-navy-300:#87978A;
  --color-navy-900:#0B120C;--color-navy-800:#16241C;--color-navy-700:#22362A;--color-navy-500:#A7B8A9;
  --color-white:#1B241D;--color-off:#0E140F;
  --color-success:#8FC98F;--color-success-soft:#1D2B1F;
  --color-danger:#F0A79A;--color-danger-soft:#33211E;
  --color-warning:#E7C173;--color-warning-soft:#2C2517;
  --color-yellow:#E7C173;
  --color-brand-red:#8FC98F;--color-brand-red-deep:#B9DDB3;--color-brand-red-soft:#1D2B1F;
  --fg-accent:#8FC98F;--fg-link:#9FD39F;
  --accent-bg:#8FC98F;--fg-on-accent:#101710;
  --color-partial:#D9AE6A;
  --focus:#9FD39F;
  --overlay-dark:rgba(6,10,7,.78);--overlay-light:rgba(20,28,22,.92);
  --panel-dark-bg:#0B120C;--panel-dark-bg-hover:#16241C;--panel-dark-fg:#EAF0E9;
  --shadow-2:0 4px 12px rgba(0,0,0,.45),0 1px 2px rgba(0,0,0,.35);
  --shadow-3:0 12px 32px rgba(0,0,0,.55),0 2px 6px rgba(0,0,0,.4);
 }
}
*{box-sizing:border-box}
html{font-family:var(--font-body);color:var(--fg-1);background:var(--bg-canvas);color-scheme:light dark}
body{margin:0;background:var(--color-off);font-family:var(--font-body);color:var(--fg-1);font-size:15px;line-height:1.4;-webkit-font-smoothing:antialiased;-webkit-text-size-adjust:100%}
a{color:var(--fg-link);text-decoration:none}a:hover{color:var(--color-brand-red-deep)}
img{display:block}
em{font-style:italic}
.r-shell{display:grid;grid-template-columns:1fr;min-height:100vh;align-items:start}
.r-rail{display:none}
.r-pad{padding:16px 16px 104px;width:100%}
.r-quiz{display:grid;grid-template-columns:1fr;gap:16px;align-items:start}
.r-two{display:grid;grid-template-columns:1fr;gap:24px;align-items:start}
.r-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(148px,1fr));gap:12px}
.r-cats{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px}
@media(min-width:900px){
 .r-shell{grid-template-columns:236px 1fr}
 .r-rail{display:flex}
 .r-tabs{display:none!important}
 .r-pad{padding:28px 40px 56px;max-width:1240px}
 .r-quiz{grid-template-columns:1.1fr .9fr;gap:32px}
 .r-two{grid-template-columns:1.5fr 1fr;gap:40px}
 .r-grid{grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:16px}
}
.nb{display:flex;align-items:center;gap:10px;width:100%;padding:10px 12px;border:0;border-radius:8px;background:transparent;color:var(--fg-3);font:600 14px/1 var(--font-body);cursor:pointer;text-align:left;transition:background 120ms,color 120ms}
.nb:hover{background:var(--color-navy-50);color:var(--fg-1)}
.nb[data-on="1"]{background:var(--accent-bg);color:var(--fg-on-accent)}
.tb{display:flex;flex-direction:column;align-items:center;gap:4px;flex:1;padding:9px 0 7px;border:0;background:transparent;color:var(--fg-3);font:600 10px/1 var(--font-body);cursor:pointer;letter-spacing:.02em;min-height:56px}
.tb[data-on="1"]{color:var(--color-brand-red)}
.ch{padding:7px 12px;border:1px solid var(--border);border-radius:999px;background:var(--bg-card);color:var(--fg-2);font:600 13px/1 var(--font-body);cursor:pointer;white-space:nowrap;transition:all 120ms}
.ch:hover{border-color:var(--color-navy-300)}
.ch[data-on="1"]{background:var(--accent-bg);border-color:var(--accent-bg);color:var(--fg-on-accent)}
.dd{position:relative;display:inline-block;vertical-align:middle;z-index:50}
.ch.sel{display:inline-flex;align-items:center;gap:7px;font-size:24px;font-weight:700;padding:4px 10px 4px 14px;border-radius:8px;border-color:var(--color-navy-200);color:var(--fg-1)}
.ch.sel svg{opacity:.5}
.menu{position:absolute;top:calc(100% + 6px);left:0;z-index:60;min-width:200px;max-height:280px;overflow-y:auto;display:flex;flex-direction:column;padding:6px;background:var(--bg-card);border:1px solid var(--border);border-radius:8px;box-shadow:var(--shadow-3);animation:pop 140ms cubic-bezier(.16,1,.3,1) both}
.mi{display:block;width:100%;padding:9px 12px;border:0;border-radius:6px;background:transparent;color:var(--fg-2);font:600 15px/1.2 var(--font-body);text-align:left;cursor:pointer;white-space:nowrap}
.mi:hover{background:var(--color-navy-50);color:var(--fg-1)}
.mi[data-on="1"]{background:var(--color-brand-red-soft);color:var(--color-brand-red-deep)}
.opt{display:flex;align-items:center;justify-content:space-between;gap:10px;width:100%;padding:14px 16px;border:1px solid var(--border);border-radius:8px;background:var(--bg-card);color:var(--fg-1);font:600 15px/1.25 var(--font-body);cursor:pointer;text-align:left;min-height:52px;transition:border-color 120ms,transform 90ms}
.opt:hover{border-color:var(--color-navy-500)}
.opt:active{transform:scale(.99)}
.opt[data-s="ok"]{border-color:var(--color-success);background:var(--color-success-soft)}
.opt[data-s="no"]{border-color:var(--color-danger);background:var(--color-danger-soft)}
.opt[data-s="dim"]{opacity:.45}
.gc{display:block;width:100%;padding:0;border:1px solid var(--border);border-radius:8px;background:var(--bg-card);overflow:hidden;cursor:pointer;text-align:left;transition:box-shadow 140ms,transform 140ms,border-color 140ms}
.gc:hover{box-shadow:var(--shadow-2);transform:translateY(-2px);border-color:var(--color-navy-200)}
.ib{display:inline-flex;align-items:center;justify-content:center;gap:8px;padding:10px 14px;border:1px solid var(--border);border-radius:8px;background:var(--bg-card);color:var(--fg-2);font:600 13px/1 var(--font-body);cursor:pointer;transition:all 120ms}
.ib:hover{border-color:var(--color-navy-500);color:var(--fg-1)}
.pb{width:100%;padding:16px 20px;border:0;border-radius:8px;background:var(--color-brand-red);color:var(--fg-on-accent);font:700 16px/1 var(--font-body);cursor:pointer;display:flex;align-items:center;justify-content:center;gap:10px;transition:background 120ms,transform 90ms;min-height:56px}
.pb:hover{background:var(--color-brand-red-deep)}
.pb:active{transform:scale(.985)}
.pb[data-k="dark"]{background:var(--panel-dark-bg);color:var(--panel-dark-fg)}
.pb[data-k="dark"]:hover{background:var(--panel-dark-bg-hover)}
.fv{font:400 13px/1.35 var(--font-body);color:var(--fg-1)}
.fv[data-b="1"]{filter:blur(5px);background:var(--color-navy-100);border-radius:4px;cursor:pointer;user-select:none;color:var(--fg-2)}
.inf{width:16px;height:16px;flex:0 0 auto;display:inline-flex;align-items:center;justify-content:center;padding:0;border:1px solid var(--color-navy-200);border-radius:999px;background:var(--bg-card);color:var(--fg-3);font:700 10px/1 var(--font-body);cursor:pointer}
.inf:hover{border-color:var(--color-brand-red);color:var(--color-brand-red)}
.inf[data-on="true"]{background:var(--accent-bg);border-color:var(--accent-bg);color:var(--fg-on-accent)}
.gloss{margin:8px 0 2px;padding:10px 12px;border-radius:6px;background:var(--color-navy-50);font:400 12px/1.5 var(--font-body);color:var(--fg-2);animation:pop 140ms cubic-bezier(.16,1,.3,1) both}
input{font-family:var(--font-body)}
:focus-visible{outline:2px solid var(--color-brand-red);outline-offset:2px}
@keyframes pop{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
@keyframes flyL{to{transform:translateX(-130%) rotate(-14deg);opacity:0}}
@keyframes flyR{to{transform:translateX(130%) rotate(14deg);opacity:0}}
a:focus-visible,button:focus-visible,input:focus-visible,[tabindex]:focus-visible{
 outline:3px solid var(--focus);outline-offset:2px;border-radius:4px}
@media (prefers-reduced-motion: reduce){
 *,*::before,*::after{animation-duration:.01ms!important;animation-iteration-count:1!important;
  transition-duration:.01ms!important;scroll-behavior:auto!important}
 .critcard{transition:none!important}
}
.anim{animation:pop 220ms cubic-bezier(.16,1,.3,1) both}
.flyL{animation:flyL 260ms cubic-bezier(.65,0,.35,1) both}
.flyR{animation:flyR 260ms cubic-bezier(.65,0,.35,1) both}
.quizwrap{background:var(--color-brand-red-soft);border:1px solid var(--color-line-strong);border-radius:14px;padding:16px}
@media(min-width:900px){.quizwrap{padding:22px}}
.quizbar{display:flex;align-items:center;gap:11px;margin-bottom:16px;padding:11px 15px;border-radius:10px;background:var(--panel-dark-bg);color:var(--panel-dark-fg)}
.quizbar .qt{font:700 10px/1.1 var(--font-condensed);letter-spacing:.14em;text-transform:uppercase;color:var(--color-yellow)}
.quizbar .ql{font:700 15px/1.2 var(--font-body);color:var(--panel-dark-fg);margin-top:3px}
.dd[data-open="1"]{z-index:200}
.qphoto{width:100%;max-height:42vh;object-fit:contain;display:block;background:var(--color-navy-50)}
@media(min-width:900px){.qphoto{max-height:66vh}}
.critstack{position:relative;height:52vh;min-height:240px;margin:2px 0 4px}
@media(min-width:900px){.critstack{height:44vh;min-height:280px}}
.critcard{position:absolute;inset:0;display:flex;flex-direction:column;border:1px solid var(--border);border-radius:12px;overflow:hidden;background:var(--bg-card);will-change:transform,opacity}
.critcard.critback{transform:scale(.96);opacity:.55;pointer-events:none}
.cimg{flex:1 1 auto;min-height:0;background:var(--color-navy-50);overflow:hidden}
.cimg img{width:100%;height:100%;object-fit:cover;display:block}
.cmeta{padding:12px 14px;text-align:center;flex:0 0 auto}
.critbanner{padding:12px 14px;border-radius:10px;font:700 14px/1.35 var(--font-body);text-align:center}
.critbanner.ok{background:var(--color-success-soft);color:var(--color-success)}
.etat{padding:9px 14px;font:600 12px/1.4 var(--font-body);text-align:center}
.etat-off{background:var(--color-warning-soft);color:var(--color-warning)}
.etat-maj{background:var(--accent-bg);color:var(--fg-on-accent)}
.etat .lien{background:none;border:0;color:inherit;font:inherit;text-decoration:underline;cursor:pointer;padding:0 2px}
kbd{font:600 11px/1 var(--font-mono);padding:2px 5px;border:1px solid var(--border-strong);border-radius:4px;background:var(--bg-card);color:var(--fg-2)}
.imgcredit{font:400 10px/1.45 var(--font-body);color:var(--fg-3);margin-top:6px}
.imgcredit a{text-decoration:underline}
.critbanner.no{background:var(--color-danger-soft);color:var(--color-danger)}
"""

BODY = '<div id="app"></div>'

JS = r"""
const SPECIES_DATA = /*__DATA__*/;
// Vocabulaire des aspects, injecté au build depuis scripts/atlas_data.py (source unique)
const ASPECTS_DATA = /*__ASPECTS__*/;
// Poids des photos par catégorie + nom du cache d'images (cf. scripts/site_sw.py)
const OFFLINE_DATA = /*__OFFLINE__*/;
const CHEV='<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M6 9l6 6 6-6"></path></svg>';
const ARROW='<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M5 12h13M12 5l7 7-7 7"></path></svg>';
const ICONS={reviser:'<circle cx="12" cy="12" r="9"></circle><circle cx="12" cy="12" r="3.5"></circle>',atlas:'<rect x="3.5" y="3.5" width="7" height="7" rx="1"></rect><rect x="13.5" y="3.5" width="7" height="7" rx="1"></rect><rect x="3.5" y="13.5" width="7" height="7" rx="1"></rect><rect x="13.5" y="13.5" width="7" height="7" rx="1"></rect>',trier:'<path d="M4 5h16l-6 7v7l-4-2v-5z"></path>',progres:'<path d="M4 20V11M10 20V4M16 20v-6M2 20h20"></path>'};
function navIcon(k,sz){return '<svg aria-hidden="true" focusable="false" width="'+sz+'" height="'+sz+'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round">'+ICONS[k]+'</svg>';}
let H=[];
function h(fn){H.push(fn);return H.length-1;}
function e(s){return (s==null?'':''+s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
// Attribution d'une photo (auteur, licence) : exigée par les licences CC-BY / CC-BY-SA.
// Vide tant que le crédit est inconnu — cf. img/CREDITS.tsv et scripts/credits.py.
// width/height déclarés : le navigateur réserve la place, la page ne saute pas au chargement
function dim(w,h){return (w&&h)?(' width="'+w+'" height="'+h+'"'):'';}
function credit(txt,url){if(!txt)return '';
  const dedans=url?('<a href="'+e(url)+'" target="_blank" rel="noopener noreferrer" style="color:inherit">'+e(txt)+'</a>'):e(txt);
  return '<div class="imgcredit">'+dedans+'</div>';}

class App{
  CATS=[['ligneux','Ligneux'],['herbace','Herbacées'],['champignon','Champignons'],['faune','Faune'],['divers','Diverses'],['mixte','Tout']];
  ASP=[['tout','Tout']].concat(ASPECTS_DATA.map(a=>[a.id,a.label]));
  QT=[['photo','une photo'],['fiche','sa fiche']];
  DF=[['qcm','QCM'],['sosies','Sosies'],['saisie','Saisie libre']];
  MD=[['apprendre','Apprendre'],['reviser','Réviser']];
  FIELDS=[['groupe','Groupe'],['type','Type'],['cycle','Cycle'],['famille','Famille'],['ecologie','Écologie'],['hote','Arbre / substrat'],['habitat','Habitat'],['role','Rôle'],['regime','Régime'],['saison','Saison'],['lumiere','Lumière'],['fixn','Fixation N'],['mycorhize','Mycorhize'],['succession','Succession'],['strate','Strate'],['fonction','Fonction'],['comestible','Comestible'],['repartition','Où on la trouve'],['notes','Notes']];
  CRIT=[
    {id:'fixn', q:"Fixe l'azote ?", has:s=>'fixn' in s.fields, ok:s=>/rhizobium|frankia/i.test(s.fields.fixn||'')},
    {id:'soleil', q:'Aime le plein soleil ?', has:s=>'lumiere' in s.fields, ok:s=>/☀/.test(s.fields.lumiere||'')},
    {id:'ombre', q:"Supporte l'ombre ?", has:s=>'lumiere' in s.fields, ok:s=>/☾/.test(s.fields.lumiere||'')},
    {id:'vivace', q:'Est-ce une vivace ?', has:s=>'cycle' in s.fields, ok:s=>/vivace/i.test(s.fields.cycle||'')},
    // verdict calculé au build par atlas_data.is_edible() (testé côté Python), pas ici
    {id:'comest', q:'Est-ce comestible ?', has:s=>'edible' in s, ok:s=>!!s.edible},
    {id:'arbre', q:'Est-ce un arbre (pas un arbuste) ?', has:s=>s.cat==='ligneux'&&'type' in s.fields, ok:s=>/^arbre/i.test(s.fields.type||'')}
  ];
  GLOSS={
    mycorhize:'AM = mycorhize arbusculaire (endomycorhize, la plus courante) · ECTO = ectomycorhize (chênes, hêtre, pins…) · éricoïde = symbiose propre aux Éricacées · Dual = les deux types · (actino.) = actinorhize, pas une mycorhize.',
    succession:'Place dans la dynamique forestière : pion = pionnière (colonise les sols nus) · int = intermédiaire · post = post-pionnière · clim = climacique (stade final, tolère l’ombre).',
    lumiere:'Besoin en lumière : ☀ plein soleil · ◐ mi-ombre · ☾ ombre. Plusieurs symboles = amplitude large.',
    fixn:'Fixation de l’azote atmosphérique via une bactérie symbiotique : Rhizobium (Fabacées) ou Frankia (aulne, argousier, chalef). « non » = ne fixe pas, même chez une légumineuse.',
    strate:'Étage occupé en forêt-jardin, de 1 (canopée) à 7 (racines et tubercules).',
    fonction:'Rôle dans le système : fix = fixateur d’azote · cs = couvre-sol · att = attire les auxiliaires · mel = mellifère · bio = biomasse / paillage.',
    cycle:'Durée de vie : annuelle (un cycle), bisannuelle (deux ans), vivace (repousse chaque année).',
    comestible:'Partie consommable. « toxique » ou « TOXIQUES » = ne jamais consommer, même cuit.'
  };
  props={quickSessions:true,showMastery:true};
  _recent=[];
  _critBusy=false;
  state={
    open:null, reveal:{}, info:null, tab:'reviser', view:'home',
    cfg:{cat:'ligneux',mode:'apprendre',aspect:'tout',qtype:'photo',diff:'qcm'},
    data:SPECIES_DATA||null, q:null, picked:null, ok:false, typed:'',
    sess:{s:0,c:0,streak:0,best:0},
    query:'', listCat:'mixte', fiche:null, fimg:0, ficheFrom:'atlas',
    crit:null, cq:[], cp:0, csess:{s:0,c:0}, cfb:null, canim:'',
    progMsg:'', progMsgOk:true,
    enLigne:(typeof navigator!=='undefined'&&'onLine' in navigator)?navigator.onLine:true,
    majPrete:false, dl:null, offMsg:'',
    prog:{}
  };
  setState(patch,cb){Object.assign(this.state,patch);this.render();if(cb)cb.call(this);}
  mount(){
    try{const p=localStorage.getItem('atlas-v2-prog');if(p)this.state.prog=JSON.parse(p);}catch(e){}
    this.render();
    this.initHorsLigne();
    try{history.replaceState(this.snapshot(),'');}catch(e){}
  }
  // progress
  key(id,qt){return id+'|'+qt;}
  st(id,qt){return this.state.prog[this.key(id,qt||this.state.cfg.qtype)]||{s:0,c:0};}
  known(id,qt){const x=this.st(id,qt);return x.s>=3&&x.c/x.s>=0.75;}
  knownAny(id){return this.known(id,'photo')&&this.known(id,'fiche');}
  bumpKeys(keys,ok){const prog=Object.assign({},this.state.prog);keys.forEach(k=>{const x=prog[k]||{s:0,c:0};prog[k]={s:x.s+1,c:x.c+(ok?1:0)};});try{localStorage.setItem('atlas-v2-prog',JSON.stringify(prog));}catch(e){}return prog;}
  aspStat(a){const all=this.all(),P=this.state.prog;const cov=a==='tout'?all:all.filter(s=>s.imgs.some(i=>i.a.indexOf(a)>=0));let reps=0,cor=0,k=0;cov.forEach(s=>{const x=P[a==='tout'?s.id+'|photo':s.id+'|photo:'+a]||{s:0,c:0};reps+=x.s;cor+=x.c;if(x.s>=3&&x.c/x.s>=0.75)k++;});return{n:cov.length,reps,k,pct:cov.length?Math.round(100*k/cov.length):0,acc:reps?Math.round(100*cor/reps):0};}
  ficheStat(){const all=this.all(),P=this.state.prog;let reps=0,cor=0,k=0;all.forEach(s=>{const x=P[s.id+'|fiche']||{s:0,c:0};reps+=x.s;cor+=x.c;if(x.s>=3&&x.c/x.s>=0.75)k++;});return{n:all.length,reps,k,pct:all.length?Math.round(100*k/all.length):0,acc:reps?Math.round(100*cor/reps):0};}
  mastery(id){const a=this.st(id,'photo'),b=this.st(id,'fiche');const s=a.s+b.s,c=a.c+b.c;return s?Math.round(100*c/s):0;}
  all(){return this.state.data||[];}
  aspAvail(){const cat=this.state.cfg.cat,set=new Set();this.all().forEach(s=>{if(this.inCat(s,cat))s.imgs.forEach(i=>i.a.forEach(a=>set.add(a)));});return ASPECTS_DATA.map(a=>a.id).filter(a=>set.has(a));}
  label(list,id){const f=list.find(x=>x[0]===id);return f?f[1]:id;}
  // __MATCH_DEBUT__  (bloc extrait et test\u00e9 sous node par tests/test_saisie.py)
  norm(s){return (s||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]/g,'');}
  // Orthographes accept\u00e9es pour une esp\u00e8ce : le champ \u00ab alt \u00bb vient du build
  // (atlas_data.answer_variants) ; on les normalise une fois pour toutes.
  alts(sp){if(!sp._alt)sp._alt=((sp.alt&&sp.alt.length?sp.alt:[sp.name])).map(x=>this.norm(x)).filter(Boolean);return sp._alt;}
  // Vrai si \u00ab v \u00bb (orthographe attendue) est \u00e0 au plus une faute de frappe de \u00ab t \u00bb.
  // Pas de tol\u00e9rance sur les mots courts : \u00ab pois \u00bb et \u00ab poix \u00bb ne sont pas la m\u00eame r\u00e9ponse.
  near(t,v){if(t===v)return true;if(v.length<=5)return false;
    const lt=t.length,lv=v.length;if(Math.abs(lt-lv)>1)return false;
    let i=0,j=0,f=0;
    while(i<lt&&j<lv){if(t[i]===v[j]){i++;j++;continue;}
      if(++f>1)return false;
      if(lt>lv)i++;else if(lt<lv)j++;else{i++;j++;}}
    return f+(lt-i)+(lv-j)<=1;}
  // La r\u00e9ponse saisie (ou l'option cliqu\u00e9e) d\u00e9signe-t-elle bien cette esp\u00e8ce ?
  // exact = pas de tol\u00e9rance orthographique (mode QCM, o\u00f9 les libell\u00e9s viennent des donn\u00e9es).
  answerOk(typed,sp,exact){const t=this.norm(typed);if(!t||!sp)return false;
    if(this.alts(sp).indexOf(t)>=0)return true;
    if(exact)return false;
    const autres=this.all().filter(s=>s.id!==sp.id);
    if(autres.some(s=>this.alts(s).indexOf(t)>=0))return false;   // c'est le nom d'une autre esp\u00e8ce
    const proche=s=>this.alts(s).some(v=>this.near(t,v));
    return proche(sp)&&!autres.some(proche);}                     // faute de frappe non ambigu\u00eb
  // __MATCH_FIN__
  clean(s){return (s||'').replace(/\*\*/g,'');}
  // Affichage petit (grille, bandeau, carte Oui/Non) : la vignette légère produite au build
  // (cf. scripts/derives.py) ; sinon l'original. Les grandes vues gardent l'original.
  petite(im){return im?(im.t||im.u):'';}
  // __HORSLIGNE_DEBUT__  (bloc extrait et testé sous node par tests/test_horsligne.py)
  octetsLisibles(o){o=o||0;
    if(o<900*1024)return Math.max(1,Math.round(o/1024))+' ko';
    return (o/1048576).toFixed(o<10*1048576?1:0).replace('.',',')+' Mo';}
  // Toutes les images d'une catégorie (original + vignette), sans doublon : ce qu'il faut
  // télécharger pour consulter cette catégorie hors ligne.
  urlsCategorie(cat){const vu={},out=[];
    this.all().forEach(s=>{if(cat!=='mixte'&&s.cat!==cat)return;
      s.imgs.forEach(im=>[im.u,im.t].forEach(u=>{if(u&&!vu[u]){vu[u]=1;out.push(u);}}));});
    return out;}
  // __HORSLIGNE_FIN__
  horsLigneDispo(){return typeof navigator!=='undefined'&&'serviceWorker' in navigator&&typeof caches!=='undefined';}
  initHorsLigne(){
    if(typeof window==='undefined')return;
    window.addEventListener('online',()=>this.setState({enLigne:true}));
    window.addEventListener('offline',()=>this.setState({enLigne:false}));
    if(!this.horsLigneDispo())return;
    navigator.serviceWorker.addEventListener('controllerchange',()=>{if(this._recharge)location.reload();});
    navigator.serviceWorker.register('sw.js').then(reg=>{
      const voir=()=>{if(reg.waiting&&navigator.serviceWorker.controller)this.setState({majPrete:true});};
      voir();
      reg.addEventListener('updatefound',()=>{const sw=reg.installing;
        if(sw)sw.addEventListener('statechange',voir);});
    }).catch(()=>{});
  }
  appliquerMaj=()=>{this._recharge=true;
    navigator.serviceWorker.getRegistration().then(reg=>{
      if(reg&&reg.waiting)reg.waiting.postMessage({type:'ACTIVER'});else location.reload();
    }).catch(()=>location.reload());};
  telecharger(cat){return async ()=>{
    if(this.state.dl||!this.horsLigneDispo())return;
    const urls=this.urlsCategorie(cat);
    this.setState({dl:{cat,fait:0,total:urls.length,echecs:0},offMsg:''});
    let cache;
    try{cache=await caches.open(OFFLINE_DATA.cache);}
    catch(e){this.setState({dl:null,offMsg:'Cache indisponible dans ce navigateur.'});return;}
    for(let i=0;i<urls.length;i++){
      try{
        if(!(await cache.match(urls[i]))){          // déjà là = rien à retélécharger
          const rep=await fetch(urls[i]);
          if(rep&&rep.ok)await cache.put(urls[i],rep.clone());else this.state.dl.echecs++;
        }
      }catch(e){this.state.dl.echecs++;}
      this.state.dl.fait=i+1;
      if((i+1)%8===0||i+1===urls.length)this.render();
    }
    const d=this.state.dl;
    this.setState({dl:null,offMsg:d.total+' photo'+(d.total>1?'s':'')+' disponible'+(d.total>1?'s':'')+' hors ligne'
      +(d.echecs?' ('+d.echecs+' échec'+(d.echecs>1?'s':'')+')':'')+'.'});};}
  viderImages=async ()=>{
    if(!this.horsLigneDispo())return;
    if(!confirm('Vider les photos gardées hors ligne ? Elles seront retéléchargées à la demande.'))return;
    try{await caches.delete(OFFLINE_DATA.cache);this.setState({offMsg:'Photos hors ligne effacées.'});}
    catch(e){this.setState({offMsg:'Effacement impossible.'});}};
  // « Ne pas confondre » du quiz : en mode sosies, le critère du groupe qui a fourni les
  // distracteurs ; sinon tous les critères de l'espèce.
  quizTips(q,sp){if(!sp||!sp.conf||!sp.conf.length)return [];
    const g=q&&q.conf>=0?sp.conf[q.conf]:null;
    return (g?[g]:sp.conf).map(x=>({txt:this.clean(x.tip)}));}
  // __SOSIES_DEBUT__  (bloc extrait et testé sous node par tests/test_sosies.py)
  inCat(s,cat){return cat==='mixte'||s.cat===cat;}
  // Les 3 mauvaises réponses du QCM, et le groupe de confusion qui a servi à les tirer (-1 sinon).
  // En mode sosies, on puise d'abord dans « Confusions - référence.md » : les confusions qui
  // comptent sont souvent inter-familles (ail des ours / colchique / muguet), là où le genre
  // latin et la famille passent à côté. Le genre/famille ne sert qu'à compléter.
  distracteurs(sp,cfg,rand){
    const melange=arr=>arr.slice().sort(()=>rand()-0.5);
    const autres=this.all().filter(s=>s.id!==sp.id&&this.inCat(s,cfg.cat));
    const parId={};autres.forEach(s=>{parId[s.id]=s;});
    let choisis=[],conf=-1;
    if(cfg.diff==='sosies'){
      const groupes=(sp.conf||[]).map((g,i)=>({i,sosies:(g.ids||[]).map(id=>parId[id]).filter(Boolean)}))
        .filter(g=>g.sosies.length)
        .sort((a,b)=>b.sosies.length-a.sosies.length);   // le groupe le plus fourni d'abord
      if(groupes.length){
        conf=groupes[0].i;
        const vus={};
        groupes.forEach(g=>melange(g.sosies).forEach(s=>{if(!vus[s.id]){vus[s.id]=1;choisis.push(s);}}));
      }
    }
    if(choisis.length<3){   // repli historique : genre/famille en sosies, même catégorie sinon
      let pool;
      if(cfg.diff==='sosies'){
        const genre=(sp.latin||'').split(' ')[0];
        const proches=autres.filter(s=>(s.latin||'').split(' ')[0]===genre||s.fields.famille===sp.fields.famille);
        pool=proches.length>=3?proches:autres;
      }else{
        const memeCat=autres.filter(s=>s.cat===sp.cat);
        pool=memeCat.length>=3?memeCat:autres;
      }
      const vus={};choisis.forEach(s=>{vus[s.id]=1;});
      melange(pool).forEach(s=>{if(choisis.length<3&&!vus[s.id]){vus[s.id]=1;choisis.push(s);}});
    }
    return {noms:choisis.slice(0,3).map(s=>s.name),conf};}
  // __SOSIES_FIN__
  pool(){const {cfg}=this.state;const base=this.all().filter(s=>this.inCat(s,cfg.cat));const byMode=base.filter(s=>cfg.mode==='apprendre'?!this.known(s.id,cfg.qtype):this.known(s.id,cfg.qtype));let p=(byMode.length>=4?byMode:base);if(cfg.qtype==='photo'&&cfg.aspect!=='tout'){const f=p.filter(s=>s.imgs.some(i=>i.a.indexOf(cfg.aspect)>=0));if(f.length>=4)p=f;}return p;}
  buildQ(){const {cfg}=this.state;const p=this.pool();if(!p.length)return null;
    const win=Math.min(12,Math.max(0,p.length-1));const recent=new Set(this._recent.slice(-win));
    let cand=p.filter(s=>!recent.has(s.id));
    if(!cand.length)cand=p.filter(s=>!this.state.q||s.id!==this.state.q.sp.id);
    if(!cand.length)cand=p;
    const sp=cand[Math.floor(Math.random()*cand.length)];
    this._recent.push(sp.id);if(this._recent.length>Math.max(win,1))this._recent=this._recent.slice(-Math.max(win,1));
    let imgs=sp.imgs;if(cfg.aspect!=='tout'){const f=imgs.filter(i=>i.a.indexOf(cfg.aspect)>=0);if(f.length)imgs=f;}const img=imgs[Math.floor(Math.random()*imgs.length)]||sp.imgs[0];let opts=[],conf=-1;
    if(cfg.diff!=='saisie'){const d=this.distracteurs(sp,cfg,Math.random);conf=d.conf;
      opts=d.noms.concat([sp.name]).sort(()=>Math.random()-0.5);}
    return{sp,img,opts,conf};}
  top(){window.scrollTo(0,0);}
  start=()=>{this._recent=[];const q=this.buildQ();this.setState({view:'quiz',tab:'reviser',q,picked:null,ok:false,typed:'',sess:{s:0,c:0,streak:this.state.sess.streak,best:this.state.sess.best}});this.top();this.pushNav();};
  next=()=>{this.setState({q:this.buildQ(),picked:null,ok:false,typed:'',reveal:{},info:null});this.top();};
  grade(name){const {q,cfg,sess}=this.state;if(!q||this.state.picked)return;const ok=this.answerOk(name,q.sp);const streak=ok?sess.streak+1:0;let keys=[q.sp.id+'|'+cfg.qtype];if(cfg.qtype==='photo'&&q.img&&q.img.a)keys=keys.concat(q.img.a.map(a=>q.sp.id+'|photo:'+a));this.setState({picked:name,ok,prog:this.bumpKeys(keys,ok),sess:{s:sess.s+1,c:sess.c+(ok?1:0),streak,best:Math.max(sess.best,streak)}});
    setTimeout(()=>{const el=document.getElementById('quiz-fb');if(el&&window.innerWidth<900)el.scrollIntoView({behavior:'smooth',block:'center'});},30);}
  setCfg(k,v){return ()=>{const cfg=Object.assign({},this.state.cfg);cfg[k]=v;this.setState({cfg});};}
  pick(k,v){return ()=>{const cfg=Object.assign({},this.state.cfg);cfg[k]=v;this.setState({cfg,open:null});};}
  goReviser=()=>{this.setState({tab:'reviser',view:'home'});this.top();this.pushNav();};
  goAtlas=()=>{this.setState({tab:'atlas',view:'atlas'});this.top();this.pushNav();};
  goTrier=()=>{this.setState({tab:'trier',view:'trierPick',crit:null});this.top();this.pushNav();};
  goProgres=()=>{this.setState({tab:'progres',view:'progres'});this.top();this.pushNav();};
  snapshot(){const s=this.state;return {v:s.view,tab:s.tab,fiche:s.fiche,ficheFrom:s.ficheFrom,crit:s.crit?s.crit.id:null};}
  pushNav(){try{history.pushState(this.snapshot(),'');}catch(e){}}
  restore(st){const from=this.state.view;
    if(st.v==='trierPlay'&&!this.state.cq.length){this.setState({view:'trierPick',tab:'trier',crit:null});window.scrollTo(0,0);return;}
    const patch={view:st.v,tab:st.tab||'reviser',fiche:st.fiche||null,ficheFrom:st.ficheFrom||'atlas'};
    if(st.crit){const c=this.CRIT.find(x=>x.id===st.crit);if(c)patch.crit=c;}
    this.setState(patch);
    if(from==='fiche'&&(st.v==='atlas'||st.v==='quiz'))window.scrollTo(0,this._ficheScroll||0);else window.scrollTo(0,0);}
  back=()=>{try{history.back();}catch(e){this.setState({view:'home',tab:'reviser'});}};
  openFiche(id){return ()=>{this._ficheScroll=window.scrollY;this.setState({view:'fiche',tab:'atlas',fiche:id,fimg:0,ficheFrom:'atlas'});this.top();this.pushNav();};}
  atlasArr(){const q=this.norm(this.state.query);return this.all().filter(s=>this.inCat(s,this.state.listCat)).filter(s=>!q||this.norm(s.name+s.latin+(s.fields.famille||'')).indexOf(q)>=0).slice().sort((a,b)=>a.name.localeCompare(b.name,'fr'));}
  moveFiche(d){return ()=>{const arr=this.atlasArr();const i=arr.findIndex(s=>s.id===this.state.fiche);const n=arr[(i+d+arr.length)%arr.length];if(n)this.setState({fiche:n.id,fimg:0});};}
  startCrit(c){return ()=>{this._critBusy=false;const q=this.all().filter(s=>this.inCat(s,this.state.cfg.cat)&&c.has(s)).sort(()=>Math.random()-0.5);this.setState({view:'trierPlay',tab:'trier',crit:c,cq:q,cp:0,csess:{s:0,c:0},cfb:null,cfbOk:false,canim:''});this.top();this.pushNav();};}
  critAns(yes){return ()=>{if(this._critBusy)return;const {crit,cq,cp,csess}=this.state;const sp=cq[cp];if(!sp)return;
    const truth=crit.ok(sp),ok=truth===yes;this._critBusy=true;
    this.setState({cfb:(ok?'✅ Bravo':'❌ Raté')+' — '+sp.name+' : c’était '+(truth?'oui':'non'),cfbOk:ok,csess:{s:csess.s+1,c:csess.c+(ok?1:0)},canim:yes?'flyR':'flyL',prog:this.bumpKeys(['crit|'+crit.id],ok)});
    setTimeout(()=>{this._critBusy=false;this.setState({cp:(cp+1)%cq.length,canim:''});},320);};}
  // __PROG_DEBUT__  (bloc extrait et testé sous node par tests/test_progression.py)
  // Clés de progression : « <espèce>|photo », « <espèce>|photo:<aspect> », « <espèce>|fiche »,
  // « crit|<question> ». Une entrée = {s: réponses, c: correctes}.
  CLE_PROG=/^(?:crit\|[^|]+|[^|]+\|photo(?::[a-z]+)?|[^|]+\|fiche)$/;
  progExport(prog){return JSON.stringify({v:1,app:'atlas-especes',prog:prog||{}});}
  // Lit un fichier de progression : enveloppe {v:1,prog:…} ou ancien format (objet plat).
  // Les entrées non conformes sont comptées et ignorées, pas rejetées en bloc.
  progParse(txt){
    let o;
    try{o=JSON.parse(txt);}catch(e){return {erreur:'Fichier illisible : ce n’est pas du JSON.'};}
    if(o&&typeof o==='object'&&!Array.isArray(o)&&o.prog&&typeof o.prog==='object')o=o.prog;
    if(!o||typeof o!=='object'||Array.isArray(o))return {erreur:'Fichier inattendu : aucune progression trouvée.'};
    const prog={};let ignores=0;
    Object.keys(o).forEach(k=>{const v=o[k];
      const bon=this.CLE_PROG.test(k)&&v&&typeof v==='object'
        &&Number.isInteger(v.s)&&Number.isInteger(v.c)&&v.s>=0&&v.c>=0&&v.c<=v.s;
      if(bon)prog[k]={s:v.s,c:v.c};else ignores++;});
    if(!Object.keys(prog).length)
      return {erreur:'Aucune entrée exploitable dans ce fichier'+(ignores?' ('+ignores+' ignorée'+(ignores>1?'s':'')+')':'')+'.'};
    return {prog,ignores};}
  // Fusion additive : c'est le cas d'usage (« je récupère ma progression d'un autre appareil »).
  progFusion(actuel,entrant){const prog=Object.assign({},actuel||{});let ajoutes=0,fusionnes=0;
    Object.keys(entrant).forEach(k=>{const e=entrant[k];
      if(prog[k]){prog[k]={s:prog[k].s+e.s,c:prog[k].c+e.c};fusionnes++;}
      else{prog[k]={s:e.s,c:e.c};ajoutes++;}});
    return {prog,ajoutes,fusionnes};}
  // Résumé de ce qui vient de se passer : on compte les entrées **du fichier**, pas le total
  // après fusion, sinon les nombres ne s'additionnent pas pour l'utilisateur.
  progResume(r,remplace){const n=r.ajoutes+r.fusionnes;
    return (remplace?'Progression remplacée : ':'Progression importée : ')+n+' entrée'+(n>1?'s':'')
      +(remplace?'':' ('+r.ajoutes+' ajoutée'+(r.ajoutes>1?'s':'')+', '+r.fusionnes+' fusionnée'+(r.fusionnes>1?'s':'')+')')
      +(r.ignores?' · '+r.ignores+' ignorée'+(r.ignores>1?'s':''):'')+'.';}
  // __PROG_FIN__
  exportProg=()=>{try{const b=new Blob([this.progExport(this.state.prog)],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='atlas-progression.json';document.body.appendChild(a);a.click();a.remove();}catch(e){}};
  pickImport(remplace){return ()=>{this._remplace=remplace;const el=document.getElementById('prog-file');if(el){el.value='';el.click();}};}
  onImportFile=ev=>{const f=ev.target&&ev.target.files&&ev.target.files[0];if(!f)return;
    const remplace=!!this._remplace;const r=new FileReader();
    r.onerror=()=>this.setState({progMsg:'Fichier illisible.',progMsgOk:false});
    r.onload=()=>{const lu=this.progParse(String(r.result||''));
      if(lu.erreur){this.setState({progMsg:lu.erreur,progMsgOk:false});return;}
      const n=Object.keys(lu.prog).length,actuel=Object.keys(this.state.prog).length;
      if(remplace&&actuel&&!confirm('Remplacer toute ta progression ('+actuel+' entrées) par ce fichier ('+n+' entrées) ? Ton avancement actuel sera perdu.'))return;
      const res=remplace?{prog:lu.prog,ajoutes:n,fusionnes:0}:this.progFusion(this.state.prog,lu.prog);
      try{localStorage.setItem('atlas-v2-prog',JSON.stringify(res.prog));}catch(e){}
      this.setState({prog:res.prog,progMsg:this.progResume({ajoutes:res.ajoutes,fusionnes:res.fusionnes,ignores:lu.ignores},remplace),progMsgOk:true});};
    r.readAsText(f);};
  resetProg=()=>{if(!confirm('Réinitialiser toute la progression ?'))return;try{localStorage.removeItem('atlas-v2-prog');}catch(e){}this.setState({prog:{},sess:{s:0,c:0,streak:0,best:0},progMsg:'Progression réinitialisée.',progMsgOk:true});};
  fieldRows(sp,quiz){if(!sp)return [];const hidden={comestible:1,notes:1};return this.FIELDS.filter(f=>sp.fields[f[0]]).map(f=>{const k=f[0],rk=sp.id+'|'+k,blur=!!(quiz&&hidden[k]&&!this.state.reveal[rk]);return{l:f[1],v:this.clean(sp.fields[k]),b:blur?'1':'0',go:blur?(()=>{const r=Object.assign({},this.state.reveal);r[rk]=1;this.setState({reveal:r});}):(()=>{}),hasInfo:!!this.GLOSS[k],info:this.GLOSS[k]||'',openInfo:this.state.info===rk,goInfo:()=>this.setState({info:this.state.info===rk?null:rk})};});}

  renderVals(){
    const S=this.state,cfg=S.cfg,all=this.all();const catList=this.CATS;
    const aspAv=this.aspAvail();if(cfg.aspect!=='tout'&&aspAv.indexOf(cfg.aspect)<0)cfg.aspect='tout';
    const showAsp=cfg.qtype==='photo'&&aspAv.length>0;
    const catOf=c=>all.filter(s=>this.inCat(s,c));
    const knownIn=c=>catOf(c).filter(s=>this.knownAny(s.id)).length;
    const heroAll=catOf(cfg.cat),heroK=knownIn(cfg.cat);
    const q=S.q,sp=q&&q.sp,answered=!!S.picked;
    const correct=answered&&!!S.ok;   // verdict posé par grade() (cf. answerOk)
    const fiche=all.find(s=>s.id===S.fiche);
    const fimgs=fiche?fiche.imgs:[];const fcur=fimgs[S.fimg]||fimgs[0];
    const critSp=S.cq[S.cp];
    const titles={home:'Ma session',quiz:'Quiz',atlas:'Atlas des espèces',fiche:'Fiche espèce',trierPick:'Questions oui / non',trierPlay:S.crit?S.crit.q:'Questions oui / non',progres:'Ma progression'};
    const crumbs={home:'Réviser',quiz:this.label(this.CATS,cfg.cat)+' · '+this.label(this.QT,cfg.qtype),atlas:all.length+' espèces',fiche:S.ficheFrom==='quiz'?'Quiz':'Atlas',trierPick:'Oui / Non',trierPlay:this.label(this.CATS,cfg.cat),progres:'Progrès'};
    return {
      onReviser:S.tab==='reviser'?'1':'0',onAtlas:S.tab==='atlas'?'1':'0',onTrier:S.tab==='trier'?'1':'0',onProgres:S.tab==='progres'?'1':'0',
      goReviser:this.goReviser,goAtlas:this.goAtlas,goTrier:this.goTrier,goProgres:this.goProgres,back:this.back,
      showBack:S.view!=='home'&&S.view!=='atlas'&&S.view!=='progres'&&S.view!=='trierPick',
      title:titles[S.view]||'',crumb:crumbs[S.view]||'',streak:S.sess.streak,best:S.sess.best,
      totalKnown:all.filter(s=>this.knownAny(s.id)).length,totalCount:all.length,
      totalPct:all.length?Math.round(100*all.filter(s=>this.knownAny(s.id)).length/all.length):0,
      totalSeen:all.filter(s=>this.st(s.id,'photo').s+this.st(s.id,'fiche').s>0).length,
      totalReps:Object.keys(S.prog).reduce((a,k)=>a+S.prog[k].s,0),
      isHome:S.view==='home',showQuick:this.props.quickSessions!==false,showMastery:this.props.showMastery!==false,
      isQuiz:S.view==='quiz'&&!!q,isAtlas:S.view==='atlas',isFiche:S.view==='fiche'&&!!fiche,
      isTrierPick:S.view==='trierPick',isTrierPlay:S.view==='trierPlay'&&!!critSp,isProgres:S.view==='progres',
      heroPct:heroAll.length?Math.round(100*heroK/heroAll.length):0,start:this.start,
      presets:[
        {tag:'10 minutes',title:'Écorces d’hiver',sub:'Ligneux, photo d’écorce, QCM',go:()=>this.setState({cfg:{cat:'ligneux',mode:'apprendre',aspect:'ecorce',qtype:'photo',diff:'qcm'}},this.start)},
        {tag:'Piège',title:'Sosies mortels',sub:'Champignons, choix entre sosies',go:()=>this.setState({cfg:{cat:'champignon',mode:'apprendre',aspect:'tout',qtype:'photo',diff:'sosies'}},this.start)},
        {tag:'Sans photo',title:'Deviner d’après la fiche',sub:'Toutes catégories, caractères',go:()=>this.setState({cfg:{cat:'mixte',mode:'apprendre',aspect:'tout',qtype:'fiche',diff:'qcm'}},this.start)}
      ],
      cfgCatLabel:this.label(catList,cfg.cat).toLowerCase(),cfgAspectLabel:cfg.aspect==='tout'?'tous les aspects':this.label(this.ASP,cfg.aspect).toLowerCase(),
      cfgQtypeLabel:this.label(this.QT,cfg.qtype),cfgDiffLabel:this.label(this.DF,cfg.diff),
      openCat:S.open==='cat',openAsp:S.open==='asp',openQt:S.open==='qt',openDf:S.open==='df',anyOpen:!!S.open,
      toggleCat:()=>this.setState({open:S.open==='cat'?null:'cat'}),toggleAsp:()=>this.setState({open:S.open==='asp'?null:'asp'}),
      toggleQt:()=>this.setState({open:S.open==='qt'?null:'qt'}),toggleDf:()=>this.setState({open:S.open==='df'?null:'df'}),
      closeAll:()=>this.setState({open:null}),
      catOpts:catList.map(c=>({label:c[1],on:cfg.cat===c[0]?'1':'0',go:this.pick('cat',c[0])})),
      showAsp:showAsp,
      aspOpts:[['tout','Tous les aspects']].concat(aspAv.map(a=>[a,this.label(this.ASP,a)])).map(c=>({label:c[1],on:cfg.aspect===c[0]?'1':'0',go:this.pick('aspect',c[0])})),
      qtOpts:this.QT.map(c=>({label:c[0]==='photo'?'Une photo':'Sa fiche de caractères',on:cfg.qtype===c[0]?'1':'0',go:this.pick('qtype',c[0])})),
      dfOpts:this.DF.map(c=>({label:c[1],on:cfg.diff===c[0]?'1':'0',go:this.pick('diff',c[0])})),
      poolCount:this.pool().length,
      quizModeLine:this.label(this.CATS,cfg.cat)+' · '+(cfg.qtype==='photo'?('photo'+(cfg.aspect!=='tout'?' — '+this.label(this.ASP,cfg.aspect).toLowerCase():'')):'fiche')+' · '+this.label(this.DF,cfg.diff).toLowerCase(),
      isPhotoQ:!!q&&cfg.qtype==='photo',isFicheQ:!!q&&cfg.qtype==='fiche',
      qImg:q?q.img.u:'',qW:q&&q.img.w?q.img.w:'',qH:q&&q.img.h?q.img.h:'',qAspect:q?(q.img.a.map(a=>this.label(this.ASP,a)).join(' · ')||'Divers'):'',
      // l'alternative textuelle ne doit pas donner la réponse avant validation
      qAlt:q?((answered?sp.name:'Espèce à identifier')+' — '+(q.img.a.map(a=>this.label(this.ASP,a)).join(', ')||'vue d’ensemble')):'',
      qCredit:(answered&&q&&q.img.c)?q.img.c:'',qCreditUrl:(answered&&q&&q.img.cu)?q.img.cu:'',
      qFields:q?this.fieldRows(sp,!answered):[],
      hasOptions:!!q&&cfg.diff!=='saisie',isTyped:!!q&&cfg.diff==='saisie',typed:S.typed,
      onType:ev=>{this.state.typed=ev.target.value;},onTypeKey:ev=>{if(ev.key==='Enter')this.grade(this.state.typed);},submitTyped:()=>this.grade(this.state.typed),
      options:q?q.opts.map(o=>({label:o,hint:'',s:!answered?'':(this.answerOk(o,sp,true)?'ok':(o===S.picked?'no':'dim')),go:()=>this.grade(o)})):[],
      answered,fbColor:correct?'var(--color-success)':'var(--color-danger)',fbLabel:correct?'Bonne réponse':'Raté',
      answerName:sp?sp.name:'',answerLatin:sp?sp.latin:'',answerNote:sp?this.clean(sp.note==='—'?(sp.fields.repartition||''):sp.note):'',
      hasTips:!!(sp&&sp.conf&&sp.conf.length),tips:this.quizTips(q,sp),
      next:this.next,openAnswerFiche:()=>{this._ficheScroll=window.scrollY;this.setState({view:'fiche',tab:'atlas',fiche:sp.id,fimg:0,ficheFrom:'quiz'});this.top();this.pushNav();},
      sessLine:S.sess.c+' / '+S.sess.s+' cette session',sessPct:S.sess.s?Math.round(100*S.sess.c/S.sess.s):0,
      query:S.query,onSearch:ev=>{this.state.query=ev.target.value;this.render();},atlasCount:this.atlasArr().length,
      listChips:catList.map(c=>({label:c[1],on:S.listCat===c[0]?'1':'0',go:()=>this.setState({listCat:c[0]})})),
      atlasList:this.atlasArr().slice(0,500).map(s=>{const m=this.mastery(s.id),seen=this.st(s.id,'photo').s+this.st(s.id,'fiche').s;const half=!this.knownAny(s.id)&&(this.known(s.id,'photo')||this.known(s.id,'fiche'));return{name:s.name,latin:s.latin,thumb:this.petite(s.imgs[0]),pct:m,badge:this.knownAny(s.id)?'maîtrisée':(half?(this.known(s.id,'photo')?'photo OK':'fiche OK'):(seen?m+'%':(s.imgs.length>1?s.imgs.length+' photos':'1 photo'))),barColor:this.knownAny(s.id)?'var(--color-success)':'var(--color-partial)',go:this.openFiche(s.id)};}),
      fName:fiche?fiche.name:'',fLatin:fiche?fiche.latin:'',fCat:fiche?this.label(catList,fiche.cat):'',
      fImg:fcur?fcur.u:'',fW:fcur&&fcur.w?fcur.w:'',fH:fcur&&fcur.h?fcur.h:'',
      fAlt:fiche&&fcur?(fiche.name+' — '+(fcur.a.map(a=>this.label(this.ASP,a)).join(', ')||'vue d’ensemble')):'',
      fImgAsp:fcur?('Cette photo montre : '+(fcur.a.map(a=>this.label(this.ASP,a)).join(', ')||'divers')):'',
      fCredit:fcur&&fcur.c?fcur.c:'',fCreditUrl:fcur&&fcur.cu?fcur.cu:'',
      fThumbs:fimgs.map((im,i)=>({u:this.petite(im),border:i===S.fimg?'var(--fg-1)':'transparent',go:()=>this.setState({fimg:i})})),
      fFields:this.fieldRows(fiche,false),
      fHasTips:!!(fiche&&fiche.conf&&fiche.conf.length),fTips:fiche&&fiche.conf?fiche.conf.map(g=>({txt:this.clean(g.tip)})):[],
      fPrev:this.moveFiche(-1),fNext:this.moveFiche(1),
      catChips:catList.map(c=>({label:c[1],on:cfg.cat===c[0]?'1':'0',go:this.setCfg('cat',c[0])})),
      criteria:this.CRIT.map(c=>({q:c.q,n:all.filter(s=>this.inCat(s,cfg.cat)&&c.has(s)).length,go:this.startCrit(c)})).filter(x=>x.n>=4),
      critQ:S.crit?S.crit.q:'',critTopImg:critSp?this.petite(critSp.imgs[0]):'',critTopName:critSp?critSp.name:'',critTopLatin:critSp?critSp.latin:'',
      critHasBack:!!S.cq[S.cp+1],critBackImg:S.cq[S.cp+1]?this.petite(S.cq[S.cp+1].imgs[0]):'',critBackName:S.cq[S.cp+1]?S.cq[S.cp+1].name:'',
      critAnim:S.canim,critHasFb:!!S.cfb,critFb:S.cfb||'',critFbOk:!!S.cfbOk,
      critYes:this.critAns(true),critNo:this.critAns(false),critScore:S.csess.c+' / '+S.csess.s+' · carte '+(S.cp+1)+' sur '+S.cq.length,
      skillRows:this.ASP.map(a=>{const st=this.aspStat(a[0]);return{label:a[0]==='tout'?'Photo — vue d’ensemble':'Photo — '+a[1].toLowerCase(),n:st.n,right:st.k+' / '+st.n+' maîtrisées',acc:st.reps?st.acc+'% de réussite · '+st.reps+(st.reps>1?' réponses':' réponse'):'jamais travaillé',pct:st.pct,bar:st.reps?'var(--color-success)':'var(--color-line-strong)'};}).filter(r=>r.n>0).concat([(f=>({label:'Fiche de caractères (sans photo)',right:f.k+' / '+f.n+' maîtrisées',n:f.n,acc:f.reps?f.acc+'% de réussite · '+f.reps+(f.reps>1?' réponses':' réponse'):'jamais travaillé',pct:f.pct,bar:f.reps?'var(--color-success)':'var(--color-line-strong)'}))(this.ficheStat())]),
      critRows:this.CRIT.map(c=>{const x=S.prog['crit|'+c.id]||{s:0,c:0},acc=x.s?Math.round(100*x.c/x.s):0;return{label:c.q,right:x.s?x.c+' / '+x.s+' bonnes réponses':'jamais joué',acc:x.s>=6?(acc>=75?'Solide':(acc>=50?'À consolider':'Fragile')):(x.s?'Trop peu de réponses':'—'),pct:acc,bar:x.s?(acc>=75?'var(--color-success)':(acc>=50?'var(--color-partial)':'var(--color-danger)')):'var(--color-line-strong)'};}),
      catCards:catList.filter(c=>c[0]!=='mixte').map(c=>{const arr=catOf(c[0]),k=knownIn(c[0]);return{label:c[1],n:arr.length,pct:arr.length?Math.round(100*k/arr.length):0};}),
      exportProg:this.exportProg,resetProg:this.resetProg,
      horsLigneDispo:this.horsLigneDispo()?'1':'0',horsLigne:S.enLigne?'0':'1',
      majPrete:S.majPrete?'1':'0',appliquerMaj:this.appliquerMaj,
      offMsg:S.offMsg,viderImages:this.viderImages,
      dlEnCours:S.dl?'1':'0',
      dlLibelle:S.dl?(this.label(this.CATS,S.dl.cat)+' — '+S.dl.fait+' / '+S.dl.total+' photos'):'',
      dlPct:S.dl&&S.dl.total?Math.round(100*S.dl.fait/S.dl.total):0,
      offCats:Object.keys(OFFLINE_DATA.cats||{}).map(c=>({
        label:this.label(this.CATS,c),
        taille:this.octetsLisibles((OFFLINE_DATA.cats[c]||{}).o),
        n:(OFFLINE_DATA.cats[c]||{}).n||0,
        go:this.telecharger(c)})),
      importProg:this.pickImport(false),replaceProg:this.pickImport(true),
      onImportFile:this.onImportFile,progMsg:S.progMsg,progMsgOk:S.progMsgOk?'1':'0'
    };
  }
"""

# suite du JS (templates + bind + render) dans site_ui_part2
JS += r"""
  ddMenu(V,openKey,opts){
    if(!V[openKey])return '';
    return '<div class="menu">'+opts.map(o=>'<button class="mi" data-on="'+o.on+'" data-h="'+h(o.go)+'">'+e(o.label)+'</button>').join('')+'</div>';
  }
  chip(V,label,openKey,toggle,opts){
    return '<span class="dd"'+(V[openKey]?' data-open="1"':'')+'><button class="ch sel" data-on="'+(V[openKey]?'1':'0')+'" data-h="'+h(toggle)+'">'+e(label)+CHEV+'</button>'+this.ddMenu(V,openKey,opts)+'</span>';
  }
  fieldsHtml(rows,flex){
    return rows.map(f=>'<div style="padding:10px 0;border-bottom:1px solid var(--border)"><div style="display:flex;gap:12px;align-items:baseline"><span style="flex:0 0 '+flex+';display:flex;align-items:center;gap:6px;font:600 13px/1.35 var(--font-body);color:var(--fg-3)">'+e(f.l)+(f.hasInfo?'<button class="inf" data-on="'+f.openInfo+'" data-h="'+h(f.goInfo)+'">i</button>':'')+'</span><span class="fv" style="flex:1" data-b="'+f.b+'" data-h="'+h(f.go)+'">'+e(f.v)+'</span></div>'+(f.openInfo?'<div class="gloss">'+e(f.info)+'</div>':'')+'</div>').join('');
  }
  viewHtml(V){
    if(V.isHome){
      return '<div style="max-width:760px;margin:0 auto;padding-top:16px;display:flex;flex-direction:column;gap:26px">'
      +'<div style="font:700 10px/1 var(--font-condensed);letter-spacing:.14em;text-transform:uppercase;color:var(--color-brand-red)">Une session, une phrase</div>'
      +'<div style="font:400 27px/1.5 var(--font-body);letter-spacing:-.01em;padding-bottom:4px">Je révise les '
        +this.chip(V,V.cfgCatLabel,'openCat',V.toggleCat,V.catOpts)
        +' d\'après '+this.chip(V,V.cfgQtypeLabel,'openQt',V.toggleQt,V.qtOpts)
        +(V.showAsp?', en me concentrant sur '+this.chip(V,V.cfgAspectLabel,'openAsp',V.toggleAsp,V.aspOpts):'')
        +', en mode '+this.chip(V,V.cfgDiffLabel,'openDf',V.toggleDf,V.dfOpts)+'.</div>'
      +(V.anyOpen?'<div data-h="'+h(V.closeAll)+'" style="position:fixed;inset:0;z-index:40"></div>':'')
      +'<div style="display:flex;flex-wrap:wrap;gap:24px;padding:18px 0;border-top:1px solid var(--border);border-bottom:1px solid var(--border)">'
        +'<div><div style="font:700 22px/1 var(--font-headline-data)">'+V.poolCount+'</div><div style="font:600 11px/1.2 var(--font-body);color:var(--fg-3);margin-top:5px">espèces dans le tirage</div></div>'
        +'<div><div style="font:700 22px/1 var(--font-headline-data)">'+V.heroPct+'%</div><div style="font:600 11px/1.2 var(--font-body);color:var(--fg-3);margin-top:5px">déjà maîtrisé</div></div>'
        +'<div><div style="font:700 22px/1 var(--font-headline-data)">'+V.best+'</div><div style="font:600 11px/1.2 var(--font-body);color:var(--fg-3);margin-top:5px">meilleure série</div></div></div>'
      +'<button class="pb" data-k="dark" data-h="'+h(V.start)+'">Lancer'+ARROW+'</button>'
      +(V.showQuick?'<div><div style="font:700 10px/1 var(--font-condensed);letter-spacing:.14em;text-transform:uppercase;color:var(--fg-3);margin-bottom:10px">Ou une séance déjà réglée</div><div class="r-cats">'
        +V.presets.map(p=>'<button class="gc" style="padding:16px;display:flex;flex-direction:column;gap:8px;min-height:112px" data-h="'+h(p.go)+'"><div style="font:700 10px/1 var(--font-condensed);letter-spacing:.12em;text-transform:uppercase;color:var(--color-brand-red)">'+e(p.tag)+'</div><div style="font:700 16px/1.25 var(--font-body);padding-bottom:2px">'+e(p.title)+'</div><div style="font:400 13px/1.4 var(--font-body);color:var(--fg-3)">'+e(p.sub)+'</div></button>').join('')
        +'</div></div>':'')
      +'<div style="font:400 13px/1.5 var(--font-body);color:var(--fg-3)">Chaque mot souligné est un réglage : clique pour changer. Le mode <em>Apprendre</em> tire les espèces jamais vues, <em>Réviser</em> celles déjà acquises.</div>'
      +'</div>';
    }
    if(V.isQuiz){
      let left='';
      if(V.isPhotoQ) left='<div style="position:relative;border:1px solid var(--border);border-radius:12px;overflow:hidden;background:var(--color-navy-50)"><img class="qphoto" src="'+e(V.qImg)+'"'+dim(V.qW,V.qH)+' alt="'+e(V.qAlt)+'"><div style="position:absolute;top:12px;left:12px;padding:6px 11px;border-radius:999px;background:var(--overlay-dark);font:700 10px/1 var(--font-condensed);letter-spacing:.12em;text-transform:uppercase;color:var(--panel-dark-fg)">'+e(V.qAspect)+'</div></div>';
      else left='<div style="border:1px solid var(--border);border-radius:12px;background:var(--bg-card);padding:20px"><div style="font:700 10px/1 var(--font-condensed);letter-spacing:.12em;text-transform:uppercase;color:var(--color-brand-red)">Fiche de caractères</div><div style="margin-top:14px">'+this.fieldsHtml(V.qFields,'40%')+'</div><div style="margin-top:12px;font:italic 400 12px/1.4 var(--font-body);color:var(--fg-3)">Deux lignes sont floutées : elles trahissent l\'espèce. Clique dessus pour l\'indice. Le « i » explique les abréviations.</div></div>';
      left+='<div style="display:flex;align-items:center;justify-content:space-between;gap:12px;margin-top:12px"><div role="status" aria-live="polite" style="font:600 12px/1 var(--font-body);color:var(--fg-3)">'+e(V.sessLine)+'</div><div style="font:600 12px/1 var(--font-mono);color:var(--fg-3)">'+V.sessPct+'%</div></div><div style="height:3px;margin-top:8px;background:var(--color-navy-100);border-radius:999px;overflow:hidden"><div style="height:100%;background:var(--color-brand-red);width:'+V.sessPct+'%"></div></div>';
      let right='';
      if(V.isTyped) right+='<div style="display:flex;gap:8px"><input id="q-typed" aria-label="Nom de l’espèce" value="'+e(V.typed)+'" data-hi="'+h(V.onType)+'" data-hk="'+h(V.onTypeKey)+'" placeholder="Tape le nom de l\'espèce…" style="flex:1;padding:14px 16px;border:1px solid var(--border);border-radius:8px;font:400 15px/1 var(--font-body);color:var(--fg-1);min-width:0"><button class="ib" style="padding:12px 18px" data-h="'+h(V.submitTyped)+'">Valider</button></div>';
      if(V.hasOptions) right+=V.options.map(o=>'<button class="opt" data-s="'+o.s+'" data-h="'+h(o.go)+'"><span>'+e(o.label)+'</span></button>').join('');
      if(V.answered){
        right+='<div class="anim" id="quiz-fb" role="status" aria-live="polite" style=""margin-top:6px;border:1px solid var(--border);border-left:3px solid '+V.fbColor+';border-radius:8px;background:var(--bg-card);padding:16px">'
        +'<span style="font:700 10px/1 var(--font-condensed);letter-spacing:.12em;text-transform:uppercase;color:'+V.fbColor+'">'+e(V.fbLabel)+'</span>'
        +'<div style="margin-top:10px;font:700 20px/1.2 var(--font-body)">'+e(V.answerName)+'</div><div style="font:italic 400 13px/1.35 var(--font-body);color:var(--fg-3)">'+e(V.answerLatin)+'</div>'
        +(V.answerNote?'<div style="margin-top:10px;font:400 14px/1.45 var(--font-body);color:var(--fg-2)">'+e(V.answerNote)+'</div>':'')
        +credit(V.qCredit,V.qCreditUrl)
        +(V.hasTips?'<div style="margin-top:12px;padding:12px;border-radius:8px;background:var(--color-warning-soft)"><div style="font:700 9px/1 var(--font-condensed);letter-spacing:.14em;text-transform:uppercase;color:var(--color-warning)">Ne pas confondre</div>'+V.tips.map(t=>'<div style="margin-top:8px;font:400 13px/1.45 var(--font-body);color:var(--fg-1)">'+e(t.txt)+'</div>').join('')+'</div>':'')
        +'<div style="display:flex;gap:8px;margin-top:16px"><button class="pb" style="min-height:48px;font-size:15px" data-k="dark" data-h="'+h(V.next)+'">Suivante'+ARROW+'</button><button class="ib" data-h="'+h(V.openAnswerFiche)+'">Voir la fiche</button></div></div>';
      }
      const bar='<div class="quizbar"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--color-yellow)" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="9"></circle><circle cx="12" cy="12" r="3.5"></circle></svg><div><div class="qt">Quiz — identifie l\'espèce</div><div class="ql">'+e(V.quizModeLine)+'</div></div></div>';
      return '<div class="quizwrap">'+bar+'<div class="r-quiz"><div>'+left+'</div><div style="display:flex;flex-direction:column;gap:10px">'+right+'</div></div></div>';
    }
    if(V.isAtlas){
      return '<div style="display:flex;flex-direction:column;gap:16px">'
      +'<div style="display:flex;flex-wrap:wrap;align-items:center;gap:10px"><div style="display:flex;align-items:center;gap:8px;flex:1 1 240px;padding:11px 14px;border:1px solid var(--border);border-radius:8px;background:var(--bg-card);min-width:0"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--fg-3)" stroke-width="1.75" stroke-linecap="round"><circle cx="11" cy="11" r="7"></circle><path d="M20 20l-4.2-4.2"></path></svg><input id="q-search" type="search" aria-label="Chercher une espèce par nom, nom latin ou famille" value="'+e(V.query)+'" data-hi="'+h(V.onSearch)+'" placeholder="Chercher un nom, un latin, une famille…" style="flex:1;border:0;outline:0;font:400 14px/1 var(--font-body);color:var(--fg-1);min-width:0;background:transparent"></div><div style="font:600 12px/1 var(--font-mono);color:var(--fg-3)">'+V.atlasCount+' espèces</div></div>'
      +'<div style="display:flex;flex-wrap:wrap;gap:6px">'+V.listChips.map(c=>'<button class="ch" data-on="'+c.on+'" aria-pressed="'+(c.on==='1')+'" data-h="'+h(c.go)+'">'+e(c.label)+'</button>').join('')+'</div>'
      +'<div class="r-grid">'+V.atlasList.map(s=>'<button class="gc" data-h="'+h(s.go)+'"><div style="position:relative"><img src="'+e(s.thumb)+'" alt="" loading="lazy" style="width:100%;aspect-ratio:1/1;object-fit:cover;background:var(--color-navy-50)"><div style="position:absolute;top:8px;right:8px;padding:3px 8px;border-radius:999px;background:var(--overlay-light);font:700 10px/1.3 var(--font-mono);color:var(--fg-2)">'+e(s.badge)+'</div></div><div style="padding:11px 12px 13px"><div style="font:700 13px/1.25 var(--font-body)">'+e(s.name)+'</div><div style="font:italic 400 11px/1.3 var(--font-body);color:var(--fg-3)">'+e(s.latin)+'</div><div style="height:3px;margin-top:9px;background:var(--color-navy-100);border-radius:999px;overflow:hidden"><div style="height:100%;background:'+s.barColor+';width:'+s.pct+'%"></div></div></div></button>').join('')+'</div></div>';
    }
    if(V.isFiche){
      return '<div class="r-two"><div><div style="border:1px solid var(--border);border-radius:12px;overflow:hidden;background:var(--color-navy-50)"><img src="'+e(V.fImg)+'"'+dim(V.fW,V.fH)+' alt="'+e(V.fAlt)+'" style="width:100%;max-height:64vh;object-fit:contain;display:block;background:var(--color-navy-50)"></div>'
      +'<div style="display:flex;gap:8px;overflow-x:auto;padding:12px 0 4px">'+V.fThumbs.map(t=>'<button type="button" aria-label="Voir : '+e(t.alt)+'" aria-current="'+t.courant+'" data-h="'+h(t.go)+'" style="padding:0;border:2px solid '+t.border+';border-radius:8px;background:none;cursor:pointer;flex:0 0 auto"><img src="'+e(t.u)+'" alt="" loading="lazy" width="72" height="72" style="width:72px;height:72px;object-fit:cover;border-radius:6px;display:block;background:var(--color-navy-50)"></button>').join('')+'</div>'
      +'<div style="font:600 12px/1.3 var(--font-body);color:var(--fg-3)">'+e(V.fImgAsp)+'</div>'
      +credit(V.fCredit,V.fCreditUrl)+'</div>'
      +'<div><div style="font:700 10px/1 var(--font-condensed);letter-spacing:.14em;text-transform:uppercase;color:var(--color-brand-red)">'+e(V.fCat)+'</div><div style="margin-top:10px;font:700 28px/1.12 var(--font-brand);letter-spacing:-.015em">'+e(V.fName)+'</div><div style="font:italic 400 15px/1.35 var(--font-body);color:var(--fg-3)">'+e(V.fLatin)+'</div>'
      +'<div style="margin-top:20px">'+this.fieldsHtml(V.fFields,'38%')+'</div>'
      +(V.fHasTips?'<div style="margin-top:18px;padding:14px;border-radius:8px;background:var(--color-warning-soft)"><div style="font:700 9px/1 var(--font-condensed);letter-spacing:.14em;text-transform:uppercase;color:var(--color-warning)">Confusions fréquentes</div>'+V.fTips.map(t=>'<div style="margin-top:9px;font:400 13px/1.45 var(--font-body)">'+e(t.txt)+'</div>').join('')+'</div>':'')
      +'<div style="display:flex;gap:8px;margin-top:18px"><button class="ib" data-h="'+h(V.fPrev)+'">Précédente</button><button class="ib" data-h="'+h(V.fNext)+'">Suivante</button></div></div></div>';
    }
    if(V.isTrierPick){
      return '<div style="max-width:720px;display:flex;flex-direction:column;gap:18px"><div><div style="font:700 26px/1.15 var(--font-brand);letter-spacing:-.015em">Oui ou non, espèce par espèce</div><div style="font:400 14px/1.45 var(--font-body);color:var(--fg-3);max-width:54ch">Choisis une question — fixation d\'azote, exposition, comestibilité… — puis réponds oui ou non pour chaque espèce.</div></div>'
      +'<div style="display:flex;flex-wrap:wrap;gap:6px">'+V.catChips.map(c=>'<button class="ch" data-on="'+c.on+'" aria-pressed="'+(c.on==='1')+'" data-h="'+h(c.go)+'">'+e(c.label)+'</button>').join('')+'</div>'
      +'<div style="display:flex;flex-direction:column;gap:8px">'+(V.criteria.length?V.criteria.map(c=>'<button class="opt" data-h="'+h(c.go)+'"><span>'+e(c.q)+'</span><span style="font:600 11px/1 var(--font-mono);color:var(--fg-3)">'+c.n+' espèces</span></button>').join(''):'<div style="font:400 14px/1.5 var(--font-body);color:var(--fg-3)">Aucune question applicable à cette catégorie — change de catégorie ci-dessus.</div>')+'</div></div>';
    }
    if(V.isTrierPlay){
      return '<div style="max-width:440px;margin:0 auto;display:flex;flex-direction:column;gap:12px"><div style="text-align:center;font:700 19px/1.3 var(--font-body)">'+e(V.critQ)+'</div>'
      +'<div class="critstack">'
        +(V.critHasBack?'<div class="critcard critback"><div class="cimg"><img src="'+e(V.critBackImg)+'" alt=""></div><div class="cmeta"><div style="font:700 17px/1.2 var(--font-body)">'+e(V.critBackName)+'</div></div></div>':'')
        +'<div class="critcard '+V.critAnim+'" data-drag="1" tabindex="0" role="group" aria-label="'+e(V.critTopName)+' — répondre par les flèches, O pour oui, N pour non"><div class="cimg"><img src="'+e(V.critTopImg)+'" alt=""></div><div class="cmeta"><div style="font:700 17px/1.2 var(--font-body)">'+e(V.critTopName)+'</div><div style="font:italic 400 12px/1.3 var(--font-body);color:var(--fg-3);margin-top:3px">'+e(V.critTopLatin)+'</div></div></div>'
      +'</div>'
      +'<div role="status" aria-live="polite">'+(V.critHasFb?'<div class="critbanner '+(V.critFbOk?'ok':'no')+'">'+e(V.critFb)+'</div>':'')+'</div>'
      +(V.critHasFb?'':'<div style="font:400 12px/1.4 var(--font-body);color:var(--fg-3);text-align:center">Swipe la carte, ou les boutons, ou au clavier : <kbd>←</kbd> / <kbd>N</kbd> non &nbsp;·&nbsp; <kbd>→</kbd> / <kbd>O</kbd> oui</div>')
      +'<div style="display:flex;gap:10px"><button class="opt" style="justify-content:center" data-h="'+h(V.critNo)+'"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--color-danger)" stroke-width="2" stroke-linecap="round"><path d="M18 6L6 18M6 6l12 12"></path></svg>Non</button><button class="opt" style="justify-content:center" data-h="'+h(V.critYes)+'"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--color-success)" stroke-width="2" stroke-linecap="round"><path d="M20 6L9 17l-5-5"></path></svg>Oui</button></div>'
      +'<div role="status" aria-live="polite" style="text-align:center;font:600 12px/1 var(--font-mono);color:var(--fg-3)">'+e(V.critScore)+'</div></div>';
    }
    if(V.isProgres){
      const row=r=>'<div style="padding:12px 0;border-bottom:1px solid var(--border)"><div style="display:flex;align-items:baseline;justify-content:space-between;gap:12px;flex-wrap:wrap"><span style="font:600 14px/1.2 var(--font-body)">'+e(r.label)+'</span><span style="font:700 12px/1 var(--font-mono);color:var(--fg-3)">'+e(r.right)+'</span></div><div style="height:6px;margin-top:10px;background:var(--color-navy-100);border-radius:999px;overflow:hidden"><div style="height:100%;background:'+r.bar+';width:'+r.pct+'%"></div></div><div style="margin-top:7px;font:500 11px/1.2 var(--font-body);color:var(--fg-3)">'+e(r.acc)+'</div></div>';
      const stat=(n,l,c)=>'<div><div style="font:700 34px/1 var(--font-headline-data)'+(c?';color:'+c:'')+'">'+n+'</div><div style="font:600 11px/1.2 var(--font-body);color:var(--fg-3);margin-top:6px">'+l+'</div></div>';
      return '<div style="display:flex;flex-direction:column;gap:24px;max-width:820px">'
      +'<div style="display:flex;flex-wrap:wrap;gap:28px;padding-bottom:22px;border-bottom:1px solid var(--border)">'+stat(V.totalKnown,'espèces maîtrisées')+stat(V.totalSeen,'espèces vues')+stat(V.totalReps,'réponses données')+stat(V.best,'meilleure série','var(--color-success)')+'</div>'
      +'<div><div style="font:700 9px/1 var(--font-condensed);letter-spacing:.14em;text-transform:uppercase;color:var(--fg-3);margin-bottom:6px">Reconnaissance — par compétence</div><div style="font:400 13px/1.5 var(--font-body);color:var(--fg-3);max-width:60ch;margin-bottom:14px">Reconnaître une écorce, une fleur ou une fiche de caractères sont des compétences distinctes : chacune est suivie séparément.</div>'+V.skillRows.map(row).join('')+'</div>'
      +'<div><div style="font:700 9px/1 var(--font-condensed);letter-spacing:.14em;text-transform:uppercase;color:var(--fg-3);margin-bottom:6px">Critères écologiques — oui / non</div><div style="font:400 13px/1.5 var(--font-body);color:var(--fg-3);max-width:60ch;margin-bottom:14px">Ta fiabilité question par question.</div>'+V.critRows.map(row).join('')+'</div>'
      +'<div><div style="font:700 9px/1 var(--font-condensed);letter-spacing:.14em;text-transform:uppercase;color:var(--fg-3);margin-bottom:14px">Couverture par catégorie</div>'+V.catCards.map(c=>'<div style="padding:12px 0;border-bottom:1px solid var(--border)"><div style="display:flex;align-items:baseline;justify-content:space-between;gap:12px"><span style="font:600 14px/1 var(--font-body)">'+e(c.label)+'</span><span style="font:700 12px/1 var(--font-mono);color:var(--fg-3)">'+c.n+'</span></div><div style="height:6px;margin-top:10px;background:var(--color-navy-100);border-radius:999px;overflow:hidden"><div style="height:100%;background:var(--color-navy-900);width:'+c.pct+'%"></div></div></div>').join('')+'</div>'
      +'<div><div style="font:700 9px/1 var(--font-condensed);letter-spacing:.14em;text-transform:uppercase;color:var(--fg-3);margin-bottom:12px">Sauvegarde</div><div style="font:400 13px/1.5 var(--font-body);color:var(--fg-3);max-width:56ch;margin-bottom:14px">La progression reste dans ce navigateur. Exporte un fichier pour la garder ou changer d\'appareil.</div><div style="display:flex;flex-wrap:wrap;gap:8px"><button class="ib" data-h="'+h(V.exportProg)+'">Exporter ma progression</button><button class="ib" data-h="'+h(V.importProg)+'">Importer un fichier</button><button class="ib" data-h="'+h(V.replaceProg)+'">Remplacer par un fichier…</button><button class="ib" data-h="'+h(V.resetProg)+'" style="color:var(--color-brand-red)">Réinitialiser</button></div><input id="prog-file" type="file" accept="application/json,.json" data-hc="'+h(V.onImportFile)+'" style="display:none">'+(V.progMsg?'<div role="status" style="margin-top:12px;padding:10px 12px;border-radius:8px;font:600 12px/1.45 var(--font-body);background:'+(V.progMsgOk==='1'?'var(--color-success-soft);color:var(--color-success)':'var(--color-warning-soft);color:var(--color-warning)')+'">'+e(V.progMsg)+'</div>':'')+'</div>'
      +(V.horsLigneDispo==='1'?'<div><div style="font:700 9px/1 var(--font-condensed);letter-spacing:.14em;text-transform:uppercase;color:var(--fg-3);margin-bottom:12px">Hors ligne</div>'
        +'<div style="font:400 13px/1.5 var(--font-body);color:var(--fg-3);max-width:56ch;margin-bottom:14px">L\'app fonctionne sans réseau une fois ouverte, et garde les photos déjà vues. Pour partir sur le terrain, télécharge les photos d\'une catégorie à l\'avance.</div>'
        +'<div style="display:flex;flex-wrap:wrap;gap:8px">'+V.offCats.map(c=>'<button class="ib" data-h="'+h(c.go)+'"'+(V.dlEnCours==='1'?' disabled':'')+'>'+e(c.label)+' · '+e(c.taille)+'</button>').join('')
        +'<button class="ib" data-h="'+h(V.viderImages)+'" style="color:var(--color-brand-red)">Vider les photos</button></div>'
        +(V.dlEnCours==='1'?'<div style="margin-top:12px"><div style="font:600 12px/1.4 var(--font-body);color:var(--fg-2)">'+e(V.dlLibelle)+'</div><div style="height:6px;margin-top:6px;background:var(--color-navy-100);border-radius:999px;overflow:hidden"><div style="height:100%;width:'+V.dlPct+'%;background:var(--color-success)"></div></div></div>':'')
        +(V.offMsg?'<div role="status" style="margin-top:12px;padding:10px 12px;border-radius:8px;font:600 12px/1.45 var(--font-body);background:var(--color-success-soft);color:var(--color-success)">'+e(V.offMsg)+'</div>':'')
        +'</div>':'')
      +'<div style="font:400 11px/1.5 var(--font-body);color:var(--fg-4);padding-top:8px;border-top:1px solid var(--border)">Photos : Wikimedia Commons &amp; iNaturalist (licences libres / CC). <a href="https://github.com/iribarnesy/atlas-especes" target="_blank" rel="noopener">Contribuer sur GitHub</a></div>'
      +'</div>';
    }
    return '';
  }
  navBtn(cls,key,label,onKey,goKey,V,sz){const actif=V[onKey]==='1';
    return '<button class="'+cls+'" data-on="'+V[onKey]+'"'+(actif?' aria-current="page"':'')
      +' data-h="'+h(V[goKey])+'">'+navIcon(key,sz)+label+'</button>';}
  tpl(V){
    const rail='<aside class="r-rail" style="flex-direction:column;gap:2px;position:sticky;top:0;height:100vh;padding:24px 16px;background:var(--bg-card);border-right:1px solid var(--border)">'
      +'<div style="display:flex;align-items:center;gap:10px;padding:0 4px 22px"><div style="width:4px;height:34px;background:var(--color-brand-red)"></div><div><div style="font:800 15px/1.05 var(--font-brand);letter-spacing:-.01em">Atlas des espèces</div><div style="font:700 9px/1.4 var(--font-condensed);letter-spacing:.14em;text-transform:uppercase;color:var(--fg-3)">Forêt-jardin · tempéré</div></div></div>'
      +this.navBtn('nb','reviser','Réviser','onReviser','goReviser',V,18)+this.navBtn('nb','atlas','Atlas','onAtlas','goAtlas',V,18)+this.navBtn('nb','trier','Oui / Non','onTrier','goTrier',V,18)+this.navBtn('nb','progres','Progrès','onProgres','goProgres',V,18)
      +'<div style="flex:1"></div>'
      +(V.showMastery?'<div style="padding:14px;border:1px solid var(--border);border-radius:8px;background:var(--color-navy-50)"><div style="font:700 9px/1 var(--font-condensed);letter-spacing:.14em;text-transform:uppercase;color:var(--fg-3)">Maîtrisées</div><div style="display:flex;align-items:baseline;gap:6px;margin-top:6px"><span style="font:700 26px/1 var(--font-headline-data)">'+V.totalKnown+'</span><span style="font:600 13px/1 var(--font-body);color:var(--fg-3)">/ '+V.totalCount+' espèces</span></div><div style="margin-top:6px;font:500 10px/1.35 var(--font-body);color:var(--fg-3)">photo <em>et</em> fiche acquises</div><div style="height:4px;margin-top:10px;background:var(--color-navy-200);border-radius:999px;overflow:hidden"><div style="height:100%;background:var(--color-brand-red);width:'+V.totalPct+'%"></div></div></div>':'')
      +'</aside>';
    const header='<header style="position:sticky;top:0;z-index:30;display:flex;align-items:center;justify-content:space-between;gap:12px;padding:10px 16px;background:var(--bg-card);border-bottom:1px solid var(--border)"><div style="display:flex;align-items:center;gap:10px;min-width:0">'
      +(V.showBack?'<button class="ib" style="padding:8px 12px" data-h="'+h(V.back)+'"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M15 18l-6-6 6-6"></path></svg>Retour</button>':'')
      +'<div style="min-width:0"><div style="font:700 9px/1.3 var(--font-condensed);letter-spacing:.14em;text-transform:uppercase;color:var(--color-brand-red)">'+e(V.crumb)+'</div><div style="font:700 15px/1.2 var(--font-body);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">'+e(V.title)+'</div></div></div>'
      +'<div style="display:flex;align-items:center;gap:7px;padding:7px 12px;border-radius:999px;background:var(--panel-dark-bg);color:var(--panel-dark-fg)"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--color-yellow)" stroke-width="2" stroke-linecap="round"><path d="M12 3l2.6 5.6 6.1.8-4.5 4.2 1.2 6-5.4-3-5.4 3 1.2-6L3.3 9.4l6.1-.8z"></path></svg><span style="font:700 13px/1 var(--font-mono);color:var(--panel-dark-fg)">'+V.streak+'</span><span style="font:600 11px/1 var(--font-body);color:var(--color-navy-300)">série</span></div></header>';
    const tabs='<nav class="r-tabs" style="position:fixed;bottom:0;left:0;right:0;z-index:40;display:flex;background:var(--bg-card);border-top:1px solid var(--border);padding-bottom:env(safe-area-inset-bottom)">'
      +this.navBtn('tb','reviser','Réviser','onReviser','goReviser',V,21)+this.navBtn('tb','atlas','Atlas','onAtlas','goAtlas',V,21)+this.navBtn('tb','trier','Oui / Non','onTrier','goTrier',V,21)+this.navBtn('tb','progres','Progrès','onProgres','goProgres',V,21)+'</nav>';
    return '<div class="r-shell">'+rail+'<main style="min-width:0;width:100%">'+header+'<div class="r-pad">'+this.viewHtml(V)+'</div>'+tabs+'</main></div>';
  }
  bind(){
    const root=document.getElementById('app');
    root.querySelectorAll('[data-h]').forEach(el=>{el.addEventListener('click',ev=>{const f=H[+el.getAttribute('data-h')];if(f)f(ev);});});
    root.querySelectorAll('[data-hi]').forEach(el=>{el.addEventListener('input',ev=>{const f=H[+el.getAttribute('data-hi')];if(f)f(ev);});});
    root.querySelectorAll('[data-hk]').forEach(el=>{el.addEventListener('keydown',ev=>{const f=H[+el.getAttribute('data-hk')];if(f)f(ev);});});
    root.querySelectorAll('[data-hc]').forEach(el=>{el.addEventListener('change',ev=>{const f=H[+el.getAttribute('data-hc')];if(f)f(ev);});});
    const top=root.querySelector('.critstack [data-drag]');
    if(top){let x0=0,dx=0,drag=false;const self=this;top.style.touchAction='pan-y';
      top.addEventListener('pointerdown',ev=>{if(self._critBusy)return;drag=true;x0=ev.clientX;dx=0;try{top.setPointerCapture(ev.pointerId);}catch(e){}});
      top.addEventListener('pointermove',ev=>{if(!drag)return;dx=ev.clientX-x0;top.style.transform='translateX('+dx+'px) rotate('+(dx/22)+'deg)';top.style.opacity=String(1-Math.min(Math.abs(dx)/480,.4));});
      top.addEventListener('pointerup',()=>{if(!drag)return;drag=false;if(Math.abs(dx)>70){self.critAns(dx>0)();}else{top.style.transition='transform .15s,opacity .15s';top.style.transform='';top.style.opacity='1';setTimeout(()=>{top.style.transition='';},160);}dx=0;});}
  }
  // Bandeaux d'état : sans réseau (l'app marche quand même) et nouvelle version prête.
  bandeaux(V){let out='';
    if(V.horsLigne==='1')out+='<div class="etat etat-off" role="status">Hors ligne — l\'atlas et les photos déjà vues restent disponibles.</div>';
    if(V.majPrete==='1')out+='<div class="etat etat-maj" role="status">Nouvelle version téléchargée. <button class="lien" data-h="'+h(V.appliquerMaj)+'">Recharger</button></div>';
    return out;}
  render(){
    const ae=document.activeElement,aid=ae&&ae.id,asel=(ae&&ae.selectionStart!=null)?ae.selectionStart:null;
    H=[];const V=this.renderVals();
    document.getElementById('app').innerHTML=this.bandeaux(V)+this.tpl(V);this.bind();
    if(aid){const el=document.getElementById(aid);if(el){el.focus();try{if(asel!=null)el.setSelectionRange(asel,asel);}catch(e){}}}
  }
}
const APP=new App();
window.addEventListener('popstate',ev=>{if(ev.state&&ev.state.v)APP.restore(ev.state);});
window.addEventListener('keydown',ev=>{
  if(APP.state.view==='trierPlay'&&!APP._critBusy){
    const k=ev.key.toLowerCase();
    if(ev.key==='ArrowRight'||k==='o'||k==='y'){ev.preventDefault();APP.critAns(true)();}
    else if(ev.key==='ArrowLeft'||k==='n'){ev.preventDefault();APP.critAns(false)();}}
});
APP.mount();
"""
