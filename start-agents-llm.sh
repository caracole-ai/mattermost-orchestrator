#!/bin/bash
# Lance les agents IA avec LLM

cd "$(dirname "$0")"

# Vérifier l'API key
if ! grep -q "ANTHROPIC_API_KEY=sk-" .env 2>/dev/null; then
    echo "❌ ANTHROPIC_API_KEY manquante dans .env"
    echo ""
    echo "Ajoute ta clé API Anthropic :"
    echo "  1. Va sur https://console.anthropic.com/"
    echo "  2. Génère une clé API"
    echo "  3. Ajoute-la dans .env :"
    echo "     ANTHROPIC_API_KEY=sk-ant-..."
    echo ""
    exit 1
fi

echo "🚀 Lancement des agents IA avec LLM..."
echo ""

source venv/bin/activate
python3 agents_llm.py
