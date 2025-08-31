from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from .. import models, schemas

router = APIRouter(prefix="/teams", tags=["teams"])

@router.post("", response_model=schemas.TeamOut)
def create_team(payload: schemas.TeamCreate, db: Session = Depends(get_db)):
    # Ensure season exists
    if not db.get(models.Season, payload.season_id):
        raise HTTPException(404, "Season not found")
    team = models.Team(**payload.dict())
    db.add(team)
    db.commit()
    db.refresh(team)
    return team
