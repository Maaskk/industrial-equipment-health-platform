# Validation finale de production

Responsable : Aya Moujoud  
Compte GitHub : `ayamoujoud`

Suivi : [issue GitHub 13](https://github.com/Maaskk/industrial-equipment-health-platform/issues/13)

Cette fiche donne à Aya un travail de validation réel et vérifiable. Elle doit
être exécutée le jour de la répétition finale, puis mise à jour avec la date,
le commit et les résultats observés.

## Informations de version

| Contrôle | Valeur à relever |
|---|---|
| Date et heure | À compléter |
| Commit déployé | À compléter |
| Version du champion MLflow | À compléter |
| Stack Komodo | `industrial-equipment-health-platform` |
| Configuration de production | `TRAIN_SUBSETS=FD001` |

## API

| Requête | Résultat attendu | Résultat observé |
|---|---|---|
| `GET /health` | HTTP 200, modèle chargé | À compléter |
| `GET /demo-payload` | HTTP 200, 88 variables de requête | À compléter |
| `POST /predict` | HTTP 200, RUL, risque, version | À compléter |
| `GET /api/model/info` | champion et métriques visibles | À compléter |
| `GET /api/fleet/summary` | résumé des moteurs disponible | À compléter |
| `GET /api/monitoring/summary` | volume et latence disponibles | À compléter |
| `GET /api/drift/latest` | résultat et source identifiables | À compléter |

## Komodo et conteneurs

| Contrôle | Résultat attendu | Résultat observé |
|---|---|---|
| Stack | état `running` | À compléter |
| API | conteneur sain | À compléter |
| MLflow | conteneur sain | À compléter |
| Dagster webserver | conteneur sain | À compléter |
| Dagster daemon | conteneur actif | À compléter |
| Initialisation | tâche terminée avec code 0 | À compléter |

## Preuves à conserver

1. Capture de la Stack Komodo et de ses services.
2. Capture du champion dans MLflow.
3. Capture du planning Dagster à 06:00.
4. Réponse JSON de santé et une prédiction.
5. Résumé de monitoring avec la source du drift.

## Validation

Je confirme avoir exécuté les contrôles ci-dessus et relu les limites présentées
pendant la soutenance.

Nom : Aya Moujoud  
Date : 15/09/2026  
Commit de validation : 15/09/2026  
