"""Client API Mattermost v4."""
import requests
import logging
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


class MattermostClient:
    """Wrapper pour l'API REST Mattermost v4."""
    
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict]:
        """Requête HTTP générique avec gestion d'erreurs."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.request(method, url, headers=self.headers, **kwargs)
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur API {method} {endpoint}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            return None
    
    # === Users & Bots ===
    
    def create_bot(self, username: str, display_name: str, description: str = "") -> Optional[Dict]:
        """Crée un bot account."""
        data = {
            "username": username,
            "display_name": display_name,
            "description": description
        }
        return self._request("POST", "/bots", json=data)
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Récupère un utilisateur (ou bot) par son username."""
        return self._request("GET", f"/users/username/{username}")
    
    def get_bot_by_username(self, username: str) -> Optional[Dict]:
        """Récupère un bot par son username (via l'endpoint users)."""
        user = self.get_user_by_username(username)
        if user and user.get('is_bot'):
            # Construire un objet bot-like
            return {"user_id": user['id'], "username": user['username'], "display_name": user.get('first_name', '')}
        return None
    
    def create_bot_token(self, bot_user_id: str, description: str = "Orchestrator token") -> Optional[Dict]:
        """Crée un token d'accès pour un bot."""
        data = {"description": description}
        return self._request("POST", f"/users/{bot_user_id}/tokens", json=data)
    
    def get_me(self) -> Optional[Dict]:
        """Récupère les infos de l'utilisateur courant (via le token)."""
        return self._request("GET", "/users/me")
    
    # === Teams ===
    
    def get_teams(self) -> Optional[List[Dict]]:
        """Liste toutes les teams."""
        return self._request("GET", "/teams")
    
    def create_team(self, name: str, display_name: str, team_type: str = "O") -> Optional[Dict]:
        """Crée une team."""
        data = {
            "name": name,
            "display_name": display_name,
            "type": team_type  # O = Open, I = Invite only
        }
        return self._request("POST", "/teams", json=data)
    
    # === Channels ===
    
    def create_channel(self, team_id: str, name: str, display_name: str, 
                      purpose: str = "", channel_type: str = "O") -> Optional[Dict]:
        """Crée un channel dans une team."""
        data = {
            "team_id": team_id,
            "name": name,
            "display_name": display_name,
            "purpose": purpose,
            "type": channel_type  # O = public, P = private
        }
        return self._request("POST", "/channels", json=data)
    
    def get_channel_by_name(self, team_id: str, channel_name: str) -> Optional[Dict]:
        """Récupère un channel par son nom."""
        return self._request("GET", f"/teams/{team_id}/channels/name/{channel_name}")
    
    def add_user_to_team(self, team_id: str, user_id: str) -> Optional[Dict]:
        """Ajoute un utilisateur à une team."""
        data = {"user_id": user_id, "team_id": team_id}
        return self._request("POST", f"/teams/{team_id}/members", json=data)
    
    def add_user_to_channel(self, channel_id: str, user_id: str) -> Optional[Dict]:
        """Ajoute un utilisateur à un channel."""
        data = {"user_id": user_id}
        return self._request("POST", f"/channels/{channel_id}/members", json=data)
    
    # === Posts ===
    
    def create_post(self, channel_id: str, message: str, props: Dict = None) -> Optional[Dict]:
        """Poste un message dans un channel."""
        data = {
            "channel_id": channel_id,
            "message": message
        }
        if props:
            data["props"] = props
        return self._request("POST", "/posts", json=data)
    
    # === Helpers ===
    
    def get_or_create_bot(self, username: str, display_name: str, description: str = "") -> Optional[Dict]:
        """Récupère un bot existant ou le crée s'il n'existe pas."""
        bot = self.get_bot_by_username(username)
        if bot:
            logger.info(f"Bot {username} existe déjà")
            return bot
        
        logger.info(f"Création du bot {username}...")
        return self.create_bot(username, display_name, description)
    
    def ensure_channel_exists(self, team_id: str, name: str, display_name: str, 
                             purpose: str = "", channel_type: str = "O") -> Optional[Dict]:
        """Récupère un channel existant ou le crée."""
        channel = self.get_channel_by_name(team_id, name)
        if channel:
            logger.info(f"Channel {name} existe déjà")
            return channel
        
        logger.info(f"Création du channel {name}...")
        return self.create_channel(team_id, name, display_name, purpose, channel_type)
