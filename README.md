# MatchLens: Explainable Match Intelligence

AI agents that turn **synthetic football events** into **explainable match intelligence**: live narratives, broadcast-ready overlays and automated recaps, personalised per viewer and language.

Built for the **Microsoft Premier League Hackathon** (submission deadline: **27 Oct 2026, 11:59 pm PT**).

## The five-stage pipeline

| # | Stage | Module | Output |
|---|-------|--------|--------|
| 1 | Ingest | `simulator/`, `orchestration/` | validated `MatchEvent` stream |
| 2 | Interpret | `analyst/` | stats, pass quality, momentum, key moments |
| 3 | Explain | `explainer/` | structured *why it matters* facts |
| 4 | Render | `agents/overlay.py` | timed, machine-readable JSON overlays |
| 5 | Personalise | `agents/personalizer.py`, `agents/narrator.py` | per-viewer, per-language output |

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest                                   # run tests
python scripts/demo.py                   # generate a match + print overlays
uvicorn matchlens.api.main:app --reload  # start API on :8000
```

## Documentation

| Doc | Purpose |
|-----|---------|
| [01 Architecture](docs/01-ARCHITECTURE.md) | components, data flow, design decisions |
| [02 Event Schema](docs/02-EVENT-SCHEMA.md) | the data contract for events, moments, overlays |
| [03 Agents](docs/03-AGENTS.md) | agent roles, inputs, outputs, handoffs, failure handling |
| [04 API](docs/04-API.md) | REST endpoints |
| [05 Deployment](docs/05-DEPLOYMENT.md) | Azure services, environment, CI/CD |
| [06 Testing](docs/06-TESTING.md) | test strategy and quality gates |
| [07 Roadmap](docs/07-ROADMAP.md) | week-by-week plan and status |
| [08 Submission Checklist](docs/08-SUBMISSION-CHECKLIST.md) | rules compliance and judging map |

## Repository layout

```
src/matchlens/
  schemas/        pydantic data contracts
  simulator/      synthetic match generator (seeded, deterministic)
  analyst/        metrics, momentum, key-moment detection
  explainer/      rule-based explanation engine
  agents/         narrator, personalizer, overlay renderer
  orchestration/  pipeline (swappable for Microsoft Agent Framework)
  llm/            Foundry client interface
  api/            FastAPI app
tests/  docs/  frontend/  infra/  scripts/  data/
```

## Status

Phase 1 complete. Phase 2 partial: Foundry client, supervised workflow, WebSocket stream, event ingest, frontend (open `/`), Dockerfile, CI, Bicep starter.
Microsoft Agent Framework workflow built (`GET /matches/{id}/agent-run`). Not yet built: Event Hubs, Cosmos DB. See the [roadmap](docs/07-ROADMAP.md).

## Licence

MIT. All match data is **synthetic**. No real match footage or Premier League data is used (Rules §4.7).
