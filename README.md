# 🌳 Atlas & quiz des espèces

Un atlas et un quiz d'identification d'espèces (arbres & arbustes, herbacées & aromatiques,
champignons, faune, fougères/graminées/mousses/lichens) orienté **forêt-jardin, agroforesterie
et écosystèmes tempérés**.

- **Quiz** : reconnaître une espèce à la photo **ou** d'après sa fiche de caractères (deux
  compétences suivies séparément), en mode *Apprendre* / *Réviser*, filtrable par aspect
  (feuille, écorce, fruit, fleur, port), en facile (QCM) ou difficile (saisie).
- **Atlas** : fiche complète de chaque espèce + toutes ses photos.
- **Progression** sauvegardée dans le navigateur, exportable / importable (fichier `.json`).

Le site est **statique** : une page `index.html` + les images. Aucune donnée n'est envoyée
nulle part ; tout reste dans ton navigateur.

## 🌐 Site en ligne

Publié via **GitHub Pages** (voir l'URL dans l'onglet *Settings → Pages* du dépôt).

## 🤝 Contribuer

Tout le monde peut proposer des **photos**, des **notes** ou de **nouvelles espèces** via une
Pull Request. Voir **[CONTRIBUTING.md](CONTRIBUTING.md)**.

## 🛠 Lancer / construire en local

```bash
python3 scripts/build_web.py _site        # construit le site dans _site/
cd _site && python3 -m http.server 8000   # puis ouvrir http://localhost:8000
```

Le build est en Python pur (aucune dépendance, pas de compression d'image) : il lit les
atlas Markdown + les images et produit `index.html` avec des liens d'images **en pleine
résolution**. À chaque push sur `main`, GitHub Actions reconstruit et redéploie le site.

## 📁 Structure

```
Espèces - référence.md            atlas des ligneux (arbres/arbustes)
Espèces herbacées - référence.md  herbacées, légumes, aromatiques
Champignons - référence.md        champignons
Faune - référence.md              faune (auxiliaires, pollinisateurs, ravageurs…)
Espèces diverses - référence.md   fougères, graminées, mousses, lichens
img/especes/                      vignette principale de chaque espèce
img/quiz-extra/                   photos supplémentaires + _aspects.tsv (annotation des aspects)
scripts/build_web.py              build du site statique (utilisé par la CI)
scripts/generer_quiz.py           build local des versions autonome / Artifact (macOS)
```

## 🖼 Crédits photos

Wikimedia Commons & iNaturalist (licences libres / CC). Chaque contributeur reste responsable
des droits des images qu'il ajoute (voir CONTRIBUTING).
