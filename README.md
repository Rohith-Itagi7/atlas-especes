# 🌳 Atlas & quiz des espèces

Un atlas et un quiz d'identification d'espèces (arbres & arbustes, herbacées & aromatiques,
champignons, faune, fougères/graminées/mousses/lichens) orienté **forêt-jardin, agroforesterie
et écosystèmes tempérés**.

- **Quiz** : reconnaître une espèce à la photo **ou** d'après sa fiche de caractères (deux
  compétences suivies séparément), en mode *Apprendre* / *Réviser*, filtrable par aspect
  (feuille, écorce, fruit, fleur, port), en facile (QCM) ou difficile (saisie).
- **Atlas** : fiche complète de chaque espèce + toutes ses photos.
- **Progression** sauvegardée dans le navigateur, **exportable / importable** (fichier `.json`) :
  l'import **fusionne** par défaut (additionne les compteurs, pour récupérer sa progression
  depuis un autre appareil), avec un bouton séparé pour **remplacer**. Les fichiers exportés
  par les versions précédentes restent lisibles.

Le site est **statique** : une page `index.html` + les images. Aucune donnée n'est envoyée
nulle part ; tout reste dans ton navigateur.

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

Le build est en Python pur (aucune dépendance, pas de compression d'image) : il lit les
atlas Markdown + les images et produit `index.html` avec des liens d'images **en pleine
résolution**. À chaque push sur `main`, GitHub Actions reconstruit et redéploie le site.

## ✅ Lancer les tests

```bash
python3 -m pip install -r requirements-dev.txt   # une fois : installe pytest
python3 -m pytest                                # ~1 s
```

Les tests couvrent la lecture des atlas (colonnes, vignettes, aspects des photos), les
contributions (`tag` / `reassign` / `remove`), les groupes de confusion, la règle
« Est-ce comestible ? » du mode Oui/Non, et un test de bout en bout du build du site.
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
COUVERTURE.md                     carte des aspects présents/manquants par espèce (généré)
scripts/atlas_data.py             couche de données : atlas, photos, contributions, vocabulaire
                                  des aspects (constante ASPECTS = source unique)
scripts/build_web.py              build du site statique (utilisé par la CI)
scripts/site_ui.py                interface du site (CSS + app vanilla)
scripts/generer_quiz.py           build local des versions autonome / Artifact (macOS, `sips`)
scripts/couverture.py             (re)génère COUVERTURE.md
scripts/verifier_atlas.py         validation des atlas et des photos (CI sur les PR)
scripts/consolider_contributions.py  fait entrer les contributions dans les sources
tests/                            tests pytest (CI sur les PR)
```

## 🖼 Crédits photos

Wikimedia Commons & iNaturalist (licences libres / CC). Chaque contributeur reste responsable
des droits des images qu'il ajoute (voir CONTRIBUTING).
