"""FastAPI app. See docs/04-API.md."""
from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from pydantic import BaseModel

from matchlens.orchestration.pipeline import Analysis, Pipeline
from matchlens.schemas.events import SCHEMA_VERSION, EventType, MatchEvent, ViewerProfile
from matchlens.simulator.generator import MatchSimulator

app = FastAPI(title="MatchLens", version="0.1.0")
pipeline = Pipeline()
STORE: dict[str, Analysis] = {}


class NewMatch(BaseModel):
    seed: int = 42
    home: str = "Northbridge FC"
    away: str = "Eastport United"


def _get(match_id: str) -> Analysis:
    if match_id not in STORE:
        raise HTTPException(404, "unknown match")
    return STORE[match_id]


@app.get("/health")
def health():
    return {"status": "ok", "schema_version": SCHEMA_VERSION}


@app.post("/matches")
def create_match(body: NewMatch | None = None):
    body = body or NewMatch()
    m = MatchSimulator(body.seed, body.home, body.away).generate()
    STORE[m.match_id] = pipeline.analyse(m)
    return {"match_id": m.match_id, "score": m.score, "event_count": len(m.events)}


@app.get("/matches/{match_id}/stats")
def stats(match_id: str):
    a = _get(match_id)
    return {"schema_version": SCHEMA_VERSION, "stats": a.stats, "momentum": a.momentum}


@app.get("/matches/{match_id}/moments")
def moments(match_id: str):
    a = _get(match_id)
    return {"schema_version": SCHEMA_VERSION, "moments": a.moments, "explanations": a.explanations}


@app.get("/matches/{match_id}/overlays")
def overlays(match_id: str, mode: Literal["analyst", "casual"] = "casual", lang: Literal["en", "es", "fr"] = "en",
             favourite_team: Literal["home", "away"] | None = None, focus_player: str | None = None,
             max_overlays: int = 25):
    a = _get(match_id)
    p = ViewerProfile(mode=mode, lang=lang, favourite_team=favourite_team, focus_player=focus_player,
                      max_overlays=max_overlays)
    return {"schema_version": SCHEMA_VERSION, "overlays": pipeline.overlays(a, p)}


@app.get("/matches/{match_id}/recap")
def recap(match_id: str, mode: Literal["analyst", "casual"] = "casual", lang: Literal["en", "es", "fr"] = "en"):
    a = _get(match_id)
    return {"recap": pipeline.recap(a, ViewerProfile(mode=mode, lang=lang))}


FRONTEND = Path(os.getenv("FRONTEND_DIR", Path(__file__).resolve().parents[3] / "frontend"))


@app.get("/", include_in_schema=False)
def index():
    f = FRONTEND / "index.html"
    return FileResponse(f) if f.exists() else {"service": "matchlens", "docs": "/docs"}


@app.get("/matches/{match_id}/trace")
def trace(match_id: str):
    _get(match_id)
    return {"trace": list(pipeline.supervisor.trace)}


@app.post("/matches/{match_id}/events")
def ingest(match_id: str, events: list[MatchEvent]):
    """Ingest external synthetic events (validated by schema) and re-analyse."""
    m = _get(match_id).match
    seen = {e.event_id for e in m.events}
    bad = [e.event_id for e in events
           if e.match_id != match_id or e.player_id not in m.players or e.event_id in seen]
    if bad:
        raise HTTPException(422, f"rejected events (wrong match, unknown player or duplicate id): {bad}")
    allev = sorted(m.events + events, key=lambda e: (e.clock_s, e.event_id))
    score = {s: sum(e.type == EventType.GOAL and e.team == s for e in allev) for s in ("home", "away")}
    STORE[match_id] = pipeline.analyse(m.model_copy(update={"events": allev, "score": score}))
    return {"accepted": len(events), "event_count": len(allev), "score": score}


@app.websocket("/matches/{match_id}/stream")
async def stream(ws: WebSocket, match_id: str, mode: str = "casual", lang: str = "en",
                 favourite_team: str | None = None, focus_player: str | None = None,
                 speed: float = 60.0):
    """Push overlays as the (accelerated) match clock reaches them."""
    await ws.accept()
    try:
        profile = ViewerProfile(mode=mode, lang=lang, favourite_team=favourite_team or None,
                                focus_player=focus_player or None)
    except Exception:
        return await ws.close(code=4400)
    if match_id not in STORE or speed <= 0:
        return await ws.close(code=4404)
    prev = 0.0
    try:
        for o in pipeline.overlays(STORE[match_id], profile):
            await asyncio.sleep(max(0.0, (o.t_start_s - prev) / speed))
            prev = o.t_start_s
            await ws.send_json({"type": "overlay", "overlay": o.model_dump()})
        await ws.send_json({"type": "end"})
        await ws.close()
    except WebSocketDisconnect:
        pass


@app.get("/matches/{match_id}/agent-run")
async def agent_run(match_id: str, mode: Literal["analyst", "casual"] = "casual",
                    lang: Literal["en", "es", "fr"] = "en"):
    """Run the multi-agent workflow (Microsoft Agent Framework) and return its handoffs and trace."""
    a = _get(match_id)
    try:
        from matchlens.orchestration.agent_workflow import run_agents
    except ImportError:
        raise HTTPException(501, "Install the agents extra: pip install -e '.[agents]'")
    job = await run_agents(ViewerProfile(mode=mode, lang=lang), match=a.match,
                           llm=pipeline.narrator.llm)
    return {"agents": job.handoffs, "trace": list(job.sv.trace), "overlays": job.overlays}