#!/usr/bin/env python3
"""Auto-réponse simplifiée et robuste."""
import time
import logging
from orchestrator import MattermostOrchestrator
from agents_llm import WINSTON, AMELIA, JOHN
import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Stocker les IDs déjà traités
processed_ids = set()

def main():
    logger.info("🎭 Auto-réponse SIMPLIFIÉE activée")
    logger.info("📍 Surveillance de #party-mode\n")
    
    # Setup
    orch = MattermostOrchestrator()
    orch.setup_admin()
    orch.setup_team()
    orch.setup_channels()
    orch.setup_bots()
    
    # Trouver party-mode
    team_id = orch.team_id
    channels = orch.admin_client._request("GET", f"/teams/{team_id}/channels")
    party_channel = None
    for ch in channels:
        if 'party' in ch.get('name', '').lower():
            party_channel = ch
            break
    
    if not party_channel:
        logger.error("Channel party-mode introuvable!")
        return
    
    channel_id = party_channel['id']
    logger.info(f"✅ Channel: {party_channel['display_name']} (ID: {channel_id[:8]}...)\n")
    
    # Charger l'historique existant pour ne pas retraiter
    posts = orch.admin_client._request("GET", f"/channels/{channel_id}/posts?per_page=50")
    if posts and posts.get('order'):
        for pid in posts['order']:
            processed_ids.add(pid)
        logger.info(f"✅ {len(processed_ids)} messages existants ignorés\n")
    
    # Boucle de surveillance
    while True:
        try:
            posts = orch.admin_client._request("GET", f"/channels/{channel_id}/posts?per_page=10")
            
            if not posts or not posts.get('order'):
                time.sleep(3)
                continue
            
            # Chercher les nouveaux messages de Lio
            for post_id in posts['order']:
                # Déjà traité ?
                if post_id in processed_ids:
                    continue
                
                post = posts['posts'][post_id]
                processed_ids.add(post_id)
                
                # Message de bot ?
                from_bot = post.get('props', {}).get('from_bot')
                if from_bot == 'true' or from_bot is True:
                    continue
                
                # Message de Lio ?
                if post['user_id'] != config.ADMIN_USER_ID:
                    continue
                
                # BINGO ! Nouveau message de Lio
                message = post['message']
                logger.info(f"\n💬 NOUVEAU MESSAGE DE LIO: '{message}'\n")
                
                # Agents réagissent
                for agent_name, agent_obj, emoji in [
                    ("winston", WINSTON, "🏗️"),
                    ("amelia", AMELIA, "💻"),
                    ("john", JOHN, "📋")
                ]:
                    reaction = agent_obj.format_message(agent_obj.think(message))
                    orch.post_as_agent(agent_name, 'party_mode', reaction)
                    logger.info(f"  ✅ {emoji} {agent_obj.name} a répondu")
                    time.sleep(2)
                
                logger.info("\n✅ Tous les agents ont répondu!\n")
            
            time.sleep(3)  # Check toutes les 3 secondes
            
        except KeyboardInterrupt:
            logger.info("\n🛑 Arrêt")
            break
        except Exception as e:
            logger.error(f"Erreur: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
