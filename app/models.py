from __future__ import annotations
from datetime import datetime
from sqlalchemy import (
    BigInteger, Integer, String, DateTime, ForeignKey, Enum, UniqueConstraint, CheckConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base
import enum

class GameStatus(enum.Enum):
    live = "live"
    final = "final"

class HalfInning(enum.Enum):
    top = "top"
    bottom = "bottom"

class PAResult(enum.Enum):
    SINGLE = "1B"
    DOUBLE = "2B"
    TRIPLE = "3B"
    HOMERUN = "HR"
    WALK = "BB"
    HBP = "HBP"
    STRIKEOUT = "K"
    SAC_FLY = "SF"
    OUT = "OUT"

class Season(Base):
    __tablename__ = "seasons"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    year: Mapped[int] = mapped_column(Integer, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    teams: Mapped[list["Team"]] = relationship(back_populates="season", cascade="all, delete-orphan")
    games: Mapped[list["Game"]] = relationship(back_populates="season", cascade="all, delete-orphan")

class Team(Base):
    __tablename__ = "teams"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    season_id: Mapped[int] = mapped_column(ForeignKey("seasons.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120), index=True)

    season: Mapped["Season"] = relationship(back_populates="teams")
    players: Mapped[list["Player"]] = relationship(back_populates="team", cascade="all, delete-orphan")

class Player(Base):
    __tablename__ = "players"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"), index=True)
    first_name: Mapped[str] = mapped_column(String(80))
    last_name: Mapped[str] = mapped_column(String(80))
    handedness: Mapped[str | None] = mapped_column(String(2), nullable=True)  # e.g., R/L/S

    team: Mapped["Team"] = relationship(back_populates="players")

class Game(Base):
    __tablename__ = "games"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    season_id: Mapped[int] = mapped_column(ForeignKey("seasons.id", ondelete="CASCADE"), index=True)
    home_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    away_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    start_time: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[GameStatus] = mapped_column(Enum(GameStatus), default=GameStatus.live)

    season: Mapped["Season"] = relationship(back_populates="games")
    home_team: Mapped["Team"] = relationship(foreign_keys=[home_team_id])
    away_team: Mapped["Team"] = relationship(foreign_keys=[away_team_id])
    lineups: Mapped[list["Lineup"]] = relationship(back_populates="game", cascade="all, delete-orphan")
    plate_appearances: Mapped[list["PlateAppearance"]] = relationship(back_populates="game", cascade="all, delete-orphan")

class Lineup(Base):
    __tablename__ = "lineups"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id", ondelete="CASCADE"), index=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"), index=True)
    batting_order: Mapped[int] = mapped_column(Integer)  # 1..9
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"))
    defensive_position: Mapped[str | None] = mapped_column(String(3), nullable=True)

    __table_args__ = (
        UniqueConstraint("game_id", "team_id", "batting_order", name="uq_lineup_order"),
        CheckConstraint("batting_order BETWEEN 1 AND 9", name="ck_batting_order_range"),
    )

    game: Mapped["Game"] = relationship(back_populates="lineups")
    player: Mapped["Player"] = relationship()

class PlateAppearance(Base):
    __tablename__ = "plate_appearances"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id", ondelete="CASCADE"), index=True)
    inning: Mapped[int] = mapped_column(Integer)  # 1..N
    half: Mapped[HalfInning] = mapped_column(Enum(HalfInning))
    batter_id: Mapped[int] = mapped_column(ForeignKey("players.id"))
    pitcher_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"), nullable=True)
    result: Mapped[PAResult] = mapped_column(Enum(PAResult))
    rbis: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str | None] = mapped_column(String(250), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    client_event_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    __table_args__ = (
        UniqueConstraint("game_id", "client_event_id", name="uq_pa_game_client_event"),
    )

    game: Mapped["Game"] = relationship(back_populates="plate_appearances")
