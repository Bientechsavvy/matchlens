"""Analyst: stats, pass quality, momentum, key-moment detection."""
from __future__ import annotations

import math

from matchlens.schemas.events import (
    EventType,
    KeyMoment,
    Match,
    MatchEvent,
    MatchStats,
    Outcome,
    PassQuality,
    TeamStats,
)

WINDOW_S, STEP_S = 300, 60


def rel_x(ev: MatchEvent, x: float | None = None) -> float:
    v = ev.x if x is None else x
    return v if ev.team == "home" else 100 - v


def pass_quality(ev: MatchEvent) -> PassQuality:
    assert ev.type == EventType.PASS and ev.end_x is not None and ev.end_y is not None
    dist = math.hypot((ev.end_x - ev.x) * 1.05, (ev.end_y - ev.y) * 0.68)
    fwd = (rel_x(ev, ev.end_x) - rel_x(ev)) * 1.05
    diff = 0.15 + dist / 60 + 0.5 * (ev.pressure_level or 0) + (0.15 if rel_x(ev, ev.end_x) > 76 else 0)
    return PassQuality(event_id=ev.event_id, distance_m=round(dist, 1), forward_m=round(fwd, 1),
                       difficulty=round(min(max(diff, 0), 1), 3),
                       accurate=ev.outcome == Outcome.SUCCESS, ball_speed_kmh=ev.ball_speed_kmh)


def compute_stats(match: Match) -> MatchStats:
    out = {}
    passes_total = sum(1 for e in match.events if e.type == EventType.PASS) or 1
    top_speed, top_player = 0.0, None
    for side in ("home", "away"):
        ev = [e for e in match.events if e.team == side]
        ps = [e for e in ev if e.type == EventType.PASS]
        sh = [e for e in ev if e.type == EventType.SHOT]
        pq = [pass_quality(e).difficulty for e in ps]
        out[side] = TeamStats(
            possession_pct=round(100 * len(ps) / passes_total, 1),
            passes=len(ps),
            pass_accuracy_pct=round(100 * sum(e.outcome == Outcome.SUCCESS for e in ps) / max(len(ps), 1), 1),
            shots=len(sh),
            shots_on_target=sum(e.outcome in (Outcome.GOAL, Outcome.SAVED) for e in sh),
            xg=round(sum(e.xg or 0 for e in sh), 2),
            goals=match.score[side],
            tackles=sum(e.type == EventType.TACKLE for e in ev),
            avg_pass_difficulty=round(sum(pq) / max(len(pq), 1), 3),
        )
        for e in sh:
            if (e.ball_speed_kmh or 0) > top_speed:
                top_speed, top_player = e.ball_speed_kmh or 0, e.player_id
    return MatchStats(home=out["home"], away=out["away"], top_shot_speed_kmh=top_speed,
                      top_shot_player_id=top_player)


def _threat(ev: MatchEvent) -> float:
    if ev.type == EventType.SHOT:
        return 2 + 5 * (ev.xg or 0)
    if ev.type == EventType.PASS and ev.outcome == Outcome.SUCCESS and ev.end_x is not None:
        return 1.0 if rel_x(ev, ev.end_x) > 66 else 0.0
    if ev.type == EventType.PRESSURE:
        return 0.3
    return 0.0


def momentum_series(match: Match) -> list[tuple[float, float]]:
    """Returns [(clock_s, momentum)] where momentum in [-1, 1]: +1 = home dominance."""
    series = []
    for end in range(WINDOW_S, 5400 + 1, STEP_S):
        h = a = 0.0
        for e in match.events:
            if end - WINDOW_S < e.clock_s <= end:
                if e.team == "home":
                    h += _threat(e)
                else:
                    a += _threat(e)
        series.append((float(end), round((h - a) / (h + a), 3) if h + a else 0.0))
    return series


def turnovers_per_min(match: Match, t: float, window: float = 300) -> float:
    n = sum(1 for e in match.events
            if e.type == EventType.POSSESSION_CHANGE and t - window < e.clock_s <= t)
    return round(n / (min(window, max(t, 1)) / 60), 2)


def detect_key_moments(match: Match) -> list[KeyMoment]:
    moments: list[KeyMoment] = []
    n = 0
    for e in match.events:
        if e.type == EventType.GOAL:
            n += 1
            moments.append(KeyMoment(moment_id=f"km_{n:03d}", kind="goal", clock_s=e.clock_s,
                                     team=e.team, player_id=e.player_id, xg=e.xg))
        elif e.type == EventType.SHOT and (e.xg or 0) >= 0.3 and e.outcome != Outcome.GOAL:
            n += 1
            moments.append(KeyMoment(moment_id=f"km_{n:03d}", kind="big_chance", clock_s=e.clock_s,
                                     team=e.team, player_id=e.player_id, xg=e.xg))
    series = momentum_series(match)
    step = WINDOW_S // STEP_S
    last = -1e9
    for i in range(step, len(series)):
        (_, before), (t, after) = series[i - step], series[i]
        if before * after < 0 and abs(after - before) >= 0.6 and t - last >= 600:
            n += 1
            last = t
            moments.append(KeyMoment(moment_id=f"km_{n:03d}", kind="momentum_shift", clock_s=t,
                                     team="home" if after > 0 else "away",
                                     momentum_before=before, momentum_after=after))
    return sorted(moments, key=lambda m: m.clock_s)
