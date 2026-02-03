#!/bin/bash
# Lance une conversation entre les agents sur un sujet donné

cd "$(dirname "$0")"
source venv/bin/activate

TOPIC="${1:-un nouveau projet}"

python3 << EOF
from orchestrator import MattermostOrchestrator
from agents import get_party_conversation
import time

print("\n🎭 Lancement d'une conversation sur : $TOPIC\n")

orch = MattermostOrchestrator()
orch.setup_admin()
orch.setup_team()
orch.setup_channels()
orch.setup_bots()

conversation = get_party_conversation("$TOPIC")

for agent_name, message in conversation:
    orch.post_as_agent(agent_name, 'party_mode', message)
    print(f'✅ {agent_name} a parlé')
    time.sleep(2)

print('\n✅ Conversation terminée ! Consultez #party-mode dans Mattermost\n')
EOF
