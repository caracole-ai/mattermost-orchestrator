#!/usr/bin/env python3
"""
Orchestrateur d'agents IA pour Mattermost.

Gère la création de bots, channels, et simule des conversations multi-agents
inspirées de la méthode BMAD (party-mode).
"""
import logging
import time
import sys
from typing import Dict, Optional

from mattermost_client import MattermostClient
from agents import WINSTON, AMELIA, JOHN, get_party_conversation
import config

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MattermostOrchestrator:
    """Orchestrateur principal."""
    
    def __init__(self):
        self.admin_client: Optional[MattermostClient] = None
        self.team_id: Optional[str] = None
        self.channels: Dict[str, str] = {}  # name -> channel_id
        self.bot_clients: Dict[str, MattermostClient] = {}  # agent_name -> client
        
    def setup_admin(self):
        """Configure le client admin."""
        if not config.ADMIN_TOKEN:
            logger.error("ADMIN_TOKEN manquant dans .env")
            logger.info("Lancez d'abord Mattermost et créez un compte admin, puis générez un token personnel.")
            return False
        
        self.admin_client = MattermostClient(config.API_BASE, config.ADMIN_TOKEN)
        
        # Vérifier la connexion
        me = self.admin_client.get_me()
        if not me:
            logger.error("Impossible de se connecter avec ADMIN_TOKEN")
            return False
        
        logger.info(f"✅ Connecté en tant que: {me.get('username')} (ID: {me.get('id')})")
        return True
    
    def setup_team(self):
        """Récupère ou crée la team principale."""
        teams = self.admin_client.get_teams()
        if teams is None:
            logger.error("Impossible de récupérer les teams")
            return False
        
        # Utiliser la première team ou en créer une
        if len(teams) > 0:
            self.team_id = teams[0]['id']
            logger.info(f"✅ Team: {teams[0]['display_name']} (ID: {self.team_id})")
        else:
            team = self.admin_client.create_team("agents-ia", "Agents IA")
            if not team:
                return False
            self.team_id = team['id']
            logger.info(f"✅ Team créée: {team['display_name']}")
        
        return True
    
    def setup_channels(self):
        """Crée les channels nécessaires."""
        for key, channel_config in config.CHANNELS.items():
            channel = self.admin_client.ensure_channel_exists(
                team_id=self.team_id,
                name=channel_config['name'],
                display_name=channel_config['display_name'],
                purpose=channel_config['purpose'],
                channel_type=channel_config['type']
            )
            
            if channel:
                self.channels[key] = channel['id']
                logger.info(f"✅ Channel: {channel_config['display_name']}")
                
                # Inviter l'admin
                if config.ADMIN_USER_ID:
                    self.admin_client.add_user_to_channel(channel['id'], config.ADMIN_USER_ID)
            else:
                logger.error(f"❌ Échec création channel {channel_config['name']}")
                return False
        
        return True
    
    def setup_bots(self):
        """Crée les bots et génère leurs tokens."""
        for agent_name, agent_config in config.AGENTS.items():
            # Récupérer ou créer le bot
            bot = self.admin_client.get_or_create_bot(
                username=agent_config['username'],
                display_name=agent_config['display_name'],
                description=agent_config['description']
            )
            
            if not bot:
                logger.error(f"❌ Échec création bot {agent_name}")
                continue
            
            bot_user_id = bot.get('user_id')
            logger.info(f"✅ Bot {agent_config['display_name']} (ID: {bot_user_id})")
            
            # Utiliser le token existant ou en créer un nouveau
            token = agent_config.get('token')
            if not token:
                token_data = self.admin_client.create_bot_token(bot_user_id)
                if token_data:
                    token = token_data.get('token')
                    logger.warning(f"⚠️  Token généré pour {agent_name}: {token}")
                    logger.warning("   👉 Ajoutez-le dans le fichier .env !")
            
            if token:
                # Créer un client pour ce bot
                self.bot_clients[agent_name] = MattermostClient(config.API_BASE, token)
                
                # Ajouter le bot à la team d'abord
                self.admin_client.add_user_to_team(self.team_id, bot_user_id)
                
                # Puis ajouter le bot à tous les channels
                for channel_id in self.channels.values():
                    self.admin_client.add_user_to_channel(channel_id, bot_user_id)
        
        return True
    
    def post_as_agent(self, agent_name: str, channel_key: str, message: str):
        """Poste un message depuis un agent."""
        if agent_name not in self.bot_clients:
            logger.error(f"Agent {agent_name} non configuré")
            return
        
        if channel_key not in self.channels:
            logger.error(f"Channel {channel_key} introuvable")
            return
        
        client = self.bot_clients[agent_name]
        channel_id = self.channels[channel_key]
        
        result = client.create_post(channel_id, message)
        if result:
            logger.info(f"📤 {agent_name} -> {channel_key}")
    
    def run_party_mode_demo(self, topic: str = "l'architecture du nouveau projet"):
        """Démonstration du mode party (conversation multi-agents)."""
        logger.info("🎉 Lancement du Party Mode...")
        
        conversation = get_party_conversation(topic)
        
        for agent_name, message in conversation:
            self.post_as_agent(agent_name, "party_mode", message)
            time.sleep(2)  # Pause pour que ce soit lisible
        
        logger.info("✅ Party Mode terminé")
    
    def run_individual_reflexions(self):
        """Chaque agent poste une réflexion dans #agent-reflexions."""
        logger.info("💭 Agents en réflexion...")
        
        self.post_as_agent("winston", "agent_reflexions", WINSTON.format_message(WINSTON.think()))
        time.sleep(1)
        self.post_as_agent("amelia", "agent_reflexions", AMELIA.format_message(AMELIA.think()))
        time.sleep(1)
        self.post_as_agent("john", "agent_reflexions", JOHN.format_message(JOHN.think()))
        
        logger.info("✅ Réflexions postées")
    
    def run(self):
        """Point d'entrée principal."""
        logger.info("🚀 Démarrage de l'orchestrateur Mattermost...")
        
        # Setup
        if not self.setup_admin():
            return 1
        if not self.setup_team():
            return 1
        if not self.setup_channels():
            return 1
        if not self.setup_bots():
            return 1
        
        logger.info("\n" + "="*60)
        logger.info("✅ SETUP TERMINÉ !")
        logger.info("="*60)
        
        # Demos
        self.run_individual_reflexions()
        time.sleep(3)
        self.run_party_mode_demo()
        
        logger.info("\n🎯 Orchestrateur prêt. Consultez Mattermost sur http://localhost:8065")
        return 0


if __name__ == "__main__":
    orchestrator = MattermostOrchestrator()
    sys.exit(orchestrator.run())
