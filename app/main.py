from fastapi import FastAPI
from .routers import seasons, teams, players, games, plate_appearances
from .db import Base, engine

app = FastAPI(title="Baseball Scorecard API", version="0.1.0")

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

app.include_router(seasons.router)
app.include_router(teams.router)
app.include_router(players.router)
app.include_router(games.router)
app.include_router(plate_appearances.router)
