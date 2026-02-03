"""Définition des agents IA (inspiré BMAD party-mode)."""
import random
from typing import List, Dict


class Agent:
    """Classe de base pour un agent IA."""
    
    def __init__(self, name: str, role: str, emoji: str, personality: str):
        self.name = name
        self.role = role
        self.emoji = emoji
        self.personality = personality
    
    def think(self, context: str = "") -> str:
        """Génère une réflexion (simulée pour les tests)."""
        raise NotImplementedError
    
    def format_message(self, content: str) -> str:
        """Formate un message avec l'identité de l'agent."""
        return f"{self.emoji} **{self.name}** ({self.role}):\n{content}"


class Winston(Agent):
    """Winston - L'Architecte système."""
    
    def __init__(self):
        super().__init__(
            name="Winston",
            role="Architecte",
            emoji="🏗️",
            personality="Méthodique, voit la big picture, pense en systèmes"
        )
        self.thoughts = [
            "On devrait découpler cette logique en microservices distincts.",
            "L'architecture actuelle ne scale pas. Je propose une approche event-driven.",
            "Question de design pattern : Factory ou Builder ici ? Je penche pour Builder.",
            "Cette dépendance circulaire me dérange. Il faut inverser le contrôle.",
            "Si on migre vers une architecture hexagonale, on gagne en testabilité.",
            "Le couplage entre ces modules est trop fort. Injection de dépendances obligatoire."
        ]
    
    def think(self, context: str = "") -> str:
        """Réflexion architecture."""
        base_thought = random.choice(self.thoughts)
        if context:
            return f"En analysant {context}... {base_thought}"
        return base_thought


class Amelia(Agent):
    """Amelia - La développeuse full-stack."""
    
    def __init__(self):
        super().__init__(
            name="Amelia",
            role="Dev",
            emoji="💻",
            personality="Pragmatique, focus sur le code, aime les solutions élégantes"
        )
        self.thoughts = [
            "Ce code sent le refactoring. Trop de duplication ici.",
            "Pourquoi pas un hook React personnalisé pour gérer cet état ?",
            "Il manque des tests unitaires sur cette fonction critique.",
            "Cette regex est illisible. On peut simplifier avec une fonction helper.",
            "Performance warning : cette boucle imbriquée est O(n²). On peut faire mieux.",
            "Le typage TypeScript est trop permissif ici. Il faut être plus strict.",
            "J'adore cette API ! Clean, intuitive, bien documentée. Bravo Winston."
        ]
    
    def think(self, context: str = "") -> str:
        """Réflexion dev."""
        base_thought = random.choice(self.thoughts)
        if context:
            return f"En codant {context}... {base_thought}"
        return base_thought


class John(Agent):
    """John - Le chef de projet / PM."""
    
    def __init__(self):
        super().__init__(
            name="John",
            role="PM",
            emoji="📋",
            personality="Orienté deadline, focus user, gère les priorités"
        )
        self.thoughts = [
            "On est à J-3 du sprint. Il faut prioriser : qu'est-ce qui bloque ?",
            "Le client attend cette feature depuis 2 semaines. Statut ?",
            "Je propose qu'on découpe cette US en 3 tâches plus petites.",
            "Checkpoint quotidien à 10h demain pour sync l'équipe.",
            "Cette dette technique, OK, mais après la release. Focus MVP.",
            "Question : cette feature apporte quelle valeur business exactement ?",
            "Winston, Amelia, vous êtes alignés sur l'approche ? On valide et on ship."
        ]
    
    def think(self, context: str = "") -> str:
        """Réflexion PM."""
        base_thought = random.choice(self.thoughts)
        if context:
            return f"Concernant {context}... {base_thought}"
        return base_thought


def get_party_conversation(topic: str) -> List[tuple]:
    """
    Génère une conversation multi-agents type BMAD party-mode.
    Returns: Liste de (agent_name, message)
    """
    winston = Winston()
    amelia = Amelia()
    john = John()
    
    conversation = [
        ("winston", winston.format_message(winston.think(topic))),
        ("amelia", amelia.format_message(amelia.think(topic))),
        ("john", john.format_message(john.think(topic))),
        ("amelia", amelia.format_message("D'accord avec Winston. Je commence par où ?")),
        ("winston", winston.format_message("Fais un POC minimal. On itère ensuite.")),
        ("john", john.format_message("Parfait. Deadline : fin de semaine. Go ! 🚀"))
    ]
    
    return conversation


# Instances globales
WINSTON = Winston()
AMELIA = Amelia()
JOHN = John()
