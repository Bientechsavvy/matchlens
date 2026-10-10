from matchlens.schemas.events import EventType
from matchlens.simulator.generator import MatchSimulator


def test_deterministic():
    a, b = MatchSimulator(7).generate(), MatchSimulator(7).generate()
    assert a.events == b.events and a.score == b.score


def test_different_seeds_differ():
    assert MatchSimulator(1).generate().events != MatchSimulator(2).generate().events


def test_events_valid_and_ordered():
    m = MatchSimulator(3).generate()
    assert len(m.events) > 500
    assert [e.event_id for e in m.events] == list(range(1, len(m.events) + 1))
    clocks = [e.clock_s for e in m.events if e.type != EventType.PRESSURE]
    assert clocks == sorted(clocks)
    assert all(e.player_id in m.players for e in m.events)


def test_score_matches_goal_events():
    m = MatchSimulator(11).generate()
    for side in ("home", "away"):
        goals = sum(1 for e in m.events if e.type == EventType.GOAL and e.team == side)
        assert goals == m.score[side]


def test_two_periods():
    assert {e.period for e in MatchSimulator(5).generate().events} == {1, 2}
