# 🚀 Dernière étape : Ajouter ta clé API

## 1. Récupère ta clé Anthropic

Va sur https://console.anthropic.com/settings/keys et génère une clé API.

## 2. Ajoute-la au .env

```bash
cd ~/Desktop/mattermost-orchestrator
nano .env
```

Remplace la ligne :
```
ANTHROPIC_API_KEY=your_key_here
```

Par :
```
ANTHROPIC_API_KEY=sk-ant-api03-...
```

Sauvegarde : `Ctrl+O` puis `Enter`, puis `Ctrl+X`

## 3. Lance les agents

```bash
./start-agents-llm.sh
```

Tu devrais voir :
```
✅ Channel trouvé: 🎉 Party Mode (BMAD)
🔑 API Key Claude: ✅ OK

🎯 Agents LLM en écoute...
   Channel: nixqnhjz9p849eqfz85mkriufc
   Interval: 15s
```

## 4. Teste

Dans un autre terminal :
```bash
cd ~/Desktop/mattermost-orchestrator
./send-message.sh "Les gars, on doit créer une API REST. Vous proposez quoi ?"
```

Attends 15-30 secondes et regarde Party Mode dans Mattermost.

Les 3 agents vont répondre avec de vrais LLM ! 🤖

---

**Tout est prêt. Plus qu'à ajouter la clé API et lancer.**
