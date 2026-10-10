import pytest
from fastapi.testclient import TestClient

from matchlens.api.main import app
from matchlens.llm.foundry_client import NullClient, get_client
from matchlens.orchestration.pipeline import Pipeline
from matchlens.orchestration.workflow import Supervisor
from matchlens.schemas.events import ViewerProfile
from matchlens.simulator.generator import MatchSimulator

c = TestClient(app)


def test_supervisor_retry_then_ok():
    calls = []

    def flaky():
        calls.append(1)
        if len(calls) < 2:
            raise RuntimeError("boom")
        return "ok"
    sv = Supervisor(retries=2)
    assert sv.run("s", flaky) == "ok" and sv.trace[-1]["status"] == "retried"


def test_supervisor_fallback_and_failure():
    sv = Supervisor(retries=1)

    def bad():
        raise RuntimeError("x")
    assert sv.run("s", bad, fallback=lambda: "fb") == "fb" and sv.trace[-1]["status"] == "fallback"
    with pytest.raises(RuntimeError):
        sv.run("s", bad)


def test_llm_enrichment_and_failure_fallback():
    class Good:
        def complete(self, s, p):
            return "LLM text"

    a = Pipeline(Good())
    an = a.analyse(MatchSimulator(42).generate())
    ov = a.overlays(an, ViewerProfile(mode="analyst"))
    assert any(o.payload.get("source") == "llm" for o in ov if o.kind == "lower_third")

    class Broken:
        def complete(self, s, p):
            raise RuntimeError("down")
    b = Pipeline(Broken())
    ov = b.overlays(an, ViewerProfile(mode="analyst"))
    assert all(o.payload["source"] == "template" for o in ov if o.kind == "lower_third")
    assert b.supervisor.trace[-1]["status"] == "fallback"


def test_get_client_defaults_to_null(monkeypatch):
    monkeypatch.delenv("USE_LLM", raising=False)
    assert isinstance(get_client(), NullClient)
    monkeypatch.setenv("USE_LLM", "true")
    monkeypatch.delenv("FOUNDRY_ENDPOINT", raising=False)
    assert isinstance(get_client(), NullClient)


def test_websocket_stream():
    mid = c.post("/matches", json={"seed": 42}).json()["match_id"]
    with c.websocket_connect(f"/matches/{mid}/stream?speed=1000000&lang=es") as ws:
        frames = []
        while True:
            f = ws.receive_json()
            frames.append(f)
            if f["type"] == "end":
                break
    assert len(frames) > 2 and frames[0]["overlay"]["lang"] == "es"


def test_ingest_validates_and_updates():
    mid = c.post("/matches", json={"seed": 9}).json()["match_id"]
    ev = {"event_id": 99999, "match_id": mid, "clock_s": 100, "period": 1, "type": "goal",
          "team": "home", "player_id": "home_9", "x": 100, "y": 50, "outcome": "goal", "xg": 0.5}
    before = c.get(f"/matches/{mid}/moments").json()["moments"]
    r = c.post(f"/matches/{mid}/events", json=[ev]).json()
    assert r["accepted"] == 1
    assert len(c.get(f"/matches/{mid}/moments").json()["moments"]) == len(before) + 1
    assert c.post(f"/matches/{mid}/events", json=[ev]).status_code == 422
    assert c.post(f"/matches/{mid}/events", json=[dict(ev, event_id=1, player_id="x")]).status_code == 422


def test_trace_and_index():
    mid = c.post("/matches", json={"seed": 3}).json()["match_id"]
    c.get(f"/matches/{mid}/overlays")
    assert c.get(f"/matches/{mid}/trace").json()["trace"]
    assert "MatchLens" in c.get("/").text
