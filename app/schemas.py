from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional
from .models import GameStatus, HalfInning, PAResult

# ---- Seasons / Teams / Players ----
class SeasonCreate(BaseModel):
    name: str
    year: int

class SeasonOut(SeasonCreate):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

class TeamCreate(BaseModel):
    season_id: int
    name: str

class TeamOut(TeamCreate):
    id: int
    class Config:
        from_attributes = True

class PlayerCreate(BaseModel):
    team_id: int
    first_name: str
    last_name: str
    handedness: Optional[str] = None

class PlayerOut(PlayerCreate):
    id: int
    class Config:
        from_attributes = True

# ---- Games & Lineups ----
class GameCreate(BaseModel):
    season_id: int
    home_team_id: int
    away_team_id: int

class GameOut(GameCreate):
    id: int
    start_time: datetime
    status: GameStatus
    class Config:
        from_attributes = True

class LineupEntry(BaseModel):
    team_id: int
    batting_order: int = Field(ge=1, le=9)
    player_id: int
    defensive_position: Optional[str] = None

class LineupSet(BaseModel):
    entries: List[LineupEntry]

# ---- Plate Appearances ----
class PACreate(BaseModel):
    game_id: int
    inning: int = Field(ge=1)
    half: HalfInning
    batter_id: int
    pitcher_id: Optional[int] = None
    result: PAResult
    rbis: int = 0
    notes: Optional[str] = None
    client_event_id: Optional[str] = None

class PAOut(PACreate):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

# ---- Stats ----
class PlayerStats(BaseModel):
    player_id: int
    first_name: str
    last_name: str
    ab: int
    h: int
    bb: int
    hbp: int
    sf: int
    tb: int
    avg: float
    obp: float
    slg: float
    ops: float

class BoxScore(BaseModel):
    game_id: int
    batting: list[PlayerStats]

class PitcherStats(BaseModel):
    pitcher_id: int
    first_name: str
    last_name: str
    bf: int
    ab: int
    h: int
    bb: int
    hbp: int
    so: int
    hr: int
    sf: int
    outs: int          # raw outs
    ip: str            # e.g., "5.2"
    ra: int            # runs allowed (RBIs proxy)
    era: float         # ERA (approx from RA)

class GamePitching(BaseModel):
    game_id: int
    pitching: list[PitcherStats]