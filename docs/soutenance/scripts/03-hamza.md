# Hamza

Diapositives 6 et 7. Durée cible : 4 minutes.

## Texte à présenter

« Ma contribution porte sur la qualité des données, le lignage, les tests et la
validation continue. Les contrats définissent les colonnes attendues, leurs
types et les règles principales. Les tests contrôlent les valeurs nulles, les
domaines, l'unicité du couple moteur-cycle et la cohérence des volumes. Une
erreur n'est pas simplement enregistrée : elle bloque la suite du pipeline. »

« Le lignage permet de répondre à une question simple : d'où vient une
prédiction ? Nous pouvons repartir du journal de prédiction, retrouver la
version du modèle dans MLflow, le mart de features, les tables dlt et les
fichiers NASA d'origine. Cette traçabilité est nécessaire pour analyser une
erreur et pour reproduire un résultat. »

« J'ai également travaillé sur les contrôles dans GitHub Actions. La CI vérifie
les données et dbt, les tests Python, la compilation et les règles statiques.
Elle exécute ensuite l'entraînement et le registre, construit l'image Docker,
puis effectue un smoke test sur la santé et la prédiction. Pendant la
démonstration, j'ouvre la dernière exécution verte et j'annonce l'identifiant et
le commit visibles à l'écran. »

« Le rôle de ma partie dans le pipeline est donc de créer une barrière avant le
modèle et avant le déploiement. Un code qui fonctionne mais utilise des données
incorrectes ne doit pas être livré. Une fois ces contrôles validés, Mouhcine
peut comparer les modèles avec un protocole fiable. »

## Décision technique à défendre

Les contrôles sont bloquants et exécutés à plusieurs niveaux : contrats,
tests dbt, tests Python et smoke test Docker. Cette redondance protège des
erreurs différentes au lieu de dépendre d'un seul test final.

## Questions probables

1. Différence entre contrat et test ? Le contrat décrit la structure attendue.
   Le test vérifie une propriété sur les données réellement chargées.
2. Pourquoi un smoke test après le build ? Il vérifie que l'image démarre et que
   l'API répond, pas seulement que le code compile.
3. Que prouve la CI ? Elle prouve la reproductibilité des contrôles sur le commit
   testé, pas la qualité future de toutes les données industrielles.
