# 02. Event Schema (Data Contract)

Source of truth: `src/matchlens/schemas/events.py`.

## MatchEvent

| Field | Type | Notes |
|-------|------|-------|
| `event_id` | int | monotonic, unique per match |
| `match_id` | str | |
| `clock_s` | float | seconds since kickoff |
| `period` | int | 1 or 2 |
| `type` | enum | `kickoff, pass, shot, goal, tackle, possession_change, pressure` |
| `team` | `home`/`away` | acting team |
| `player_id` | str | e.g. `home_7` |
| `x`, `y` | float 0-100 | event start (absolute pitch coords) |
| `end_x`, `end_y` | float? | pass/shot end |
| `outcome` | enum | `success, fail, goal, saved, off_target, none` |
| `ball_speed_kmh` | float? | passes and shots |
| `xg` | float? | shots only |
| `pressure_level` | float 0-1? | opposition pressure at event time |

## Derived: PassQuality
`distance_m`, `difficulty` (0-1), `forward_m`, `accurate` (bool).
Difficulty = 0.15 + distance/60 + 0.5 x pressure + 0.15 if ending in the final third (clipped 0-1).

## Derived: KeyMoment
`moment_id, kind (goal|big_chance|momentum_shift), clock_s, team, player_id, xg?, momentum_before?, momentum_after?`

## Derived: Explanation
`moment_id, category, priority (1-5), facts{}`. Facts are language-neutral values (team side, player name, minute, xg, control label, turnovers per minute, momentum values).

## Overlay (output)

```json
{
  "overlay_id": "ov_0007",
  "match_id": "m_42",
  "kind": "lower_third",
  "t_start_s": 1843.0,
  "duration_s": 8.0,
  "lang": "en",
  "priority": 5,
  "payload": {
    "headline": "GOAL! Adrian Cole, 31'",
    "body": "A 0.41 xG chance converted ...",
    "team": "home",
    "player_id": "home_9",
    "source": "template"
  }
}
```

Overlay kinds emitted today: `lower_third` (key moments) and `stat_card` (analyst mode only, at 15', 45' and 90', computed from events up to that time). `momentum_bar` and `recap` exist in the schema but are not emitted; the recap is served as text at `/matches/{id}/recap`.

`payload.source` is `llm` when a Foundry model wrote the body and `template` otherwise. In casual mode `payload.body` is empty and no model call is made.

## Versioning
`schema_version: "1.0"` is included in API responses. Breaking changes bump the major version.
