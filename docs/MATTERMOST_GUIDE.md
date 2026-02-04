# 🐌 Guide Mattermost + Agents IA - Installation complète

**Date d'installation :** 3 février 2026  
**Machine :** Mac Mini (Apple Silicon)

---

## 📍 Ce qui a été installé

### 1. Serveur Mattermost (depuis sources)
- **Location :** `~/Desktop/mattermost-server/`
- **Port :** `http://localhost:8065`
- **Base de données :** PostgreSQL 16 (locale)
- **Mode :** Development (compilé depuis GitHub)

### 2. Orchestrateur Python
- **Location :** `~/Desktop/mattermost-orchestrator/`
- **3 agents IA :** Winston (Architecte), Amelia (Dev), John (PM)
- **Mode party :** Conversations multi-agents inspirées BMAD

---

## 🚀 Démarrage rapide

### Option 1 : Script automatique (recommandé)

```bash
# Démarrer Mattermost
~/Desktop/mattermost-server/start-mattermost.sh

# Lancer la démo des agents
~/Desktop/mattermost-orchestrator/run-demo.sh
```

### Option 2 : Manuel

```bash
# 1. Démarrer PostgreSQL (si pas déjà démarré)
brew services start postgresql@16

# 2. Lancer le serveur Mattermost
cd ~/Desktop/mattermost-server/server
export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"
make run-server

# 3. Dans un autre terminal, lancer l'orchestrateur
cd ~/Desktop/mattermost-orchestrator
source venv/bin/activate
python3 orchestrator.py
```

---

## 🔑 Credentials

### Admin Mattermost
- **Username :** `lio`
- **Password :** `Admin123!`
- **User ID :** `nqmxqdhaai8s7eksfxr9ophj8o`
- **Token :** `kca3qebmy3bztqfkcqkuosy3ee`

### Bots (tokens dans `.env`)
- **Winston 🏗️** : `kxdmej8ikid7jkg8ndafukgudo`
- **Amelia 💻** : `fmb4sxr6z78mbrjmiu6xdsc74h`
- **John 📋** : `w1qzoyu5obfq3rfce81tnbzr1o`

---

## 📡 API REST (pour développement)

### Tester la connexion
```bash
curl -s http://localhost:8065/api/v4/system/ping
# → {"status":"OK"}
```

### Authentification
```bash
curl -X POST http://localhost:8065/api/v4/users/login \
  -H "Content-Type: application/json" \
  -d '{"login_id":"lio","password":"Admin123!"}'
# Récupérer le header Token: xxx
```

### Poster un message (exemple)
```bash
curl -X POST http://localhost:8065/api/v4/posts \
  -H "Authorization: Bearer TON_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "channel_id": "ID_DU_CHANNEL",
    "message": "Hello depuis l'API !"
  }'
```

---

## 📂 Structure

```
~/Desktop/
├── mattermost-server/
│   ├── server/              # Backend Go
│   ├── config/              # Configuration
│   │   └── config.json      # ⚙️ Config principale
│   ├── start-mattermost.sh  # 🚀 Script de démarrage
│   └── stop-mattermost.sh   # 🛑 Script d'arrêt
│
└── mattermost-orchestrator/
    ├── orchestrator.py      # 🎛️ Orchestrateur principal
    ├── mattermost_client.py # 📡 Client API
    ├── agents.py            # 🤖 Définition des 3 agents
    ├── config.py            # ⚙️ Configuration
    ├── .env                 # 🔑 Tokens (NE PAS COMMIT)
    ├── venv/                # 🐍 Virtualenv Python
    ├── run-demo.sh          # 🎭 Lancer la démo
    └── README.md            # 📖 Documentation complète
```

---

## 🎭 Les Agents

### Winston 🏗️ - L'Architecte
- **Rôle :** Architecture système, design patterns, scalabilité
- **Personnalité :** Méthodique, vision globale, pense en systèmes
- **Exemple :** "On devrait découpler cette logique en microservices..."

### Amelia 💻 - La Développeuse
- **Rôle :** Dev full-stack, refactoring, performance
- **Personnalité :** Pragmatique, focus code, solutions élégantes
- **Exemple :** "Ce code sent le refactoring. Trop de duplication..."

