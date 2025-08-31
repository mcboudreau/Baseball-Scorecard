from fastapi import FastAPI
from .routers import seasons, teams, players, games, plate_appearances
from .db import Base, engine

# Create tables if they don't exist (alembic is preferred, but this helps first run)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Baseball Scorecard API", version="0.1.0")

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

app.include_router(seasons.router)
app.include_router(teams.router)
app.include_router(players.router)
app.include_router(games.router)
app.include_router(plate_appearances.router)
