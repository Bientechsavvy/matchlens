"""Multi-agent workflow on Microsoft Agent Framework (see docs/03-AGENTS.md).

Six executors, each a specialised agent with one role, hand a shared Job along a chain:
simulator -> analyst -> explainer -> personalizer -> narrator -> overlay_renderer
Every agent runs under the Supervisor (retry, fallback, trace).
"""
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from agent_framework import WorkflowBuilder, WorkflowContext, executor

from matchlens.agents.narrator import Narrator
from matchlens.agents.overlay import moment_overlays, stat_card
from matchlens.agents.personalizer import personalize
from matchlens.analyst.metrics import compute_stats, detect_key_moments, momentum_series
from matchlens.explainer.rules import explain
from matchlens.orchestration.pipeline import stats_until
from matchlens.orchestration.workflow import Supervisor
from matchlens.schemas.events import Match, ViewerProfile
from matchlens.simulator.generator import MatchSimulator


# The Agent Framework copies every message passed between agents. Objects such as an HTTP/LLM
# client cannot be copied, so the Job carries only a run_id and the client lives in this registry.
_LLM_REGISTRY: dict[str, Any] = {}


@dataclass
class Job:
    profile: ViewerProfile
    match: Optional[Match] = None
    seed: int = 42
    run_id: str = ""
    sv: Supervisor = field(default_factory=Supervisor)
    stats: Any = None
    momentum: list = field(default_factory=list)
    moments: list = field(default_factory=list)
    explanations: list = field(default_factory=list)
    chosen: list = field(default_factory=list)
    overlays: list = field(default_factory=list)
    handoffs: list = field(default_factory=list)


@executor(id="simulator")
async def simulator(job: Job, ctx: WorkflowContext[Job]) -> None:
    if job.match is None:
        job.match = job.sv.run("simulator", lambda: MatchSimulator(job.seed).generate())
    job.handoffs.append("simulator")
    await ctx.send_message(job)


@executor(id="analyst")
async def analyst(job: Job, ctx: WorkflowContext[Job]) -> None:
    job.stats = job.sv.run("analyst", lambda: compute_stats(job.match))
    job.momentum = momentum_series(job.match)
    job.moments = detect_key_moments(job.match)
    job.handoffs.append("analyst")
    await ctx.send_message(job)


@executor(id="explainer")
async def explainer(job: Job, ctx: WorkflowContext[Job]) -> None:
    job.explanations = job.sv.run("explainer", lambda: explain(job.match, job.moments))
    job.handoffs.append("explainer")
    await ctx.send_message(job)


@executor(id="personalizer")
async def personalizer(job: Job, ctx: WorkflowContext[Job]) -> None:
    job.chosen = job.sv.run("personalizer", lambda: personalize(job.explanations, job.profile))
    job.handoffs.append("personalizer")
    await ctx.send_message(job)


@executor(id="narrator")
async def narrator(job: Job, ctx: WorkflowContext[Job]) -> None:
    job.overlays = job.sv.run(
        "narrator",
        lambda: moment_overlays(job.match, job.chosen, job.profile, Narrator(_LLM_REGISTRY.get(job.run_id))),
        fallback=lambda: moment_overlays(job.match, job.chosen, job.profile, Narrator()))
    job.handoffs.append("narrator")
    await ctx.send_message(job)


@executor(id="overlay_renderer")
async def overlay_renderer(job: Job, ctx: WorkflowContext[Job, Job]) -> None:
    if job.profile.mode == "analyst":
        for k, t in enumerate((900.0, 2700.0, 5400.0)):
            job.overlays.append(stat_card(job.match, stats_until(job.match, t), t,
                                          job.profile.lang, 1000 + k))
    job.overlays.sort(key=lambda o: o.t_start_s)
    job.handoffs.append("overlay_renderer")
    await ctx.yield_output(job)


def build_workflow():
    return (WorkflowBuilder(start_executor=simulator)
            .add_chain([simulator, analyst, explainer, personalizer, narrator, overlay_renderer])
            .build())


async def run_agents(profile: ViewerProfile, match: Optional[Match] = None, seed: int = 42,
                     llm: Any = None) -> Job:
    run_id = uuid.uuid4().hex
    _LLM_REGISTRY[run_id] = llm
    try:
        result = await build_workflow().run(Job(profile=profile, match=match, seed=seed, run_id=run_id))
    finally:
        _LLM_REGISTRY.pop(run_id, None)
    return result.get_outputs()[0]