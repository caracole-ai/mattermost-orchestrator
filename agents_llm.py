#!/usr/bin/env python3
"""Agents IA avec vrais LLM (Anthropic Claude)."""
import os
import requests
import json
import time
from typing import Optional
from config import MATTERMOST_URL, AGENTS
from mattermost_client import MattermostClient

# Configuration LLM
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
if not ANTHROPIC_API_KEY:
    print("❌ ANTHROPIC_API_KEY manquant dans .env")
    exit(1)

# Personnalités des agents
AGENT_PERSONAS = {
    "winston": {
        "name": "Winston",
        "role": "Architecte Système Senior",
        "personality": """Tu es Winston, un architecte système expérimenté et pragmatique.
        
Style:
- Direct et concis
- Focus sur scalabilité, performance, maintenabilité
- Propose des architectures éprouvées (pas de hype tech)
- Parle en bullet points souvent
- Utilise des emojis techniques 🏗️ 📊 ⚡

Ton job:
- Analyser les besoins techniques
- Proposer des architectures solides
- Identifier les risques et bottlenecks
- Challenger les choix techniques hasardeux

Tu réponds TOUJOURS en français."""
    },
    
    "amelia": {
        "name": "Amelia",
        "role": "Développeuse Full-Stack",
        "personality": """Tu es Amelia, une développeuse passionnée et pragmatique.
        
Style:
- Enthousiaste mais réaliste
- Focus sur l'implémentation concrète
- Mentionne les frameworks/libs pertinents
- Parle de code, d'APIs, de tests
- Utilise des emojis dev 💻 🚀 ✨

Ton job:
- Traduire les specs en code
- Proposer des solutions techniques
- Identifier les complexités d'implémentation
- Estimer les délais de dev réalistes

Tu réponds TOUJOURS en français."""
    },
    
    "john": {
        "name": "John",
        "role": "Chef de Projet / Product Manager",
        "personality": """Tu es John, un PM expérimenté qui pense business et délais.
        
Style:
- Questions précises et business-oriented
- Focus sur ROI, deadlines, priorités
- Ramène toujours à la réalité du terrain
- Pousse à clarifier les specs floues
- Utilise des emojis PM 📋 📈 🎯

Ton job:
- Poser les bonnes questions
- Identifier les ambiguïtés
- Prioriser les features
- Veiller aux délais et budgets
- Assurer la cohérence projet

Tu réponds TOUJOURS en français."""
    }
}


def call_claude(prompt: str, system: str) -> Optional[str]:
    """Appelle Claude API."""
    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 800,
                "system": system,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=30
        )
        
        if response.ok:
            data = response.json()
            return data["content"][0]["text"]
        else:
            print(f"❌ Claude API error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Exception calling Claude: {e}")
        return None


def get_recent_messages(channel_id: str, admin_token: str, limit: int = 10) -> list:
    """Récupère les derniers messages d'un channel."""
    try:
        response = requests.get(
            f"{MATTERMOST_URL}/api/v4/channels/{channel_id}/posts",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"per_page": limit}
        )
        
        if response.ok:
            data = response.json()
            messages = []
            
            for post_id in data.get("order", []):
                post = data["posts"][post_id]
                username = post.get("username", "unknown")
                message = post["message"]
                
                # Skip bot messages
                if username not in ["winston-architecte", "amelia-dev", "john-pm"]:
                    messages.append(f"{username}: {message}")
            
            return list(reversed(messages[-5:]))  # 5 derniers messages (ordre chrono)
        
        return []
        
    except Exception as e:
        print(f"❌ Error getting messages: {e}")
        return []


def agent_should_respond(agent_name: str, message_count: int) -> bool:
    """Détermine si l'agent doit répondre (éviter spam)."""
    # Winston et Amelia répondent plus souvent
    if agent_name in ["winston", "amelia"]:
        return message_count % 2 == 0  # 1 fois sur 2
    else:  # John
        return message_count % 3 == 0  # 1 fois sur 3


def agent_think_and_respond(agent_name: str, channel_id: str, context: list, admin_token: str):
    """Agent réfléchit et poste une réponse."""
    
    agent = AGENTS[agent_name]
    persona = AGENT_PERSONAS[agent_name]
    
    # Construire le contexte
    context_str = "\n".join(context) if context else "Aucun message récent."
    
    prompt = f"""Contexte de la conversation récente dans le channel :

{context_str}

En tant que {persona['role']}, réponds de manière pertinente et concise (max 4-5 lignes).

Si la conversation n'a pas besoin de ton expertise pour le moment, dis juste quelque chose de bref et pertinent.

Ta réponse :"""

    # Appeler Claude
    print(f"  🤔 {persona['name']} réfléchit...")
    response = call_claude(prompt, persona["personality"])
    
    if response:
        # Formater la réponse avec l'emoji de l'agent
        formatted_response = f"{persona['name'].upper()[0]} **{persona['name']}** ({persona['role']}):\n\n{response}"
        
        # Poster dans Mattermost
        client = MattermostClient(f"{MATTERMOST_URL}/api/v4", agent["token"])
        client.create_post(channel_id, formatted_response)
        
        print(f"  ✅ {persona['name']} a répondu")
    else:
        print(f"  ❌ {persona['name']} n'a pas pu répondre")


def watch_and_respond(channel_id: str, admin_token: str, interval: int = 15):
    """Surveille le channel et fait réagir les agents."""
    
    print("🎯 Agents LLM en écoute...")
    print(f"   Channel: {channel_id}")
    print(f"   Interval: {interval}s\n")
    
    last_message_count = 0
    
    while True:
        try:
            # Récupérer les messages récents
            messages = get_recent_messages(channel_id, admin_token)
            current_count = len(messages)
            
            # Nouveau message détecté ?
            if current_count > last_message_count:
                print(f"\n💬 Nouveau message détecté ! ({current_count} messages)")
                
                # Faire réagir les agents (pas tous en même temps)
                for agent_name in ["winston", "amelia", "john"]:
                    if agent_should_respond(agent_name, current_count):
                        agent_think_and_respond(agent_name, channel_id, messages, admin_token)
                        time.sleep(3)  # Délai entre agents
                
                last_message_count = current_count
            
            time.sleep(interval)
            
        except KeyboardInterrupt:
            print("\n\n👋 Arrêt des agents")
            break
        except Exception as e:
            print(f"❌ Erreur: {e}")
            time.sleep(interval)


if __name__ == "__main__":
    # Récupérer l'admin token et le channel ID
    from dotenv import load_dotenv
    load_dotenv()
    
    ADMIN_TOKEN = os.getenv("MATTERMOST_ADMIN_TOKEN")
    TEAM_ID = "i5a897fmgj8ntqkkt5iy9q8hfr"
    
    # Récupérer le channel party-mode
    channels = requests.get(
        f"{MATTERMOST_URL}/api/v4/teams/{TEAM_ID}/channels",
        headers={"Authorization": f"Bearer {ADMIN_TOKEN}"}
    ).json()
    
    party_channel = next((c for c in channels if c["name"] == "party-mode"), None)
    
    if not party_channel:
        print("❌ Channel party-mode introuvable")
        exit(1)
    
    print(f"✅ Channel trouvé: {party_channel['display_name']}")
    print(f"🔑 API Key Claude: {'✅ OK' if ANTHROPIC_API_KEY else '❌ MANQUANTE'}\n")
    
    # Lancer la surveillance
    watch_and_respond(party_channel["id"], ADMIN_TOKEN)
