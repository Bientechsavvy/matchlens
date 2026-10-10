# 03. Agents

Each agent has one responsibility, a typed input and output, and a deterministic fallback.

| Agent | Input | Output | LLM use (Phase 2) | Fallback |
|-------|-------|--------|-------------------|----------|
| **Event Simulator** | seed, team names | `Match` | optional: scenario/"story arc" prompts | pure code |
| **Analyst** | `Match` | `MatchStats`, momentum series, `KeyMoment[]` | none (math) | n/a |
| **Explainer** | moments + analytics | `Explanation[]` | enrich reasoning text | rule engine |
| **Narrator** | `Explanation`, lang | `Narration{short, detailed}` | natural, fluent multi-language text | EN/ES/FR templates |
| **Personalizer** | narrations + `ViewerProfile` | ranked, shaped narrations | tone adaptation | filter/rank rules |
| **Overlay Renderer** | shaped narrations + analytics | `Overlay[]` | none | n/a |

## Handoffs
Simulator -> Analyst -> Explainer -> Personalizer -> Narrator -> Overlay Renderer. Personalizing before narrating means the LLM is only called for moments the viewer will actually see. Shared state is the immutable `Match` plus an `AnalysisContext` that is passed forward. Each stage appends results and never mutates earlier results.

## Control vs chaos
Over the 5 minutes before a moment, `turnovers_per_min` (possession changes) is computed. `<= 1.2` is labelled **control**, otherwise **chaos**. The label feeds the explanation.

## ViewerProfile

| Field | Values |
|-------|--------|
| `mode` | `analyst`, `casual` |
| `lang` | `en`, `es`, `fr` (extensible) |
| `favourite_team` | `home`, `away`, null |
| `focus_player` | player_id or null (player-focus mode) |
| `max_overlays` | int cap on density |

Personalisation rules:
- **casual**: short text, no numbers beyond the scoreline, no stat cards.
- **analyst**: detailed text with xG, momentum, turnovers per min, and stat cards.
- **favourite_team**: that team's moments get +1 priority.
- **focus_player**: only moments involving that player (plus goals) are shown.

## Phase 2: supervisor and Microsoft Agent Framework mapping
**Implemented:** `orchestration/workflow.py` `Supervisor` gives every stage retry (max 2), template fallback and a trace. `FoundryClient` enriches narration and returns `None` on any error, which triggers the template path.
**Implemented:** `orchestration/agent_workflow.py` runs the six agents as Microsoft Agent Framework executors chained with `WorkflowBuilder`, exposed at `GET /matches/{id}/agent-run`. The agents are deterministic functions; only the Narrator calls a model. Next step: Foundry-hosted `Agent` objects for the Explainer.

Each agent becomes an Agent Framework agent with a Foundry-hosted model. The pipeline becomes a workflow with A2A handoffs. A supervisor retries failed stages and routes to the template fallback. This targets the *Best Multi-Agent System* category.
