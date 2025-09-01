from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..db import get_db
from .. import models, schemas
from ..services.stats import compute_season_stats, compute_season_leaderboard, compute_season_pitching

router = APIRouter(prefix="/seasons", tags=["seasons"])

@router.post("", response_model=schemas.SeasonOut)
def create_season(payload: schemas.SeasonCreate, db: Session = Depends(get_db)):
    season = models.Season(**payload.dict())
    db.add(season)
    db.commit()
    db.refresh(season)
    return season

@router.get("/{season_id}/stats", response_model=list[schemas.PlayerStats])  
def season_stats(season_id: int, db: Session = Depends(get_db)):
    if not db.get(models.Season, season_id):
        raise HTTPException(404, "Season not found")
    return compute_season_stats(db, season_id)

@router.get("/{season_id}/leaderboard", response_model=list[schemas.PlayerStats])
def season_leaderboard(
    season_id: int,
    metric: str = Query("ops", pattern="^(avg|obp|slg|ops)$", description="Which metric to rank by"),
    min_ab: int = Query(1, ge=0, description="Minimum at-bats to qualify"),
    limit: int = Query(10, ge=1, le=100, description="Max players to return"),
    db: Session = Depends(get_db),
):
    if not db.get(models.Season, season_id):
        raise HTTPException(404, "Season not found")
    return compute_season_leaderboard(db, season_id, metric=metric, min_ab=min_ab, limit=limit)

@router.get("/{season_id}/pitching", response_model=list[schemas.PitcherStats])
def season_pitching(season_id: int, db: Session = Depends(get_db)):
    if not db.get(models.Season, season_id):
        raise HTTPException(404, "Season not found")
    return compute_season_pitching(db, season_id)