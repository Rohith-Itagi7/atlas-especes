# Contributions

Ce dossier reçoit les fichiers `*.tsv` de corrections proposés **depuis l'application**
(bouton « 🚀 Publier mes changements ») ou à la main.

Format « actions » (TSV, en-tête `action⇥fichier⇥valeur`) :

| action | valeur | effet |
|---|---|---|
| `tag` | `feuille,fleur` | force les aspects d'une photo |
| `reassign` | `stem_correct` | la photo appartient en fait à cette autre espèce (déplacement) |
| `remove` | *(vide)* | retire la photo (mauvaise attribution) |

Exemple :

```
action	fichier	valeur
tag	sauge-fleur-2.jpg	fleur,feuille
reassign	abricotier-1.jpg	cerisier
remove	molinie-3.jpg
```

- Ces actions sont **appliquées au build** (elles complètent / écrasent les sources).
- Les lignes commençant par `#` sont des commentaires (ex. manques signalés) — ignorées.
- Le mainteneur consolide ensuite dans les sources (`img/quiz-extra/_aspects.tsv` pour les tags,
  renommage/suppression des fichiers pour reassign/remove) puis supprime le fichier de contribution.
