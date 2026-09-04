# 🌳 Atlas & quiz des espèces

Un atlas et un quiz d'identification d'espèces (arbres & arbustes, herbacées & aromatiques,
champignons, faune, fougères/graminées/mousses/lichens) orienté **forêt-jardin, agroforesterie
et écosystèmes tempérés**.

- **Quiz** : reconnaître une espèce à la photo **ou** d'après sa fiche de caractères (deux
  compétences suivies séparément), filtrable par aspect (feuille, écorce, fruit, fleur,
  port), en facile (QCM) ou difficile (saisie).
- **Atlas** : fiche complète de chaque espèce + toutes ses photos.
- **Révision espacée** : le tirage n'est pas aléatoire. Chaque carte (une espèce × une
  compétence) monte d'une boîte à chaque bonne réponse et redescend d'une à chaque erreur,
  avec des écarts de 1, 3, 7, 16 puis 35 jours. Le quiz sert d'abord les cartes **échues**
  (les plus en retard d'abord), puis celles jamais vues, puis les plus anciennes.
- **Progression** sauvegardée dans le navigateur, **exportable / importable** (fichier `.json`) :
  l'import **fusionne** par défaut (additionne les compteurs, pour récupérer sa progression
  depuis un autre appareil), avec un bouton séparé pour **remplacer**. Les fichiers exportés
  par les versions précédentes restent lisibles.

Le site est **statique** : une page `index.html` + les images. Aucune donnée n'est envoyée
nulle part ; tout reste dans ton navigateur.

## 🔗 Liens partageables

Chaque écran a son adresse, lisible et copiable — un bouton *Copier le lien* est là pour ça :

| Adresse | Ce qu'elle ouvre |
|---|---|
| `#/espece/alisier` | la fiche de l'alisier torminal |
| `#/atlas?cat=champignon&q=amanite` | l'atlas filtré sur les amanites |
| `#/quiz?cat=ligneux&type=fiche&diff=saisie` | un quiz de fiches sur les ligneux, en saisie |
| `#/trier/comest` | le tri Oui/Non « est-ce comestible ? » |
| `#/progres` | ma session |

F5 revient au même écran, les boutons *Précédent* / *Suivant* du navigateur suivent la
navigation, et une espèce inconnue (fichier renommé, lien vieilli) retombe sur l'atlas
complet avec un message plutôt qu'une page vide.

## ♿ Accessibilité et thème sombre

Le site suit le **thème du système** (clair ou sombre) : toutes les couleurs passent par des
jetons CSS, aucune n'est écrite en dur, et `tests/test_contraste.py` vérifie les rapports de
contraste WCAG AA des deux thèmes à chaque exécution des tests.

Tout est utilisable **au clavier seul** (navigation, grille, fiche, quiz, Oui/Non avec
`←`/`N` et `→`/`O`), avec un anneau de focus visible. Les photos ont des alternatives
textuelles qui nomment l'espèce et l'aspect — sauf dans le quiz avant la réponse, où
l'alternative ne dit que l'aspect pour ne pas donner la solution. Les résultats sont annoncés
aux lecteurs d'écran, et `prefers-reduced-motion` désactive les animations de cartes.

## 📴 Hors ligne

L'atlas sert sur le terrain, là où il n'y a pas de réseau. Une fois la page ouverte une
première fois, elle **redémarre sans connexion** (service worker), et toute photo consultée
reste consultable. Le site s'**installe** aussi sur l'écran d'accueil (Android, iOS).

Les 33 Mo de photos ne sont **pas** téléchargés d'office : dans *Progrès → Hors ligne*, un
bouton par catégorie annonce sa taille et télécharge ses photos à la demande
(ligneux ~19 Mo, herbacées ~16 Mo, champignons ~2,9 Mo, faune ~2,1 Mo, diverses ~2,0 Mo),
avec une barre de progression et un bouton pour tout effacer.

Quand une nouvelle version est publiée, elle est téléchargée en arrière-plan et un bandeau
propose de **recharger** — rien ne change sous les pieds pendant une session de quiz.

