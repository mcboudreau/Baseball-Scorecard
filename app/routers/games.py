from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from .. import models, schemas
from ..services.stats import compute_boxscore, compute_game_pitching

router = APIRouter(prefix="/games", tags=["games"])

@router.post("", response_model=schemas.GameOut)
def create_game(payload: schemas.GameCreate, db: Session = Depends(get_db)):
    for tid in (payload.home_team_id, payload.away_team_id):
        if not db.get(models.Team, tid):
            raise HTTPException(404, f"Team {tid} not found")
    game = models.Game(**payload.dict())
    db.add(game)
    db.commit()
    db.refresh(game)
    return game

@router.post("/{game_id}/lineup")
def set_lineup(game_id: int, body: schemas.LineupSet, db: Session = Depends(get_db)):
    game = db.get(models.Game, game_id)
    if not game:
        raise HTTPException(404, "Game not found")

    # Clear existing lineup for this game
    db.query(models.Lineup).filter(models.Lineup.game_id == game_id).delete()

    # Validate batting orders are 1..9 and unique per team
    seen = {}
    for entry in body.entries:
        key = (entry.team_id, entry.batting_order)
        if key in seen:
            raise HTTPException(400, f"Duplicate batting order {entry.batting_order} for team {entry.team_id}")
        seen[key] = True
        if not db.get(models.Player, entry.player_id):
            raise HTTPException(404, f"Player {entry.player_id} not found")
        db.add(models.Lineup(
            game_id=game_id,
            team_id=entry.team_id,
            batting_order=entry.batting_order,
            player_id=entry.player_id,
            defensive_position=entry.defensive_position
        ))
    db.commit()
    return {"ok": True}


@router.get("/{game_id}/pitching", response_model=schemas.GamePitching)
def game_pitching(game_id: int, db: Session = Depends(get_db)):
    game = db.get(models.Game, game_id)
    if not game:
        raise HTTPException(404, "Game not found")
    return compute_game_pitching(db, game_id)