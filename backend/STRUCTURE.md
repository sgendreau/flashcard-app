# Backend — structure

`server.py` (1215 lignes) a été découpé en modules. **Aucun changement de comportement** :
les 33 routes `/api/...` sont identiques. Trois améliorations propres et sûres :
`get_current_user` est désormais une dépendance FastAPI (`Depends`), le `logger` est
défini en haut, et `@app.on_event(...)` (déprécié) devient un *lifespan handler*.

```
backend/
├── server.py              # Entrypoint mince : app, lifespan, montage des routers, CORS
└── app/
    ├── __init__.py        # Charge .env avant tout accès à os.environ
    ├── config.py          # Constantes : JWT, niveaux + helpers, XP, défis, badges
    ├── db.py              # Client Mongo + handle `db`
    ├── security.py        # Hash mots de passe, JWT, dépendance get_current_user
    ├── helpers.py         # user_response, codes classe/parrainage, get_week_start
    ├── schemas.py         # Modèles Pydantic (entrées)
    ├── seed.py            # Données seed (matières, cartes) + seed_data()
    └── routers/
        ├── __init__.py    # Liste ordonnée des routers
        ├── auth.py        # /auth/*
        ├── users.py       # /user/* (niveau, notifications, thème)
        ├── subjects.py    # /subjects
        ├── flashcards.py  # /flashcards/*, /export, /import
        ├── study.py       # /study/*, /progress/*
        ├── classes.py     # /classes/* (+ leaderboard, decks partagés)
        ├── engagement.py  # /rewards/*, /challenges/*, /referral/*, /share/*
        ├── ai.py          # /ai/generate
        └── system.py      # /sync/status
```

## Lancer

Le point d'entrée ASGI reste `server:app` (inchangé) :

```bash
uvicorn server:app --reload
```

Variables d'environnement attendues (dans `backend/.env`) :
`MONGO_URL`, `DB_NAME`, `JWT_SECRET`, et optionnellement `ADMIN_EMAIL`,
`ADMIN_PASSWORD`, `EMERGENT_LLM_KEY`.

## Note

Une seule micro-déduplication a été faite : la logique de calcul de progression
des défis hebdo, qui était copiée dans `get_challenges` et `claim_challenge`, est
factorisée dans `engagement._challenge_progress` (comportement identique).
