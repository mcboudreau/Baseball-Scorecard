from __future__ import annotations
from sqlalchemy.orm import Session
from collections import defaultdict
from ..models import PlateAppearance, PAResult, Player, Game
from ..schemas import PlayerStats, BoxScore
from typing import Literal, List

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

def _outs_to_ip_str(outs: int) -> str:
    # 3 outs per inning; remainder is .0/.1/.2 style
    return f"{outs // 3}.{outs % 3}"

def _era_approx(ra: int, outs: int) -> float:
    ip = outs / 3.0
    return round((9.0 * ra / ip) if ip > 0 else 0.0, 2)

def compute_game_pitching(db: Session, game_id: int) -> GamePitching:
    rows = (
        db.query(PlateAppearance, Player)
          .join(Player, Player.id == PlateAppearance.pitcher_id)
          .filter(PlateAppearance.game_id == game_id, PlateAppearance.pitcher_id.isnot(None))
          .all()
    )

    agg = {}
    for pa, pitcher in rows:
        pid = pitcher.id
        s = agg.setdefault(pid, {
            "first": pitcher.first_name, "last": pitcher.last_name,
            "bf": 0, "ab": 0, "h": 0, "bb": 0, "hbp": 0, "so": 0, "hr": 0, "sf": 0, "outs": 0, "ra": 0
        })
        s["bf"] += 1

        r = pa.result
        # AB, hits, HR
        if r in (PAResult.SINGLE, PAResult.DOUBLE, PAResult.TRIPLE, PAResult.HOMERUN, PAResult.OUT, PAResult.STRIKEOUT):
            s["ab"] += 1
        if r in (PAResult.SINGLE, PAResult.DOUBLE, PAResult.TRIPLE, PAResult.HOMERUN):
            s["h"] += 1
        if r == PAResult.HOMERUN:
            s["hr"] += 1

        # Walk / HBP
        if r == PAResult.WALK:
            s["bb"] += 1
        if r == PAResult.HBP:
            s["hbp"] += 1

        # Outs recorded while this pitcher is in:
        # count K, OUT, SF as outs
        if r in (PAResult.STRIKEOUT, PAResult.OUT, PAResult.SAC_FLY):
            s["outs"] += 1
        if r == PAResult.STRIKEOUT:
            s["so"] += 1
        if r == PAResult.SAC_FLY:
            s["sf"] += 1

        # Runs allowed proxy (sum RBIs)
        s["ra"] += (pa.rbis or 0)

    result = []
    for pid, s in agg.items():
        ip = _outs_to_ip_str(s["outs"])
        era = _era_approx(s["ra"], s["outs"])
        result.append(
            PitcherStats(
                pitcher_id=pid, first_name=s["first"], last_name=s["last"],
                bf=s["bf"], ab=s["ab"], h=s["h"], bb=s["bb"], hbp=s["hbp"], so=s["so"], hr=s["hr"], sf=s["sf"],
                outs=s["outs"], ip=ip, ra=s["ra"], era=era
            )
        )
    return GamePitching(game_id=game_id, pitching=result)

def compute_season_pitching(db: Session, season_id: int) -> list[PitcherStats]:
    rows = (
        db.query(PlateAppearance, Player)
          .join(Player, Player.id == PlateAppearance.pitcher_id)
          .join(Game, Game.id == PlateAppearance.game_id)
          .filter(Game.season_id == season_id, PlateAppearance.pitcher_id.isnot(None))
          .all()
    )

    agg = {}
    for pa, pitcher in rows:
        pid = pitcher.id
        s = agg.setdefault(pid, {
            "first": pitcher.first_name, "last": pitcher.last_name,
            "bf": 0, "ab": 0, "h": 0, "bb": 0, "hbp": 0, "so": 0, "hr": 0, "sf": 0, "outs": 0, "ra": 0
        })
        s["bf"] += 1
        r = pa.result
        if r in (PAResult.SINGLE, PAResult.DOUBLE, PAResult.TRIPLE, PAResult.HOMERUN, PAResult.OUT, PAResult.STRIKEOUT):
            s["ab"] += 1
        if r in (PAResult.SINGLE, PAResult.DOUBLE, PAResult.TRIPLE, PAResult.HOMERUN):
            s["h"] += 1
        if r == PAResult.HOMERUN:
            s["hr"] += 1
        if r == PAResult.WALK:
            s["bb"] += 1
        if r == PAResult.HBP:
            s["hbp"] += 1
        if r in (PAResult.STRIKEOUT, PAResult.OUT, PAResult.SAC_FLY):
            s["outs"] += 1
        if r == PAResult.STRIKEOUT:
            s["so"] += 1    
        if r == PAResult.SAC_FLY:
            s["sf"] += 1
        s["ra"] += (pa.rbis or 0)

    result = []
    for pid, s in agg.items():
        ip = _outs_to_ip_str(s["outs"])
        era = _era_approx(s["ra"], s["outs"])
        result.append(
            PitcherStats(
                pitcher_id=pid, first_name=s["first"], last_name=s["last"],
                bf=s["bf"], ab=s["ab"], h=s["h"], bb=s["bb"], hbp=s["hbp"], so=s["so"], hr=s["hr"], sf=s["sf"],
                outs=s["outs"], ip=ip, ra=s["ra"], era=era
            )
        )
    return result

def compute_season_pitching_leaderboard(
    db: Session,
    season_id: int,
    min_ip: float = 0.0,   # e.g., 10.0 means 10 innings minimum
    limit: int = 10,
) -> List[PitcherStats]:
    # Reuse the season aggregation
    stats = compute_season_pitching(db, season_id)

    # Convert min_ip to outs for filtering (3 outs per inning)
    min_outs = int(min_ip * 3 + 0.5)

    # Filter: pitchers meeting minimum IP (outs) AND with any IP
    qualified = [s for s in stats if s.outs >= max(1, min_outs)]

    # Sort by ERA ascending; tie-breakers: more outs (IP), fewer RA, more SO
    qualified.sort(
        key=lambda s: (s.era, -s.outs, s.ra, -s.so)
    )

    return qualified[: max(0, limit)]