# MatchLens: Explainable Match Intelligence

AI agents that turn **synthetic football events** into **explainable match intelligence**: live narratives, broadcast-style overlays and match recaps, personalised by viewer type, language, favourite team and player.

Built for the **Microsoft Premier League Hackathon**.

- **Live demo:** [LIVE_URL](https://matchlens-api.salmondune-d51fb9da.eastus2.azurecontainerapps.io)
- **Repository:** https://github.com/bientechsavvy/matchlens
- **Data:** 100% synthetic. No real match footage or Premier League data is used.

## What it does

1. **Ingest** synthetic match events (passes, shots, tackles, pressure, possession changes).
2. **Interpret** them into stats, pass quality, momentum and key moments.
3. **Explain** why a moment matters (control vs chaos, momentum swings, goal context).
4. **Render** timed, machine-readable JSON overlays that sync to the match clock.
5. **Personalise** for an analyst or a casual fan, in English, Spanish or French.

## Technology

| Area | Technology | Status |
|---|---|---|
| Orchestration | Microsoft Agent Framework, six-agent workflow | built |
| AI commentary | Microsoft Foundry, `gpt-4.1-mini` deployment | built |
| Hosting | Azure Container Apps | built |
| Identity | Managed identity, no keys stored | built |
| CI/CD | GitHub Actions builds the image into GitHub Container Registry | built |
| Backend | Python 3.12, FastAPI, Pydantic, WebSockets | built |
| Frontend | Single-page HTML and JavaScript served by the API | built |
| State and events | Azure Cosmos DB, Azure Event Hubs | planned, not built |

The live feed (`/stream`, `/overlays`) runs on a plain Python pipeline. The same six steps also run as a Microsoft Agent Framework workflow, available at `GET /matches/{id}/agent-run`, and the two paths produce identical overlays (this is tested). See [Agents](docs/03-AGENTS.md).

## Quick start (Windows PowerShell)

Use Python 3.12 from python.org. The MSYS2 Python cannot install the dependencies.

```powershell
py -3.12 -m venv .venv312
.venv312\Scripts\Activate.ps1
pip install -e ".[dev,azure,agents]"
python -m pytest
python -m uvicorn matchlens.api.main:app --reload
```

Open http://localhost:8000. On Mac or Linux use `python3.12 -m venv .venv312` and `source .venv312/bin/activate`.

## Configuration

Copy `.env.example` to `.env` (never commit it) and set:

| Variable | Meaning |
|---|---|
| `USE_LLM` | `true` to let a Foundry model write the detailed commentary. Default `false` (built-in templates) |
| `FOUNDRY_ENDPOINT` | Azure OpenAI endpoint, e.g. `https://<resource>.openai.azure.com/openai/v1` (a Foundry project endpoint also works) |
| `FOUNDRY_MODEL` | the name of your model deployment |

Authentication uses your Azure login (`az login`) locally and a managed identity on Azure. The identity needs the **Cognitive Services OpenAI User** role on the Foundry resource. If anything fails, the app falls back to templates and keeps working.

## Repository layout

```
src/matchlens/
  schemas/        data contracts (Pydantic)
  simulator/      seeded synthetic match generator
  analyst/        stats, pass quality, momentum, key moments
  explainer/      rule-based explanations
  agents/         narrator, personalizer, overlay renderer
  orchestration/  pipeline, supervisor, Agent Framework workflow
  llm/            Foundry client (and the no-op client)
  api/            FastAPI app (REST, WebSocket, static frontend)
frontend/         single-page UI
tests/            30 tests, run offline
docs/             technical documentation
infra/            Bicep starter (not used for the live deployment)
.github/workflows CI and image publishing
```

## Documentation

| Doc | Purpose |
|---|---|
| [01 Architecture](docs/01-ARCHITECTURE.md) | components, data flow, decisions |
| [02 Event Schema](docs/02-EVENT-SCHEMA.md) | data contracts |
| [03 Agents](docs/03-AGENTS.md) | agent roles, handoffs, AI policy |
| [04 API](docs/04-API.md) | endpoints |
| [05 Deployment](docs/05-DEPLOYMENT.md) | how it runs on Azure, and how to update it |
| [06 Testing](docs/06-TESTING.md) | test strategy and smoke tests |
| [07 Roadmap](docs/07-ROADMAP.md) | status and next steps |
| [08 Submission Checklist](docs/08-SUBMISSION-CHECKLIST.md) | rules compliance and judging map |
| [09 Troubleshooting](docs/09-TROUBLESHOOTING.md) | problems we hit and their fixes |

## Known limitations

- Match state is held in memory, so the app runs as a single replica and a restart loses matches. Cosmos DB is the planned fix.
- Analyst mode writes one AI commentary call per moment, one after another, so it takes several seconds.
- `agent-run` ignores the favourite-team and player-focus settings.
- The public API has no authentication, so anyone with the link can start a match.

## Licence

MIT. See `LICENSE`.
