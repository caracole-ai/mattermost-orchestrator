# 🤖 Agents IA avec vrais LLM

## 🎯 Différence avec la version précédente

**AVANT** : Messages pré-écrits (simulation)
**MAINTENANT** : Agents avec Claude 3.5 Sonnet qui répondent dynamiquement

## 🔧 Setup

### 1. Récupère ta clé API Anthropic

```bash
# Va sur https://console.anthropic.com/
# Génère une API key
```

### 2. Ajoute-la dans .env

```bash
cd ~/Desktop/mattermost-orchestrator
nano .env
```

Ajoute cette ligne :
```
ANTHROPIC_API_KEY=sk-ant-api03-...
```

### 3. Lance les agents

```bash
./start-agents-llm.sh
```

## 🎭 Les 3 agents

**🏗️ Winston** - Architecte Système
- Analyse technique
- Propose des architectures solides
- Identifie les risques

**💻 Amelia** - Développeuse Full-Stack
- Solutions d'implémentation
- Frameworks et librairies
- Estimations de développement

**📋 John** - Chef de Projet / PM
- Questions business
- Priorisation
- Deadlines et ROI

## 💬 Comment ça marche

1. Les agents écoutent le channel **#party-mode**
2. Quand un nouveau message arrive :
   - Ils analysent le contexte (5 derniers messages)
   - Réfléchissent avec Claude
   - Répondent selon leur personnalité
3. Pas tous en même temps (anti-spam)

## 🚀 Tester

1. Lance les agents : `./start-agents-llm.sh`
2. Envoie un message dans Party Mode :
   ```bash
   ./send-message.sh "On doit faire un système de notifications temps réel, vous proposez quoi ?"
   ```
3. Attends 15-30 secondes
4. Les agents répondent automatiquement avec des vrais LLM !

## ⚙️ Configuration

**Fichier `agents_llm.py` :**
- `interval` : Fréquence de vérification (défaut 15s)
- `max_tokens` : Longueur max des réponses (défaut 800)
- Personnalités modifiables dans `AGENT_PERSONAS`

## 🛑 Arrêter les agents

`Ctrl+C` dans le terminal où tu as lancé `start-agents-llm.sh`

---

**Note :** Les agents utilisent Claude 3.5 Sonnet (~$3 pour 1M tokens). Coût négligeable pour usage normal.
