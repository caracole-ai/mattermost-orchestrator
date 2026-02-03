#!/usr/bin/env python3
"""
Fait réagir les agents à un message de Lio dans un channel.
Usage: python3 agent-react.py "channel_key" "message de Lio"
"""
import sys
import time
from orchestrator import MattermostOrchestrator
from agents import WINSTON, AMELIA, JOHN

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 agent-react.py <channel_key> <message>")
        print("Channels disponibles: orchestrator_log, agent_reflexions, party_mode")
        sys.exit(1)
    
    channel_key = sys.argv[1]
    user_message = sys.argv[2]
    
    print(f"\n💬 Message reçu : '{user_message}'")
    print(f"📍 Channel : {channel_key}\n")
    
    # Setup orchestrateur
    orch = MattermostOrchestrator()
    orch.setup_admin()
    orch.setup_team()
    orch.setup_channels()
    orch.setup_bots()
    
    # Les agents réagissent dans l'ordre
    agents = [
        ("winston", WINSTON, "winston analyse la demande..."),
        ("amelia", AMELIA, "amelia donne son avis technique..."),
        ("john", JOHN, "john évalue la faisabilité...")
    ]
    
    for agent_name, agent_obj, status in agents:
        print(f"🤔 {status}")
        reaction = agent_obj.format_message(
            f"Suite au message de Lio : {agent_obj.think(user_message)}"
        )
        orch.post_as_agent(agent_name, channel_key, reaction)
        time.sleep(2)
    
    print("\n✅ Les 3 agents ont répondu !\n")

if __name__ == "__main__":
    main()
