#!/bin/bash
# Surveille les messages des agents en temps réel

TOKEN="kca3qebmy3bztqfkcqkuosy3ee"
PARTY_CHANNEL="6g83qqk5ajbc7ym4mnion6t3er"
REFLEX_CHANNEL="c66iy3kxhfbu5fnzm4fe4k7qsy"

while true; do
    clear
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║         🎭 MATTERMOST - AGENTS IA EN TEMPS RÉEL              ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo ""
    
    echo "🎉 PARTY MODE (conversations multi-agents)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    curl -s -H "Authorization: Bearer $TOKEN" \
      "http://localhost:8065/api/v4/channels/$PARTY_CHANNEL/posts?per_page=10" | \
      jq -r '.order[] as $id | .posts[$id] | select(.message != "" and (.message | contains("added to") | not)) | .message' | \
      tail -6
    echo ""
    
    echo "💭 RÉFLEXIONS INDIVIDUELLES"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    curl -s -H "Authorization: Bearer $TOKEN" \
      "http://localhost:8065/api/v4/channels/$REFLEX_CHANNEL/posts?per_page=10" | \
      jq -r '.order[] as $id | .posts[$id] | select(.message != "" and (.message | contains("added to") | not)) | .message' | \
      tail -3
    echo ""
    
    echo "⏳ Actualisation dans 5s... (Ctrl+C pour quitter)"
    sleep 5
done
