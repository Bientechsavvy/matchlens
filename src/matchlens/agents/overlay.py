"""Overlay renderer: timed, machine-readable JSON overlays synced to the match clock."""
from __future__ import annotations

from matchlens.agents.narrator import Narrator
from matchlens.schemas.events import Explanation, Match, MatchStats, Overlay, ViewerProfile

STAT_LABELS = {
    "en": ("Possession", "Shots", "xG"), "es": ("Posesión", "Tiros", "xG"), "fr": ("Possession", "Tirs", "xG"),
}


def moment_overlays(match: Match, expl: list[Explanation], profile: ViewerProfile, narrator: Narrator,
                    start_index: int = 0) -> list[Overlay]:
    out = []
    for i, ex in enumerate(expl, start=start_index):
        n = narrator.narrate(ex, profile.lang, enrich=profile.mode == "analyst")
        body = n.detailed if profile.mode == "analyst" else n.short
        out.append(Overlay(
            overlay_id=f"ov_{i:04d}", match_id=match.match_id, kind="lower_third", t_start_s=ex.clock_s,
            duration_s=8.0, lang=profile.lang, priority=ex.priority,
            payload={"headline": n.short, "body": body if profile.mode == "analyst" else "",
                     "team": ex.team, "player_id": ex.player_id, "source": n.source}))
    return out


def stat_card(match: Match, stats: MatchStats, t: float, lang: str, idx: int) -> Overlay:
    lp, ls, lx = STAT_LABELS[lang]
    return Overlay(overlay_id=f"ov_{idx:04d}", match_id=match.match_id, kind="stat_card", t_start_s=t,
                   duration_s=10.0, lang=lang, priority=2,
                   payload={"title": f"{match.home_name} v {match.away_name}",
                            "rows": [{"label": lp, "home": stats.home.possession_pct, "away": stats.away.possession_pct},
                                     {"label": ls, "home": stats.home.shots, "away": stats.away.shots},
                                     {"label": lx, "home": stats.home.xg, "away": stats.away.xg}]})
