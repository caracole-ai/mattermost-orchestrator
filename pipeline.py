"""Pipeline Runner — Idée → discussion agents via OpenClaw → specs."""
import argparse
import logging
import os
import re
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional

import config
from mattermost_client import MattermostClient
from pipeline_agents import PipelineAgent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

# Timeout en secondes pour attendre la réponse d'un agent
AGENT_RESPONSE_TIMEOUT = 120
POLL_INTERVAL = 2


class PipelineRunner:
    """Orchestre une session pipeline : idée → discussion → specs.

    Le pipeline ne fait PAS d'appels LLM directs — il poste des messages
    dans Mattermost en mentionnant les agents, et OpenClaw gère les réponses.
    """

    def __init__(self, agent_ids: List[str] = None, budget_per_agent: int = None):
        self.agent_ids = agent_ids or ["winston", "amelia", "manolo"]
        self.budget_per_agent = budget_per_agent or config.PIPELINE_BUDGET_PER_AGENT
        self.admin_client: Optional[MattermostClient] = None
        self.agents: List[PipelineAgent] = []
        self.conversation_history: List[Dict] = []
        self.message_counts: Dict[str, int] = {}
        self.channel_id: Optional[str] = None

    # === Obsidian I/O ===

    def load_idea(self, idea_path: str) -> str:
        """Lit le fichier markdown d'une idée depuis le disque."""
        if not os.path.isabs(idea_path):
            idea_path = os.path.join(config.OBSIDIAN_VAULT_PATH, "Idées", idea_path)
        with open(idea_path, 'r', encoding='utf-8') as f:
            return f.read()

    def find_idea(self, search_term: str) -> str:
        """Cherche une idée par nom partiel dans Idées/."""
        ideas_dir = os.path.join(config.OBSIDIAN_VAULT_PATH, "Idées")
        slug = search_term.lower().replace(' ', '-')
        for filename in sorted(os.listdir(ideas_dir), reverse=True):
            if slug in filename.lower() and filename.endswith('.md'):
                return os.path.join(ideas_dir, filename)
        raise FileNotFoundError(f"Aucune idée trouvée pour '{search_term}'")

    def parse_idea_metadata(self, content: str) -> Dict:
        """Parse le frontmatter YAML basique (entre --- et ---)."""
        metadata = {"titre": "Sans titre"}
        if not content.startswith('---'):
            return metadata
        parts = content.split('---', 2)
        if len(parts) < 3:
            return metadata
        for line in parts[1].strip().split('\n'):
            if ':' in line and not line.strip().startswith('-') and not line.strip().startswith('['):
                key, value = line.split(':', 1)
                metadata[key.strip()] = value.strip().strip('"').strip("'")
        return metadata

    def write_specs_to_obsidian(self, idea_metadata: Dict, synthesis: str,
                                idea_filename: str) -> str:
        """Écrit les specs dans Obsidian/Projets/."""
        slug = self._slugify(idea_metadata.get('titre', 'pipeline-output'))
        filename = f"{slug}-specs.md"
        output_path = os.path.join(config.OBSIDIAN_VAULT_PATH, "Projets", filename)

        now = datetime.now().isoformat(timespec='seconds')
        agent_names = [a.name for a in self.agents]

        content = f"""---
titre: "Specs — {idea_metadata.get('titre', 'Sans titre')}"
type: specs
source_idee: "{os.path.basename(idea_filename)}"
pipeline_date: "{now}"
pipeline_agents:
{chr(10).join(f'  - {name}' for name in agent_names)}
statut: brouillon
---

# Specs : {idea_metadata.get('titre', 'Sans titre')}

> Généré par le pipeline mattermost-orchestrator le {datetime.now().strftime('%Y-%m-%d à %H:%M')}
> Agents : {', '.join(f'{a.emoji} {a.name}' for a in self.agents)}

{synthesis}

---

## Conversation complète

"""
        for msg in self.conversation_history:
            content += f"### {msg['agent_emoji']} {msg['agent_name']} ({msg['agent_role']}) — Message {msg['message_number']}/{self.budget_per_agent}\n\n"
            content += f"{msg['content']}\n\n"

        content += "---\n*Généré automatiquement par pipeline.py*\n"

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return output_path

    # === Mattermost ===

    def create_pipeline_channel(self, idea_title: str) -> Optional[str]:
        """Crée un channel privé dédié pour cette session pipeline."""
        slug = self._slugify(idea_title)[:30]
        timestamp = time.strftime("%Y%m%d-%H%M")
        channel_name = f"pipeline-{slug}-{timestamp}"
        display_name = f"🔬 Pipeline : {idea_title[:50]}"

        channel = self.admin_client.ensure_channel_exists(
            team_id=config.TEAM_ID,
            name=channel_name,
            display_name=display_name,
            purpose=f"Pipeline discussion pour: {idea_title}",
            channel_type="P"
        )
        return channel['id'] if channel else None

    def wait_for_agent_response(self, agent: PipelineAgent,
                                trigger_timestamp: int) -> Optional[str]:
        """Poll Mattermost jusqu'à ce que l'agent réponde.

        Args:
            agent: L'agent dont on attend la réponse
            trigger_timestamp: Timestamp (ms) du message déclencheur

        Returns:
            Le contenu du message de l'agent, ou None si timeout
        """
        start = time.time()

        while time.time() - start < AGENT_RESPONSE_TIMEOUT:
            time.sleep(POLL_INTERVAL)

            posts_data = self.admin_client.get_posts_for_channel(self.channel_id, per_page=10)
            if not posts_data or 'posts' not in posts_data:
                continue

            # Chercher un post de cet agent après le trigger
            for post_id, post in posts_data['posts'].items():
                if (post['user_id'] == agent.mattermost_user_id
                        and post['create_at'] > trigger_timestamp):
                    return post['message']

        logger.warning(f"⏱️ Timeout : {agent.name} n'a pas répondu en {AGENT_RESPONSE_TIMEOUT}s")
        return None

    # === Pipeline Core ===

    def setup_agents(self) -> None:
        """Charge les agents via PipelineAgent.from_openclaw()."""
        self.agents = []
        for agent_id in self.agent_ids:
            agent = PipelineAgent.from_openclaw(agent_id)
            self.agents.append(agent)
            self.message_counts[agent.id] = 0
        logger.info(f"👥 Agents chargés : {', '.join(f'{a.emoji} {a.name}' for a in self.agents)}")

    def build_trigger_message(self, agent: PipelineAgent, idea_content: str,
                               round_num: int, remaining: int,
                               is_first: bool) -> str:
        """Construit le message qui trigger un agent via @mention."""
        mention = agent.mention
        budget = self.budget_per_agent

        msg_num = self.message_counts[agent.id] + 1
        counter = f"[{msg_num}/{budget}]"

        if is_first and round_num == 1:
            return (
                f"{mention} {counter}\n\n"
                f"📋 **Session Pipeline — Brainstorming structuré**\n\n"
                f"**L'idée à analyser :**\n\n{idea_content}\n\n---\n\n"
                f"Tu as {budget} messages pour contribuer. "
                f"Sois concis, substantiel, et donne ton avis d'expert en {agent.role} "
                f"({', '.join(agent.expertise)}).\n"
                f"⚠️ Ne réponds qu'à CE message. Ne réagis pas aux autres agents sauf si @mentionné.\n\n"
                f"Donne ta première analyse."
            )
        elif remaining == 1:
            return (
                f"{mention} {counter} — C'est ton **dernier message**. "
                f"Fais ta synthèse et tes recommandations finales. "
                f"Après ça, tu ne réponds plus."
            )
        else:
            return (
                f"{mention} {counter} — C'est ton tour. "
                f"Il te reste {remaining} messages. "
                f"Réagis à ce qui a été dit et apporte ta perspective de {agent.role}. "
                f"Ne réponds qu'à CE message."
            )

    def run_conversation(self, idea_content: str) -> None:
        """Boucle de conversation round-robin via OpenClaw."""
        total_messages = self.budget_per_agent * len(self.agents)
        logger.info(f"💬 Démarrage conversation ({total_messages} messages, {self.budget_per_agent} par agent)")

        for round_num in range(1, self.budget_per_agent + 1):
            logger.info(f"📍 Round {round_num}/{self.budget_per_agent}")

            for i, agent in enumerate(self.agents):
                if self.message_counts[agent.id] >= self.budget_per_agent:
                    continue

                remaining = self.budget_per_agent - self.message_counts[agent.id]
                is_first = (round_num == 1 and i == 0)

                # Construire et poster le trigger
                trigger = self.build_trigger_message(
                    agent, idea_content, round_num, remaining, is_first
                )
                trigger_post = self.admin_client.create_post(self.channel_id, trigger)
                trigger_ts = trigger_post['create_at'] if trigger_post else int(time.time() * 1000)

                # Attendre la réponse de l'agent via OpenClaw
                logger.info(f"  ⏳ Attente de {agent.emoji} {agent.name}...")
                response = self.wait_for_agent_response(agent, trigger_ts)

                if response is None:
                    response = f"[{agent.name} n'a pas répondu dans le temps imparti]"
                    self.admin_client.create_post(self.channel_id, f"⚠️ {response}")

                # Tracker
                self.message_counts[agent.id] += 1
                self.conversation_history.append({
                    "agent_id": agent.id,
                    "agent_name": agent.name,
                    "agent_emoji": agent.emoji,
                    "agent_role": agent.role,
                    "content": response,
                    "round": round_num,
                    "message_number": self.message_counts[agent.id]
                })

                msg_total = sum(self.message_counts.values())
                logger.info(f"  ✅ {agent.emoji} {agent.name} — message {self.message_counts[agent.id]}/{self.budget_per_agent} (total: {msg_total}/{total_messages})")

    def request_synthesis(self) -> Optional[str]:
        """Demande une synthèse à l'orchestrateur (Cloclo) via OpenClaw.

        Cloclo est ajouté au channel dès le début du pipeline pour qu'il
        voie toute la conversation dans son contexte.
        """
        cloclo = self.synthesis_agent
        agent_names = ', '.join(f'{a.emoji} {a.name}' for a in self.agents)

        trigger = (
            f"{cloclo.mention}\n\n"
            f"🎯 **Synthèse demandée**\n\n"
            f"La discussion entre {agent_names} est terminée ({sum(self.message_counts.values())} messages).\n\n"
            f"Produis un document de specs structuré avec :\n"
            f"1. **Résumé exécutif** (3-5 lignes)\n"
            f"2. **Architecture proposée**\n"
            f"3. **Fonctionnalités clés** (priorisées)\n"
            f"4. **Stack technique recommandée**\n"
            f"5. **Risques identifiés**\n"
            f"6. **Plan d'action** (étapes concrètes)\n\n"
            f"Base-toi sur la conversation ci-dessus. Sois concis et actionnable."
        )

        trigger_post = self.admin_client.create_post(self.channel_id, trigger)
        trigger_ts = trigger_post['create_at'] if trigger_post else int(time.time() * 1000)

        logger.info(f"  ⏳ Attente de la synthèse par {cloclo.emoji} {cloclo.name}...")
        return self.wait_for_agent_response(cloclo, trigger_ts)

    # === Main Flow ===

    def run(self, idea_path: str) -> int:
        """Exécute le pipeline complet."""
        logger.info("🚀 Démarrage du pipeline...")

        # 1. Charger l'idée
        idea_content = self.load_idea(idea_path)
        metadata = self.parse_idea_metadata(idea_content)
        titre = metadata.get('titre', 'Sans titre')
        logger.info(f"📝 Idée : {titre}")

        # 2. Connexion admin Mattermost
        self.admin_client = MattermostClient(config.API_BASE, config.ADMIN_TOKEN)
        me = self.admin_client.get_me()
        if not me:
            logger.error("❌ Connexion admin Mattermost impossible")
            return 1
        logger.info("✅ Connecté à Mattermost")

        # 3. Charger les agents
        self.setup_agents()

        # 4. Créer le channel pipeline
        self.channel_id = self.create_pipeline_channel(titre)
        if not self.channel_id:
            logger.error("❌ Création du channel échouée")
            return 1
        logger.info("📢 Channel pipeline créé")

        # 5. Ajouter les agents + Cloclo (synthèse) au channel
        for agent in self.agents:
            self.admin_client.add_user_to_team(config.TEAM_ID, agent.mattermost_user_id)
            self.admin_client.add_user_to_channel(self.channel_id, agent.mattermost_user_id)

        # Ajouter Cloclo dès le départ pour qu'il voie toute la conversation
        self.synthesis_agent = PipelineAgent.from_openclaw("main")
        self.admin_client.add_user_to_team(config.TEAM_ID, self.synthesis_agent.mattermost_user_id)
        self.admin_client.add_user_to_channel(self.channel_id, self.synthesis_agent.mattermost_user_id)

        # 6. Kick-off avec règles strictes
        total = self.budget_per_agent * len(self.agents)
        kickoff = (
            f"🚀 **Pipeline : {titre}**\n\n"
            f"**Agents** : {', '.join(f'{a.emoji} {a.name} ({a.role})' for a in self.agents)}\n"
            f"**Budget** : {self.budget_per_agent} messages chacun ({total} total)\n\n"
            f"⚠️ **RÈGLES STRICTES** :\n"
            f"- Tu ne réponds **QUE** quand tu es mentionné explicitement avec `@ton_nom`\n"
            f"- Tu ne réagis **JAMAIS** aux messages des autres agents sauf si tu es @mentionné\n"
            f"- Tu respectes ton compteur de messages — quand ton budget est épuisé, tu te tais\n"
            f"- Tu ne modifies **AUCUNE** note Obsidian pendant cette session\n"
            f"- L'orchestrateur gère les tours de parole. Attends ton tour.\n"
        )
        self.admin_client.create_post(self.channel_id, kickoff)
        time.sleep(2)

        # 7. Conversation via OpenClaw
        self.run_conversation(idea_content)

        # 8. Synthèse via Cloclo
        logger.info("🎯 Demande de synthèse...")
        self.admin_client.create_post(self.channel_id, "---\n🎯 **Synthèse en cours...**")
        synthesis = self.request_synthesis()

        if not synthesis:
            synthesis = "[Synthèse non disponible — timeout]"
            self.admin_client.create_post(self.channel_id, f"⚠️ {synthesis}")

        # 9. Écriture Obsidian
        spec_path = self.write_specs_to_obsidian(metadata, synthesis, idea_path)
        logger.info(f"📝 Specs écrites : {spec_path}")
        self.admin_client.create_post(
            self.channel_id,
            f"✅ **Specs écrites dans Obsidian**\n`{os.path.basename(spec_path)}`"
        )

        # 10. Log dans orchestrator-log
        log_channel = self.admin_client.get_channel_by_name(config.TEAM_ID, "orchestrator-log")
        if log_channel:
            self.admin_client.create_post(
                log_channel['id'],
                f"✅ Pipeline terminé : **{titre}**\n"
                f"Agents : {', '.join(a.name for a in self.agents)}\n"
                f"Messages : {total}\n"
                f"Specs : `{os.path.basename(spec_path)}`"
            )

        # 11. Cleanup — retirer les agents du channel pour stopper toute réponse
        logger.info("🧹 Retrait des agents du channel...")
        all_agents = list(self.agents) + [self.synthesis_agent]
        for agent in all_agents:
            self.admin_client._request(
                "DELETE",
                f"/channels/{self.channel_id}/members/{agent.mattermost_user_id}"
            )

        logger.info("✅ Pipeline terminé avec succès")
        return 0

    # === Helpers ===

    @staticmethod
    def _slugify(text: str) -> str:
        """Convertit un texte en slug URL-safe."""
        text = text.lower().strip()
        text = re.sub(r'[àáâãäå]', 'a', text)
        text = re.sub(r'[èéêë]', 'e', text)
        text = re.sub(r'[ìíîï]', 'i', text)
        text = re.sub(r'[òóôõö]', 'o', text)
        text = re.sub(r'[ùúûü]', 'u', text)
        text = re.sub(r'[ç]', 'c', text)
        text = re.sub(r'[^a-z0-9]+', '-', text)
        return text.strip('-')


