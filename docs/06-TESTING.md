# 06. Testing

| Layer | What | Where |
|-------|------|-------|
| Unit | simulator determinism, event validity, metric maths | `tests/test_simulator.py`, `tests/test_analyst.py` |
| Pipeline | end-to-end overlays, personalisation differs by profile and language | `tests/test_pipeline.py` |
| API | endpoints via TestClient | `tests/test_api.py` |
| Phase 2 | supervisor retry/fallback, LLM failure fallback, WebSocket, ingest validation, trace | `tests/test_phase2.py` |

Quality gates: `pytest` green, `ruff check` clean, type hints on public functions.
Phase 2 adds LLM-output evaluation (Foundry evaluators): groundedness against `facts`, language correctness.
