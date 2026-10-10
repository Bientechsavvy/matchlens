"""Explainer: turns key moments into structured, language-neutral facts."""
from __future__ import annotations

from matchlens.analyst.metrics import turnovers_per_min
from matchlens.schemas.events import Explanation, KeyMoment, Match

CHAOS_THRESHOLD = 1.2


def explain(match: Match, moments: list[KeyMoment]) -> list[Explanation]:
    out = []
    score = {"home": 0, "away": 0}
    for m in moments:
        tpm = turnovers_per_min(match, m.clock_s)
        label = "control" if tpm <= CHAOS_THRESHOLD else "chaos"
        facts = {
            "team": m.team, "team_name": match.team_name(m.team), "minute": int(m.clock_s // 60) + 1,
            "player": match.players[m.player_id].name if m.player_id else None,
            "xg": m.xg, "game_state": label, "turnovers_per_min": tpm,
            "momentum_before": m.momentum_before, "momentum_after": m.momentum_after,
        }
        if m.kind == "goal":
            score[m.team] += 1
            facts["score_home"], facts["score_away"] = score["home"], score["away"]
            facts["opened_scoring"] = score["home"] + score["away"] == 1
            facts["equalised"] = score["home"] == score["away"]
            prio = 5
        elif m.kind == "big_chance":
            prio = 4
        else:
            prio = 3
        out.append(Explanation(moment_id=m.moment_id, category="goal_context" if m.kind == "goal" else m.kind,
                               priority=prio, clock_s=m.clock_s, team=m.team,
                               player_id=m.player_id, facts=facts))
    return out
