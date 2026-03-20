"""Configuration pour l'orchestrateur Mattermost."""
import os
from dotenv import load_dotenv

load_dotenv()

# Serveur Mattermost
MATTERMOST_URL = os.getenv("MATTERMOST_URL", "http://localhost:8065")
API_BASE = f"{MATTERMOST_URL}/api/v4"

# Tokens (à remplir après création des bots)
ADMIN_TOKEN = os.getenv("MATTERMOST_ADMIN_TOKEN", "")
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID", "")
TEAM_ID = os.getenv("MATTERMOST_TEAM_ID", "i5a897fmgj8ntqkkt5iy9q8hfr")

# Paths
OBSIDIAN_VAULT_PATH = os.getenv("OBSIDIAN_VAULT_PATH", "/Users/caracole/Documents/ObsidianVault")
OPENCLAW_PATH = os.getenv("OPENCLAW_PATH", "/Users/caracole/.openclaw")
OPENCLAW_AGENTS_FILE = os.path.join(OPENCLAW_PATH, "sources", "agents.json")

# Pipeline (les agents sont pilotés par OpenClaw, pas d'appel API direct)
PIPELINE_BUDGET_PER_AGENT = int(os.getenv("PIPELINE_BUDGET_PER_AGENT", "5"))

# Agents
AGENTS = {
    "winston": {
        "username": "winston-architecte",
        "display_name": "Winston 🏗️",
        "description": "Agent IA spécialisé en architecture système",
        "emoji": "🏗️",
        "token": os.getenv("AGENT_WINSTON_TOKEN", "")
    },
    "amelia": {
        "username": "amelia-dev",
        "display_name": "Amelia 💻",
        "description": "Agent IA développeuse full-stack",
        "emoji": "💻",
        "token": os.getenv("AGENT_AMELIA_TOKEN", "")
    },
    "john": {
        "username": "john-pm",
        "display_name": "John 📋",
        "description": "Agent IA chef de projet",
        "emoji": "📋",
        "token": os.getenv("AGENT_JOHN_TOKEN", "")
    }
}

# Channels
CHANNELS = {
    "orchestrator_log": {
        "name": "orchestrator-log",
        "display_name": "🎛️ Orchestrator Log",
        "purpose": "Logs système de l'orchestrateur",
        "type": "O"  # O = public, P = private
    },
    "agent_reflexions": {
        "name": "agent-reflexions",
        "display_name": "💭 Réflexions des Agents",
        "purpose": "Pensées et analyses des agents IA",
        "type": "O"
    },
    "party_mode": {
        "name": "party-mode",
        "display_name": "🎉 Party Mode (BMAD)",
        "purpose": "Discussions multi-agents style BMAD",
        "type": "O"
    }
}
