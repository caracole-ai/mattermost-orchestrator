"""Agents de pipeline avec chargement dynamique depuis OpenClaw."""
import json
import os
import logging
from typing import List

import config

logger = logging.getLogger(__name__)


class PipelineAgent:
    """Agent chargé dynamiquement depuis OpenClaw pour les sessions pipeline."""

    def __init__(self, agent_id: str, name: str, emoji: str, role: str,
                 mattermost_token: str, mattermost_user_id: str,
                 mattermost_username: str, expertise: List[str]):
        self.id = agent_id
        self.name = name
        self.emoji = emoji
        self.role = role
        self.mattermost_token = mattermost_token
        self.mattermost_user_id = mattermost_user_id
        self.mattermost_username = mattermost_username
        self.expertise = expertise

    @classmethod
    def from_openclaw(cls, agent_id: str) -> 'PipelineAgent':
        """Charge un agent depuis agents.json."""
        with open(config.OPENCLAW_AGENTS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        agent_data = None
        for a in data['agents']:
            if a['id'] == agent_id:
                agent_data = a
                break

        if not agent_data:
            raise ValueError(f"Agent '{agent_id}' introuvable dans agents.json")

        return cls(
            agent_id=agent_data['id'],
            name=agent_data['name'],
            emoji=agent_data['emoji'],
            role=agent_data['role'],
            mattermost_token=agent_data['mattermost']['token'],
            mattermost_user_id=agent_data['mattermost']['userId'],
            mattermost_username=agent_data['mattermost']['username'],
            expertise=agent_data.get('expertise', [])
        )

    @property
    def mention(self) -> str:
        """Retourne la mention Mattermost de l'agent."""
        return f"@{self.mattermost_username}"