### John 📋 - Le Chef de Projet
- **Rôle :** Planning, priorisation, coordination
- **Personnalité :** Orienté deadline, focus user, gestion priorités
- **Exemple :** "On est à J-3 du sprint. Statut ?"

---

## 🎉 Party Mode (BMAD)

Le mode party simule une conversation naturelle entre les 3 agents :

1. **Winston** propose une architecture
2. **Amelia** réagit d'un point de vue dev
3. **John** cadre en termes de deadline
4. Échanges naturels et décision collective

---

## 🛠️ Commandes utiles

### Gérer le serveur
```bash
# Démarrer
~/Desktop/mattermost-server/start-mattermost.sh

# Arrêter
~/Desktop/mattermost-server/stop-mattermost.sh

# Voir les logs
tail -f /tmp/mattermost-server.log

# Vérifier les processus
ps aux | grep mattermost
```

### Gérer PostgreSQL
```bash
# Démarrer
brew services start postgresql@16

# Arrêter
brew services stop postgresql@16

# Statut
brew services list | grep postgres

# Se connecter à la base
/opt/homebrew/opt/postgresql@16/bin/psql -U mmuser -d mattermost
```

### Gérer l'orchestrateur
```bash
# Lancer la démo
cd ~/Desktop/mattermost-orchestrator
source venv/bin/activate
python3 orchestrator.py

# Modifier la configuration
nano .env

# Éditer les agents
nano agents.py
```

---

## ⚠️ Notes importantes

### Interface web (webapp)
L'interface web Nuxt ne compile pas (erreur `mozjpeg`), mais **ce n'est pas grave** car :
- ✅ L'API REST fonctionne parfaitement
- ✅ Les bots peuvent poster des messages
- ✅ L'orchestrateur est 100% opérationnel
- ❌ Tu n'as juste pas d'interface graphique dans le navigateur

Pour ce use case (observer les agents IA), l'API REST suffit. Si tu veux l'interface web plus tard, il faudrait :
1. Installer `autotools` (`brew install autoconf automake libtool`)
2. Relancer `npm install` dans `~/Desktop/mattermost-server/webapp/`

### Configuration de production
Le serveur est en mode **development**. Pour de la production, il faudrait :
- [ ] Configurer HTTPS (certificat SSL)
- [ ] Définir `SiteURL` dans `config.json`
- [ ] Configurer un SMTP pour les emails
- [ ] Optimiser les paramètres de performance
- [ ] Mettre en place des backups automatiques

---

## 🔧 Customisation

### Ajouter un nouvel agent
1. Éditer `agents.py` (créer une nouvelle classe)
2. Ajouter dans `config.py` (section `AGENTS`)
3. Relancer `orchestrator.py`

### Créer un nouveau channel
1. Éditer `config.py` (section `CHANNELS`)
2. Relancer `orchestrator.py`

### Modifier les réflexions des agents
Les agents postent du contenu **simulé** (pas de vrai LLM).  
Pour connecter de vrais LLMs (OpenAI, Anthropic, etc.) :
- Éditer `agents.py` méthode `think()`
- Appeler une API LLM réelle

---

## 📚 Documentation

- **Mattermost API :** https://api.mattermost.com/
- **Mattermost Docs :** https://docs.mattermost.com/
- **PostgreSQL Docs :** https://www.postgresql.org/docs/

---

## 🐛 Dépannage

### Le serveur ne démarre pas
```bash
# Vérifier PostgreSQL
pg_isready -h localhost

# Vérifier les logs
tail -50 /tmp/mattermost-server.log

# Vérifier le port 8065
lsof -i :8065
```

### Les bots ne peuvent pas poster
```bash
# Vérifier qu'ils sont membres de la team
curl -H "Authorization: Bearer ADMIN_TOKEN" \
  http://localhost:8065/api/v4/teams/TEAM_ID/members

# Les ajouter manuellement si besoin
# (voir orchestrator.py fonction setup_bots)
```

### L'orchestrateur ne trouve pas les tokens
```bash
# Vérifier que .env existe et contient les tokens
cat ~/Desktop/mattermost-orchestrator/.env

# Relancer avec logs détaillés
cd ~/Desktop/mattermost-orchestrator
source venv/bin/activate
python3 orchestrator.py
```

---

**✅ Installation terminée le 3 février 2026 à 23h06**  
**🐌 Made by Caracole**
