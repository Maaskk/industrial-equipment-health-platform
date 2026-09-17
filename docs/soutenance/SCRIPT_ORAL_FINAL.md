# Script oral final

Durée cible : 28 minutes de présentation, puis 5 minutes de démonstration.  
Chaque membre reste sous 5 minutes.

## Ilyass, diapositives 1 à 3, environ 4 minutes

### Introduction

« Notre projet aide à anticiper la dégradation d'un moteur. Nous estimons sa
durée de vie restante afin de classer les équipements par niveau de risque. »

### Données

« J'ai travaillé sur l'analyse du jeu NASA C MAPSS. Les données suivent les
cycles de 709 moteurs d'entraînement et 707 moteurs de test. Chaque cycle contient
trois réglages et 21 mesures de capteurs. J'ai conservé l'ordre temporel pour
éviter d'utiliser des informations futures. »

### Transition

« Cette analyse définit les données utiles. Mohamed montre maintenant comment
nous les chargeons et les transformons. »

## Mohamed, diapositives 4 et 5, environ 4 minutes

« J'ai construit la partie DataOps. dlt charge les fichiers NASA, DuckDB stocke
les tables, puis dbt prépare les données de travail. Dagster impose l'ordre des
étapes et permet de relancer le pipeline. J'ai choisi DuckDB car il est simple à
reproduire dans Docker et suffisant pour ce volume. »

« Une sortie dbt devient l'entrée de la modélisation. Avant cela, Hamza vérifie
que les contrats et les tests sont respectés. »

## Hamza, diapositives 6 et 7, environ 4 minutes

« Ma partie porte sur la qualité. Les contrats décrivent les colonnes, les types
et les limites attendues. Les tests dbt vérifient les données avant
l'entraînement. La CI reprend ces contrôles dans GitHub Actions. Une erreur de
qualité arrête le pipeline avant l'enregistrement d'un modèle. »

« Une fois les données validées, Mouhcine peut comparer les modèles sur une base
reproductible. »

## Mouhcine, diapositives 8 et 9, environ 4 minutes

« J'ai travaillé sur les variables et la comparaison des modèles. Le modèle
final utilise 89 variables, notamment des moyennes, écarts types et pentes sur
une fenêtre de cinq cycles. Nous comparons plusieurs références. Le gradient
boosting obtient une MAE de 12,56 cycles et une RMSE de 16,93 cycles sur le
dernier cycle des 707 moteurs de test. »

« Le modèle retenu devient ensuite un candidat dans MLflow. Ossama explique la
gestion de cette version. »

## Ossama, diapositives 10 à 12, environ 4 minutes

« Ma partie relie l'entraînement au déploiement. MLflow enregistre les paramètres,
les métriques et le modèle. Chaque entraînement crée un candidat. Le code compare
sa MAE et sa RMSE avec le champion. L'alias change seulement si les deux mesures
ne se dégradent pas. »

« Dagster lance le pipeline chaque jour à 06:00, heure de Casablanca. Le drift ne
déclenche pas l'entraînement. Docker exécute l'API, MLflow et Dagster. Komodo gère
la Stack sur le serveur partagé. La production de démonstration utilise FD001,
alors que l'évaluation hors ligne utilise les quatre sous ensembles. »

« Hajar présente maintenant le contrat utilisé par l'application. »

## Hajar, diapositives 13 et 14, environ 4 minutes

« J'ai préparé le contrat FastAPI et le parcours de démonstration. La route de
santé confirme que le modèle est chargé. La prédiction reçoit un identifiant de
moteur, le cycle et 88 valeurs. L'API ajoute le cycle comme variable interne, ce
qui donne 89 variables pour le modèle. La réponse contient la RUL, le risque et
la version. »

« Le tableau de bord utilise les mêmes routes pour afficher la flotte, suivre un
moteur et lancer une prédiction. Aya vérifie ensuite que tout est prêt en
production. »

## Aya Moujoud, diapositives 15 à 17, environ 4 minutes

« J'ai rejoint la phase finale pour prendre en charge la validation. Je vérifie
les conteneurs, les codes HTTP, la version du champion, la latence et la source
du rapport de drift. Je contrôle aussi la Stack Komodo et je conserve des
captures pour le plan de secours. »

« Le monitoring de dérive compare la moyenne des RUL prédites. Il reste simple et
ne remplace pas une surveillance industrielle complète. C MAPSS contient des
données simulées et les seuils de risque viennent de règles sur la RUL. Ces
limites sont importantes pour interpréter le résultat. »

## Démonstration et questions, diapositive 18, environ 5 minutes

Suivre l'ordre de `DEMO_CHECKLIST_FINAL.md`. Une seule personne pilote l'écran.
Chaque membre commente uniquement sa partie.
