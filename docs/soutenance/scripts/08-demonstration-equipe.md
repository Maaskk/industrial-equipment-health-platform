# Démonstration de l'équipe

Diapositive 18. Durée maximale : 5 minutes.

Une seule personne pilote l'écran. Les autres prennent la parole uniquement au
moment de leur preuve.

## 0:00 à 0:45, Hajar

Ouvrir l'application. Montrer la flotte et sélectionner un moteur. Dire :

« L'interface interroge la même API que celle testée dans la CI. Nous allons
suivre un moteur, exécuter une prédiction et vérifier les preuves MLOps. »

## 0:45 à 1:30, Hajar

Afficher l'historique, lancer `POST /predict` et montrer la RUL, le risque, la
version et la latence.

## 1:30 à 2:10, Ossama

Ouvrir MLflow. Montrer le modèle enregistré et l'alias champion sur la version
2. Ne pas réciter un ancien run ID. Ouvrir le run visible dans l'interface.

## 2:10 à 2:50, Mohamed

Ouvrir Dagster. Montrer les assets et le planning quotidien à 06:00. Préciser :

« Le drift est produit après le training. Il ne déclenche pas le job. »

## 2:50 à 3:40, Aya

Ouvrir Komodo. Montrer la Stack, les conteneurs et un état de santé ou un log
récent. Confirmer la révision active selon la checklist.

## 3:40 à 4:20, Hamza

Ouvrir GitHub Actions et montrer le run réussi. Relier le contrôle de qualité,
le build Docker et le smoke test.

## 4:20 à 4:45, Mouhcine

Montrer le rapport d'évaluation. Rappeler les valeurs finales : MAE 12,56, RMSE
16,93 et score NASA 4 466 sur 707 moteurs.

## 4:45 à 5:00, Ilyass

Conclure :

« La démonstration relie donc les données, les contrôles, le modèle versionné et
le service réellement déployé. Nous sommes prêts pour vos questions. »

## Plan de secours

Si un service externe ne répond pas, utiliser les captures datées, les réponses
JSON et les rapports conservés dans le dépôt. Ne jamais annoncer une valeur qui
ne peut pas être reliée à une preuve.
