from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ..db import get_db
from .. import models, schemas
from ..services.stats import compute_boxscore

router = APIRouter(prefix="/pa", tags=["plate_appearances"])

@router.post("", response_model=schemas.PAOut)
def add_pa(payload: schemas.PACreate, db: Session = Depends(get_db)):
    if not db.get(models.Game, payload.game_id):
        raise HTTPException(404, "Game not found")
    if not db.get(models.Player, payload.batter_id):
        raise HTTPException(404, "Batter not found")
    if payload.pitcher_id and not db.get(models.Player, payload.pitcher_id):
        raise HTTPException(404, "Pitcher not found")
    
    if payload.client_event_id:
        existing = (
            db.query(models.PlateAppearance)
              .filter(
                  models.PlateAppearance.client_event_id == payload.client_event_id,
                  models.PlateAppearance.game_id == payload.game_id,
              )
              .one_or_none()
        )
        if existing:
            return existing

    pa = models.PlateAppearance(**payload.dict())
    db.add(pa)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # Likely a race on unique constraint; fetch and return existing
        if payload.client_event_id:
            existing = (
                db.query(models.PlateAppearance)
                  .filter(
                      models.PlateAppearance.game_id == payload.game_id,
                      models.PlateAppearance.client_event_id == payload.client_event_id,
                  )
                  .one_or_none()
            )
            if existing:
                return existing
        # If we get here, it was some other integrity error
        raise
    db.refresh(pa)
    return pa

@router.get("/boxscore/{game_id}", response_model=schemas.BoxScore)
def get_boxscore(game_id: int, db: Session = Depends(get_db)):
    if not db.get(models.Game, game_id):
        raise HTTPException(404, "Game not found")
    return compute_boxscore(db, game_id)
