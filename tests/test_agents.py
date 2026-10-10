import asyncio

import pytest

pytest.importorskip("agent_framework")

from fastapi.testclient import TestClient  # noqa: E402

from matchlens.api.main import app  # noqa: E402
from matchlens.orchestration.agent_workflow import run_agents  # noqa: E402
from matchlens.orchestration.pipeline import Pipeline  # noqa: E402
from matchlens.schemas.events import ViewerProfile  # noqa: E402
from matchlens.simulator.generator import MatchSimulator  # noqa: E402

ORDER = ["simulator", "analyst", "explainer", "personalizer", "narrator", "overlay_renderer"]


def test_agents_hand_off_in_order_and_match_pipeline():
    m = MatchSimulator(42).generate()
    p = ViewerProfile(mode="analyst", lang="es")
    job = asyncio.run(run_agents(p, match=m))
    pl = Pipeline()
    ref = pl.overlays(pl.analyse(m), p)
    assert job.handoffs == ORDER
    assert [o.model_dump() for o in job.overlays] == [o.model_dump() for o in ref]


def test_agents_can_simulate_from_seed():
    job = asyncio.run(run_agents(ViewerProfile(), seed=7))
    assert job.match.match_id == "m_7" and job.overlays


def test_agent_run_endpoint():
    c = TestClient(app)
    mid = c.post("/matches", json={"seed": 42}).json()["match_id"]
    r = c.get(f"/matches/{mid}/agent-run", params={"mode": "analyst"}).json()
    assert r["agents"] == ORDER and r["trace"] and r["overlays"]

def test_agents_accept_unshareable_llm_client():
    import threading

    class Holder:  # like a real HTTP client: it cannot be copied or pickled
        def __init__(self):
            self.lock = threading.Lock()

        def complete(self, system, prompt):
            return "AI text"

    job = asyncio.run(run_agents(ViewerProfile(mode="analyst"), seed=7, llm=Holder()))
    assert any(o.payload.get("source") == "llm" for o in job.overlays if o.kind == "lower_third")    