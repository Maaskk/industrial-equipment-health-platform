# Checklist finale de démonstration

Responsable de la validation : Aya Moujoud  
Durée cible de la démonstration : 5 minutes

## Avant la soutenance

```bash
git status --short
git rev-parse HEAD
docker compose -f deploy/compose.production.yml config --quiet
docker compose -f deploy/compose.production.yml ps
```

Résultats attendus : dépôt propre, commit identifié, configuration Compose
valide, API, MLflow et Dagster actifs. `training-init` doit avoir terminé avec le
code 0.

## Contrôles de l'API

```bash
curl -f http://127.0.0.1:8001/health
curl -f http://127.0.0.1:8001/demo-payload -o /tmp/demo-payload.json
curl -f -H 'Content-Type: application/json' \
  --data @/tmp/demo-payload.json http://127.0.0.1:8001/predict
curl -f http://127.0.0.1:8001/api/model/info
curl -f http://127.0.0.1:8001/api/fleet/summary
curl -f http://127.0.0.1:8001/api/monitoring/summary
curl -f http://127.0.0.1:8001/api/drift/latest
```

Résultats attendus : HTTP 200, modèle chargé depuis MLflow, réponse de prédiction
avec RUL et risque, puis informations du modèle, de la flotte et du monitoring.

## Outils de la plateforme

1. MLflow : ouvrir l'expérience et le modèle `industrial-equipment-health-model`.
2. Vérifier l'alias `champion` et la décision de promotion.
3. Dagster : ouvrir les assets et le planning quotidien à 06:00.
4. Komodo : vérifier la Stack, le serveur, les conteneurs et le commit déployé.
5. GitHub Actions : ouvrir la dernière exécution de `CI` et vérifier le job `quality`.

## Ordre de démonstration

1. Vue de la flotte.
2. Historique d'un moteur.
3. Prédiction en direct.
4. Documentation FastAPI.
5. Champion MLflow.
6. Planning Dagster.
7. Stack Komodo.
8. Monitoring et source du drift.

## Contrôle de production observé le 17 septembre 2026

Le contrôle direct sur le serveur a trouvé l'API, MLflow et Dagster actifs depuis
cinq semaines. `/health` et `/predict` répondaient correctement avec le champion
MLflow version 2. Le serveur exécutait encore le commit `a9c7db4` avec
`TRAIN_SUBSETS=FD001`. Les routes enrichies
`/api/model/info`, `/api/fleet/summary`, `/api/monitoring/summary` et
`/api/drift/latest` renvoyaient 404 sur cette ancienne image. Il faut donc
redéployer le commit final validé avant la soutenance, puis refaire cette fiche.

## Plan de secours

Conserver hors ligne :

1. capture de la Stack Komodo et des conteneurs ;
2. capture de MLflow avec le champion ;
3. capture de Dagster avec le planning ;
4. réponses JSON de santé, prédiction, modèle, flotte et monitoring ;
5. `reports/model_metrics/final_evaluation.json` ;
6. `reports/model_metrics/promotion_decision.json` ;
7. `reports/monitoring/drift_report.json` avec sa source ;
8. `docs/screenshots/engine-observatory.png`.

Si le réseau tombe, présenter ces preuves dans le même ordre que la démonstration.