def main():
    parser = argparse.ArgumentParser(
        description="Pipeline Runner — idée → specs via agents IA (OpenClaw)"
    )

    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("idea_path", nargs="?",
                             help="Chemin vers le fichier idée (.md)")
    input_group.add_argument("--idea", "-i",
                             help="Recherche par nom (ex: 'agent-de-trading')")

    parser.add_argument("--agents", "-a", nargs=3,
                        default=["winston", "amelia", "manolo"],
                        help="3 agent IDs (default: winston amelia manolo)")
    parser.add_argument("--budget", "-b", type=int, default=None,
                        help=f"Messages par agent (default: {config.PIPELINE_BUDGET_PER_AGENT})")
    parser.add_argument("--dry-run", action="store_true",
                        help="Affiche le plan sans exécuter")

    args = parser.parse_args()

    runner = PipelineRunner(agent_ids=args.agents, budget_per_agent=args.budget)

    # Résoudre l'idée
    if args.idea:
        idea_path = runner.find_idea(args.idea)
    else:
        idea_path = args.idea_path

    logger.info(f"📄 Fichier idée : {idea_path}")

    if args.dry_run:
        idea_content = runner.load_idea(idea_path)
        metadata = runner.parse_idea_metadata(idea_content)
        runner.setup_agents()

        print(f"\n{'='*60}")
        print(f"🔬 PIPELINE DRY RUN")
        print(f"{'='*60}")
        print(f"📝 Idée     : {metadata.get('titre', 'Sans titre')}")
        print(f"📄 Fichier  : {idea_path}")
        print(f"👥 Agents   : {', '.join(f'{a.emoji} {a.name} ({a.role})' for a in runner.agents)}")
        print(f"💬 Budget   : {runner.budget_per_agent} msg/agent ({runner.budget_per_agent * len(runner.agents)} total)")
        print(f"🔗 OpenClaw : les agents répondent via Mattermost (pas d'appel API direct)")
        print(f"🎯 Synthèse : déléguée à Cloclo (orchestrateur)")
        print(f"{'='*60}\n")
        return 0

    sys.exit(runner.run(idea_path))


if __name__ == "__main__":
    main()
