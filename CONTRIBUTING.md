# Contribuer à l'atlas

Merci ! On peut contribuer de trois façons, toutes par **Pull Request**. Pas besoin de savoir
coder : il s'agit d'éditer des tableaux Markdown et de déposer des images.

> Workflow général : **Fork** le dépôt → fais tes changements → ouvre une **Pull Request**.
> Un mainteneur relit, puis fusionne. Le site se reconstruit et se redéploie tout seul.

## Où contribuer en priorité ?

Le fichier **[COUVERTURE.md](COUVERTURE.md)** liste, pour chaque espèce, les aspects
(feuille, écorce, fruit, fleur, port) qui ont déjà une photo (✓) et ceux qui **manquent** (✗).
C'est la meilleure carte des trous à combler. Il est régénéré par `scripts/couverture.py`.

## Ce que la vérification automatique contrôle

À chaque Pull Request, `scripts/verifier_atlas.py` relit tout le dépôt. Il distingue les
**erreurs** ❌ (la PR ne passe pas : la donnée est cassée ou n'apparaîtra pas dans le site)
des **avertissements** ⚠ (à corriger, sans bloquer).

| Ce qui est contrôlé | Niveau |
|---|---|
| Tableaux : nombre de colonnes, vignette `![[...]]` présente et fichier existant, nom non vide | ❌ |
| Nom latin : forme « Genre espèce » (tolère `sp.`, hybrides `×`, sous-espèces, cultivars, notes entre parenthèses, alternatives `A / B`) | ❌ |
| Deux espèces qui partagent la même vignette (elles partageraient toutes leurs photos) | ❌ |
| Photo de `img/quiz-extra/` rattachée à aucune espèce, ou à plusieurs | ❌ |
| `_aspects.tsv` : aspect inconnu, ligne visant un fichier qui n'existe pas | ❌ |
| `contributions/*.tsv` : action inconnue, fichier absent, `reassign` vers une espèce inexistante, aspect inconnu | ❌ |
| `Confusions - référence.md` : espèce inconnue, groupe sans « ce qui tranche » | ❌ |
| Mot-clé d'aspect non reconnu dans un nom de photo (l'aspect est perdu) | ⚠ |
| Vignette de `img/especes/` utilisée par aucune espèce | ⚠ |
| Ligne sans tabulation dans un `.tsv`, `tag` sans aspect, groupe de confusion à une seule espèce | ⚠ |

Lance-le en local avant d'ouvrir ta PR : `python3 scripts/verifier_atlas.py`.

## 1. Ajouter / corriger une **note** ou un **champ**

Ouvre le fichier d'atlas concerné (par ex. `Espèces herbacées - référence.md`), trouve la
ligne de l'espèce et modifie la cellule voulue (colonne *Notes*, *Comestible*, etc.). Garde le
format du tableau (mêmes colonnes, séparées par `|`).

## 2. Ajouter une **photo** à une espèce existante

1. Repère le **stem** (préfixe de fichier) de l'espèce = le nom de sa vignette dans
   `img/especes/` (par ex. `sauge.jpg` → stem = `sauge`).
2. Dépose ta photo dans **`img/quiz-extra/`** en la nommant :
   `stem-aspect-n.jpg` — où *aspect* ∈ `feuille`, `ecorce`, `fruit`, `fleur`, `port`,
   `rameau` (rameau d'hiver / bourgeons, comme on identifie un ligneux hors saison).
   Plusieurs aspects possibles avec `_`, ex. `sauge-feuille_fleur-1.jpg`.
   Synonymes acceptés : `feuilles`, `fruits`, `fleurs`, `rameaux`, `bourgeon`, `hiver`,
   `silhouette`. La liste fait foi dans `scripts/atlas_data.py` (constante `ASPECTS`).
   Exemple : `sauge-fleur-2.jpg`.
   Le **tiret après le stem est obligatoire** : `ail_des_ours-1.jpg` est une photo de l'ail
   des ours, pas de l'ail. Une photo qui ne suit pas la convention n'est rattachée à aucune
   espèce — `scripts/verifier_atlas.py` la signale.
3. Formats : **JPG**, idéalement ≤ ~1500 px de large (photos nettes, sujet bien visible).

> Tu peux aussi annoter l'aspect d'une image sans la renommer, via le fichier
> `img/quiz-extra/_aspects.tsv` (une ligne `nom_du_fichier.jpg⇥feuille,fleur`).

## 3. Ajouter une **nouvelle espèce**

1. Ajoute **une ligne** dans le bon fichier d'atlas, en respectant exactement les colonnes de
   l'en-tête du tableau. Regarde une ligne existante comme modèle.
   - La 1re cellule est la vignette : `![[stem.jpg\|200]]`.
2. Ajoute la vignette correspondante dans **`img/especes/stem.jpg`**.
3. (Facultatif) Ajoute des photos supplémentaires dans `img/quiz-extra/` (voir §2).

## Droits des images ⚠️

N'ajoute que des photos **que tu as prises** ou sous **licence libre** (Wikimedia Commons,
iNaturalist CC, etc.). Indique la source dans la description de ta Pull Request si ce n'est pas
une de tes photos. Les images sans droits clairs seront retirées.

## Vérifier en local (facultatif)

```bash
python3 scripts/verifier_atlas.py         # tableaux bien formés, vignettes présentes
python3 scripts/build_web.py _site
cd _site && python3 -m http.server 8000   # http://localhost:8000
```

Si tu touches aux **scripts** (et non seulement aux données), lance aussi les tests :

```bash
python3 -m pip install -r requirements-dev.txt   # une fois
python3 -m pytest
```

Ces deux vérifications tournent de toute façon automatiquement sur ta Pull Request.

## Sécurité / bon sens

- Une espèce **toxique ou mortelle** ? Signale-le clairement dans *Comestible* / *Notes*
  (avec ⚠), et mentionne les confusions dangereuses.
- Ce site est une aide à l'apprentissage, **jamais** une clé de comestibilité fiable : ne
  jamais consommer sur la seule foi de l'atlas.
