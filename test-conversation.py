#!/usr/bin/env python3
"""Test : nouvelle conversation complète."""
from config import MATTERMOST_URL, ADMIN_TOKEN, AGENTS
from mattermost_client import MattermostClient
import requests
import time

# Get channel ID
TEAM_ID = 'i5a897fmgj8ntqkkt5iy9q8hfr'
channels = requests.get(
    f'{MATTERMOST_URL}/api/v4/teams/{TEAM_ID}/channels',
    headers={'Authorization': f'Bearer {ADMIN_TOKEN}'}
).json()
party = next((c for c in channels if c['name'] == 'party-mode'), None)
if not party:
    print('❌ Channel party-mode introuvable')
    exit(1)
channel_id = party['id']

admin_client = MattermostClient(f'{MATTERMOST_URL}/api/v4', ADMIN_TOKEN)

print('🎬 Lancement test conversation...\n')

# Lio lance le sujet
print('📝 Lio pose une question...')
admin_client.create_post(channel_id, '''**Question urgente !**

Les gars, on a un client qui veut migrer son infra vers Kubernetes. Il a actuellement 20 services Docker sur 3 serveurs.

Quelle stratégie vous proposez ?''')
time.sleep(2)

# Winston (architecte) répond
print('🏗️ Winston analyse...')
winston = MattermostClient(f'{MATTERMOST_URL}/api/v4', AGENTS['winston']['token'])
winston.create_post(channel_id, '''🏗️ **Winston** (Architecte):

Migration K8s pour 20 services, OK. Stratégie :

**Phase 1** - Audit (1 semaine)
- Cartographie des dépendances
- Identifier les services stateful vs stateless
- Analyser les configs réseau actuelles

**Phase 2** - POC (2 semaines)
- Setup cluster K8s (3 nodes minimum)
- Migrer 2-3 services non-critiques
- Tests charge + résilience

**Phase 3** - Migration progressive
- 5 services/semaine
- Monitoring intensif
- Rollback plan pour chaque batch

Budget estimé : 15-20 jours dev + 5k€ infra. Faisable ?''')
time.sleep(2)

# Amelia (dev) rebondit
print('💻 Amelia donne son avis technique...')
amelia = MattermostClient(f'{MATTERMOST_URL}/api/v4', AGENTS['amelia']['token'])
amelia.create_post(channel_id, '''💻 **Amelia** (Dev):

+1 sur l'approche de Winston.

Points techniques à anticiper :
- **Secrets management** : passer de .env à K8s Secrets
- **Volumes** : les services stateful vont être chiants (PostgreSQL, Redis...)
- **CI/CD** : refonte complète du pipeline Docker → K8s
- **Logging** : centraliser avec Loki ou ELK

Je propose qu'on dockerise TOUT d'abord (certains services ne le sont peut-être pas à 100%), puis on attaque K8s.

Délai réaliste : 6 semaines total.''')
time.sleep(2)

# John (PM) pose des questions business
print('📋 John pose les vraies questions...')
john = MattermostClient(f'{MATTERMOST_URL}/api/v4', AGENTS['john']['token'])
john.create_post(channel_id, '''📋 **John** (PM):

Questions business critiques :

1. **Budget client** : il a combien ? 5k€ infra c'est juste le cluster ou avec la migration ?
2. **Deadline** : il veut ça pour quand ? 6 semaines c'est serré.
3. **Downtime** : tolérance zéro ou on peut faire des maintenances ?
4. **Équipe** : on est combien sur le projet ? 2 devs suffisent pas.
5. **Support post-go-live** : qui maintient le cluster après ?

Sans ces réponses, on peut pas chiffrer correctement. @Winston tu proposes quoi comme team size ?''')
time.sleep(2)

# Winston répond à John
print('🏗️ Winston répond aux questions...')
winston.create_post(channel_id, '''🏗️ **Winston** (Architecte):

@John bonnes questions.

**Team recommandée** :
- 1 archi/DevOps (moi) - setup cluster + monitoring
- 2 devs backend (dont Amelia) - migration services
- 1 QA - tests non-régression
= 4 personnes pendant 6 semaines

**Budget détaillé** :
- Infra K8s : 5k€ (3 nodes + load balancer + storage)
- Consulting/dev : 40 jours × 4 personnes × 600€ = 96k€
- **Total : ~100k€**

Si le client a pas ce budget, on fait un "lift & shift" basique sans refonte. Mais ça sera fragile.

On attend la réponse client avant de démarrer quoi que ce soit.''')

print('\n✅ Conversation terminée !')
print('👉 Vérifie Party Mode dans Mattermost pour voir les 5 nouveaux messages')
