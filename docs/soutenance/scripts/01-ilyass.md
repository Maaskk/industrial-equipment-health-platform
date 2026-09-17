# Ilyass

Diapositives 1 à 3. Durée cible : 4 minutes 15.

## Texte à présenter

« Bonjour. Nous allons présenter Industrial Equipment Health Platform, notre
plateforme de maintenance prédictive. L'objectif du projet n'est pas seulement
d'entraîner un modèle. Nous avons construit une chaîne complète qui part des
données, contrôle leur qualité, entraîne et versionne le modèle, puis expose la
prédiction dans une application déployée. Chaque membre va expliquer la partie
qu'il a prise en charge. »

« Dans l'industrie, on distingue trois stratégies. La maintenance corrective
intervient après la panne. Elle est simple, mais elle arrive trop tard et peut
provoquer un arrêt coûteux. La maintenance préventive intervient selon un
calendrier. Elle réduit le risque, mais elle peut remplacer un composant encore
utilisable. La maintenance prédictive utilise l'état réel de l'équipement pour
choisir le bon moment. Notre question est donc : combien de cycles reste-t-il
avant la défaillance ? Cette estimation est la RUL, la Remaining Useful Life. »

« Ma contribution porte sur l'analyse des données, l'EDA et les indicateurs
métier. Nous utilisons NASA C-MAPSS, un jeu qui simule la dégradation de moteurs
de turboréacteurs. Les quatre sous-ensembles FD001 à FD004 contiennent 160 359
lignes d'entraînement et 104 897 lignes de test. Nous avons 709 moteurs pour
l'entraînement, 707 pour le test, trois réglages opérationnels et 21 capteurs. »

« L'analyse exploratoire montre que les durées de vie sont dispersées, que
certains capteurs sont presque constants et que d'autres présentent des
tendances utiles. J'ai conservé l'ordre des cycles afin de ne jamais utiliser
une information future. Les indicateurs du produit sont la RUL, le niveau de
risque, la version du modèle et la latence. Les seuils sont simples : risque
élevé sous 30 cycles, moyen entre 30 et 80, faible au-dessus de 80. »

« Ces données constituent l'entrée du pipeline. Mohamed va maintenant expliquer
comment elles sont ingérées, stockées et orchestrées. »

## Décision technique à défendre

La séparation temporelle et la séparation par moteur évitent les fuites de
données. La RUL est plafonnée à 125 cycles afin de limiter l'effet de la longue
phase initiale où la dégradation est peu visible.

## Questions probables

1. Pourquoi C-MAPSS ? Parce qu'il fournit des trajectoires multivariées jusqu'à
   la défaillance avec une vérité terrain RUL adaptée à un projet reproductible.
2. Pourquoi trois niveaux de risque ? Ils transforment une valeur continue en
   priorité opérationnelle compréhensible. Ce ne sont pas des classes apprises.
3. Quelle limite principale ? Les données sont simulées et ne remplacent pas une
   télémétrie industrielle réelle.