## 🌐 Site en ligne

Publié via **GitHub Pages** (voir l'URL dans l'onglet *Settings → Pages* du dépôt).

## 🤝 Contribuer

Tout le monde peut proposer des **photos**, des **notes** ou de **nouvelles espèces** via une
Pull Request. Voir **[CONTRIBUTING.md](CONTRIBUTING.md)**.

## 📝 Quels fichiers éditer ?

**✍️ À éditer à la main (sources) :**

| Fichier | Rôle |
|---|---|
| `Espèces*.md`, `Champignons*.md`, `Faune*.md` | Les espèces et leurs infos (tableaux Markdown) |
| `img/especes/`, `img/quiz-extra/` | Les photos |
| `img/quiz-extra/_aspects.tsv` | Annotation des aspects : `fichier → aspects` |
| `contributions/*.tsv` | Contributions d'aspects (via l'app ou à la main) |

**🤖 Générés automatiquement — NE PAS éditer (écrasés au build) :**

| Fichier | Généré par |
|---|---|
| `COUVERTURE.md` | `scripts/couverture.py` (CI, à chaque merge sur `main`) |
| `index.html` du site, `_site/` | `scripts/build_web.py` (CI) |
| `Quiz especes*.html` (local) | `scripts/generer_quiz.py` |

## 🛠 Lancer / construire en local

```bash
python3 scripts/build_web.py _site        # construit le site dans _site/
cd _site && python3 -m http.server 8000   # puis ouvrir http://localhost:8000
```

Le build lit les atlas Markdown + les images et produit `index.html`. Les photos sont
copiées telles quelles (le quiz et la fiche les affichent en pleine résolution), et le build
produit en plus **une vignette de 320 px par image** pour les affichages petits — grille de
l'atlas, bandeau de la fiche, cartes Oui/Non. Le premier écran de l'atlas passe ainsi de
~2,1 Mo à ~0,5 Mo.

Les vignettes demandent **Pillow** (`pip install Pillow`), seule dépendance du build, et
seulement pour cette étape : sans elle, `build_web.py` fonctionne comme avant et sert les
originaux, avec un avertissement. Les vignettes déjà à jour ne sont pas régénérées (un
manifeste dans le dossier de sortie compare date et taille des sources), donc un rebuild
local est instantané.

À chaque push sur `main`, GitHub Actions reconstruit et redéploie le site.

## ✅ Lancer les tests

```bash
python3 -m pip install -r requirements-dev.txt   # une fois : installe pytest
python3 -m pytest                                # ~1 s
```

Les tests couvrent la lecture des atlas (colonnes, vignettes, aspects des photos), les
contributions (`tag` / `reassign` / `remove`), les groupes de confusion, la règle
« Est-ce comestible ? » du mode Oui/Non, et un test de bout en bout du build du site.

La **planification de la révision** est testée à part (`tests/test_revision.py`) : le JS
réellement livré est rejoué sous node avec des dates simulées — barème des intervalles,
séquences de bonnes et de mauvaises réponses, ordre de la file, migration des progressions
d'avant la planification, et le numéro de jour sous cinq fuseaux (dont deux nuits de
changement d'heure, qui ne font pas 24 h).
Ils tournent sur chaque Pull Request, à côté de `scripts/verifier_atlas.py`.

Le parsing est testé sur de **faux atlas** montés dans un dossier temporaire (le contenu
réel bouge à chaque contribution) ; seul `tests/test_build_smoke.py` s'appuie sur les vrais
atlas du dépôt.

## 📁 Structure

