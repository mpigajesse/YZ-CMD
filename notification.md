## Objectif

Définir des stratégies pour externaliser la gestion des notifications (temps réel, Web Push, e‑mail, SMS/WhatsApp) afin de réduire le code applicatif, fiabiliser la diffusion et améliorer l’observabilité, tout en conservant la persistance côté Django (historique, filtres « lues/non lues »).

## Contexte et enjeux

- Besoin d’un centre de notifications in‑app fluide (sans erreurs MIME/SSE).
- Besoin d’alertes hors application (e‑mail/SMS) pour certains événements critiques.
- Volonté de minimiser le code custom et les effets de bord (CSRF, SSE, polling, etc.).
- Traçabilité et logs robustes demandés (audit, debug, métriques, SLA).

## Exigences clés

- In‑app temps réel fiable (reconnexion, latence faible, backoff).
- Web Push navigateur (optionnel) avec consentement utilisateur.
- Multi‑canaux (e‑mail/SMS/WhatsApp) pour messages importants.
- Persistance dans la base Django pour l’historique et les filtres.
- Observabilité: logs structurés, tableaux de bord, alerting.
- Sécurité et conformité (GDPR, minimisation PII, consentements).

## Options d’externalisation

### Option 1 — Plateforme Web Push/Push gérée (OneSignal ou FCM Web Push)

- Cas d’usage: notifications navigateur (même hors de l’appli), campagnes ciblées, segmentation.
- Avantages: gestion des permissions, segmentation, analytics, A/B tests, faible code client.
- Limites: nécessite un Service Worker, consentement explicite, pas d’updates DOM in‑app par défaut.
- Effort d’intégration Django: faible (SDK JS + endpoints de collecte tokens + webhooks d’accusé de réception si besoin).

### Option 2 — Diffusion temps réel in‑app (Pusher, Ably, PubNub)

- Cas d’usage: mises à jour instantanées du centre de notifications, badges, toasts.
- Avantages: canaux pub/sub managés, présence, authentification via webhook, SDK simples, faible latence, reconnection gérée.
- Limites: coût selon volume connexions/messages, vendor lock‑in léger.
- Effort Django: moyen-faible (endpoint d’auth pour canaux privés, émission d’événements via SDK Python, conservation DB des notifications).

### Option 3 — Orchestrateur multi‑canaux cloud (AWS SNS/Pinpoint, GCP Pub/Sub + providers)

- Cas d’usage: gros volume, règles d’envoi par canal, analytics avancés, scénarios marketing.
- Avantages: scalabilité, routage multi‑canaux, KPIs.
- Limites: mise en place plus lourde, coût/complexité cloud.
- Effort Django: moyen/élevé (intégration SDK + IAM + webhooks).

### Option 4 — E‑mail/SMS uniquement (Brevo/Sendinblue, Twilio, Mailgun, SendGrid)

- Cas d’usage: alertes critiques, récap quotidiens/hebdomadaires.
- Avantages: intégration simple, fiabilité délivrabilité, analytics.
- Limites: pas de temps réel in‑app, moins d’UX.
- Effort Django: faible (SDK/API + webhooks de statut).

### Option 5 — Bus d’événements + workers (Kafka, RabbitMQ, Redis Streams) avec « Notification Service »

- Cas d’usage: architecture événementielle, découplage fort, haute volumétrie.
- Avantages: résilience, extensibilité, back‑pressure, replays.
- Limites: opérer l’infra, compétence DevOps requise, time‑to‑market plus long.
- Effort Django: élevé (produc/consum, schéma événements, observabilité).

## Recommandation MVP (pragmatique)

- In‑app temps réel: Pusher (ou Ably) pour remplacer SSE. Utiliser canaux privés par utilisateur, auth via Django. Émettre un événement « notification_created » à chaque création en base; le client met à jour la liste et les compteurs.
- Hors app: Brevo (e‑mail) et Twilio (SMS/WhatsApp) en opt‑in pour événements critiques.
- Web Push (optionnel): OneSignal si besoin d’alerter hors onglet et faire des campagnes.
- Persistance: on conserve les modèles Django (`NotificationOperateur`) pour l’historique, filtres et « marquer comme lu ».

