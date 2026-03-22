"""Incubation Pipeline — Idée → Projet via team incubation (3 phases, 6 agents).

Gère la distribution de parole par phase :
  Phase 1 — Germination   : iris (visionnaire) ↔ hugo (critique)       → 6 messages
  Phase 2 — Structuration  : stella (stratège) ↔ felix (facilitateur)   → 4 messages
  Phase 3 — Concrétisation : remi (réalisateur) ↔ gaelle (gardien)     → 4 messages
  Feedback (optionnel)     : gaelle → stella ou iris                    → 4 messages max
  Synthèse                 : cloclo                                     → 1 message
  Validation               : gaelle                                     → 1 message
  ─────────────────────────────────────────────────────────────────────
  TOTAL MAX : 20 messages (hard limit)
"""
import logging
import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import config
from mattermost_client import MattermostClient
from pipeline_agents import PipelineAgent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

AGENT_RESPONSE_TIMEOUT = 120
POLL_INTERVAL = 2
HARD_LIMIT = 20


@dataclass
class Phase:
    """Définition d'une phase d'incubation."""
    name: str
    agent_ids: List[str]
    messages_per_agent: int
    description: str

    @property
    def total_messages(self) -> int:
        return len(self.agent_ids) * self.messages_per_agent


# Phases fixes du pipeline incubation
INCUBATION_PHASES = [
    Phase(
        name="Germination",
        agent_ids=["iris", "hugo"],
        messages_per_agent=3,
        description="Explorer le potentiel de l'idée. Iris ouvre le champ des possibles, Hugo ancre dans le réel."
    ),
    Phase(
        name="Structuration",
        agent_ids=["stella", "felix"],
        messages_per_agent=2,
        description="Prioriser et cadrer. Stella définit les objectifs et le scope, Felix fluidifie."
    ),
    Phase(
        name="Concrétisation",
        agent_ids=["remi", "gaelle"],
        messages_per_agent=2,
        description="Produire le livrable. Remi rédige la fiche projet, Gaelle vérifie la cohérence."
    ),
]


