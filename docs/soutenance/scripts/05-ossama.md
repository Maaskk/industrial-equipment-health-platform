# Ossama

Diapositives 10 à 12. Durée cible : 4 minutes 30.

## Texte à présenter

« Ma contribution relie l'entraînement au déploiement. J'ai pris en charge
l'intégration MLOps, MLflow, la règle de promotion, Docker et la configuration
Komodo. Chaque entraînement crée un run MLflow avec les paramètres, les
métriques et les artefacts. Le modèle est ensuite enregistré comme candidat
dans le registre. L'API charge l'alias champion, pas un numéro codé en dur. Le
champion observé en production est actuellement la version 2. »

« La promotion est contrôlée. Le premier candidat devient champion lorsqu'aucun
alias n'existe. Pour les candidats suivants, le code compare la MAE et la RMSE
avec le champion. Le nouvel alias n'est appliqué que si les deux métriques ne se
dégradent pas. Si les métriques du champion manquent, la promotion est bloquée.
La décision est conservée dans MLflow et dans un rapport JSON. »

« Le réentraînement automatique existe. Dagster lance le job complet tous les
jours à 06:00, heure de Casablanca. Le drift ne déclenche pas ce job. Il est
calculé après l'entraînement et sert au monitoring. Nous avons donc une
automatisation planifiée et une promotion conditionnelle, mais pas une boucle de
réentraînement déclenchée par la dérive. »

« Pour l'industrialisation, GitHub Actions valide le commit, construit l'image
et réalise le smoke test. Juste avant la soutenance, nous vérifions la révision
déployée et le dernier run vert au lieu de réciter une ancienne valeur. Docker
Compose décrit FastAPI, MLflow et Dagster. Komodo gère cette Stack sur le serveur
partagé. La production de démonstration utilise FD001 pour rester légère, alors
que l'évaluation scientifique couvre FD001 à FD004 et 707 moteurs. »

« Hajar va maintenant présenter le contrat FastAPI utilisé par l'application et
le parcours de démonstration. »

## Décision technique à défendre

FastAPI charge `models:/industrial-equipment-health-model@champion`. Cette URI
découple le service d'un numéro de version. La règle de promotion évite qu'un
simple entraînement planifié remplace automatiquement un meilleur modèle.

## Questions probables

1. Pourquoi comparer MAE et RMSE ? La MAE mesure l'erreur typique et la RMSE
   protège contre l'augmentation des grandes erreurs.
2. Que se passe-t-il si MLflow est indisponible ? Le service de production doit
   échouer clairement ; le repli local est réservé aux tests explicites.
3. Pourquoi FD001 en production ? Pour limiter les ressources de la démo. Le
   modèle final reste évalué sur les quatre sous-ensembles.
