# Mouhcine

Diapositives 8 et 9. Durée cible : 4 minutes 15.

## Texte à présenter

« Ma contribution concerne le feature engineering, la comparaison des modèles
et l'évaluation finale. Les mesures brutes ne décrivent qu'un cycle isolé. Pour
capturer la dégradation récente, nous calculons sur une fenêtre de cinq cycles
la moyenne, l'écart type et la pente de chaque capteur. Avec le cycle, le
sous-ensemble, les réglages opérationnels et les mesures, le modèle utilise 89
variables internes. »

« Nous avons comparé cinq familles dans le même protocole : une baseline moyenne,
un Ridge utilisant surtout le cycle, un Ridge sur les variables brutes, une
forêt aléatoire et un HistGradientBoostingRegressor. La séparation est faite par
moteur afin qu'un moteur de validation ne soit jamais présent dans
l'entraînement. »

« L'évaluation standard utilise le dernier cycle observé des 707 moteurs de
test. La MAE indique l'erreur absolue moyenne en cycles. La RMSE donne plus de
poids aux grandes erreurs. Le score NASA est asymétrique et pénalise davantage
une surestimation de la RUL, car annoncer trop de durée de vie peut retarder une
maintenance nécessaire. »

« Le modèle retenu est le HistGradientBoostingRegressor. Il obtient une MAE de
12,56 cycles, une RMSE de 16,93 cycles et un score NASA de 4 466. La forêt
aléatoire obtient une MAE proche, 12,73 cycles. Le choix ne repose donc pas sur
une différence spectaculaire de MAE. Le gradient boosting offre aussi le
meilleur score NASA et une inférence adaptée au service. »

« Le modèle retenu devient un candidat dans MLflow. Ossama va expliquer comment
nous suivons cette expérience, décidons d'une promotion et déployons le service. »

## Décision technique à défendre

Le protocole final évalue un point par moteur au dernier cycle, ce qui correspond
à la convention C-MAPSS. Les modèles sont comparés avec trois métriques, pas avec
la MAE seule.

## Questions probables

1. Pourquoi une fenêtre de cinq cycles ? Elle capture une tendance récente sans
   trop lisser les changements.
2. Pourquoi le score NASA ? Une surestimation est plus risquée qu'une
   sous-estimation dans un contexte de maintenance.
3. Pourquoi ne pas choisir automatiquement la forêt aléatoire ? Sa MAE est
   proche, mais son score NASA est moins bon et son coût d'inférence est supérieur.
