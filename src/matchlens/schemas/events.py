"""Data contracts. See docs/02-EVENT-SCHEMA.md."""
from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

Side = Literal["home", "away"]
SCHEMA_VERSION = "1.0"


class EventType(str, Enum):
    KICKOFF = "kickoff"
    PASS = "pass"
    SHOT = "shot"
    GOAL = "goal"
    TACKLE = "tackle"
    POSSESSION_CHANGE = "possession_change"
    PRESSURE = "pressure"


class Outcome(str, Enum):
    SUCCESS = "success"
    FAIL = "fail"
    GOAL = "goal"
    SAVED = "saved"
    OFF_TARGET = "off_target"
    NONE = "none"


class MatchEvent(BaseModel):
    event_id: int
    match_id: str
    clock_s: float = Field(ge=0, le=6000)
    period: int = Field(ge=1, le=2)
    type: EventType
    team: Side
    player_id: str
    x: float = Field(ge=0, le=100)
    y: float = Field(ge=0, le=100)
    end_x: float | None = Field(default=None, ge=0, le=100)
    end_y: float | None = Field(default=None, ge=0, le=100)
    outcome: Outcome = Outcome.NONE
    ball_speed_kmh: float | None = None
    xg: float | None = Field(default=None, ge=0, le=1)
    pressure_level: float | None = Field(default=None, ge=0, le=1)


class Player(BaseModel):
    player_id: str
    name: str
    team: Side
    position: Literal["GK", "DEF", "MID", "FWD"]
    number: int


class Match(BaseModel):
    match_id: str
    home_name: str
    away_name: str
    players: dict[str, Player]
    events: list[MatchEvent]
    score: dict[str, int]

    def team_name(self, side: Side) -> str:
        return self.home_name if side == "home" else self.away_name


class PassQuality(BaseModel):
    event_id: int
    distance_m: float
    forward_m: float
    difficulty: float
    accurate: bool
    ball_speed_kmh: float | None = None


class TeamStats(BaseModel):
    possession_pct: float
    passes: int
    pass_accuracy_pct: float
    shots: int
    shots_on_target: int
    xg: float
    goals: int
    tackles: int
    avg_pass_difficulty: float


class MatchStats(BaseModel):
    home: TeamStats
    away: TeamStats
    top_shot_speed_kmh: float
    top_shot_player_id: str | None = None


class KeyMoment(BaseModel):
    moment_id: str
    kind: Literal["goal", "big_chance", "momentum_shift"]
    clock_s: float
    team: Side
    player_id: str | None = None
    xg: float | None = None
    momentum_before: float | None = None
    momentum_after: float | None = None


class Explanation(BaseModel):
    moment_id: str
    category: Literal["goal_context", "big_chance", "momentum_shift"]
    priority: int = Field(ge=1, le=5)
    clock_s: float
    team: Side
    player_id: str | None = None
    facts: dict


class ViewerProfile(BaseModel):
    mode: Literal["analyst", "casual"] = "casual"
    lang: Literal["en", "es", "fr"] = "en"
    favourite_team: Side | None = None
    focus_player: str | None = None
    max_overlays: int = Field(default=25, ge=1, le=200)


class Narration(BaseModel):
    moment_id: str
    short: str
    detailed: str
    source: Literal["template", "llm"] = "template"


class Overlay(BaseModel):
    overlay_id: str
    match_id: str
    kind: Literal["lower_third", "stat_card", "momentum_bar", "recap"]
    t_start_s: float
    duration_s: float
    lang: str
    priority: int = 3
    payload: dict
