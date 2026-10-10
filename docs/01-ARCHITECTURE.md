# 01. Architecture

## 1. Goals
1. Convert raw synthetic football events into explainable insight in near real time.
2. Output must be **machine-readable** (overlay JSON synced to the match clock) and **human-readable** (narratives, recaps).
3. Same intelligence, different experiences: analyst vs casual fan, any language, favourite club, player focus.
4. Deterministic and testable core, with LLMs layered on top (never required for correctness).

## 2. Logical architecture

```
            +-------------------+
            |  Event Simulator  |  seeded, football-realistic
            +---------+---------+
                      | MatchEvent stream
                      v
 +--------------------+--------------------+
 |              Orchestrator               |  Phase 1: pipeline.py
 |   (Microsoft Agent Framework in Phase 2)|  Phase 2: Agent Framework
 +--+---------+----------+---------+-------+
    |         |          |         |
    v         v          v         v
 Analyst   Explainer   Narrator  Personalizer --> Overlay Renderer
 (metrics) (why)       (text/i18n) (viewer)       (JSON overlays)
                                                     |
                                                     v
                                   REST API / WebSocket --> React frontend
```

## 3. Design decisions

| Decision | Rationale |
|----------|-----------|
| Deterministic core, LLM enrichment | Judges must be able to run the project reliably. If Foundry is unavailable, templates produce valid output. |
| Structured `facts` between Explainer and Narrator | Narration in any language is rendered from facts. No hallucinated numbers. |
| Pitch coordinates 0-100 (x along the pitch, y across) | Provider-agnostic, easy to convert to metres (x*1.05, y*0.68). |
| Seeded simulator | Reproducible demos, tests and video recordings. |
| Pydantic contracts | Validation at every boundary, auto-generated JSON Schema and OpenAPI. |
| Pipeline behind one interface (`run`) | Swap in Agent Framework without touching agents. |
| Overlay = `{t_start_s, duration_s, kind, payload}` | Rendering partner can schedule against the live clock. |

## 4. Coordinate system
Absolute pitch coordinates: `home` attacks toward `x = 100`, `away` attacks toward `x = 0`. Analytics convert to **team-relative** x (`x` for home, `100 - x` for away) so "final third" is always `rel_x > 66`.

## 5. Clock model
`clock_s` = seconds since kickoff (0-5400). Period 1: 0-2700, period 2: 2700-5400. Overlays reference `clock_s`; a live feed maps its own match clock to this value.

## 6. Azure mapping (target state)

| Concern | Service |
|---------|---------|
| LLM + agent management | Microsoft Foundry |
| Orchestration | Microsoft Agent Framework (A2A handoffs) |
| Event streaming | Azure Event Hubs |
| Compute | Azure Container Apps (API), Azure Functions (stream processors) |
| State | Azure Cosmos DB (match state, overlays) |
| Observability | Application Insights / OpenTelemetry |
| Secrets | Azure Key Vault + managed identity |

## 7. Failure handling
- Each agent call is wrapped with timeout + retry (max 2) and a deterministic fallback.
- LLM failure results in template narration (`source: "template"` flag in payload).
- Invalid events are rejected at ingest and counted in metrics. They never crash the pipeline.

## 8. Non-goals
Real broadcast video processing, real provider data, betting or odds features.