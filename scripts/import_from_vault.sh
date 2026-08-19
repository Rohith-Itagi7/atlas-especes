#!/usr/bin/env bash
# Aide MAINTENEUR : réimporte les atlas + images depuis un coffre Obsidian vers ce dépôt,
# pour garder le dépôt public synchronisé avec tes notes de travail.
#
#   ./scripts/import_from_vault.sh "/chemin/vers/mon/coffre-Obsidian"
#
# Copie les 5 fichiers d'atlas + img/especes + img/quiz-extra depuis le coffre.
set -euo pipefail
VAULT="${1:?Usage: import_from_vault.sh <chemin-du-coffre-Obsidian>}"
REPO="$(cd "$(dirname "$0")/.." && pwd)"

for f in "Espèces - référence.md" "Espèces herbacées - référence.md" \
         "Champignons - référence.md" "Faune - référence.md" "Espèces diverses - référence.md"; do
  cp "$VAULT/$f" "$REPO/$f"
done
rsync -a --delete "$VAULT/img/especes/"    "$REPO/img/especes/"
rsync -a --delete "$VAULT/img/quiz-extra/" "$REPO/img/quiz-extra/"
echo "Import terminé. Vérifie avec :  python3 scripts/build_web.py _site"
