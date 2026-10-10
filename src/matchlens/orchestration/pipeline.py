"""Pipeline orchestrator. Phase 2 replaces this with a Microsoft Agent Framework workflow."""
from __future__ import annotations

import logging

from matchlens.agents.narrator import Narrator
from matchlens.agents.overlay import moment_overlays, stat_card
from matchlens.agents.personalizer import personalize
from matchlens.analyst.metrics import compute_stats, detect_key_moments, momentum_series
from matchlens.explainer.rules import explain
from matchlens.llm.foundry_client import LLMClient, get_client
from matchlens.orchestration.workflow import Supervisor
from matchlens.schemas.events import Explanation, Match, MatchStats, Overlay, ViewerProfile

log = logging.getLogger("matchlens.pipeline")


class Analysis:
    """Immutable-by-convention analysis context shared between stages."""
    def __init__(self, match: Match):
        self.match = match
        self.stats: MatchStats = compute_stats(match)
        self.momentum = momentum_series(match)
        self.moments = detect_key_moments(match)
        self.explanations: list[Explanation] = explain(match, self.moments)


class Pipeline:
    def __init__(self, llm: LLMClient | None = None):
        self.narrator = Narrator(llm or get_client())
        self.supervisor = Supervisor()

    def analyse(self, match: Match) -> Analysis:
        return Analysis(match)

    def overlays(self, a: Analysis, profile: ViewerProfile) -> list[Overlay]:
        sv = self.supervisor
        chosen = sv.run("personalize", lambda: personalize(a.explanations, profile))
        out = sv.run("narrate_render", lambda: moment_overlays(a.match, chosen, profile, self.narrator),
                     fallback=lambda: moment_overlays(a.match, chosen, profile, Narrator()))
        if profile.mode == "analyst":
            for k, t in enumerate((900.0, 2700.0, 5400.0)):
                out.append(stat_card(a.match, stats_until(a.match, t), t, profile.lang, 1000 + k))
        return sorted(out, key=lambda o: o.t_start_s)

    def recap(self, a: Analysis, profile: ViewerProfile) -> str:
        h, w = a.match.home_name, a.match.away_name
        s, sc = a.stats, a.match.score
        goals = [self.narrator.narrate(e, profile.lang).short for e in a.explanations if e.category == "goal_context"]
        head = {"en": f"Full time: {h} {sc['home']}-{sc['away']} {w}.",
                "es": f"Final: {h} {sc['home']}-{sc['away']} {w}.",
                "fr": f"Fin du match : {h} {sc['home']}-{sc['away']} {w}."}[profile.lang]
        if profile.mode == "casual":
            return " ".join([head] + goals)
        det = {"en": f"Possession {s.home.possession_pct}%-{s.away.possession_pct}%, xG {s.home.xg}-{s.away.xg}, shots {s.home.shots}-{s.away.shots}.",
               "es": f"Posesión {s.home.possession_pct}%-{s.away.possession_pct}%, xG {s.home.xg}-{s.away.xg}, tiros {s.home.shots}-{s.away.shots}.",
               "fr": f"Possession {s.home.possession_pct}%-{s.away.possession_pct}%, xG {s.home.xg}-{s.away.xg}, tirs {s.home.shots}-{s.away.shots}."}[profile.lang]
        return " ".join([head, det] + goals)
    

def stats_until(match, t):
    """Team stats using only events up to clock time t (for in-match stat cards)."""
    ev = [e for e in match.events if e.clock_s <= t]
    score = {s: sum(e.type.value == "goal" and e.team == s for e in ev) for s in ("home", "away")}
    return compute_stats(match.model_copy(update={"events": ev, "score": score}))
