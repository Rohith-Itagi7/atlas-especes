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
- Les lignes commençant par `#` sont des commentaires (ex. manques signalés). Elles ne sont
  pas perdues : la consolidation les recopie dans [NOTES.md](NOTES.md).

## Consolider dans les sources

Tant qu'une contribution reste ici, elle est réappliquée à chaque build : la vérité est en
deux endroits. Un script la fait entrer dans les sources et supprime le fichier traité :

```bash
python3 scripts/consolider_contributions.py           # décrit le plan, ne touche à rien
python3 scripts/consolider_contributions.py --apply   # exécute
```

| Action | Ce que fait la consolidation |
|---|---|
| `tag` | écrit la ligne dans `img/quiz-extra/_aspects.tsv` (fichier trié) |
| `reassign` | renomme la photo en `<stem cible>-<aspects>-<n>.jpg`, au premier numéro libre, et déplace son entrée d'aspects |
| `remove` | supprime la photo et son entrée d'aspects |

Garde-fous : **rien n'est modifié si une seule action est invalide** (fichier absent, aspect
hors vocabulaire, `reassign` vers une espèce inexistante, `remove` ou `reassign` visant une
vignette d'espèce) — le rapport est complet et la consolidation est tout ou rien. Un `remove`
l'emporte sur un `tag` du même fichier, pour ne pas laisser d'entrée morte. Relancer le
script après coup ne fait rien.

Le workflow **Consolider les contributions** (déclenchement manuel, onglet *Actions*) fait
la même chose et ouvre une Pull Request : les renommages et suppressions de photos se
relisent avant d'entrer dans `main`.
