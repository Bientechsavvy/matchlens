# 03. Agents

Each agent has one responsibility, a typed input and output, and a deterministic fallback.

| Agent | Input | Output | Uses a model? |
|---|---|---|---|
| **Simulator** | seed | `Match` | no |
| **Analyst** | `Match` | stats, momentum series, key moments | no |
| **Explainer** | key moments | `Explanation[]` with language-neutral facts | no (rules) |
| **Personalizer** | explanations, `ViewerProfile` | the moments this viewer should see | no |
| **Narrator** | explanation, language | short headline and detailed text | yes, in analyst mode only |
| **Overlay Renderer** | narrations, stats | timed `Overlay[]` | no |

## Handoff order
Simulator -> Analyst -> Explainer -> Personalizer -> Narrator -> Overlay Renderer. Personalizing before narrating means the model is only called for moments the viewer will actually see.

## Two execution paths
1. **Pipeline** (`orchestration/pipeline.py`): used by the live feed (`/overlays`, `/stream`).
2. **Agent Framework workflow** (`orchestration/agent_workflow.py`): the same six steps as Microsoft Agent Framework executors chained with `WorkflowBuilder`, served at `GET /matches/{id}/agent-run`. It returns the handoff order, the supervisor trace and the overlays.

A test asserts both paths return identical overlays. The Simulator step is skipped when a match already exists.

### Why the model client is not in the workflow message
The framework copies every message passed between agents. A Foundry client holds network connections and cannot be copied, so the message carries only a `run_id` and the client sits in a registry that is cleared after each run.

## Supervisor
`orchestration/workflow.py` wraps each stage with up to 2 retries, an optional fallback and a trace entry (`stage`, `status` of `ok`, `retried`, `fallback` or `failed`, `attempts`, `ms`). The Narrator falls back to template text. Only stages run through the supervisor appear in the trace (analyst, explainer, personalizer, narrator).

## AI policy
- The model receives only structured facts and writes the detailed text. Headlines, the recap and every number come from code.
- AI is used only in **analyst** mode, because casual mode shows headlines only.
- Calls are made one after another, with a 10 second timeout each. Any failure returns no text and the template is used.
- `payload.source` records `llm` or `template` for each overlay.

## ViewerProfile

| Field | Values |
|---|---|
| `mode` | `analyst` or `casual` |
| `lang` | `en`, `es`, `fr` |
| `favourite_team` | `home`, `away` or none |
| `focus_player` | a player id such as `home_9`, or none |
| `max_overlays` | density cap, default 25 |

Rules:
- **casual**: only goals and priority 4-5 moments, headlines only, no stat cards.
- **analyst**: all moments with detailed text, plus three stat cards.
- **favourite team**: its moments get +1 priority.
- **focus player**: only that player's moments plus all goals.

## Known limitations
- `agent-run` uses only `mode` and `lang`, not the favourite-team or player-focus settings.
- Analyst-mode commentary is sequential, so it takes several seconds for a full match.