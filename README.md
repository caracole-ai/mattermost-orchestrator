# 🎛️ Mattermost AI Agents Orchestrator

Système d'orchestration d'agents IA pour Mattermost, inspiré de la méthode BMAD (party-mode).

## 📋 Vue d'ensemble

Cet orchestrateur gère automatiquement :
- **3 agents IA** avec des personnalités distinctes (Winston l'Architecte, Amelia la Dev, John le PM)
- **Création automatique de bots** via l'API Mattermost
- **Channels dédiés** pour différents types d'interactions
- **Mode Party** : conversations multi-agents simulées
- **Invitation automatique** de l'admin (Lio) dans tous les channels

## 🏗️ Architecture

```
mattermost-orchestrator/
├── orchestrator.py          # Point d'entrée principal
├── mattermost_client.py     # Wrapper API Mattermost v4
├── agents.py                # Définition des 3 agents (Winston, Amelia, John)
├── config.py                # Configuration (serveur, agents, channels)
├── requirements.txt         # Dépendances Python
├── .env.example             # Template de configuration
└── README.md                # Cette documentation
```

## 🚀 Installation

### 1. Prérequis

- Python 3.8+
- Serveur Mattermost en cours d'exécution sur `http://localhost:8065`
- Compte admin Mattermost configuré

### 2. Installation des dépendances

```bash
cd ~/Desktop/mattermost-orchestrator
pip3 install -r requirements.txt
```

### 3. Configuration

1. Copier le fichier d'exemple :
```bash
cp .env.example .env
```

2. Éditer `.env` avec vos valeurs :
```env
MATTERMOST_URL=http://localhost:8065
MATTERMOST_ADMIN_TOKEN=<votre_token_admin>
ADMIN_USER_ID=<votre_user_id>
```

**Comment obtenir le token admin :**
1. Connectez-vous à Mattermost
2. Menu utilisateur → **Profile** → **Security** → **Personal Access Tokens**
3. Créer un nouveau token avec description "Orchestrator"
4. Copier le token généré dans `.env`

**Comment obtenir votre user_id :**
1. Dans Mattermost, ouvrir la console développeur (F12)
2. Onglet **Network**, recharger la page
3. Chercher une requête `/api/v4/users/me`
4. Le champ `id` dans la réponse est votre `user_id`

## 🎮 Utilisation

### Lancement

```bash
python3 orchestrator.py
```

### Première exécution

L'orchestrateur va automatiquement :
1. Se connecter avec le token admin
2. Récupérer ou créer une team
3. Créer 3 channels :
   - `#orchestrator-log` 🎛️ - Logs système
   - `#agent-reflexions` 💭 - Pensées individuelles des agents
   - `#party-mode` 🎉 - Conversations multi-agents
4. Créer 3 bots (Winston, Amelia, John)
5. Générer des tokens pour chaque bot (à sauvegarder dans `.env`)
6. Inviter Lio (admin) dans tous les channels
7. Lancer une démo : réflexions individuelles + conversation party-mode

### Tokens des bots

Au premier lancement, des tokens seront générés pour chaque bot. **Copiez-les dans `.env` :**

```env
AGENT_WINSTON_TOKEN=xxxxxxxxxxxxx
AGENT_AMELIA_TOKEN=xxxxxxxxxxxxx
AGENT_JOHN_TOKEN=xxxxxxxxxxxxx
```

## 🤖 Les Agents

### Winston 🏗️ - L'Architecte
- **Personnalité** : Méthodique, voit la big picture, pense en systèmes
- **Spécialité** : Architecture, design patterns, scalabilité
- **Style** : "On devrait découpler cette logique..."

### Amelia 💻 - La Développeuse
- **Personnalité** : Pragmatique, focus sur le code, aime les solutions élégantes
- **Spécialité** : Développement full-stack, refactoring, performance
- **Style** : "Ce code sent le refactoring..."

### John 📋 - Le Chef de Projet
- **Personnalité** : Orienté deadline, focus user, gère les priorités
- **Spécialité** : Planning, priorisation, coordination d'équipe
- **Style** : "On est à J-3 du sprint. Statut ?"

## 🎉 Party Mode (BMAD)

Le mode party simule une conversation naturelle entre les 3 agents sur un sujet donné :

```python
orchestrator.run_party_mode_demo(topic="l'architecture du nouveau projet")
```

Résultat dans `#party-mode` :
1. Winston propose une architecture
2. Amelia réagit d'un point de vue dev
3. John cadre en termes de deadline
4. Échanges naturels
5. Décision collective

## 📡 API Mattermost

L'orchestrateur utilise l'API REST v4 de Mattermost :
- `/api/v4/users/me` - Info utilisateur
- `/api/v4/teams` - Gestion teams
- `/api/v4/channels` - Gestion channels
- `/api/v4/bots` - Gestion bots
- `/api/v4/posts` - Création de messages
- `/api/v4/users/{id}/tokens` - Génération tokens

Documentation officielle : https://api.mattermost.com/

## 🔧 Développement

### Ajouter un nouvel agent

1. Créer la classe dans `agents.py` :
```python
class NewAgent(Agent):
    def __init__(self):
        super().__init__(name="Alice", role="DevOps", emoji="🔧", 
                        personality="Focus infra")
    
    def think(self, context=""):
        return "Réflexion DevOps..."
```

2. Ajouter dans `config.py` :
```python
"alice": {
    "username": "alice-devops",
    "display_name": "Alice 🔧",
    "description": "Agent DevOps",
    "emoji": "🔧",
    "token": ""
}
```

3. Relancer l'orchestrateur

### Créer un nouveau channel

Modifier `config.py` :
```python
"new_channel": {
    "name": "incidents",
    "display_name": "🚨 Incidents",
    "purpose": "Gestion des incidents",
    "type": "P"  # P = privé
}
```

## 🐛 Debugging

Activer les logs détaillés :
```python
logging.basicConfig(level=logging.DEBUG)
```

Tester la connexion manuellement :
```python
from mattermost_client import MattermostClient
client = MattermostClient("http://localhost:8065/api/v4", "votre_token")
print(client.get_me())
```

## 📝 Notes

- Les bots n'ont **pas** besoin de licence Mattermost Enterprise
- Les tokens générés sont **permanents** (sauf révocation manuelle)
- Les channels publics (`type: "O"`) sont visibles par tous
- Les messages sont postés en temps réel (pas de batch)

## 🎯 Prochaines étapes

- [ ] Intégration avec de vrais LLMs (OpenAI, Anthropic)
- [ ] Webhooks pour réactions automatiques
- [ ] Système de routage intelligent des conversations
- [ ] Dashboard de monitoring des agents
- [ ] Export des conversations en Markdown

---

**Made with 🐌 by Caracole**
