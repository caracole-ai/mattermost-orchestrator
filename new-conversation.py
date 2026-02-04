#!/usr/bin/env python3
"""Lance une nouvelle conversation entre les agents."""
from config import MATTERMOST_URL, ADMIN_TOKEN
from mattermost_client import MattermostClient
import time

client = MattermostClient(MATTERMOST_URL, ADMIN_TOKEN)

# IDs
TEAM_ID = 'r4mh4iks3bntdxfg7xge4tm73a'
WINSTON_ID = 'nr9m43m13igz7mdcr6fte39jnr'
AMELIA_ID = '6oowpgnaytyxzxucc1pgrzpdkr'
JOHN_ID = 'pswgw1zzajgm3fpcps1bi3jize'

# Récupérer le channel Party Mode
party_channel = client.get_channel_by_name(TEAM_ID, 'party-mode')

if not party_channel:
    print('❌ Channel party-mode introuvable')
    exit(1)

channel_id = party_channel['id']

# Nouveau sujet
print('🚀 Lancement nouvelle conversation...')
client.create_post(channel_id, '''🔥 **Nouveau challenge : Dashboard Monitoring**

Lio demande un système de monitoring temps réel pour tracker :
- Performance API (latence, throughput)
- Santé serveurs (CPU, RAM, disk)
- Alertes automatiques

À vous de jouer !''')
time.sleep(1.5)

# Winston (architecte)
print('  🏗️ Winston répond...')
# Temporairement se connecter en tant que Winston
winston_client = MattermostClient(MATTERMOST_URL, 'p1zhfs71mjdhpygcxax68gihew')
winston_client.create_post(channel_id, 
    '''🏗️ **Winston** (Architecte):

Stack proposée :
- **Prometheus** pour collecter les métriques
- **Grafana** pour les dashboards
- **AlertManager** pour les alertes
- Architecture scalable et battle-tested

On peut démarrer avec un POC minimaliste ?''')
time.sleep(2)

# Amelia (dev)
print('  💻 Amelia répond...')
amelia_client = MattermostClient(MATTERMOST_URL, 'n6ws69ty6bd1zmfjjwdqthr8go')
amelia_client.create_post(channel_id,
    '''💻 **Amelia** (Dev):

+1 pour Prometheus/Grafana. J'ai déjà travaillé avec.

Mon plan technique :
1. Instrumenter l'API avec le client Prometheus
2. Exposer /metrics endpoint
3. Setup Grafana avec quelques dashboards de base
4. WebSocket pour le refresh temps réel côté frontend ?

Je peux livrer ça en 2 jours.''')
time.sleep(1.5)

# John (PM)
print('  📋 John répond...')
john_client = MattermostClient(MATTERMOST_URL, 'x9943j4wyf8ntc7e3u66jhrr4w')
john_client.create_post(channel_id,
    '''📋 **John** (PM):

Questions business :
- Quels KPIs sont **critiques** vs nice-to-have ?
- Qui consulte ce dashboard ? Dev ? Ops ? Management ?
- Besoin d'alertes Slack/email ou juste le dashboard suffit ?
- Budget infra pour héberger Prometheus/Grafana ?

On clarifie avant de coder.''')
time.sleep(1.5)

# Winston rebondit
print('  🏗️ Winston rebondit...')
winston_client.create_post(channel_id,
    '''🏗️ **Winston** (Architecte):

KPIs prioritaires selon moi :
1. **Latence API** (p50, p95, p99) → impact UX direct
2. **Taux d'erreur 5xx** → détecte les crashs
3. **Throughput** (req/sec) → capacité
4. **Health checks** → alerte précoce

Pour l'hébergement : on peut dockeriser le tout et déployer sur un VPS low-cost. Budget <50€/mois.

@Amelia tu confirmes la faisabilité en 2j ?''')

print('✅ Conversation lancée dans Party Mode !')
print('👉 Ouvre Mattermost pour voir la discussion')
