"""Seeded, football-realistic synthetic match generator."""
from __future__ import annotations

import math
import random

from matchlens.schemas.events import EventType, Match, MatchEvent, Outcome, Player, Side

FIRST = ["Adrian", "Marcus", "Luca", "Tomas", "Jonas", "Idris", "Mateo", "Kofi", "Rafael", "Ben",
         "Samir", "Niko", "Elias", "Tunde", "Hugo", "Callum", "Yusuf", "Dario", "Ola", "Felix"]
LAST = ["Cole", "Reyes", "Okafor", "Brandt", "Silva", "Novak", "Mensah", "Larsen", "Duarte",
        "Hale", "Ibrahim", "Moreau", "Santos", "Keane", "Adeyemi", "Ricci", "Vega", "Strand"]
POSITIONS = ["GK", "DEF", "DEF", "DEF", "DEF", "MID", "MID", "MID", "MID", "FWD", "FWD"]
ZONE_W = {  # position weights by zone: own third, middle, final third
    "GK": (0.6, 0.0, 0.0), "DEF": (3.0, 1.0, 0.3), "MID": (2.0, 3.0, 1.5), "FWD": (0.5, 1.5, 3.0),
}
MATCH_SECONDS = 5400
HALF = 2700


def _clip(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def other(side: Side) -> Side:
    return "away" if side == "home" else "home"


class MatchSimulator:
    def __init__(self, seed: int = 42, home: str = "Northbridge FC", away: str = "Eastport United"):
        self.seed, self.home, self.away = seed, home, away

    # ---------- public ----------
    def generate(self) -> Match:
        rng = random.Random(self.seed)
        match_id = f"m_{self.seed}"
        players = self._roster(rng)
        by_side = {s: [p for p in players.values() if p.team == s] for s in ("home", "away")}
        events: list[MatchEvent] = []
        score = {"home": 0, "away": 0}
        eid = 0

        def emit(**kw) -> MatchEvent:
            nonlocal eid
            eid += 1
            ev = MatchEvent(event_id=eid, match_id=match_id, **kw)
            events.append(ev)
            return ev

        def pick(side: Side, rel_x: float) -> Player:
            zone = 0 if rel_x < 33 else 1 if rel_x < 66 else 2
            ps = by_side[side]
            return rng.choices(ps, weights=[ZONE_W[p.position][zone] + 0.01 for p in ps])[0]

        def absx(side: Side, rx: float) -> float:
            return rx if side == "home" else 100 - rx

        def absy(side: Side, ry: float) -> float:
            return ry if side == "home" else 100 - ry

        t, period = 0.0, 1
        poss: Side = "home"
        rx, ry = 50.0, 50.0  # ball position relative to possessing team
        emit(clock_s=0, period=1, type=EventType.KICKOFF, team=poss,
             player_id=pick(poss, 50).player_id, x=50, y=50)

        while t < MATCH_SECONDS:
            t = min(t + rng.uniform(3, 9), MATCH_SECONDS)
            if period == 1 and t >= HALF:  # half-time: restart before emitting anything past 2700s
                period, t, poss, rx, ry = 2, float(HALF), "away", 50.0, 50.0
                emit(clock_s=t, period=2, type=EventType.KICKOFF, team=poss,
                     player_id=pick(poss, 50).player_id, x=50, y=50)
                continue
            opp = other(poss)
            press = self._press(opp, t)
            actor = pick(poss, rx)
            ts = round(t, 1)

            if rx > 76 and rng.random() < 0.2:  # ---- shot ----
                dist = math.hypot((100 - rx) * 1.05, (ry - 50) * 0.68)
                xg = round(_clip(0.9 * math.exp(-dist / 9), 0.01, 0.6), 3)
                roll = rng.random()
                outcome = Outcome.GOAL if roll < xg else (
                    Outcome.SAVED if roll < xg + 0.3 else Outcome.OFF_TARGET)
                ex, ey = 100.0, _clip(50 + rng.gauss(0, 8), 40, 60)
                emit(clock_s=ts, period=period, type=EventType.SHOT, team=poss,
                     player_id=actor.player_id, x=absx(poss, rx), y=absy(poss, ry),
                     end_x=absx(poss, ex), end_y=absy(poss, ey), outcome=outcome,
                     ball_speed_kmh=round(rng.uniform(70, 125), 1), xg=xg,
                     pressure_level=round(press, 2))
                if outcome == Outcome.GOAL:
                    score[poss] += 1
                    emit(clock_s=ts, period=period, type=EventType.GOAL, team=poss,
                         player_id=actor.player_id, x=absx(poss, 100), y=absy(poss, 50),
                         outcome=Outcome.GOAL, xg=xg)
                    poss, rx, ry = opp, 50.0, 50.0
                else:
                    poss, rx, ry = opp, 12.0, 50.0
                continue

            # ---- pass ----
            ex = _clip(rx + rng.gauss(7, 12), 1, 99)
            ey = _clip(ry + rng.gauss(0, 14), 2, 98)
            dist = math.hypot((ex - rx) * 1.05, (ey - ry) * 0.68)
            diff = _clip(0.15 + dist / 60 + 0.5 * press + (0.15 if ex > 76 else 0), 0, 1)
            if press > 0.55 and rng.random() < 0.4:
                d = pick(opp, 100 - rx)
                emit(clock_s=round(max(ts - 0.5, 0), 1), period=period, type=EventType.PRESSURE,
                     team=opp, player_id=d.player_id, x=absx(poss, rx), y=absy(poss, ry),
                     pressure_level=round(press, 2))
            ok = rng.random() < 0.98 - 0.5 * diff
            emit(clock_s=ts, period=period, type=EventType.PASS, team=poss,
                 player_id=actor.player_id, x=absx(poss, rx), y=absy(poss, ry),
                 end_x=absx(poss, ex), end_y=absy(poss, ey),
                 outcome=Outcome.SUCCESS if ok else Outcome.FAIL,
                 ball_speed_kmh=round(_clip(35 + dist * 1.8, 30, 100), 1),
                 pressure_level=round(press, 2))
            if ok:
                rx, ry = ex, ey
            else:
                d = pick(opp, 100 - ex)
                if rng.random() < 0.4:
                    emit(clock_s=ts, period=period, type=EventType.TACKLE, team=opp,
                         player_id=d.player_id, x=absx(poss, ex), y=absy(poss, ey),
                         outcome=Outcome.SUCCESS)
                emit(clock_s=ts, period=period, type=EventType.POSSESSION_CHANGE, team=opp,
                     player_id=d.player_id, x=absx(poss, ex), y=absy(poss, ey))
                poss, rx, ry = opp, 100 - ex, 100 - ey

        return Match(match_id=match_id, home_name=self.home, away_name=self.away,
                     players=players, events=events, score=score)

    # ---------- helpers ----------
    @staticmethod
    def _press(defending: Side, t: float) -> float:
        """Pressing intensity oscillates so each team has spells of control."""
        phase = 0.0 if defending == "home" else math.pi
        return _clip(0.4 + 0.3 * math.sin(2 * math.pi * t / 900 + phase), 0, 1)

    def _roster(self, rng: random.Random) -> dict[str, Player]:
        out: dict[str, Player] = {}
        for side in ("home", "away"):
            names: set[str] = set()
            for i, pos in enumerate(POSITIONS, start=1):
                while True:
                    n = f"{rng.choice(FIRST)} {rng.choice(LAST)}"
                    if n not in names and n not in {p.name for p in out.values()}:
                        break
                names.add(n)
                pid = f"{side}_{i}"
                out[pid] = Player(player_id=pid, name=n, team=side, position=pos, number=i)
        return out