Pourquoi: time‑to‑market court, peu de code, UX temps réel robuste, possibilité d’étendre ensuite.

## Architecture cible (vue d’ensemble)

1. Django enregistre la notification en DB et publie un événement via SDK (Pusher/Ably) sur un canal utilisateur.
2. Le client écoute ce canal et met à jour la vue (badge, liste, statut).
3. Pour messages critiques, Django déclenche en parallèle un envoi Brevo/Twilio (feature flaggable).
4. Logs: chaque émission est tracée (INFO/ERROR) avec corrélation ID; métriques exposées (compte/minute, taux d’échec).

## Plan de migration

1) Audit & feature flags
- Cartographier les points d’émission actuels (création session, commandes, alertes).
- Introduire un `NOTIFICATIONS_PROVIDER` (env) et des flags par canal (IN_APP, EMAIL, SMS, WEB_PUSH).

2) Adapter « provider »
- Créer un module `notifications_providers/adapter.py` avec une interface simple: `emit_in_app(user_id, payload)`, `send_email(to, template_id, data)`, `send_sms(to, text)`.
- Implémentation Pusher/Ably (in‑app), Brevo (e‑mail), Twilio (SMS). Choix par settings.

3) Intégration progressive
- Remplacer SSE côté client par l’abonnement SDK JS (Pusher/Ably). Conserver la DB et tout le front (centre de notifications, filtres).
- Laisser le backend émettre les événements en parallèle du flux actuel, puis couper SSE une fois validé.

4) Observabilité
- Ajouter logs structurés (JSON) sur émission/échec, latence, retries.
- Table de « delivery attempts » facultative pour audit fin (horodatage, canal, provider, statut).

5) Rollback
- Conservation du code SSE derrière flag pour retour arrière rapide si besoin pendant la bascule.

## Sécurité & conformité

- Minimiser PII dans les payloads providers; préférer des IDs et récupérer les détails via l’appli.
- Gestion des consentements (Web Push, SMS/WhatsApp) et préférence par canal dans le profil utilisateur.
- Stockage pays/région (hébergement providers), DPA (accords de traitement), chiffrement en transit, TTL raisonnables.

## Coûts (ordre de grandeur, à affiner)

- Pusher/Ably: selon connexions concurrentes et messages/mois (starter souvent suffisant au début).
- OneSignal (Web Push): gratuit/tiers payant selon MAU/segmentations.
- Brevo: e‑mails/mois; Twilio: coût par SMS/WhatsApp.
- Option bus d’événements: coût d’opération (temps équipe + infra).

## Checklist d’implémentation (MVP Pusher/Ably + Brevo)

- [ ] Créer le compte provider (Pusher/Ably) et configurer clés (env).
- [ ] Ajouter endpoint d’auth canaux privés (Django) + middleware permission.
- [ ] Implémenter `emit_in_app(user_id, payload)` et remplacer SSE.
- [ ] Adapter le JS client pour s’abonner et mettre à jour la vue (liste, badges, « lue »).
- [ ] Ajouter métriques et logs (succès/échecs, latence).
- [ ] Activer Brevo pour e‑mails critiques (templates, variables).
- [ ] Tests E2E: latence, déconnexion/reconnexion, marquage « lu », cohérence DB/DOM.

## Risques & atténuations

- Vendor lock‑in: isoler via un adapter, prévoir 2 providers in‑app (flag switch).
- Débit élevé: limiter le volume (batch côté client, agrégation), utiliser digests e‑mail.
- Pannes provider: fallback (file d’attente + retries), bascule vers provider B si SLA critique.

## Roadmap étendue (post‑MVP)

- Préférences utilisateur par canal et par type d’événement.
- Digests quotidiens/hebdo configurables.
- Web Push (OneSignal) si besoin hors appli.
- Tableau de bord d’observabilité (Grafana/Datadog) et alerting Sentry pour erreurs d’émission.

## Annexe — Choix rapide selon besoin

- Besoin « centre de notifications » fluide: Pusher ou Ably.
- Besoin d’alerter en dehors du navigateur: OneSignal (Web Push) ou SMS (Twilio).
- Besoin campagnes/e‑mail transactionnel: Brevo/SendGrid.
- Besoin volumétrie + découplage fort: bus d’événements + service dédié.


