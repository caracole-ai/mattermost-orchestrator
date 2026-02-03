#!/usr/bin/env python3
"""
Surveille les messages de Lio et fait réagir automatiquement les agents.
Les agents répondent uniquement aux nouveaux messages.
"""
import time
import logging
from orchestrator import MattermostOrchestrator
from agents import WINSTON, AMELIA, JOHN
import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ID de Lio
LIO_USER_ID = config.ADMIN_USER_ID

# Stockage du dernier message traité
last_processed_post_id = None

def main():
    logger.info("🎭 Auto-réponse des agents activée")
    logger.info("📍 Surveillance de #party-mode")
    logger.info("💬 Les agents réagiront à tes messages automatiquement\n")
    
    # Setup orchestrateur
    orch = MattermostOrchestrator()
    orch.setup_admin()
    orch.setup_team()
    orch.setup_channels()
    orch.setup_bots()
    
    party_channel_id = orch.channels.get('party_mode')
    
    global last_processed_post_id
    
    # Récupérer le dernier post pour éviter de retraiter l'historique
    posts = orch.admin_client._request("GET", f"/channels/{party_channel_id}/posts?per_page=1")
    if posts and posts.get('order'):
        last_processed_post_id = posts['order'][0]
        logger.info(f"✅ Démarrage à partir du post {last_processed_post_id[:8]}...\n")
    
    # Boucle de surveillance
    while True:
        try:
            # Récupérer les posts récents
            posts = orch.admin_client._request("GET", f"/channels/{party_channel_id}/posts?per_page=10")
            
            if not posts or not posts.get('order'):
                time.sleep(5)
                continue
            
            # Parcourir les posts dans l'ordre chronologique (inverse)
            for post_id in reversed(posts['order']):
                # Passer les posts déjà traités
                if last_processed_post_id and post_id <= last_processed_post_id:
                    continue
                
                post = posts['posts'][post_id]
                
                # Ignorer les messages des bots
                if post.get('props', {}).get('from_bot'):
                    last_processed_post_id = post_id
                    continue
                
                # Traiter uniquement les messages de Lio
                if post['user_id'] == LIO_USER_ID:
                    message = post['message']
                    logger.info(f"\n💬 Nouveau message de Lio : '{message}'")
                    
                    # Les agents réagissent
                    agents = [
                        ("winston", WINSTON, "🏗️ Winston"),
                        ("amelia", AMELIA, "💻 Amelia"),
                        ("john", JOHN, "📋 John")
                    ]
                    
                    for agent_name, agent_obj, display_name in agents:
                        reaction = agent_obj.format_message(
                            agent_obj.think(message)
                        )
                        orch.post_as_agent(agent_name, 'party_mode', reaction)
                        logger.info(f"✅ {display_name} a répondu")
                        time.sleep(2)
                    
                    logger.info("✅ Tous les agents ont répondu\n")
                
                last_processed_post_id = post_id
            
            time.sleep(5)  # Vérifier toutes les 5 secondes
            
        except KeyboardInterrupt:
            logger.info("\n\n🛑 Arrêt de l'auto-réponse")
            break
        except Exception as e:
            logger.error(f"Erreur : {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
