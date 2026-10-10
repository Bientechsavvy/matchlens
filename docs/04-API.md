# 04. API

Base URL (local): `http://localhost:8000`. OpenAPI docs at `/docs`.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | liveness |
| POST | `/matches` | generate a synthetic match `{seed?, home?, away?}` returns `{match_id, score, event_count}` |
| GET | `/matches/{id}/stats` | team stats and momentum series |
| GET | `/matches/{id}/moments` | key moments with explanations |
| GET | `/matches/{id}/overlays` | overlays; query: `mode, lang, favourite_team, focus_player, max_overlays` |
| GET | `/matches/{id}/recap` | full-time recap; query: `mode, lang` |

## Errors
`404` unknown match, `422` validation error (standard FastAPI body).

## Phase 2 endpoints (implemented)
- `WS /matches/{id}/stream?mode=&lang=&favourite_team=&focus_player=&speed=60`: frames `{type:"overlay", overlay}` then `{type:"end"}`. Close codes: 4400 bad profile, 4404 unknown match.
- `POST /matches/{id}/events`: body is a list of `MatchEvent`; 422 on wrong match, unknown player or duplicate id. Re-runs analysis.
- `GET /matches/{id}/trace`: supervisor trace (`stage, status ok|retried|fallback|failed, attempts, ms`).
- `GET /`: the frontend (`frontend/index.html`, override directory with `FRONTEND_DIR`).