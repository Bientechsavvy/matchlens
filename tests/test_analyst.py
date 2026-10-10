from matchlens.analyst.metrics import (
    compute_stats,
    detect_key_moments,
    momentum_series,
    pass_quality,
)
from matchlens.schemas.events import EventType
from matchlens.simulator.generator import MatchSimulator

M = MatchSimulator(42).generate()


def test_possession_sums_to_100():
    s = compute_stats(M)
    assert abs(s.home.possession_pct + s.away.possession_pct - 100) < 0.2


def test_stats_consistent():
    s = compute_stats(M)
    assert s.home.goals == M.score["home"] and s.home.shots >= s.home.goals
    assert 0 < s.home.pass_accuracy_pct <= 100


def test_pass_quality_bounds():
    for e in [e for e in M.events if e.type == EventType.PASS][:200]:
        q = pass_quality(e)
        assert 0 <= q.difficulty <= 1 and q.distance_m >= 0


def test_momentum_bounds():
    assert all(-1 <= v <= 1 for _, v in momentum_series(M))


def test_key_moments_include_all_goals():
    goals = [m for m in detect_key_moments(M) if m.kind == "goal"]
    assert len(goals) == sum(M.score.values())
