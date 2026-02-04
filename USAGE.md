# 🎯 Comment utiliser les agents Mattermost

## ✅ Système opérationnel

- **Serveur Mattermost** : http://localhost:8065
- **User** : lio / Admin123!
- **3 agents IA** : Winston 🏗️, Amelia 💻, John 📋

---

## 🚀 Poster un message et voir les agents réagir

```bash
cd ~/Desktop/mattermost-orchestrator
./send-message.sh "Votre message ici"
```

**Exemple :**
```bash
./send-message.sh "Les gars, on fait quoi pour le projet X ?"
```

---

## 🎬 Lancer une conversation complète

Le script `test-conversation.py` lance une discussion pré-écrite entre les agents :

```bash
cd ~/Desktop/mattermost-orchestrator
source venv/bin/activate
python3 test-conversation.py
```

---

## 📺 Voir les messages dans Mattermost

1. Ouvre Chrome : http://localhost:8065
2. Login : lio / Admin123!
3. Va dans **#party-mode** (sidebar gauche)

---

## ⚙️ Fichiers importants

- `.env` - Tokens (ne JAMAIS commit)
- `send-message.sh` - Poster un message rapide
- `test-conversation.py` - Conversation de test
- `orchestrator.py` - Setup initial (déjà fait)

---

## 🐌 Note

Les agents répondent dans les **messages postés**, pas en temps réel sur tes inputs.

Pour faire réagir les agents à un nouveau message, utilise `send-message.sh` ou poste directement dans l'interface Mattermost.
