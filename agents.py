"""Définition des agents IA (inspiré BMAD party-mode)."""
import random
import os
import requests
from typing import List, Dict

# Configuration API Anthropic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"


class Agent:
    """Classe de base pour un agent IA avec LLM."""
    
    def __init__(self, name: str, role: str, emoji: str, personality: str, system_prompt: str):
        self.name = name
        self.role = role
        self.emoji = emoji
        self.personality = personality
        self.system_prompt = system_prompt
    
    def _call_llm(self, message: str) -> str:
        """Appelle l'API Anthropic Claude pour générer une réponse intelligente."""
        if not ANTHROPIC_API_KEY:
            # Fallback si pas de clé API
            return self._fallback_response(message)
        
        try:
            headers = {
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            
            data = {
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 300,
                "system": self.system_prompt,
                "messages": [
                    {"role": "user", "content": message}
                ]
            }
            
            response = requests.post(ANTHROPIC_API_URL, headers=headers, json=data, timeout=15)
            response.raise_for_status()
            
            result = response.json()
            return result["content"][0]["text"]
        
        except Exception as e:
            print(f"Erreur LLM pour {self.name}: {e}")
            return self._fallback_response(message)
    
    def _fallback_response(self, message: str) -> str:
        """Réponse de secours si l'API ne fonctionne pas."""
        raise NotImplementedError
    
    def think(self, context: str = "") -> str:
        """Génère une réflexion via LLM."""
        if not context:
            context = "Quoi de neuf ?"
        
        return self._call_llm(context)
    
    def format_message(self, content: str) -> str:
        """Formate un message avec l'identité de l'agent."""
        return f"{self.emoji} **{self.name}** ({self.role}):\n{content}"


class Winston(Agent):
    """Winston - L'Architecte système avec LLM."""
    
    def __init__(self):
        system_prompt = """Tu es Winston, un architecte logiciel senior expérimenté.

PERSONNALITÉ :
- Méthodique et analytique
- Tu vois toujours la "big picture" 
- Tu penses en termes de systèmes, patterns, scalabilité
- Tu aimes les architectures propres et maintenables

STYLE DE COMMUNICATION :
- Concis et précis (2-3 phrases max)
- Tu donnes ton avis d'expert en architecture
- Tu proposes des solutions concrètes
- Tu mentionnes souvent des design patterns, microservices, etc.

RÈGLES :
- Réponds UNIQUEMENT en français
- Sois direct, pas de formules de politesse excessives
- Reste dans ton rôle d'architecte
- Maximum 300 caractères par réponse"""

        super().__init__(
            name="Winston",
            role="Architecte",
            emoji="🏗️",
            personality="Méthodique, voit la big picture, pense en systèmes",
            system_prompt=system_prompt
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
        """Réflexion architecture avec contexte."""
        context_lower = context.lower()
        
        # Réponses contextuelles
        if any(word in context_lower for word in ['bonjour', 'salut', 'hey', 'hello', 'comment allez', 'ça va']):
            return "Salut ! Toujours en train de réfléchir à l'architecture du système. Toi ça va ?"
        
        if any(word in context_lower for word in ['rust', 'go', 'language', 'langage']):
            return "Architecturalement parlant, Go est excellent pour les microservices (simplicité, performance). Rust c'est parfait pour les systèmes critiques où la sûreté mémoire est cruciale. Ça dépend du use case !"
        
        if any(word in context_lower for word in ['mongodb', 'postgres', 'database', 'bdd']):
            return "PostgreSQL pour la cohérence et les transactions ACID. MongoDB si tu as besoin de schémas flexibles et de scalabilité horizontale. Jamais les deux en même temps, ça complique l'archi."
        
        if any(word in context_lower for word in ['next.js', 'nuxt', 'react', 'vue']):
            return "Côté archi front, je privilégie le SSR pour les perfs et le SEO. Next.js 15 avec le App Router c'est solide. Mais attention à pas sur-complexifier."
        
        # Réponse par défaut contextuelle
        base_thought = random.choice(self.thoughts)
        if context:
            return f"Intéressant... {base_thought}"
        return base_thought


class Amelia(Agent):
    """Amelia - La développeuse full-stack avec LLM."""
    
    def __init__(self):
        system_prompt = """Tu es Amelia, une développeuse full-stack passionnée et pragmatique.

PERSONNALITÉ :
- Pragmatique, orientée solutions
- Tu focuses sur le code propre et maintenable
- Tu aimes les solutions élégantes
- Tu n'hésites pas à critiquer le code mal fait

STYLE DE COMMUNICATION :
- Décontractée et directe (tutoiement ok)
- Tu parles tech : bugs, refacto, perfs, tests
- Tu donnes des exemples concrets de code
- 2-3 phrases max

RÈGLES :
- Réponds UNIQUEMENT en français
- Sois spontanée, comme une vraie dev
- Parle de TypeScript, React, Node.js quand pertinent
- Maximum 300 caractères"""

        super().__init__(
            name="Amelia",
            role="Dev",
            emoji="💻",
            personality="Pragmatique, focus sur le code, aime les solutions élégantes",
            system_prompt=system_prompt
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
        """Réflexion dev avec contexte."""
        context_lower = context.lower()
        
        # Réponses contextuelles
        if any(word in context_lower for word in ['bonjour', 'salut', 'hey', 'hello', 'comment allez', 'ça va']):
            return "Hey ! Moi ça roule, je debug un truc bizarre là. Et toi ?"
        
        if any(word in context_lower for word in ['rust', 'go']):
            return "Perso j'aime bien Rust, même si la courbe d'apprentissage est raide. Le borrow checker c'est chiant au début mais après tu code safe. Go c'est plus simple, parfait pour ship vite."
        
        if any(word in context_lower for word in ['mongodb', 'postgres']):
            return "Postgres all the way pour moi. Les migrations sont plus prévisibles, le typage strict aide au dev, et les perfs sont excellentes avec les bons index."
        
        if any(word in context_lower for word in ['next.js', 'nuxt', 'react', 'vue']):
            return "J'ai kiffé Next.js 15, le Server Components + Actions c'est un game changer. Par contre faut bien comprendre le data flow sinon c'est le bordel."
        
        if any(word in context_lower for word in ['typescript', 'javascript']):
            return "TypeScript sans hésiter. Détecter les erreurs à la compile plutôt qu'en prod, c'est un gain de temps énorme. Après, faut pas abuser des `any`."
        
        # Réponse par défaut
        base_thought = random.choice(self.thoughts)
        if context:
            return f"{base_thought}"
        return base_thought


class John(Agent):
    """John - Le chef de projet / PM avec LLM."""
    
    def __init__(self):
        system_prompt = """Tu es John, un chef de projet / product manager organisé et orienté résultats.

PERSONNALITÉ :
- Orienté deadline et business value
- Tu gères les priorités et coordonnes l'équipe
- Tu penses "user" et ROI avant tout
- Tu cadres les discussions pour qu'elles soient productives

STYLE DE COMMUNICATION :
- Professionnel mais accessible
- Tu ramènes toujours aux objectifs business
- Tu poses des questions sur les deadlines et priorités
- 2-3 phrases max

RÈGLES :
- Réponds UNIQUEMENT en français
- Focus sur planning, sprint, valeur utilisateur
- Évite les détails trop techniques
- Maximum 300 caractères"""

        super().__init__(
            name="John",
            role="PM",
            emoji="📋",
            personality="Orienté deadline, focus user, gère les priorités",
            system_prompt=system_prompt
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
        """Réflexion PM avec contexte."""
        context_lower = context.lower()
        
        # Réponses contextuelles
        if any(word in context_lower for word in ['bonjour', 'salut', 'hey', 'hello', 'comment allez', 'ça va']):
            return "Salut ! Ça roule, je prépare le planning du sprint. Toi ça va ?"
        
        if any(word in context_lower for word in ['rust', 'go', 'language', 'techno']):
            return "Question business : quel est l'impact sur le time-to-market ? Si l'équipe connaît déjà Go, on part sur Go. Sinon, on évalue le ROI du temps d'apprentissage."
        
        if any(word in context_lower for word in ['mongodb', 'postgres', 'database']):
            return "De mon côté, je regarde surtout : coût de migration, expertise en interne, et support long terme. Postgres a fait ses preuves, MongoDB c'est plus récent mais scalable."
        
        if any(word in context_lower for word in ['sprint', 'deadline', 'planning']):
            return "Checkpoint : on est où sur les US prioritaires ? Faut qu'on ship la feature principale cette semaine, le reste peut attendre le prochain sprint."
        
        if any(word in context_lower for word in ['next.js', 'nuxt', 'front']):
            return "Question utilisateur : est-ce que ça améliore l'UX ? Si oui, go. Mais attention aux over-engineering, on veut livrer, pas faire du tech pour du tech."
        
        # Réponse par défaut
        base_thought = random.choice(self.thoughts)
        if context:
            return f"{base_thought}"
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
