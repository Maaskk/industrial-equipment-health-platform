# Répartition finale des contributions

Ce tableau relie chaque partie de la soutenance à un périmètre technique réel.
Il décrit les responsabilités et les éléments à démontrer sans modifier
l'historique Git.

| Membre | Contribution | Fichiers et composants principaux | Démonstration | Décision technique |
|---|---|---|---|---|
| Ilyass | Problème métier, analyse des données et indicateurs | `mlops_project/notebooks/EDA.ipynb`, `docs/screenshots/engine-observatory.png` | expliquer les trajectoires moteur et les indicateurs utiles | conserver l'ordre temporel des cycles |
| Mohamed | Ingestion et orchestration DataOps | `src/industrial_health/ingestion/`, `dbt_project/`, `orchestration/dagster_assets.py` | suivre dlt, DuckDB, dbt et Dagster | utiliser DuckDB comme stockage analytique reproductible |
| Hamza | Contrats, qualité, traçabilité et CI | `contracts/`, `docs/data-quality.md`, `docs/data-lineage.md`, `.github/workflows/ci.yml` | montrer les tests qui bloquent les données invalides | arrêter le pipeline avant l'entraînement si la qualité échoue |
| Mouhcine | Variables, entraînement et évaluation | `ml-modeling/`, `scripts/train_model.py`, `reports/model_metrics/` | comparer les modèles et expliquer MAE et RMSE | retenir le gradient boosting selon l'évaluation finale par moteur |
| Ossama | MLflow, promotion du champion, Docker et intégration Komodo | `src/industrial_health/mlops/`, `deploy/compose.production.yml`, `komodo/resources.toml` | montrer le registre, le planning quotidien et l'architecture de déploiement | promouvoir un candidat seulement si MAE et RMSE ne se dégradent pas |
| Hajar | Contrat FastAPI et parcours de démonstration | `src/industrial_health/api/`, `demo/predict_sample.json`, `docs/api.md` | exécuter la santé, une prédiction et le parcours du tableau de bord | séparer les 88 variables de requête des 89 variables internes |
| Aya Moujoud | Validation finale, monitoring, Komodo et limites | `docs/validation/aya-final-production-validation.md`, `docs/soutenance/DEMO_CHECKLIST_FINAL.md`, `docs/monitoring.md` | vérifier les services, la latence, la source du drift et les preuves de secours | ne présenter comme mesure de production qu'une valeur datée et traçable |

## Support antérieur

Akram a participé à la phase Jira et Agile. Il ne fait pas partie des sept
présentateurs actifs.
