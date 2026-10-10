# 01. Architecture

## 1. Goals
1. Convert synthetic football events into explainable insight.
2. Output must be machine-readable (overlay JSON synced to the match clock) and human-readable (narratives, recaps).
3. The same intelligence reaches different viewers: analyst or casual, three languages, favourite team, player focus.
4. A deterministic, testable core. AI only enriches the text and is never required for correctness.

## 2. Logical architecture

```
Browser (frontend/index.html)
   |  REST + WebSocket
   v
FastAPI (api/main.py) ----------------------------+
   |                                              |
   |  live feed                                   |  GET /matches/{id}/agent-run
   v                                              v
Pipeline (orchestration/pipeline.py)      Agent Framework workflow
   |                                      (orchestration/agent_workflow.py)
   |   Both run the same steps and produce identical overlays:
   |   simulator -> analyst -> explainer -> personalizer -> narrator -> overlay renderer
   v
Narrator --(optional, analyst mode)--> Foundry model (gpt-4.1-mini)
```

The live feed uses `Pipeline`. The Agent Framework workflow is a second execution path over the same functions. A test asserts that both produce identical overlays.

## 3. Design decisions

| Decision | Rationale |
|---|---|
| Deterministic core, AI as enrichment | Judges must be able to run the project. If Foundry is unavailable, templates still produce valid output. |
| Structured `facts` between Explainer and Narrator | Text in any language is rendered from facts. Numbers never come from the model. |
| Pitch coordinates 0-100 | Provider-agnostic, easy to convert to metres (x*1.05, y*0.68). |
| Seeded simulator | Reproducible demos and tests. |
| Pydantic contracts | Validation at every boundary. |
| Supervisor per stage | Retry, fallback and a trace without changing agent code. |
| LLM client kept out of Agent Framework messages | The framework copies messages, and HTTP clients cannot be copied. The client lives in a registry keyed by `run_id`. |
| Personalise before narrate | The model is only called for moments the viewer will see. |

## 4. Coordinates and clock
`home` attacks toward `x = 100`, `away` toward `x = 0`. Analytics convert to team-relative x so "final third" is always `rel_x > 66`. `clock_s` runs 0 to 5400 (period 1: 0-2700, period 2: 2700-5400).

## 5. Azure mapping

| Concern | Service | Status |
|---|---|---|
| AI commentary | Microsoft Foundry model deployment (`gpt-4.1-mini`) | built |
| Orchestration | Microsoft Agent Framework workflow | built, served at `/agent-run` |
| Compute | Azure Container Apps (East US 2) | built |
| Identity | Managed identity with the Cognitive Services OpenAI User role | built, no keys stored |
| Image build | GitHub Actions to GitHub Container Registry | built |
| State | Azure Cosmos DB | planned. Today state is in memory |
| Event streaming | Azure Event Hubs | planned |
| Observability | Application Insights | planned. Today: the Container Apps log stream |

## 6. Failure handling
- Every stage runs under the Supervisor: up to 2 retries, then a template fallback where one exists, and a trace entry.
- Any Foundry error (permissions, timeout, wrong deployment) returns no text, so the template is used. The failure is logged as `Foundry call failed`.
- Invalid events sent to `POST /events` are rejected with 422 and never change state.

## 7. Limits
- In-memory state means one replica, and matches are lost on restart.
- No authentication on the public API.
- Non-goals: real video processing, real provider data, betting features.