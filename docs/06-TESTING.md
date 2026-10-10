# 06. Testing

30 tests, all offline, finishing in a few seconds.

| Area | What it checks | File |
|---|---|---|
| Simulator | deterministic output, valid and ordered events, score matches goal events | `test_simulator.py` |
| Analyst | possession, stat consistency, pass quality bounds, momentum bounds, all goals become key moments | `test_analyst.py` |
| Pipeline | overlays sorted, modes differ, languages differ, focus filter, recap, stat cards grow over time | `test_pipeline.py` |
| API | endpoint flow, 404 and 422 | `test_api.py` |
| Resilience | supervisor retry and fallback, AI failure falls back to templates, WebSocket stream, event ingest validation, trace, casual mode makes no model calls | `test_phase2.py` |
| Agents | six agents run in order, same overlays as the pipeline, simulate from a seed, `/agent-run`, an uncopyable model client works | `test_agents.py` |

## Offline by design
`tests/conftest.py` sets `USE_LLM=false` and stops `.env` from loading. Without it, a developer's `.env` makes the tests call the real model, which is slow, costs money and gives different text each run.

## Running
```powershell
python -m pytest
ruff check src tests
```

## Smoke test of the live deployment

1. `GET /health` returns `{"status":"ok"}`.
2. Open the address, set Viewer to **Analyst**, clear Player focus, press Kick off. Goal cards should show the **AI commentary** tag.
3. Press **Show agent run**. Six agents should appear in order with timings.
4. Switch to Español and Kick off again. Headlines should be in Spanish.