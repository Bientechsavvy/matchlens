"""Narrator: renders Explanation facts into text (EN/ES/FR templates; LLM optional)."""
from __future__ import annotations

from matchlens.llm.foundry_client import LLMClient, NullClient
from matchlens.schemas.events import Explanation, Narration

T = {
    "en": {
        "goal": "GOAL! {player}, {minute}'",
        "goal_d": "{team_name} score ({score_home}-{score_away}). {xg_txt}{ctx}",
        "big_chance": "Big chance: {player}, {minute}'",
        "big_chance_d": "{team_name} spurn a {xg:.2f} xG chance. Spell of {state_txt} ({tpm} turnovers/min).",
        "momentum_shift": "Momentum swings to {team_name}",
        "momentum_shift_d": "Momentum moved from {mb:+.2f} to {ma:+.2f} in five minutes; {team_name} now dominate.",
        "xg": "A {xg:.2f} xG chance converted. ", "ctx_open": "They open the scoring.",
        "ctx_eq": "They level the match.", "ctx_none": "",
        "control": "control", "chaos": "chaos",
    },
    "es": {
        "goal": "¡GOL! {player}, {minute}'",
        "goal_d": "{team_name} marca ({score_home}-{score_away}). {xg_txt}{ctx}",
        "big_chance": "Gran ocasión: {player}, {minute}'",
        "big_chance_d": "{team_name} desperdicia una ocasión de {xg:.2f} xG. Fase de {state_txt} ({tpm} pérdidas/min).",
        "momentum_shift": "El impulso pasa a {team_name}",
        "momentum_shift_d": "El impulso cambió de {mb:+.2f} a {ma:+.2f} en cinco minutos; {team_name} domina.",
        "xg": "Ocasión de {xg:.2f} xG convertida. ", "ctx_open": "Abren el marcador.",
        "ctx_eq": "Empatan el partido.", "ctx_none": "",
        "control": "control", "chaos": "caos",
    },
    "fr": {
        "goal": "BUT ! {player}, {minute}'",
        "goal_d": "{team_name} marque ({score_home}-{score_away}). {xg_txt}{ctx}",
        "big_chance": "Grosse occasion : {player}, {minute}'",
        "big_chance_d": "{team_name} gâche une occasion de {xg:.2f} xG. Phase de {state_txt} ({tpm} pertes/min).",
        "momentum_shift": "L'élan bascule vers {team_name}",
        "momentum_shift_d": "L'élan est passé de {mb:+.2f} à {ma:+.2f} en cinq minutes ; {team_name} domine.",
        "xg": "Occasion de {xg:.2f} xG convertie. ", "ctx_open": "Ils ouvrent le score.",
        "ctx_eq": "Ils égalisent.", "ctx_none": "",
        "control": "maîtrise", "chaos": "chaos",
    },
}


class Narrator:
    def __init__(self, llm: LLMClient | None = None):
        self.llm = llm or NullClient()

    def narrate(self, ex: Explanation, lang: str = "en", enrich: bool = True) -> Narration:
        t, f = T[lang], ex.facts
        ctx = t["ctx_open"] if f.get("opened_scoring") else t["ctx_eq"] if f.get("equalised") else t["ctx_none"]
        d = dict(f, xg=f.get("xg") or 0.0, xg_txt=t["xg"].format(xg=f.get("xg") or 0.0) if f.get("xg") else "",
                 ctx=ctx, state_txt=t[f["game_state"]], tpm=f["turnovers_per_min"],
                 mb=f.get("momentum_before") or 0.0, ma=f.get("momentum_after") or 0.0)
        short = t[ex.category.replace("goal_context", "goal")].format(**d)
        detailed = t[ex.category.replace("goal_context", "goal") + "_d"].format(**d).strip()
        source = "template"
        enriched = None if not enrich else self.llm.complete(
            f"You are a football commentator. Reply in language '{lang}'. Use ONLY the given facts.",
            f"Facts: {f}\nBase text: {detailed}")
        if enriched:
            detailed, source = enriched, "llm"
        return Narration(moment_id=ex.moment_id, short=short, detailed=detailed, source=source)
