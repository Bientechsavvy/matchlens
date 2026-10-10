"""Personalizer: ranks and filters explanations per ViewerProfile."""
from __future__ import annotations

from matchlens.schemas.events import Explanation, ViewerProfile


def personalize(explanations: list[Explanation], profile: ViewerProfile) -> list[Explanation]:
    selected = []
    for ex in explanations:
        if profile.focus_player and ex.player_id != profile.focus_player and ex.category != "goal_context":
            continue
        boost = 1 if profile.favourite_team and ex.team == profile.favourite_team else 0
        selected.append((min(5, ex.priority + boost), ex))
    if profile.mode == "casual":  # casual fans get fewer, bigger moments
        selected = [(p, e) for p, e in selected if p >= 4 or e.category == "goal_context"]
    selected.sort(key=lambda pe: (-pe[0], pe[1].clock_s))
    top = selected[: profile.max_overlays]
    return [e.model_copy(update={"priority": p}) for p, e in sorted(top, key=lambda pe: pe[1].clock_s)]
