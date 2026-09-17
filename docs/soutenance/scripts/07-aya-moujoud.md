# Aya Moujoud

Diapositives 15 à 17. Durée cible : 4 minutes 30.

## Texte à présenter

« J'ai rejoint la phase finale avec une responsabilité précise : la validation
QA, le monitoring, le contrôle Komodo et la préparation des limites. Mon rôle est
de vérifier que les éléments présentés correspondent à des preuves observables,
et pas seulement à une configuration écrite dans le dépôt. »

« Pour la validation de production, je contrôle d'abord les services FastAPI,
MLflow et Dagster. Je vérifie ensuite les codes HTTP de santé et de prédiction,
la version du champion et la latence. Le contrôle daté du 17 septembre renvoie
HTTP 200 pour la santé et la prédiction. Le champion chargé est la version 2.
La requête FD004_204 renvoie 101,87 cycles, un risque faible et une latence de
224 millisecondes. »

« Dans Komodo, je vérifie la Stack
`industrial_equipment_health_platform`, les conteneurs, les logs et l'état des
services. La révision de référence du dépôt est 3ef8c10. Juste avant la démo,
la checklist impose de confirmer que l'image active correspond à cette révision
et de refaire les captures. Nous ne créons pas de ressources artificielles pour
remplir les pages Komodo. Nous montrons uniquement les ressources réellement
utilisées par la Stack. »

« Le monitoring actuel suit la santé du service, la latence, les journaux de
prédiction et un indicateur de drift basé sur les RUL. Ce signal reste limité :
il ne couvre pas tout le drift des variables ni le concept drift. Il ne déclenche
pas le réentraînement. Dagster réentraîne selon le planning quotidien. »

« Les autres limites sont importantes. C-MAPSS contient des données simulées.
Les niveaux de risque proviennent de seuils sur la RUL et non d'un classifieur
calibré avec des coûts industriels. FD001 est utilisé pour alléger la production
de démonstration, alors que l'évaluation complète couvre les quatre
sous-ensembles. Les améliorations prioritaires sont des données réelles, un
monitoring par variable et une validation métier des alertes. »

« Nous passons maintenant à la démonstration. »

## Décision technique à défendre

Une mesure n'est annoncée comme preuve de production que si elle est datée,
traçable et reproductible. Les limites sont présentées avec le résultat pour
éviter de transformer un indicateur académique en promesse industrielle.

## Questions probables

1. Aya a-t-elle une contribution dans le dépôt ? Oui. Son périmètre est documenté
   dans `team/08-aya-moujoud-qa-monitoring.md`, la fiche de validation, la
   checklist de démonstration et les scripts de soutenance.
2. Le drift déclenche-t-il le modèle ? Non. Il informe le monitoring. Le job
   quotidien Dagster exécute le réentraînement.
3. Pourquoi ne pas remplir toutes les pages Komodo ? Une ressource n'est créée
   que si elle correspond à l'architecture réelle. La Stack et ses services sont
   les preuves pertinentes.
4. Quelle preuve montrer en premier ? La Stack et les conteneurs sains, puis
   `/health`, la prédiction, le champion MLflow et le planning Dagster.
