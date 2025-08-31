# Baseball Scorecard Backend (Starter)

A minimal FastAPI + PostgreSQL backend to record baseball plate appearances in real time
and compute basic stats (AVG, OBP, SLG, OPS) per game and season.

## Quickstart (local without Docker)

1. Create and activate a virtualenv.
2. `pip install -r requirements.txt`
3. Ensure PostgreSQL is running and create a DB (default URL in `.env.example`).
4. Copy `.env.example` → `.env` and update `DATABASE_URL` if needed.
5. Run migrations: `alembic upgrade head`
6. Start the API: `uvicorn app.main:app --reload`
7. Open docs: http://127.0.0.1:8000/docs

## Docker (preferred)

1. Install Docker & Docker Compose.
2. `docker compose up --build`
3. API will be available at http://127.0.0.1:8000/docs

## Project layout

```
app/
  main.py
  db.py
  models.py
  schemas.py
  routers/
    seasons.py
    teams.py
    players.py
    games.py
    plate_appearances.py
  services/
    stats.py
alembic/
  env.py
  versions/
alembic.ini
requirements.txt
.env (create from .env.example)
tests/
```

## Notes

- MVP focuses on plate-appearance outcomes only (no pitch-by-pitch or baserunning yet).
- Stats are computed on-the-fly from events for correctness and simplicity.
- Extend the data model over time (substitutions, pitcher stats, etc.).
