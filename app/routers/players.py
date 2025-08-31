from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from .. import models, schemas

router = APIRouter(prefix="/players", tags=["players"])

@router.post("", response_model=schemas.PlayerOut)
def create_player(payload: schemas.PlayerCreate, db: Session = Depends(get_db)):
    if not db.get(models.Team, payload.team_id):
        raise HTTPException(404, "Team not found")
    player = models.Player(**payload.dict())
    db.add(player)
    db.commit()
    db.refresh(player)
    return player
