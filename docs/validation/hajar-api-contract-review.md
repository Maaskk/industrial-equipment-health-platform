# Revue du contrat API

Responsable : Hajar Ennajdy

Suivi : [issue GitHub 14](https://github.com/Maaskk/industrial-equipment-health-platform/issues/14)

## Points à vérifier

1. `GET /health` indique si le modèle est chargé.
2. `GET /demo-payload` fournit un exemple valide avec 88 valeurs de requête.
3. `POST /predict` renvoie l'identifiant, la RUL, le risque et la version.
4. Une variable absente ou inconnue produit une erreur claire.
5. Le tableau de bord utilise les mêmes routes que la démonstration.

## Commande de test

```bash
PYTHONPATH=src python -m pytest tests/test_maaskk_api_app.py tests/test_frontend_proxy.py
```

Hajar peut exécuter cette revue, ajouter le résultat observé, puis la valider avec
son propre compte GitHub. Le document ne change pas l'auteur des fichiers API.
