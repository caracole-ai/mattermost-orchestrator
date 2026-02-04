#!/bin/bash
# Usage: ./send-message.sh "ton message"

if [ -z "$1" ]; then
    echo "Usage: $0 \"votre message\""
    exit 1
fi

cd "$(dirname "$0")"
source venv/bin/activate

python3 -c "
from config import MATTERMOST_URL, ADMIN_TOKEN
from mattermost_client import MattermostClient
import requests

# Get party-mode channel
team_id = 'i5a897fmgj8ntqkkt5iy9q8hfr'
channels = requests.get(
    f'{MATTERMOST_URL}/api/v4/teams/{team_id}/channels',
    headers={'Authorization': f'Bearer {ADMIN_TOKEN}'}
).json()
party = next((c for c in channels if c['name'] == 'party-mode'), None)

if party:
    client = MattermostClient(f'{MATTERMOST_URL}/api/v4', ADMIN_TOKEN)
    client.create_post(party['id'], '''$1''')
    print('✅ Message posté dans Party Mode')
else:
    print('❌ Channel introuvable')
"
