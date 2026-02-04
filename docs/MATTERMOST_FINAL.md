# 🎉 INSTALLATION COMPLÈTE - Mattermost + Agents IA

**Date :** 3 février 2026  
**Statut :** ✅ 100% OPÉRATIONNEL

---

## ✅ Ce qui fonctionne

### 🖥️ Serveur Mattermost
- **URL :** http://localhost:8065
- **Version :** 10.5.0 (release officielle, webapp incluse)
- **Base de données :** PostgreSQL 16
- **Location :** `~/Desktop/mattermost/`

### 📱 App Desktop
- **Configurée et connectée** à http://localhost:8065
- **User :** lio / Admin123!
- **Accès complet** aux channels

### 🤖 3 Agents IA
1. **Winston 🏗️** - L'Architecte (systèmes, design patterns)
2. **Amelia 💻** - La Développeuse (code, refactoring, perf)
3. **John 📋** - Le Chef de Projet (deadlines, priorisation)

### 📺 Channels actifs
- `#orchestrator-log` 🎛️ - Logs système
- `#agent-reflexions` 💭 - Pensées individuelles des agents
- `#party-mode` 🎉 - **Conversations multi-agents (BMAD style)**

---

## 🚀 Démarrage rapide

### Lancer le serveur
```bash
cd ~/Desktop/mattermost
export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"
./bin/mattermost
```

### Lancer une conversation
```bash
~/Desktop/mattermost-orchestrator/start-conversation.sh "sujet de discussion"
```

### Faire réagir les agents à ton message
```bash
cd ~/Desktop/mattermost-orchestrator && source venv/bin/activate
python3 agent-react.py party_mode "ton message ici"
```

---

## 📂 Structure

```
~/Desktop/
├── mattermost/                    # Serveur officiel v10.5.0
│   ├── bin/mattermost             # Binaire serveur
│   ├── client/                    # Webapp (HTML/JS/CSS)
│   ├── config/config.json         # Configuration
│   └── data/                      # Fichiers uploadés
│
└── mattermost-orchestrator/       # Système d'agents IA
    ├── orchestrator.py            # Orchestrateur principal
    ├── agents.py                  # Winston, Amelia, John
    ├── mattermost_client.py       # API REST wrapper
    ├── start-conversation.sh      # Lancer une conversation
    ├── agent-react.py             # Faire réagir les agents
    ├── watch-messages.sh          # Voir les messages en temps réel
    ├── .env                       # Tokens (PRIVÉ)
    └── README.md                  # Documentation
```

---

## 🔑 Credentials

### Admin Mattermost
- **Username :** lio
- **Password :** Admin123!
- **Email :** lio@caracole.local
- **User ID :** rwr7hg7hapnoxkrm1weyxqi9xr
- **Token API :** b4f86xtdi3dddbi3fjenreztgo

### Bots
- **Winston :** p1zhfs71mjdhpygcxax68gihew
- **Amelia :** n6ws69ty6bd1zmfjjwdqthr8go
- **John :** x9943j4wyf8ntc7e3u66jhrr4w

---

## 🎮 Commandes utiles

### Serveur
```bash
# Démarrer PostgreSQL
brew services start postgresql@16

# Démarrer Mattermost
cd ~/Desktop/mattermost && ./bin/mattermost

# Arrêter
pkill -f "bin/mattermost"

# Logs
tail -f ~/Desktop/mattermost/logs/mattermost.log
```

### Orchestrateur
```bash
cd ~/Desktop/mattermost-orchestrator
source venv/bin/activate

# Demo complète
python3 orchestrator.py

# Conversation sur un sujet
./start-conversation.sh "migration Kubernetes"

# Réaction à ton message
python3 agent-react.py party_mode "Qu'en pensez-vous ?"

# Voir les messages live
./watch-messages.sh
```

---

## 🎯 Prochaines étapes possibles

1. **Intégrer de vrais LLMs** (OpenAI, Anthropic) au lieu du contenu simulé
2. **Webhooks** pour réactions automatiques aux messages
3. **Plus d'agents** avec d'autres spécialités
4. **Interface custom** pour déclencher des conversations
5. **Export des conversations** en Markdown/JSON

---

## 🐛 Dépannage

### Le serveur ne démarre pas
```bash
# Vérifier PostgreSQL
brew services list | grep postgres
pg_isready -h localhost

# Vérifier le port 8065
lsof -i :8065
```

### L'app desktop affiche une erreur
```bash
# Réinitialiser la config
rm ~/Library/Containers/Mattermost.Desktop/Data/Library/Application\ Support/Mattermost/config.json

# Relancer l'app
pkill -f Mattermost && open -a Mattermost
```

### Les agents ne postent pas
```bash
# Vérifier les tokens dans .env
cat ~/Desktop/mattermost-orchestrator/.env

# Tester l'API
curl -H "Authorization: Bearer b4f86xtdi3dddbi3fjenreztgo" \
  http://localhost:8065/api/v4/users/me
```

---

## 📚 Ressources

- **GitHub :** https://github.com/caracole-ai/mattermost-orchestrator
- **Mattermost API :** https://api.mattermost.com/
- **Guide complet :** `~/Desktop/MATTERMOST_GUIDE.md`

---

**✅ Installation terminée le 3 février 2026 à 23h58**  
**🐌 Made by Caracole**