class IncubationPipeline:
    """Orchestre une session incubation : idée → discussion 3 phases → fiche projet.

    Distribution de parole stricte :
    - Un seul agent tagué à la fois (pas de messages croisés)
    - Alternance entre les 2 agents de chaque phase
    - Compteur global [N/20] dans chaque trigger
    - Hard limit à 20 messages, jamais dépassé
    """

    def __init__(self):
        self.admin_client: Optional[MattermostClient] = None
        self.all_agents: Dict[str, PipelineAgent] = {}
        self.synthesis_agent: Optional[PipelineAgent] = None
        self.conversation_history: List[Dict] = []
        self.global_message_count: int = 0
        self.channel_id: Optional[str] = None

    # === Agent Management ===

    def setup_agents(self) -> None:
        """Charge tous les agents incubation + Cloclo pour la synthèse."""
        all_ids = set()
        for phase in INCUBATION_PHASES:
            all_ids.update(phase.agent_ids)

        for agent_id in all_ids:
            agent = PipelineAgent.from_openclaw(agent_id)
            self.all_agents[agent_id] = agent

        self.synthesis_agent = PipelineAgent.from_openclaw("main")

        agent_list = ', '.join(f'{a.emoji} {a.name}' for a in self.all_agents.values())
        logger.info(f"👥 Agents incubation chargés : {agent_list}")

    # === Mattermost ===

    def create_channel(self, idea_title: str) -> Optional[str]:
        """Crée le channel Mattermost pour cette session incubation."""
        slug = self._slugify(idea_title)[:30]
        timestamp = time.strftime("%Y%m%d-%H%M")
        channel_name = f"incub-{slug}-{timestamp}"
        display_name = f"🧪 Incubation : {idea_title[:50]}"

        channel = self.admin_client.ensure_channel_exists(
            team_id=config.TEAM_ID,
            name=channel_name,
            display_name=display_name,
            purpose=f"Incubation idea-to-project : {idea_title}",
            channel_type="P"
        )
        return channel['id'] if channel else None

    def wait_for_response(self, agent: PipelineAgent,
                          trigger_timestamp: int) -> Optional[str]:
        """Poll Mattermost jusqu'à ce que l'agent réponde (120s timeout)."""
        start = time.time()
        while time.time() - start < AGENT_RESPONSE_TIMEOUT:
            time.sleep(POLL_INTERVAL)
            posts_data = self.admin_client.get_posts_for_channel(self.channel_id, per_page=10)
            if not posts_data or 'posts' not in posts_data:
                continue
            for post_id, post in posts_data['posts'].items():
                if (post['user_id'] == agent.mattermost_user_id
                        and post['create_at'] > trigger_timestamp):
                    return post['message']
        logger.warning(f"⏱️ Timeout : {agent.name} n'a pas répondu en {AGENT_RESPONSE_TIMEOUT}s")
        return None

    def post_and_wait(self, agent: PipelineAgent, message: str) -> Optional[str]:
        """Poste un trigger et attend la réponse de l'agent."""
        trigger_post = self.admin_client.create_post(self.channel_id, message)
        trigger_ts = trigger_post['create_at'] if trigger_post else int(time.time() * 1000)
        logger.info(f"  ⏳ [{self.global_message_count}/{HARD_LIMIT}] Attente de {agent.emoji} {agent.name}...")
        response = self.wait_for_response(agent, trigger_ts)

        if response is None:
            response = f"[{agent.name} n'a pas répondu dans le temps imparti]"
            self.admin_client.create_post(self.channel_id, f"⚠️ {response}")

        self.global_message_count += 1
        self.conversation_history.append({
            "agent_id": agent.id,
            "agent_name": agent.name,
            "agent_emoji": agent.emoji,
            "agent_role": agent.role,
            "content": response,
            "message_number": self.global_message_count,
            "phase": self._current_phase_name,
        })

        logger.info(f"  ✅ {agent.emoji} {agent.name} — [{self.global_message_count}/{HARD_LIMIT}]")
        return response

    # === Trigger Messages ===

    def build_phase_intro(self, phase: Phase) -> str:
        """Annonce le début d'une nouvelle phase dans le channel."""
        agents_str = ' et '.join(
            f'{self.all_agents[aid].emoji} {self.all_agents[aid].name} ({self.all_agents[aid].role})'
            for aid in phase.agent_ids
        )
        return (
            f"---\n"
            f"🔄 **Phase : {phase.name}** — {phase.description}\n\n"
            f"Agents convoqués : {agents_str}\n"
            f"Budget : {phase.messages_per_agent} messages chacun ({phase.total_messages} pour cette phase)\n"
        )

    def build_trigger(self, agent: PipelineAgent, phase: Phase,
                      idea_content: str, msg_in_phase: int,
                      is_first_overall: bool) -> str:
        """Construit le message trigger pour un agent dans une phase."""
        counter = f"[{self.global_message_count + 1}/{HARD_LIMIT}]"
        is_last = (msg_in_phase == phase.messages_per_agent)

        partner_id = [aid for aid in phase.agent_ids if aid != agent.id][0]
        partner = self.all_agents[partner_id]

        if is_first_overall:
            return (
                f"{agent.mention} {counter}\n\n"
                f"📋 **Session Incubation — {phase.name}**\n\n"
                f"**L'idée à incuber :**\n\n{idea_content}\n\n---\n\n"
                f"Tu es en binôme avec {partner.emoji} {partner.name} ({partner.role}). "
                f"Tu as {phase.messages_per_agent} messages pour cette phase.\n"
                f"En tant que {agent.role} ({', '.join(agent.expertise[:3])}), "
                f"donne ta première analyse de cette idée.\n"
                f"⚠️ Ne réponds qu'à CE message."
            )
        elif is_last:
            return (
                f"{agent.mention} {counter} — C'est ton **dernier message** pour cette phase. "
                f"Conclus ta contribution et formule tes recommandations clés."
            )
        elif msg_in_phase == 1:
            # Premier message de cet agent dans cette phase (mais pas le tout premier du pipeline)
            return (
                f"{agent.mention} {counter}\n\n"
                f"**Phase : {phase.name}** — Tu es en binôme avec {partner.emoji} {partner.name} ({partner.role}).\n"
                f"Tu as {phase.messages_per_agent} messages. "
                f"En tant que {agent.role}, réagis à ce qui a été dit et apporte ta perspective.\n"
                f"⚠️ Ne réponds qu'à CE message."
            )
        else:
            return (
                f"{agent.mention} {counter} — C'est ton tour. "
                f"Il te reste {phase.messages_per_agent - msg_in_phase + 1} messages. "
                f"Réagis et approfondis en tant que {agent.role}.\n"
                f"⚠️ Ne réponds qu'à CE message."
            )

    # === Phase Execution ===

    def run_phase(self, phase: Phase, idea_content: str) -> None:
        """Exécute une phase : alternance stricte entre les 2 agents."""
        self._current_phase_name = phase.name

        # Annonce de phase
        self.admin_client.create_post(self.channel_id, self.build_phase_intro(phase))
        time.sleep(1)

        agents = [self.all_agents[aid] for aid in phase.agent_ids]
        agent_msg_counts = {aid: 0 for aid in phase.agent_ids}

        # Alternance stricte : agent A, agent B, agent A, agent B...
        total_msgs = phase.total_messages
        for msg_idx in range(total_msgs):
            if self.global_message_count >= HARD_LIMIT:
                logger.warning(f"⛔ Hard limit {HARD_LIMIT} atteinte, arrêt.")
                return

            agent = agents[msg_idx % len(agents)]
            agent_msg_counts[agent.id] += 1

            is_first_overall = (self.global_message_count == 0)
            trigger = self.build_trigger(
                agent, phase, idea_content,
                msg_in_phase=agent_msg_counts[agent.id],
                is_first_overall=is_first_overall
            )
            self.post_and_wait(agent, trigger)

    def run_feedback(self, idea_content: str) -> bool:
        """Boucle de feedback optionnelle (max 4 messages).

        Gaelle évalue si le livrable est cohérent. Si non, elle remonte
        vers Stella ou Iris pour réajustement.

        Returns:
            True si feedback a été déclenché, False sinon.
        """
        if self.global_message_count >= HARD_LIMIT - 2:
            # Pas assez de budget pour feedback + synthèse + validation
            return False

        gaelle = self.all_agents["gaelle"]
        self._current_phase_name = "Feedback"

        counter = f"[{self.global_message_count + 1}/{HARD_LIMIT}]"
        trigger = (
            f"{gaelle.mention} {counter}\n\n"
            f"🔍 **Évaluation de cohérence**\n\n"
            f"Avant la synthèse finale, vérifie :\n"
            f"1. Le livrable de Remi est-il cohérent avec la vision d'Iris ?\n"
            f"2. Les objectifs de Stella sont-ils bien reflétés ?\n"
            f"3. Y a-t-il des incohérences majeures à corriger ?\n\n"
            f"Si tout est cohérent, réponds `✅ COHÉRENT` et on passe à la synthèse.\n"
            f"Si incohérence majeure, identifie-la et mentionne l'agent à qui remonter (@stella ou @iris)."
        )

        response = self.post_and_wait(gaelle, trigger)
        if not response or "COHÉRENT" in response.upper():
            logger.info("  ✅ Gaelle valide la cohérence — pas de feedback nécessaire")
            return False

        # Feedback déclenché — max 3 messages supplémentaires
        logger.info("  🔄 Feedback déclenché par Gaelle")
        feedback_budget = min(3, HARD_LIMIT - self.global_message_count - 2)  # -2 pour synthèse+validation

        for i in range(feedback_budget):
            if self.global_message_count >= HARD_LIMIT - 2:
                break

            # Déterminer l'agent à relancer (stella par défaut, iris si mentionnée)
            target_id = "stella"
            if response and "@iris" in response.lower():
                target_id = "iris"

            target = self.all_agents[target_id]
            counter = f"[{self.global_message_count + 1}/{HARD_LIMIT}]"
            trigger = (
                f"{target.mention} {counter}\n\n"
                f"🔄 **Feedback de Gaelle** — Réajustement demandé.\n"
                f"Gaelle a identifié un point à corriger. "
                f"Prends en compte son retour et ajuste ta position."
            )
            response = self.post_and_wait(target, trigger)

        return True

    def request_synthesis(self) -> Optional[str]:
        """Demande la synthèse à Cloclo — message [19/20] ou avant."""
        cloclo = self.synthesis_agent
        self._current_phase_name = "Synthèse"

        template_path = os.path.join(
            config.OBSIDIAN_VAULT_PATH, "Templates", "_template-projet.md"
        )
        skeleton = ""
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            parts = content.split('---', 2)
            if len(parts) >= 3:
                skeleton = parts[2].strip()
                # Couper avant Journal de bord
                for marker in ['## Journal de bord']:
                    idx = skeleton.find(marker)
                    if idx > 0:
                        skeleton = skeleton[:idx].rstrip()
                        break
        except FileNotFoundError:
            logger.warning("⚠️ Template projet introuvable")

        agents_str = ', '.join(f'{a.emoji} {a.name}' for a in self.all_agents.values())
        counter = f"[{self.global_message_count + 1}/{HARD_LIMIT}]"

        trigger = (
            f"{cloclo.mention} {counter}\n\n"
            f"🎯 **Synthèse demandée — Fiche projet**\n\n"
            f"La discussion d'incubation entre {agents_str} est terminée "
            f"({self.global_message_count} messages, 3 phases).\n\n"
            f"Compile les conclusions en remplissant la structure ci-dessous.\n"
            f"Chaque section doit refléter les décisions prises pendant la discussion.\n"
            f"Si une section n'a pas été abordée : `<!-- À compléter -->`.\n\n"
            f"**Structure :**\n\n{skeleton}\n\n"
            f"---\nRemplis maintenant. Sois concis et actionnable."
        )

        return self.post_and_wait(cloclo, trigger)

    def request_validation(self) -> Optional[str]:
        """Validation finale par Gaelle — message [20/20] ou dernier."""
        gaelle = self.all_agents["gaelle"]
        self._current_phase_name = "Validation"

        counter = f"[{self.global_message_count + 1}/{HARD_LIMIT}]"
        trigger = (
            f"{gaelle.mention} {counter}\n\n"
            f"🛡️ **Validation finale** — Dernier message du pipeline.\n\n"
            f"Vérifie que la synthèse de Cloclo est cohérente avec l'intention initiale "
            f"et les décisions prises. Réponds `✅ VALIDÉ` ou liste les corrections mineures."
        )
        return self.post_and_wait(gaelle, trigger)

    # === Output ===

    def write_project_to_obsidian(self, idea_metadata: Dict,
                                   synthesis: str, idea_path: str) -> str:
        """Écrit la fiche projet dans Projets/<shortname>/project.md."""
        slug = self._slugify(idea_metadata.get('titre', 'incubation-output'))
        shortname = idea_metadata.get('shortname', slug)
        project_dir = os.path.join(config.OBSIDIAN_VAULT_PATH, "Projets", shortname)
        os.makedirs(project_dir, exist_ok=True)

        now = datetime.now().isoformat(timespec='seconds')
        agents_str = ', '.join(f'{a.emoji} {a.name}' for a in self.all_agents.values())
        date_human = datetime.now().strftime('%Y-%m-%d à %H:%M')

        # project.md — load frontmatter from _template-projet.md
        project_path = os.path.join(project_dir, f"{shortname}.md")
        template_frontmatter = self._load_project_template_frontmatter()
        idea_basename = os.path.splitext(os.path.basename(idea_path))[0]
        today = datetime.now().strftime('%Y-%m-%d')

        # Merge template frontmatter with actual values
        frontmatter = template_frontmatter.copy()
        frontmatter.update({
            'titre': idea_metadata.get('titre', 'Sans titre'),
            'id': shortname,
            'statut': 'cadrage',
            'idee_source': f'[[Idées/{idea_basename}]]',
            'tags': idea_metadata.get('themes', []),
            'chemin': f'~/Desktop/coding-projects/AUTO-BUILD/{shortname}',
            'created_at': today,
            'updated_at': today,
        })

        # Build YAML frontmatter (manual serialization — no PyYAML dependency)
        frontmatter_yaml = self._serialize_frontmatter(frontmatter)

        project_content = f"""---
{frontmatter_yaml}
---

# {idea_metadata.get('titre', 'Sans titre')}

> Généré par le pipeline d'incubation le {date_human}
> Agents : {agents_str}

{synthesis}

---
*Projet issu de l'idée : [[{idea_basename}]]*
"""
        with open(project_path, 'w', encoding='utf-8') as f:
            f.write(project_content)

        # conversation.md
        conv_path = os.path.join(project_dir, "conversation-incubation.md")
        conv_content = f"""---
type: conversation
pipeline_date: "{now}"
pipeline_type: incubation
---

# Conversation incubation : {idea_metadata.get('titre', 'Sans titre')}

> {date_human} — {agents_str}
> Budget : {self.global_message_count}/{HARD_LIMIT} messages utilisés

"""
        for msg in self.conversation_history:
            conv_content += (
                f"## {msg['agent_emoji']} {msg['agent_name']} ({msg['agent_role']}) "
                f"— [{msg['message_number']}/{HARD_LIMIT}] Phase: {msg['phase']}\n\n"
                f"{msg['content']}\n\n"
            )
        conv_content += "---\n*Généré automatiquement par incubation_pipeline.py*\n"

        with open(conv_path, 'w', encoding='utf-8') as f:
            f.write(conv_content)

        return project_path

    # === Main Flow ===

    def run(self, idea_path: str) -> int:
        """Exécute le pipeline d'incubation complet."""
        logger.info("🧪 Démarrage du pipeline d'incubation...")

        # 1. Charger l'idée
        if not os.path.isabs(idea_path):
            idea_path = os.path.join(config.OBSIDIAN_VAULT_PATH, "Idées", idea_path)
        with open(idea_path, 'r', encoding='utf-8') as f:
            idea_content = f.read()
        metadata = self._parse_metadata(idea_content)
        titre = metadata.get('titre', 'Sans titre')
        logger.info(f"📝 Idée : {titre}")

        # 2. Connexion Mattermost
        self.admin_client = MattermostClient(config.API_BASE, config.ADMIN_TOKEN)
        if not self.admin_client.get_me():
            logger.error("❌ Connexion Mattermost impossible")
            return 1

        # 3. Charger les agents
        self.setup_agents()

        # 4. Créer le channel
        self.channel_id = self.create_channel(titre)
        if not self.channel_id:
            logger.error("❌ Création du channel échouée")
            return 1

        # 5. Ajouter tous les agents au channel
        all_mm_agents = list(self.all_agents.values()) + [self.synthesis_agent]
        for agent in all_mm_agents:
            self.admin_client.add_user_to_team(config.TEAM_ID, agent.mattermost_user_id)
            self.admin_client.add_user_to_channel(self.channel_id, agent.mattermost_user_id)

        # 6. Kickoff
        phases_str = '\n'.join(
            f"  {i+1}. **{p.name}** : {', '.join(f'{self.all_agents[a].emoji} {self.all_agents[a].name}' for a in p.agent_ids)} ({p.total_messages} msg)"
            for i, p in enumerate(INCUBATION_PHASES)
        )
        kickoff = (
            f"🧪 **Incubation : {titre}**\n\n"
            f"**Phases :**\n{phases_str}\n\n"
            f"**Budget total : {HARD_LIMIT} messages max**\n\n"
            f"⚠️ **RÈGLES** :\n"
            f"- Tu ne réponds **QUE** quand tu es @mentionné\n"
            f"- Tu respectes ton budget de messages par phase\n"
            f"- Tu ne modifies **AUCUNE** note Obsidian\n"
            f"- L'orchestrateur gère les tours de parole\n"
        )
        self.admin_client.create_post(self.channel_id, kickoff)
        time.sleep(2)

        # 7. Exécuter les 3 phases
        for phase in INCUBATION_PHASES:
            if self.global_message_count >= HARD_LIMIT - 2:
                logger.warning("⛔ Budget insuffisant pour continuer les phases")
                break
            logger.info(f"🔄 Phase : {phase.name}")
            self.run_phase(phase, idea_content)

        # 8. Feedback optionnel
        if self.global_message_count < HARD_LIMIT - 2:
            self.run_feedback(idea_content)

        # 9. Synthèse par Cloclo
        if self.global_message_count < HARD_LIMIT:
            logger.info("🎯 Synthèse par Cloclo...")
            self.admin_client.create_post(self.channel_id, "---\n🎯 **Synthèse en cours...**")
            synthesis = self.request_synthesis()
        else:
            synthesis = "[Budget épuisé avant synthèse]"

        # 10. Validation finale par Gaelle
        if self.global_message_count < HARD_LIMIT:
            self.request_validation()

        if not synthesis:
            synthesis = "[Synthèse non disponible — timeout]"

        # 11. Écriture Obsidian
        project_path = self.write_project_to_obsidian(metadata, synthesis, idea_path)
        logger.info(f"📝 Fiche projet écrite : {project_path}")
        self.admin_client.create_post(
            self.channel_id,
            f"✅ **Fiche projet écrite dans Obsidian**\n`{os.path.basename(project_path)}`"
        )

        # 12. Log
        log_channel = self.admin_client.get_channel_by_name(config.TEAM_ID, "orchestrator-log")
        if log_channel:
            self.admin_client.create_post(
                log_channel['id'],
                f"🧪 Incubation terminée : **{titre}**\n"
                f"Messages : {self.global_message_count}/{HARD_LIMIT}\n"
                f"Projet : `{os.path.basename(project_path)}`"
            )

        # 13. Cleanup
        logger.info("🧹 Retrait des agents du channel...")
        for agent in all_mm_agents:
            self.admin_client._request(
                "DELETE",
                f"/channels/{self.channel_id}/members/{agent.mattermost_user_id}"
            )

        logger.info(f"✅ Incubation terminée ({self.global_message_count}/{HARD_LIMIT} messages)")
        return 0

    # === Helpers ===

    @staticmethod
    def _load_project_template_frontmatter() -> Dict:
        """Return default frontmatter values for a project file.

        Uses hardcoded defaults matching _template-projet.md structure.
        No PyYAML dependency — the template structure is stable and known.
        """
        return {
            'type': 'code', 'statut': 'cadrage', 'progression': 0,
            'phase_courante': 'cadrage', 'lead': '', 'equipe': [],
            'github': {'repo': '', 'url': '', 'created': False},
            'workspace': '', 'channel': '', 'idee_source': '',
            'tags': [], 'stack': [], 'skills': [], 'mcps': [],
        }

    @staticmethod
    def _serialize_frontmatter(data: Dict) -> str:
        """Serialize a dict to YAML-like frontmatter without PyYAML dependency.

        Handles: str, int, float, bool, list of str, nested dict (1 level).
        """
        lines = []
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{key}:")
                for k, v in value.items():
                    if isinstance(v, bool):
                        lines.append(f"  {k}: {'true' if v else 'false'}")
                    elif v == '' or v is None:
                        lines.append(f'  {k}: ""')
                    else:
                        lines.append(f"  {k}: {v}")
            elif isinstance(value, list):
                lines.append(f"{key}:")
                if not value:
                    lines.append(f"  []")
                else:
                    for item in value:
                        lines.append(f"  - {item}")
            elif isinstance(value, bool):
                lines.append(f"{key}: {'true' if value else 'false'}")
            elif isinstance(value, (int, float)):
                lines.append(f"{key}: {value}")
            elif value == '' or value is None:
                lines.append(f'{key}: ""')
            else:
                # Quote strings that contain special YAML chars
                sv = str(value)
                if any(c in sv for c in ':#[]{}'):
                    lines.append(f'{key}: "{sv}"')
                else:
                    lines.append(f"{key}: {sv}")
        return '\n'.join(lines)

    @staticmethod
    def _parse_metadata(content: str) -> Dict:
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

    @staticmethod
    def _slugify(text: str) -> str:
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
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Incubation Pipeline — idée → fiche projet via team incubation"
    )
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("idea_path", nargs="?", help="Chemin vers le fichier idée (.md)")
    input_group.add_argument("--idea", "-i", help="Recherche par nom")

    parser.add_argument("--dry-run", action="store_true", help="Affiche le plan sans exécuter")

    args = parser.parse_args()
    pipeline = IncubationPipeline()

    if args.idea:
        from pipeline import PipelineRunner
        idea_path = PipelineRunner(agent_ids=[]).find_idea(args.idea)
    else:
        idea_path = args.idea_path

    if args.dry_run:
        if not os.path.isabs(idea_path):
            idea_path = os.path.join(config.OBSIDIAN_VAULT_PATH, "Idées", idea_path)
        with open(idea_path, 'r', encoding='utf-8') as f:
            content = f.read()
        metadata = pipeline._parse_metadata(content)
        pipeline.setup_agents()

        print(f"\n{'='*60}")
        print(f"🧪 INCUBATION DRY RUN")
        print(f"{'='*60}")
        print(f"📝 Idée     : {metadata.get('titre', 'Sans titre')}")
        print(f"📄 Fichier  : {idea_path}")
        print(f"💬 Budget   : {HARD_LIMIT} messages max")
        print()
        msg_count = 0
        for phase in INCUBATION_PHASES:
            agents_str = ', '.join(f'{pipeline.all_agents[a].emoji} {pipeline.all_agents[a].name}' for a in phase.agent_ids)
            msg_count += phase.total_messages
            print(f"  Phase {phase.name:15} : {agents_str:40} → {phase.total_messages} msg (cumul: {msg_count})")
        print(f"  {'Feedback':20} : {'Gaelle → Stella/Iris':40} → 4 msg max (optionnel)")
        print(f"  {'Synthèse':20} : {'Cloclo':40} → 1 msg")
        print(f"  {'Validation':20} : {'Gaelle':40} → 1 msg")
        print(f"{'='*60}\n")
        return 0

    sys.exit(pipeline.run(idea_path))


if __name__ == "__main__":
    main()
