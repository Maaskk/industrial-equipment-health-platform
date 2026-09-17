# Mohamed

Diapositives 4 et 5. Durée cible : 4 minutes.

## Texte à présenter

« Ma contribution concerne la partie DataOps et l'orchestration. L'architecture
commence avec les fichiers NASA C-MAPSS. dlt les charge de façon déclarative.
DuckDB conserve les tables brutes, les tables intermédiaires et les marts. dbt
transforme les données et exécute les tests. Le mart final alimente les features
du modèle. Ensuite, MLflow conserve les expériences, FastAPI sert le champion,
Docker décrit les services et Komodo gère la Stack sur le serveur partagé. »

« J'ai choisi DuckDB parce que le volume, environ 265 000 lignes brutes, tient
sur une seule machine. Il n'est donc pas nécessaire d'ajouter un serveur de base
de données. Ce choix simplifie l'installation, la CI et la démonstration, tout
en gardant SQL, les tables et les requêtes reproductibles. »

« Dagster impose l'ordre du pipeline. L'ingestion doit réussir avant dbt. Les
tests dbt doivent réussir avant la création des features. Le training produit
ensuite un candidat MLflow. Le rapport de drift est généré après le training.
Cette dépendance empêche une étape de contourner un contrôle précédent. »

« Le job final est planifié chaque jour à 06:00 dans le fuseau de Casablanca.
Il s'agit bien d'un réentraînement automatique planifié. Le rapport de drift ne
déclenche pas ce job. Il sert seulement au monitoring et à l'analyse. Cette
distinction évite de présenter une boucle fermée qui n'existe pas dans le code. »

« Le même point d'entrée peut être utilisé en local, dans GitHub Actions et dans
Docker. Hamza va maintenant montrer comment les contrats et les tests empêchent
des données invalides d'atteindre le modèle. »

## Décision technique à défendre

DuckDB a été préféré à une base distribuée parce qu'il couvre le volume réel du
projet avec moins d'administration. Dagster a été choisi pour rendre les
dépendances visibles, rejouables et contrôlables.

## Questions probables

1. Pourquoi dlt et dbt ensemble ? dlt gère l'ingestion et le schéma de chargement.
   dbt gère les transformations SQL, les tests et la documentation.
2. Que se passe-t-il si dbt échoue ? Les assets suivants ne s'exécutent pas.
3. Le drift lance-t-il un entraînement ? Non. Le job quotidien lance le pipeline.
