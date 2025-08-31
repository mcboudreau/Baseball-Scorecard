from __future__ import annotations
from sqlalchemy.orm import Session
from collections import defaultdict
from ..models import PlateAppearance, PAResult, Player, Game
from ..schemas import PlayerStats, BoxScore
from typing import Literal

Metric = Literal["avg", "obp", "slg", "ops"]

def _safe_div(n: int, d: int) -> float:
    return round((n / d) if d else 0.0, 3)

def compute_boxscore(db: Session, game_id: int) -> BoxScore:
    q = (
        db.query(PlateAppearance, Player)
        .join(Player, Player.id == PlateAppearance.batter_id)
        .filter(PlateAppearance.game_id == game_id)
        .all()
    )

    stat = defaultdict(lambda: dict(ab=0, h=0, bb=0, hbp=0, sf=0, tb=0, first_name="", last_name=""))
    for pa, player in q:
        s = stat[player.id]
        s["first_name"] = player.first_name
        s["last_name"] = player.last_name
        res = pa.result
        if res in (PAResult.SINGLE, PAResult.DOUBLE, PAResult.TRIPLE, PAResult.HOMERUN, PAResult.OUT, PAResult.STRIKEOUT):
            s["ab"] += 1
        if res == PAResult.SINGLE:
            s["h"] += 1; s["tb"] += 1
        elif res == PAResult.DOUBLE:
            s["h"] += 1; s["tb"] += 2
        elif res == PAResult.TRIPLE:
            s["h"] += 1; s["tb"] += 3
        elif res == PAResult.HOMERUN:
            s["h"] += 1; s["tb"] += 4
        elif res == PAResult.WALK:
            s["bb"] += 1
        elif res == PAResult.HBP:
            s["hbp"] += 1
        elif res == PAResult.SAC_FLY:
            s["sf"] += 1

    batting = []
    for pid, s in stat.items():
        ab, h, bb, hbp, sf, tb = s["ab"], s["h"], s["bb"], s["hbp"], s["sf"], s["tb"]
        avg = _safe_div(h, ab)
        obp = _safe_div(h + bb + hbp, ab + bb + hbp + sf)
        slg = _safe_div(tb, ab)
        ops = round(obp + slg, 3)
        batting.append(
            PlayerStats(
                player_id=pid,
                first_name=s["first_name"],
                last_name=s["last_name"],
                ab=ab, h=h, bb=bb, hbp=hbp, sf=sf, tb=tb,
                avg=avg, obp=obp, slg=slg, ops=ops
            )
        )

    return BoxScore(game_id=game_id, batting=batting)

def compute_season_stats(db: Session, season_id: int) -> list[PlayerStats]:
    # Join PlateAppearance -> Player -> Game and filter by season
    rows = (
        db.query(PlateAppearance, Player)
          .join(Player, Player.id == PlateAppearance.batter_id)
          .join(Game, Game.id == PlateAppearance.game_id)
          .filter(Game.season_id == season_id)
          .all()
    )

    stat = defaultdict(lambda: dict(ab=0, h=0, bb=0, hbp=0, sf=0, tb=0, first_name="", last_name=""))
    for pa, player in rows:
        s = stat[player.id]
        s["first_name"] = player.first_name
        s["last_name"] = player.last_name
        res = pa.result
        if res in (PAResult.SINGLE, PAResult.DOUBLE, PAResult.TRIPLE, PAResult.HOMERUN, PAResult.OUT, PAResult.STRIKEOUT):
            s["ab"] += 1
        if res == PAResult.SINGLE:
            s["h"] += 1; s["tb"] += 1
        elif res == PAResult.DOUBLE:
            s["h"] += 1; s["tb"] += 2
        elif res == PAResult.TRIPLE:
            s["h"] += 1; s["tb"] += 3
        elif res == PAResult.HOMERUN:
            s["h"] += 1; s["tb"] += 4
        elif res == PAResult.WALK:
            s["bb"] += 1
        elif res == PAResult.HBP:
            s["hbp"] += 1
        elif res == PAResult.SAC_FLY:
            s["sf"] += 1

    results: list[PlayerStats] = []
    for pid, s in stat.items():
        ab, h, bb, hbp, sf, tb = s["ab"], s["h"], s["bb"], s["hbp"], s["sf"], s["tb"]
        avg = _safe_div(h, ab)
        obp = _safe_div(h + bb + hbp, ab + bb + hbp + sf)
        slg = _safe_div(tb, ab)
        ops = round(obp + slg, 3)
        results.append(
            PlayerStats(
                player_id=pid,
                first_name=s["first_name"],
                last_name=s["last_name"],
                ab=ab, h=h, bb=bb, hbp=hbp, sf=sf, tb=tb,
                avg=avg, obp=obp, slg=slg, ops=ops,
            )
        )
    return results

def compute_season_leaderboard(
    db: Session,
    season_id: int,
    metric: Metric = "ops",
    min_ab: int = 1,
    limit: int = 10,
) -> list[PlayerStats]:
    # reuse existing aggregation
    stats = compute_season_stats(db, season_id)

    # filter by minimum AB
    stats = [s for s in stats if s.ab >= min_ab]

    # sort by chosen metric (tie-breakers: tb, h, ab)
    key_map = {
        "avg": lambda s: (s.avg, s.tb, s.h, s.ab),
        "obp": lambda s: (s.obp, s.tb, s.h, s.ab),
        "slg": lambda s: (s.slg, s.tb, s.h, s.ab),
        "ops": lambda s: (s.ops, s.slg, s.obp, s.ab),
    }
    key_fn = key_map.get(metric, key_map["ops"])
    stats.sort(key=key_fn, reverse=True)

    return stats[: max(0, limit)]