```
Espèces - référence.md            atlas des ligneux (arbres/arbustes)
Espèces herbacées - référence.md  herbacées, légumes, aromatiques
Champignons - référence.md        champignons
Faune - référence.md              faune (auxiliaires, pollinisateurs, ravageurs…)
Espèces diverses - référence.md   fougères, graminées, mousses, lichens
img/especes/                      vignette principale de chaque espèce
img/quiz-extra/                   photos supplémentaires + _aspects.tsv (annotation des aspects)
img/CREDITS.tsv                   crédit de chaque image : source, auteur, licence, url
COUVERTURE.md                     carte des aspects présents/manquants par espèce (généré)
scripts/atlas_data.py             couche de données : atlas, photos, contributions, vocabulaire
                                  des aspects (constante ASPECTS = source unique)
scripts/build_web.py              build du site statique (utilisé par la CI)
scripts/site_ui.py                interface du site (CSS + app vanilla)
scripts/site_sw.py                hors ligne : service worker, manifeste, icônes
scripts/derives.py                vignettes légères produites au build (Pillow optionnel)
scripts/generer_quiz.py           build local des versions autonome / Artifact (macOS, `sips`)
scripts/couverture.py             (re)génère COUVERTURE.md
scripts/verifier_atlas.py         validation des atlas et des photos (CI sur les PR)
scripts/consolider_contributions.py  fait entrer les contributions dans les sources
scripts/credits.py                crédits des images (rapport, --init, lecture des API)
tests/                            tests pytest (CI sur les PR)
```

## 🖼 Crédits photos

Le crédit de chaque image vit dans **[`img/CREDITS.tsv`](img/CREDITS.tsv)** :
`fichier⇥source⇥auteur⇥licence⇥url`. Il s'affiche sous la photo, sur la fiche d'espèce et
dans le quiz après la réponse — la plupart des licences CC (CC-BY, CC-BY-SA) l'exigent.

```bash
python3 scripts/credits.py          # combien d'images créditées, lesquelles manquent
python3 scripts/credits.py --init   # ajoute une ligne « inconnu » par image sans crédit
```

⚠️ **État actuel : les 570 images du dépôt sont en `inconnu`.** Elles ont été récupérées
par `scripts/fetch_aspects.py` (Wikimedia Commons) et `scripts/fetch_photos.py`
(iNaturalist), qui ne notaient pas l'auteur et recompressaient les fichiers : la provenance
d'une image ancienne ne peut plus être retrouvée automatiquement, elle se complète à la
main. Les nouvelles images, elles, sont créditées au téléchargement. Chaque contributeur
reste responsable des droits des images qu'il ajoute (voir CONTRIBUTING).

## ⚖️ Licences

Tout est **libre**. Le dépôt mélange trois natures de contenu, qui n'appellent pas la même
licence libre.

| Ce que c'est | Où | Licence |
|---|---|---|
| **Code** | `scripts/`, `tests/`, `.github/` | [MIT](LICENSE) |
| **Contenu rédigé** | `*.md` (atlas, confusions, docs), `*.tsv` du dépôt | [CC BY-SA 4.0](LICENSE-CONTENT) |
| **Photos** | `img/especes/`, `img/quiz-extra/` | **chacune sa licence d'origine** — voir [`img/CREDITS.tsv`](img/CREDITS.tsv) |

**En clair.** Réutilise, modifie, republie, enseigne avec, vends si tu veux. Pour le code,
MIT ne demande que de garder l'avis de copyright. Pour l'atlas, CC BY-SA demande de **citer
la source** et de repartager les versions modifiées **sous la même licence** — ce qui
maintient l'atlas dans le pot commun, façon Wikipédia.

Deux licences plutôt qu'une parce qu'elles ne visent pas la même chose : Creative Commons
déconseille ses propres licences pour du logiciel (rien sur les brevets, la distribution des
sources, la garantie), et MIT ne sait rien dire de l'attribution d'un texte. Le partage à
l'identique de CC BY-SA a l'avantage d'être **compatible avec Wikipédia**, d'où vient une
partie des informations.

⚠️ **Les photos ne sont pas relicenciées par ce dépôt** et ne le peuvent pas : elles
viennent de Wikimedia Commons et d'iNaturalist, chacune sous sa propre licence. Un
réutilisateur doit s'y référer **image par image** dans `img/CREDITS.tsv`, où l'attribution
est aujourd'hui à compléter (voir ci-dessus). En particulier, iNaturalist sert beaucoup de
**CC-BY-NC** : le code et l'atlas sont réutilisables commercialement, **certaines photos ne
le sont pas**.
