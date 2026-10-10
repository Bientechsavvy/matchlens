from matchlens.orchestration.pipeline import Pipeline
from matchlens.schemas.events import ViewerProfile
from matchlens.simulator.generator import MatchSimulator

P = Pipeline()
A = P.analyse(MatchSimulator(42).generate())


def test_overlays_sorted_and_valid():
    ov = P.overlays(A, ViewerProfile(mode="analyst"))
    assert ov and [o.t_start_s for o in ov] == sorted(o.t_start_s for o in ov)
    assert all(o.duration_s > 0 for o in ov)


def test_modes_differ():
    cas = P.overlays(A, ViewerProfile(mode="casual"))
    ana = P.overlays(A, ViewerProfile(mode="analyst"))
    assert len(ana) >= len(cas)
    assert any(o.kind == "stat_card" for o in ana) and not any(o.kind == "stat_card" for o in cas)


def test_language_changes_text():
    en = P.overlays(A, ViewerProfile(lang="en"))[0].payload["headline"]
    es = P.overlays(A, ViewerProfile(lang="es"))[0].payload["headline"]
    fr = P.overlays(A, ViewerProfile(lang="fr"))[0].payload["headline"]
    assert len({en, es, fr}) == 3


def test_focus_player_filters():
    goal = next(e for e in A.explanations if e.category == "goal_context")
    ov = P.overlays(A, ViewerProfile(mode="analyst", focus_player="nobody"))
    ids = {o.payload.get("player_id") for o in ov if o.kind == "lower_third"}
    assert ids <= {e.player_id for e in A.explanations if e.category == "goal_context"} | {None}
    assert goal


def test_recap_contains_score():
    r = P.recap(A, ViewerProfile(mode="analyst"))
    assert f"{A.match.score['home']}-{A.match.score['away']}" in r
