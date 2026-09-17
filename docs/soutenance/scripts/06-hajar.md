# Hajar

Diapositives 13 et 14. Durée cible : 4 minutes.

## Texte à présenter

« Ma contribution concerne le contrat FastAPI et le parcours de démonstration.
L'API constitue la frontière entre le modèle et l'application. La route
`GET /health` confirme que le service fonctionne et indique la version du
modèle. `GET /demo-payload` fournit un exemple valide. `POST /predict` exécute
la prédiction. Les routes sous `/api` alimentent les vues de flotte, l'historique
d'un moteur et le monitoring. »

« La validation des entrées est stricte avec Pydantic. La requête contient
l'identifiant du moteur, le cycle, les réglages et les mesures de capteurs. Le
payload de démonstration fournit 88 valeurs et le cycle complète le vecteur de
89 variables internes. Un champ inconnu ou une structure incorrecte provoque
une erreur 422 au lieu d'être ignoré silencieusement. »

« La réponse contient la RUL prédite, le niveau de risque, la version du modèle
et la latence. Cette structure permet d'afficher une décision compréhensible et
de savoir quel modèle l'a produite. Le contrat est également utilisé par les
tests, ce qui évite d'avoir une interface de démonstration différente du service
réel. »

« Pendant la démo, je commence par la vue flotte pour montrer les priorités. Je
sélectionne ensuite un moteur et son historique de cycles. Je lance une
prédiction et je vérifie la réponse. Enfin, j'ouvre les preuves de plateforme.
La visualisation du moteur sert à expliquer les mesures ; ce n'est pas une
simulation physique validée. »

« Aya va maintenant présenter les contrôles de production, le monitoring,
l'état de la Stack Komodo et les limites du projet. »

## Décision technique à défendre

Le contrat est strict et versionnable. L'API renvoie les informations nécessaires
à l'audit, notamment la version du modèle et la latence, au lieu de renvoyer une
valeur RUL isolée.

## Questions probables

1. Pourquoi 88 valeurs reçues et 89 variables internes ? Le cycle complète le
   vecteur construit pour le modèle.
2. Pourquoi FastAPI ? Il fournit validation Pydantic, documentation OpenAPI et
   tests simples autour d'un service Python.
3. La vue 3D représente-t-elle un moteur réel ? Non. Elle explique les signaux et
   l'état sélectionné, sans prétendre être un modèle physique.
