#!/bin/bash
# Lance la démo des agents Mattermost

set -e

echo "🎭 Lancement de la démo des agents IA..."

cd "$(dirname "$0")"

# Vérifier que le serveur Mattermost tourne
if ! curl -s http://localhost:8065/api/v4/system/ping | grep -q "OK"; then
    echo "❌ Le serveur Mattermost ne répond pas"
    echo "Lancez d'abord : ~/Desktop/mattermost-server/start-mattermost.sh"
    exit 1
fi

# Activer le virtualenv et lancer l'orchestrateur
source venv/bin/activate
python3 orchestrator.py
