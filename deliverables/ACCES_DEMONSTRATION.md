# Accès à la démonstration

## Services

| Service | Adresse | Accès |
| --- | --- | --- |
| Application et API | http://exp.s3.fsbm.ma:3402/ | Public |
| Documentation Swagger | http://exp.s3.fsbm.ma:3402/docs | Public |
| Santé de l'API | http://exp.s3.fsbm.ma:3402/health | Public |
| MLflow | http://exp.s3.fsbm.ma:3401 | Authentification HTTP |
| Dagster | http://exp.s3.fsbm.ma:3403 | Authentification HTTP |
| Dépôt GitHub | https://github.com/Maaskk/industrial-equipment-health-platform | Public |

## Identifiants MLflow et Dagster

MLflow et Dagster sont protégés par la même passerelle d'authentification. Pour éviter d'exposer le serveur universitaire, les identifiants ne sont pas publiés dans ce dépôt public.

Ils doivent être :

1. remis directement au professeur par un canal privé ; ou
2. saisis par un membre de l'équipe pendant la démonstration.

Le gestionnaire de mots de passe ou la note privée de l'équipe doit contenir :

```text
Utilisateur : [à remettre séparément]
Mot de passe : [à remettre séparément]
```

## Vérification rapide

Avant la démonstration :

1. ouvrir la route `/health` et vérifier `status: ready` ;
2. ouvrir Swagger et exécuter une prédiction ;
3. ouvrir MLflow et vérifier l'alias `champion` ;
4. ouvrir Dagster et vérifier le job et le planning quotidien ;
5. ouvrir Komodo avec le compte étudiant autorisé et vérifier que la Stack est `RUNNING`.

