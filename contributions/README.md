# Contributions d'aspects

Ce dossier reçoit les fichiers `*.tsv` d'annotation d'aspects proposés **depuis l'application**
(bouton « 🚀 Publier mes changements ») ou à la main.

- Format : `nom_de_fichier.jpg⇥aspect1,aspect2` (une paire par ligne, séparée par une tabulation).
- Ces fichiers sont **fusionnés** au build (ils complètent / écrasent `img/quiz-extra/_aspects.tsv`).
- Le mainteneur peut ensuite consolider leur contenu dans `img/quiz-extra/_aspects.tsv`
  puis supprimer le fichier de contribution.

Les lignes commençant par `#` sont des commentaires (ex. manques signalés) — ignorées au build.
