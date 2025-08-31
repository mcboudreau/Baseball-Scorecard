import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db import Base
from app import models
from app.services.stats import compute_boxscore
from app.models import PAResult, HalfInning

@pytest.fixture
def db():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)
    session = TestingSessionLocal()
    yield session
    session.close()

def test_basic_stats(db):
    # Build minimal season/team/players/game
    s = models.Season(name="Test", year=2025)
    db.add(s); db.flush()
    t = models.Team(season_id=s.id, name="A")
    db.add(t); db.flush()
    p1 = models.Player(team_id=t.id, first_name="Ada", last_name="Lovelace")
    p2 = models.Player(team_id=t.id, first_name="Grace", last_name="Hopper")
    db.add_all([p1, p2]); db.flush()
    g = models.Game(season_id=s.id, home_team_id=t.id, away_team_id=t.id)
    db.add(g); db.flush()

    db.add_all([
        models.PlateAppearance(game_id=g.id, inning=1, half=HalfInning.top, batter_id=p1.id, result=PAResult.SINGLE, rbis=0),
        models.PlateAppearance(game_id=g.id, inning=1, half=HalfInning.top, batter_id=p1.id, result=PAResult.WALK, rbis=0),
        models.PlateAppearance(game_id=g.id, inning=1, half=HalfInning.top, batter_id=p2.id, result=PAResult.HOMERUN, rbis=2),
        models.PlateAppearance(game_id=g.id, inning=2, half=HalfInning.top, batter_id=p2.id, result=PAResult.STRIKEOUT, rbis=0),
        models.PlateAppearance(game_id=g.id, inning=2, half=HalfInning.top, batter_id=p1.id, result=PAResult.OUT, rbis=0),
        models.PlateAppearance(game_id=g.id, inning=3, half=HalfInning.top, batter_id=p1.id, result=PAResult.SAC_FLY, rbis=1),
    ])
    db.commit()

    box = compute_boxscore(db, g.id)
    # Ada: AB=2 (1B, OUT), H=1, BB=1, SF=1, TB=1 => AVG .500, OBP (1+1)/ (2+1+0+1)=0.5, SLG 0.5, OPS 1.0
    ada = next(b for b in box.batting if b.first_name == "Ada")
    assert ada.ab == 2 and ada.h == 1 and ada.bb == 1 and ada.sf == 1 and ada.tb == 1
    assert ada.avg == 0.5 and ada.obp == 0.5 and ada.slg == 0.5 and ada.ops == 1.0
