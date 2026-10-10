# 04. API

Local base URL: `http://localhost:8000`. Interactive docs at `/docs`. The same routes are served on the Azure address.

| Method | Path | Description |
|---|---|---|
| GET | `/` | the frontend |
| GET | `/health` | liveness and schema version |
| POST | `/matches` | generate a synthetic match. Body `{seed?, home?, away?}`. Returns `{match_id, score, event_count}` |
| GET | `/matches/{id}/stats` | team stats and the momentum series |
| GET | `/matches/{id}/moments` | key moments with explanations |
| GET | `/matches/{id}/overlays` | overlays. Query: `mode`, `lang`, `favourite_team`, `focus_player`, `max_overlays` |
| GET | `/matches/{id}/recap` | full-time recap text. Query: `mode`, `lang` |
| GET | `/matches/{id}/trace` | supervisor trace |
| POST | `/matches/{id}/events` | ingest external synthetic events (list of `MatchEvent`) |
| GET | `/matches/{id}/agent-run` | run the Agent Framework workflow. Query: `mode`, `lang`. Returns `{agents, trace, overlays}` |
| WS | `/matches/{id}/stream` | live overlays |

## WebSocket
`WS /matches/{id}/stream?mode=&lang=&favourite_team=&focus_player=&speed=60`

Frames: `{"type": "overlay", "overlay": {...}}` for each overlay, then `{"type": "end"}`. `speed` is the multiple of real time.
Close codes: `4400` invalid profile, `4404` unknown match or speed not above 0.

## Event ingest
`POST /matches/{id}/events` accepts a JSON list of events. It returns 422 if an event has the wrong `match_id`, an unknown `player_id` or an `event_id` that already exists. Accepted events are merged and the analysis is rerun.

## Errors
`404` unknown match. `422` validation error. `501` from `agent-run` if the Agent Framework package is not installed. `500` on an unexpected error (check the server log).

## Example (PowerShell)

```powershell
$base = "http://localhost:8000"
Invoke-RestMethod -Method Post -Uri "$base/matches" -ContentType "application/json" -Body '{"seed":42}'
Invoke-RestMethod "$base/matches/m_42/agent-run?mode=analyst&lang=en"
```

## Notes
Matches live in memory, so a restart removes them. Call `POST /matches` again after a restart.